import os
import functools
import operator
import warnings
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv, find_dotenv

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun

# 1. Configuración
warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())

# LLM: Mistral (Ideal para análisis de perfiles y pedagogía)
llm = ChatOllama(model="mistral", temperature=0)
search_tool = [DuckDuckGoSearchRun()]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador de Talento (Talent Strategy Manager)
def talent_manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "auditor_de_habilidades"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Mapeo -> Análisis de Vacantes -> Plan de Formación
    if last_actor == "auditor_de_habilidades":
        return {"next": "analista_de_sucesion"}
    if last_actor == "analista_de_sucesion":
        return {"next": "arquitecto_de_formacion"}
    if last_actor == "arquitecto_de_formacion":
        return {"next": "FINISH"}
    
    return {"next": "auditor_de_habilidades"}

# 4. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts Especializados (HRTech)

auditor_prompt = (
    "Eres un Auditor de Talento. Tu misión es desglosar el perfil del empleado. "
    "Identifica: 1. Habilidades técnicas (Hard Skills), 2. Habilidades interpersonales (Soft Skills) "
    "y 3. Experiencia acumulada. Crea un inventario detallado de competencias actuales."
)

analista_sucesion_prompt = (
    "Eres un Analista de Sucesión. Tu tarea es investigar las competencias requeridas para roles de "
    "liderazgo (ej: CTO, Lead Developer, Manager) en 2026 usando DuckDuckGo. "
    "Compara estas competencias con las del empleado e identifica la 'Brecha de Talento' (Skill Gap)."
)

formacion_prompt = (
    "Eres un Arquitecto de Formación (L&D). Tu misión es diseñar un plan de carrera personalizado "
    "para cerrar la brecha detectada. El plan debe incluir:\n"
    "- Hitos a 6 y 12 meses.\n"
    "- Recomendaciones de certificaciones, mentorías o proyectos internos.\n"
    "- KPIs para medir el progreso del empleado hacia el rol de liderazgo."
)

# Nodos
auditor_node = create_node(llm, [], auditor_prompt, "auditor_de_habilidades")
analista_node = create_node(llm, search_tool, analista_sucesion_prompt, "analista_de_sucesion")
formacion_node = create_node(llm, [], formacion_prompt, "arquitecto_de_formacion")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", talent_manager_node)
workflow.add_node("auditor_de_habilidades", auditor_node)
workflow.add_node("analista_de_sucesion", analista_node)
workflow.add_node("arquitecto_de_formacion", formacion_node)

for node in ["auditor_de_habilidades", "analista_de_sucesion", "arquitecto_de_formacion"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "auditor_de_habilidades": "auditor_de_habilidades",
        "analista_de_sucesion": "analista_de_sucesion",
        "arquitecto_de_formacion": "arquitecto_de_formacion",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
talent_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":

    perfil_empleado = (
    "Empleado: María Fernández. Cargo: Abogada Senior "
    "Experiencia: 22 años en litigación y asesoramiento jurídico en bufetes boutique (5-10 abogados). "
    "Especialidad: Derecho Civil (Obligaciones, Contratos, Familia y Sucesiones). "
    "Habilidades: Estrategia procesal, negociación de alta complejidad, gestión de cartera de clientes, "
    "mentoría de abogados junior y administración de despachos. "
    "Aspiración: En periodo difícil para continuar trabajando de abogada, adaptarse dentro de las oportunidades laborales en España actualmente."
)
    
    inputs = {"messages": [HumanMessage(content=f"Genera un plan de sucesión para: {perfil_empleado}")]}
    
    print(f"--- PLANIFICADOR DE CARRERAS Y SUCESIÓN ---")
    
    for s in talent_app.stream(inputs, {"recursion_limit": 20}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)