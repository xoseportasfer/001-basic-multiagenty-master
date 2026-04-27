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

# LLM: Mistral (Excelente para identificar tonos de voz y perfiles)
llm = ChatOllama(model="mistral", temperature=0)
search_tool = [DuckDuckGoSearchRun()]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador de Influencia (Influencer Manager)
def influencer_manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "scout_de_creadores"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Scouting -> Análisis de Engagement -> Redacción de Propuesta
    if last_actor == "scout_de_creadores":
        return {"next": "analista_de_audiencia"}
    if last_actor == "analista_de_audiencia":
        return {"next": "redactor_de_outreach"}
    if last_actor == "redactor_de_outreach":
        return {"next": "FINISH"}
    
    return {"next": "scout_de_creadores"}

# 4. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts Especializados (Marketing de Influencia)

scout_prompt = (
    "Eres un Scout de Influencers Senior. Tu función es usar DuckDuckGo para encontrar "
    "creadores de contenido en el nicho solicitado. Busca en TikTok, Instagram y YouTube. "
    "Identifica nombres, handles y el tipo de contenido que publican (educativo, lifestyle, tech, etc.)."
)

analista_prompt = (
    "Eres un Analista de Datos de Marketing. Tu tarea es investigar (o estimar basándote en datos públicos) "
    "el engagement rate, la calidad de los comentarios y la demografía probable de la audiencia. "
    "Busca señales de autenticidad y descarta perfiles con seguidores falsos o bots."
)

redactor_prompt = (
    "Eres un Copywriter de Outreach. Tu misión es redactar una propuesta de colaboración "
    "irresistible. Debe ser personalizada, mencionar un video o post específico del creador "
    "y explicar por qué los valores de la marca encajan perfectamente con su estilo personal. "
    "Evita los mensajes genéricos; busca una conexión genuina."
)

# Nodos
scout_node = create_node(llm, search_tool, scout_prompt, "scout_de_creadores")
analista_node = create_node(llm, search_tool, analista_prompt, "analista_de_audiencia")
redactor_node = create_node(llm, [], redactor_prompt, "redactor_de_outreach")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", influencer_manager_node)
workflow.add_node("scout_de_creadores", scout_node)
workflow.add_node("analista_de_audiencia", analista_node)
workflow.add_node("redactor_de_outreach", redactor_node)

for node in ["scout_de_creadores", "analista_de_audiencia", "redactor_de_outreach"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "scout_de_creadores": "scout_de_creadores",
        "analista_de_audiencia": "analista_de_audiencia",
        "redactor_de_outreach": "redactor_de_outreach",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
influencer_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    briefing_marca_alternativo = (
        "Marca: Bankinter. Objetivo: Promocionar servicios de gestión de patrimonio y planificación sucesoria. "
        "Nicho: Golf influencers, coleccionistas de relojes/arte o perfiles de 'Lifestyle Luxury' de más de 40 años. "
        "País: España."
    )
    briefing_marca = (
        "Marca: BBVA. Objetivo: Dar a conocer la hipoteca bonificada para menores de 35 años. "
        "Nicho: Creadores de contenido sobre 'Home decor', parejas jóvenes documentando su primera vivienda o expertos inmobiliarios. "
        "País: España."
    )
    
    inputs = {"messages": [HumanMessage(content=f"Busca y contacta influencers para: {briefing_marca}")]}
    
    print(f"--- BUSCADOR DE INFLUENCERS Y COLABORACIONES ---")
    
    for s in influencer_app.stream(inputs, {"recursion_limit": 25}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)