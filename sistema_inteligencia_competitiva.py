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
from langchain_community.tools.tavily_search import TavilySearchResults

# 1. Configuración
warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())

# LLM: Mistral (Excelente para síntesis estratégica)
llm = ChatOllama(model="mistral", temperature=0)
search_tool = [TavilySearchResults(max_results=4)]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador de Inteligencia de Mercado
def manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "rastreador_mercado"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Rastreo -> Análisis de Precios -> Matriz DAFO
    if last_actor == "rastreador_mercado":
        return {"next": "analista_precios"}
    if last_actor == "analista_precios":
        return {"next": "consultor_estrategico"}
    if last_actor == "consultor_estrategico":
        return {"next": "FINISH"}
    
    return {"next": "rastreador_mercado"}

# 4. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts Especializados
rastreador_prompt = (
    "Eres un Analista de Inteligencia de Mercado. Tu misión es rastrear los últimos lanzamientos de "
    "productos, actualizaciones y noticias relevantes de los competidores indicados. "
    "Filtra la información para obtener solo movimientos significativos en el mercado."
)

precios_prompt = (
    "Eres un Especialista en Pricing. Tu tarea es investigar y desglosar la estructura de precios, "
    "niveles de suscripción y modelos de monetización de la competencia. "
    "Identifica descuentos, paquetes (bundling) y propuestas de valor asociadas al precio."
)

consultor_prompt = (
    "Eres un Consultor Estratégico. Con la información recopilada sobre lanzamientos y precios, "
    "debes generar una Matriz DAFO (Debilidades, Amenazas, Fortalezas y Oportunidades). "
    "Tu análisis debe ser accionable para el equipo directivo."
)

# Nodos
rastreador_node = create_node(llm, search_tool, rastreador_prompt, "rastreador_mercado")
precios_node = create_node(llm, search_tool, precios_prompt, "analista_precios")
consultor_node = create_node(llm, [], consultor_prompt, "consultor_estrategico")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", manager_node)
workflow.add_node("rastreador_mercado", rastreador_node)
workflow.add_node("analista_precios", precios_node)
workflow.add_node("consultor_estrategico", consultor_node)

for node in ["rastreador_mercado", "analista_precios", "consultor_estrategico"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "rastreador_mercado": "rastreador_mercado",
        "analista_precios": "analista_precios",
        "consultor_estrategico": "consultor_estrategico",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
market_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    competidor = "Inditex (ZARA) vs Shein"
    inputs = {"messages": [HumanMessage(content=f"Analiza la competencia actual entre: {competidor}")]}
    
    print(f"--- Sistema de Inteligencia Competitiva Automática ---")
    print(f"Objetivo: {competidor}\n" + "="*50)
    
    for s in market_app.stream(inputs, {"recursion_limit": 25}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)