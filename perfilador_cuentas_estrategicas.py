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

# LLM: Mistral (Excelente para síntesis de negocios y estrategia)
llm = ChatOllama(model="mistral", temperature=0)
search_tool = [DuckDuckGoSearchRun()]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador de Estrategia ABM (ABM Manager)
def abm_manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "investigador_financiero"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Noticias -> Identificación de Retos -> Match de Producto (Altia)
    if last_actor == "investigador_financiero":
        return {"next": "analista_de_retos"}
    if last_actor == "analista_de_retos":
        return {"next": "estratega_de_ventas_altia"}
    if last_actor == "estratega_de_ventas_altia":
        return {"next": "FINISH"}
    
    return {"next": "investigador_financiero"}

# 4. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts Especializados (Sector TIC & Retail)

investigador_prompt = (
    "Eres un Investigador de Mercado. Tu tarea es usar DuckDuckGo para encontrar noticias financieras "
    "recientes (2026) sobre INDITEX. Busca: resultados trimestrales, planes de expansión, "
    "inversiones en sostenibilidad y cualquier mención a retos logísticos o tecnológicos."
)

analista_retos_prompt = (
    "Eres un Consultor Estratégico. Basándote en las noticias encontradas, identifica los 3 retos "
    "principales que enfrenta INDITEX actualmente. Estos retos pueden ser: optimización de última milla, "
    "trazabilidad de la cadena de suministro, ciberseguridad en e-commerce o digitalización de tiendas físicas."
)

estratega_altia_prompt = (
    "Eres el Director de Ventas Estratégicas de ALTIA. Tu misión es hacer el 'match'. "
    "Propón cómo los servicios de ALTIA (Consultoría tecnológica, Managed Services, Ciberseguridad, "
    "Desarrollo de Software a medida o Soluciones Data & IA) resuelven los retos detectados en Inditex. "
    "Redacta una propuesta de valor de 'guante blanco' dirigida a un directivo de IT de Inditex."
)

# Nodos
investigador_node = create_node(llm, search_tool, investigador_prompt, "investigador_financiero")
analista_node = create_node(llm, [], analista_retos_prompt, "analista_de_retos")
estratega_node = create_node(llm, [], estratega_altia_prompt, "estratega_de_ventas_altia")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", abm_manager_node)
workflow.add_node("investigador_financiero", investigador_node)
workflow.add_node("analista_de_retos", analista_node)
workflow.add_node("estratega_de_ventas_altia", estratega_node)

for node in ["investigador_financiero", "analista_de_retos", "estratega_de_ventas_altia"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "investigador_financiero": "investigador_financiero",
        "analista_de_retos": "analista_de_retos",
        "estratega_de_ventas_altia": "estratega_de_ventas_altia",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
abm_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    contexto_abm = (
        "Empresa Objetivo: INDITEX (Zara, Pull&Bear, etc.). "
        "Empresa que ofrece servicios: ALTIA (Consultora TIC, servicios gestionados, Data/IA)."
    )
    
    inputs = {"messages": [HumanMessage(content=f"Realiza un perfilado estratégico para: {contexto_abm}")]}
    
    print(f"--- PERFILADOR DE CUENTAS ESTRATÉGICAS (ABM): ALTIA -> INDITEX ---")
    
    for s in abm_app.stream(inputs, {"recursion_limit": 25}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)