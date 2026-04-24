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

# Usamos Mistral vía Ollama
llm = ChatOllama(model="mistral", temperature=0)
tools = [TavilySearchResults(max_results=2)]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. El Manager Educativo (Orquestador de Activos)
def manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "gestor_activos"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo lógico: Gestión -> Estructuración -> Evaluación
    if last_actor == "gestor_activos":
        return {"next": "agente_pedagogico"}
    if last_actor == "agente_pedagogico":
        return {"next": "agente_evaluador"}
    if last_actor == "agente_evaluador":
        return {"next": "FINISH"}
    
    return {"next": "gestor_activos"}

# 4. Función para crear Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Configuración de los Especialistas
gestor_prompt = (
    "Eres un Gestor de Activos Educativos. Tu misión es identificar, filtrar y extraer "
    "los recursos de conocimiento más valiosos (fuentes académicas, videos, artículos) "
    "sobre el tema solicitado. Tu objetivo es suministrar materia prima de alta calidad "
    "debidamente verificada."
)

pedagogico_prompt = (
    "Eres un Agente Pedagógico. Tu tarea es tomar los activos educativos gestionados "
    "y estructurarlos en un Plan de Estudios organizado por niveles de dificultad: "
    "Principiante, Intermedio y Avanzado. Define objetivos de aprendizaje claros."
)

evaluador_prompt = (
    "Eres un Agente de Evaluación. Basándote en el plan de estudios creado, genera "
    "un cuestionario interactivo de 5 preguntas con opciones múltiples y la "
    "explicación de cada respuesta para validar la adquisición de conocimientos."
)

# Creamos los nodos con los nuevos nombres
gestor_node = create_node(llm, tools, gestor_prompt, "gestor_activos")
pedagogico_node = create_node(llm, [], pedagogico_prompt, "agente_pedagogico")
evaluador_node = create_node(llm, [], evaluador_prompt, "agente_evaluador")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", manager_node)
workflow.add_node("gestor_activos", gestor_node)
workflow.add_node("agente_pedagogico", pedagogico_node)
workflow.add_node("agente_evaluador", evaluador_node)

# Enlaces de retorno al manager
for node_name in ["gestor_activos", "agente_pedagogico", "agente_evaluador"]:
    workflow.add_edge(node_name, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "gestor_activos": "gestor_activos",
        "agente_pedagogico": "agente_pedagogico",
        "agente_evaluador": "agente_evaluador",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
edtech_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    tema = "Computación Cuántica para principiantes"
    inputs = {"messages": [HumanMessage(content=f"Genera una estructura educativa completa sobre: {tema}")]}
    
    print(f"--- Iniciando Sistema de Gestión de Activos Educativos ---")
    print(f"Tema: {tema}\n" + "="*50)
    
    for s in edtech_app.stream(inputs, {"recursion_limit": 20}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[ACTUANDO]: {node_name.upper()}")
                content = s[node_name]["messages"][-1].content
                print(content)
                print("-" * 50)