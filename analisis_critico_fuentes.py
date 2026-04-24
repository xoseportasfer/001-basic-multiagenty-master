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

# LLM: Mistral (enfocado en precisión técnica)
llm = ChatOllama(model="mistral", temperature=0)
# Herramienta de búsqueda (configurada para devolver más resultados para comparar)
tools = [TavilySearchResults(max_results=3)]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. El Manager de Auditoría (Orquestador Crítico)
def manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "analista_fuentes"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Análisis Crítico -> Síntesis de Contenido -> Verificación Final
    if last_actor == "analista_fuentes":
        return {"next": "sintetizador_contenidos"}
    if last_actor == "sintetizador_contenidos":
        return {"next": "verificador_hechos"}
    if last_actor == "verificador_hechos":
        return {"next": "FINISH"}
    
    return {"next": "analista_fuentes"}

# 4. Función para crear Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Configuración de los Agentes Críticos
analista_prompt = (
    "Eres un Analista Crítico de Fuentes. Tu misión es investigar el tema solicitado "
    "comparando múltiples resultados de búsqueda. Debes descartar fuentes dudosas o "
    "contradictorias y seleccionar solo aquellas con autoridad técnica o académica. "
    "Entrega un reporte de fuentes validadas y destaca los puntos de consenso."
)

sintetizador_prompt = (
    "Eres un Sintetizador de Contenidos. Tu tarea es tomar el análisis de fuentes y "
    "redactar un informe técnico coherente. Debes organizar la información de forma "
    "jerárquica, eliminando redundancias y asegurando un tono objetivo y profesional."
)

verificador_prompt = (
    "Eres un Verificador de Hechos (Fact-Checker). Revisa el informe final en busca de "
    "posibles sesgos o afirmaciones sin sustento. Tu salida debe ser el informe final "
    "con un sello de validación o correcciones finales si detectas inconsistencias."
)

# Creación de nodos
analista_node = create_node(llm, tools, analista_prompt, "analista_fuentes")
sintetizador_node = create_node(llm, [], sintetizador_prompt, "sintetizador_contenidos")
verificador_node = create_node(llm, [], verificador_prompt, "verificador_hechos")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", manager_node)
workflow.add_node("analista_fuentes", analista_node)
workflow.add_node("sintetizador_contenidos", sintetizador_node)
workflow.add_node("verificador_hechos", verificador_node)

# Conexiones
for node_name in ["analista_fuentes", "sintetizador_contenidos", "verificador_hechos"]:
    workflow.add_edge(node_name, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "analista_fuentes": "analista_fuentes",
        "sintetizador_contenidos": "sintetizador_contenidos",
        "verificador_hechos": "verificador_hechos",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
analista_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    tema = "Impacto de la computación cuántica en la criptografía actual"
    inputs = {"messages": [HumanMessage(content=f"Realiza un análisis crítico sobre: {tema}")]}
    
    print(f"--- Iniciando Analista de Fuentes y Contenidos ---")
    print(f"Objetivo: Verificación y contraste de información técnica.\n" + "="*60)
    
    for s in analista_app.stream(inputs, {"recursion_limit": 20}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                content = s[node_name]["messages"][-1].content
                print(content)
                print("-" * 60)