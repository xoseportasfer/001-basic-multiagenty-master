import os
import functools
import operator
import warnings
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv, find_dotenv

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults

# 1. Configuración
warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())

# LLM: Mistral (Temperatura baja para mantener la calma y profesionalidad en las respuestas)
llm = ChatOllama(model="mistral", temperature=0.2)
tools = [TavilySearchResults(max_results=3)]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Manager de Comunicación (Orquestador de Crisis)
def manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "monitor_de_redes"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Monitoreo -> Detección de Crisis -> Gabinete de Respuesta
    if last_actor == "monitor_de_redes":
        return {"next": "analista_de_sentimiento"}
    if last_actor == "analista_de_sentimiento":
        return {"next": "gabinete_de_crisis"}
    if last_actor == "gabinete_de_crisis":
        return {"next": "FINISH"}
    
    return {"next": "monitor_de_redes"}

# 4. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts de Gestión de Crisis (En Español)
monitor_prompt = (
    "Eres un Monitor de Redes Sociales. Tu misión es rastrear las menciones recientes "
    "sobre la marca o tema indicado. Debes recopilar comentarios, noticias y opiniones "
    "relevantes, identificando quién dice qué y en qué plataforma."
)

analista_sentimiento_prompt = (
    "Eres un Analista de Sentimiento Crítico. Tu tarea es evaluar las menciones "
    "recopiladas y detectar patrones de negatividad. Debes calificar el nivel de "
    "riesgo de crisis en una escala del 1 al 10 y explicar por qué existe (o no) una amenaza."
)

gabinete_crisis_prompt = (
    "Eres un Experto en Gabinete de Crisis y PR. Basándote en el análisis de riesgo, "
    "tu función es redactar 3 propuestas de respuesta inmediata: una para redes sociales, "
    "otra interna para la empresa y un breve borrador de comunicado de prensa. "
    "Mantén siempre un tono profesional, empático y diplomático."
)

# Nodos
monitor_node = create_node(llm, tools, monitor_prompt, "monitor_de_redes")
analista_node = create_node(llm, [], analista_sentimiento_prompt, "analista_de_sentimiento")
gabinete_node = create_node(llm, [], gabinete_crisis_prompt, "gabinete_de_crisis")

# 6. Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", manager_node)
workflow.add_node("monitor_de_redes", monitor_node)
workflow.add_node("analista_de_sentimiento", analista_node)
workflow.add_node("gabinete_de_crisis", gabinete_node)

for node_name in ["monitor_de_redes", "analista_de_sentimiento", "gabinete_de_crisis"]:
    workflow.add_edge(node_name, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "monitor_de_redes": "monitor_de_redes",
        "analista_de_sentimiento": "analista_de_sentimiento",
        "gabinete_de_crisis": "gabinete_de_crisis",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
app_crisis = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    marca_o_evento = "Aeropuerto de Santiago de Compostela tiene crisis de reputación por su cierre de primavera por obras"
    inputs = {"messages": [HumanMessage(content=f"Monitoriza y gestiona la posible crisis de: {marca_o_evento}")]}
    
    print(f"--- ACTIVANDO PROTOCOLO DE CRISIS DIGITAL ---")
    for s in app_crisis.stream(inputs, {"recursion_limit": 25}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)