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

# LLM: Mistral (Excelente para juicio ético y análisis de reputación)
llm = ChatOllama(model="mistral", temperature=0)
search_tool = [DuckDuckGoSearchRun()]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador de Ética (Ethics Compliance Manager)
def ethics_manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "rastreador_proveedores"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Rastreo General -> Detección de Denuncias -> Score de Riesgo
    if last_actor == "rastreador_proveedores":
        return {"next": "analista_de_denuncias"}
    if last_actor == "analista_de_denuncias":
        return {"next": "evaluador_score_etico"}
    if last_actor == "evaluador_score_etico":
        return {"next": "FINISH"}
    
    return {"next": "rastreador_proveedores"}

# 4. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts Especializados (ESG & Suministro)

rastreador_prompt = (
    "Eres un Especialista en Inteligencia de Suministros. Tu tarea es usar DuckDuckGo para buscar noticias "
    "recientes (2025-2026) sobre los proveedores mencionados. Identifica su ubicación, volumen de "
    "operaciones y cualquier cambio reciente en su estructura corporativa o fábricas."
)

analista_denuncias_prompt = (
    "Eres un Investigador de Derechos Humanos y Medio Ambiente. Tu misión es buscar específicamente "
    "denuncias, reportes de ONGs (como Amnesty o Greenpeace), multas ambientales o menciones a "
    "malas prácticas laborales (trabajo infantil, jornadas excesivas, falta de seguridad) vinculadas "
    "a los proveedores. Sé extremadamente crítico con la información encontrada."
)

evaluador_prompt = (
    "Eres un Auditor de Riesgos ESG. Basándote en la información recolectada, debes emitir un "
    "'Score de Riesgo Ético' del 1 al 100 (donde 100 es riesgo máximo/ético inaceptable). "
    "Justifica el score desglosándolo en: 1. Impacto Ambiental, 2. Derechos Laborales y "
    "3. Transparencia. Sugiere si la empresa debe mantener, auditar o romper la relación con el proveedor."
)

# Nodos
rastreador_node = create_node(llm, search_tool, rastreador_prompt, "rastreador_proveedores")
analista_node = create_node(llm, search_tool, analista_denuncias_prompt, "analista_de_denuncias")
evaluador_node = create_node(llm, [], evaluador_prompt, "evaluador_score_etico")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", ethics_manager_node)
workflow.add_node("rastreador_proveedores", rastreador_node)
workflow.add_node("analista_de_denuncias", analista_node)
workflow.add_node("evaluador_score_etico", evaluador_node)

for node in ["rastreador_proveedores", "analista_de_denuncias", "evaluador_score_etico"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "rastreador_proveedores": "rastreador_proveedores",
        "analista_de_denuncias": "analista_de_denuncias",
        "evaluador_score_etico": "evaluador_score_etico",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
ethics_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    lista_proveedores_alternativa = (
        "Proveedores a auditar: 1. Shein (Logística y manufactura), "
        "2. Foxconn (Ensamblaje de electrónica), 3. Ganfeng Lithium (Minería de litio)."
    )

    lista_proveedores = (
        "Proveedores a auditar: 1. WuXi AppTec (Ensayos clínicos tercerizados), "
        "2. Bayer (Uso de pesticidas y biodiversidad), 3. Pfizer (Transparencia en precios y acceso en países en desarrollo)."
    )
    
    inputs = {"messages": [HumanMessage(content=f"Realiza una auditoría ética de estos proveedores: {lista_proveedores}")]}
    
    print(f"--- AUDITOR DE ÉTICA EN LA CADENA DE SUMINISTRO ---")
    
    for s in ethics_app.stream(inputs, {"recursion_limit": 30}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)