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

# LLM: Mistral (Precisión en terminología legal y técnica)
llm = ChatOllama(model="mistral", temperature=0)
search_tool = [TavilySearchResults(max_results=5)]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador de Propiedad Intelectual
def manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "ingeniero_de_patentes"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Refinar Idea -> Buscar Antecedentes -> Redactar Borrador
    if last_actor == "ingeniero_de_patentes":
        return {"next": "investigador_prior_art"}
    if last_actor == "investigador_prior_art":
        return {"next": "redactor_legal_tecnico"}
    if last_actor == "redactor_legal_tecnico":
        return {"next": "FINISH"}
    
    return {"next": "ingeniero_de_patentes"}

# 4. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts Especializados (Alta Responsabilidad)
ingeniero_prompt = (
    "Eres un Ingeniero de Patentes. Tu tarea es tomar la idea inicial del usuario y "
    "convertirla en una descripción técnica detallada. Define el campo de la invención, "
    "el problema que resuelve y las novedades técnicas de la solución propuesta."
)

investigador_prompt = (
    "Eres un Investigador de Prior Art. Tu misión es buscar patentes existentes, "
    "publicaciones científicas y productos comerciales similares a la invención descrita. "
    "Debes identificar posibles conflictos de infracción o falta de novedad. "
    "Sé extremadamente exhaustivo en tus búsquedas."
)

redactor_prompt = (
    "Eres un Especialista en Redacción de Patentes. Basándote en la descripción y la investigación, "
    "redacta un borrador formal. Incluye: Título, Resumen, Descripción de la Invención y, "
    "lo más importante, un conjunto inicial de Reivindicaciones (Claims) que definan el alcance legal."
)

# Nodos
ingeniero_node = create_node(llm, [], ingeniero_prompt, "ingeniero_de_patentes")
investigador_node = create_node(llm, search_tool, investigador_prompt, "investigador_prior_art")
redactor_node = create_node(llm, [], redactor_prompt, "redactor_legal_tecnico")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", manager_node)
workflow.add_node("ingeniero_de_patentes", ingeniero_node)
workflow.add_node("investigador_prior_art", investigador_node)
workflow.add_node("redactor_legal_tecnico", redactor_node)

for node in ["ingeniero_de_patentes", "investigador_prior_art", "redactor_legal_tecnico"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "ingeniero_de_patentes": "ingeniero_de_patentes",
        "investigador_prior_art": "investigador_prior_art",
        "redactor_legal_tecnico": "redactor_legal_tecnico",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
patent_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    idea_invencion = "Un sistema de propulsión para drones que utiliza campos electromagnéticos para reducir el ruido de las hélices en un 80%."
    inputs = {"messages": [HumanMessage(content=f"Analiza la viabilidad y redacta borrador de patente para: {idea_invencion}")]}
    
    print(f"--- Sistema Autónomo de Análisis de Patentes ---")
    print(f"Invención: {idea_invencion}\n" + "="*50)
    
    for s in patent_app.stream(inputs, {"recursion_limit": 25}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)