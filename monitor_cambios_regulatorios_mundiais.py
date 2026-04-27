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

# LLM: Mistral (Fuerte en análisis lógico y síntesis de textos legales)
llm = ChatOllama(model="mistral", temperature=0)
search_tool = [DuckDuckGoSearchRun()]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador de Cumplimiento (Compliance Manager)
def compliance_manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "vigilante_legal"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Vigilancia -> Análisis de Impacto -> Alertas Departamentales
    if last_actor == "vigilante_legal":
        return {"next": "analista_de_impacto"}
    if last_actor == "analista_de_impacto":
        return {"next": "comunicador_de_alertas"}
    if last_actor == "comunicador_de_alertas":
        return {"next": "FINISH"}
    
    return {"next": "vigilante_legal"}

# 4. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts Especializados (Legal & Compliance)

vigilante_prompt = (
    "Eres un Vigilante Legal Internacional. Tu función es usar DuckDuckGo para buscar "
    "cambios recientes (año 2026) en regulaciones mundiales. Enfócate en leyes de privacidad (GDPR), "
    "normativas de IA, leyes laborales o impuestos digitales en las jurisdicciones solicitadas."
)

analista_impacto_prompt = (
    "Eres un Analista de Riesgo Operativo. Tu tarea es recibir las nuevas leyes y determinar "
    "cómo chocan con la operativa de una empresa multinacional. Identifica qué procesos internos "
    "deben cambiar y el nivel de urgencia (Crítico, Alto, Medio)."
)

comunicador_prompt = (
    "Eres un Oficial de Comunicaciones de Compliance. Tu misión es redactar alertas específicas "
    "para cada departamento afectado (IT, RRHH, Legal, Finanzas). Cada alerta debe ser breve y "
    "contener: 1. La norma cambiante, 2. La acción inmediata requerida y 3. El plazo estimado de cumplimiento."
)

# Nodos
vigilante_node = create_node(llm, search_tool, vigilante_prompt, "vigilante_legal")
analista_node = create_node(llm, [], analista_impacto_prompt, "analista_de_impacto")
comunicador_node = create_node(llm, [], comunicador_prompt, "comunicador_de_alertas")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", compliance_manager_node)
workflow.add_node("vigilante_legal", vigilante_node)
workflow.add_node("analista_de_impacto", analista_node)
workflow.add_node("comunicador_de_alertas", comunicador_node)

for node in ["vigilante_legal", "analista_de_impacto", "comunicador_de_alertas"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "vigilante_legal": "vigilante_legal",
        "analista_de_impacto": "analista_de_impacto",
        "comunicador_de_alertas": "comunicador_de_alertas",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
compliance_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":

    contexto_empresa = (
    "Empresa: Iberdrola S.A. Operaciones principales en: España, Reino Unido (ScottishPower), "
    "EE.UU. (Avangrid), Brasil (Neoenergia), México y Alemania. "
    "Sector: Energía Eléctrica, Energías Renovables (Eólica y Fotovoltaica), "
    "Redes Inteligentes y Almacenamiento de Hidrógeno Verde."
)
    
    inputs = {"messages": [HumanMessage(content=f"Monitoriza cambios regulatorios para: {contexto_empresa}")]}
    
    print(f"--- MONITOR DE CAMBIOS REGULATORIOS MUNDIALES ---")
    
    for s in compliance_app.stream(inputs, {"recursion_limit": 25}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)