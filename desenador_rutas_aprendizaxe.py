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

llm = ChatOllama(model="mistral", temperature=0.2)
search_tool = [TavilySearchResults(max_results=5)]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador de Aprendizaje (CORREGIDO)
def manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "evaluador_de_nivel"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Sincronización de nombres de nodos
    if last_actor == "evaluador_de_nivel":
        return {"next": "analista_fuentes_conocimiento"} # <--- CAMBIO CLAVE
    if last_actor == "analista_fuentes_conocimiento": # <--- CAMBIO CLAVE
        return {"next": "disenador_instruccional"}
    if last_actor == "disenador_instruccional":
        return {"next": "FINISH"}
    
    return {"next": "evaluador_de_nivel"}

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
evaluador_prompt = (
    "Eres un Evaluador Académico. Tu función es analizar el mensaje inicial del usuario para "
    "determinar su nivel de conocimiento. Resume el 'Perfil del Estudiante'."
)

analista_fuentes_conocimiento_prompt = (
    "Eres un Analista de Fuentes de Conocimiento. Tu misión es buscar los mejores recursos GRATUITOS. "
    "Prioriza documentación oficial y tutoriales de alta calidad."
)

disenador_prompt = (
    "Eres un Diseñador Instruccional Senior. Organiza los recursos en un Plan de Estudios por semanas "
    "con hitos de evaluación claros."
)

# Nodos (Asegurando que el 'name' coincida con el Manager)
evaluador_node = create_node(llm, [], evaluador_prompt, "evaluador_de_nivel")
analista_fuentes_conocimiento_node = create_node(llm, search_tool, analista_fuentes_conocimiento_prompt, "analista_fuentes_conocimiento")
disenador_node = create_node(llm, [], disenador_prompt, "disenador_instruccional")

# 6. Construcción del Grafo (CORREGIDO)
workflow = StateGraph(AgentState)

workflow.add_node("manager", manager_node)
workflow.add_node("evaluador_de_nivel", evaluador_node)
workflow.add_node("analista_fuentes_conocimiento", analista_fuentes_conocimiento_node)
workflow.add_node("disenador_instruccional", disenador_node)

for node in ["evaluador_de_nivel", "analista_fuentes_conocimiento", "disenador_instruccional"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "evaluador_de_nivel": "evaluador_de_nivel",
        "analista_fuentes_conocimiento": "analista_fuentes_conocimiento", # <--- COINCIDENCIA EXACTA
        "disenador_instruccional": "disenador_instruccional",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
edtech_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    tema_estudio = "Quiero aprender Django, ya sé Python pero no entiendo la gestión de memoria."
    inputs = {"messages": [HumanMessage(content=f"Crea una ruta de aprendizaje para: {tema_estudio}")]}
    
    print(f"--- Optimizador de Aprendizaje Autónomo (EdTech) ---")
    print(f"Objetivo: {tema_estudio}\n" + "="*50)
    
    for s in edtech_app.stream(inputs, {"recursion_limit": 25}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)