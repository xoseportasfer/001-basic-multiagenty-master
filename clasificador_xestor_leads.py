import os
import functools
import operator
import warnings
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv, find_dotenv

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults

# 1. Configuración
warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())

# LLM: Mistral (Excelente para análisis y tono persuasivo)
llm = ChatOllama(model="mistral", temperature=0.3) # Un poco de temperatura para el copy
search_tool = [TavilySearchResults(max_results=3)]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador de Ventas (CRM Manager)
def manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "investigador_prospectos"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Investigación -> Scoring -> Redacción de Email
    if last_actor == "investigador_prospectos":
        return {"next": "agente_scoring"}
    if last_actor == "agente_scoring":
        return {"next": "copywriter_ventas"}
    if last_actor == "copywriter_ventas":
        return {"next": "FINISH"}
    
    return {"next": "investigador_prospectos"}

# 4. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts Especializados (Enfoque en ROI y Persuasión)
investigador_prompt = (
    "Eres un Especialista en Inteligencia Comercial. Tu misión es investigar a fondo al prospecto "
    "usando las herramientas de búsqueda. Identifica su cargo actual, empresa, hitos recientes "
    "(premios, posts, cambios de trabajo) y áreas de interés profesional. "
    "Genera un resumen detallado del perfil."
)

scoring_prompt = (
    "Eres un Analista de Estrategia de Ventas. Tu tarea es evaluar el perfil del prospecto frente a nuestro "
    "Producto: 'Soluciones de Ciberseguridad para Empresas Tech'. "
    "Calcula un Score del 1 al 100 basado en: relevancia del cargo (decisor vs influenciador) "
    "y necesidad potencial. Justifica tu puntuación brevemente."
)

copywriter_prompt = (
    "Eres un Copywriter de Ventas de alto nivel. Redacta un correo electrónico de contacto frío "
    "que NO parezca un bot. Utiliza los hitos encontrados por el investigador para romper el hielo "
    "y vincula el producto con un problema que el prospecto pueda tener. "
    "El tono debe ser profesional, breve y con una llamada a la acción (CTA) clara."
)

# Nodos
investigador_node = create_node(llm, search_tool, investigador_prompt, "investigador_prospectos")
scoring_node = create_node(llm, [], scoring_prompt, "agente_scoring")
copywriter_node = create_node(llm, [], copywriter_prompt, "copywriter_ventas")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", manager_node)
workflow.add_node("investigador_prospectos", investigador_node)
workflow.add_node("agente_scoring", scoring_node)
workflow.add_node("copywriter_ventas", copywriter_node)

for node in ["investigador_prospectos", "agente_scoring", "copywriter_ventas"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "investigador_prospectos": "investigador_prospectos",
        "agente_scoring": "agente_scoring",
        "copywriter_ventas": "copywriter_ventas",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
sales_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    prospecto = "Satya Nadella, CEO de Microsoft" # Ejemplo de prueba
    inputs = {"messages": [HumanMessage(content=f"Investiga y contacta a este lead: {prospecto}")]}
    
    print(f"--- Sistema Inteligente de Prospección B2B ---")
    print(f"Lead: {prospecto}\n" + "="*50)
    
    for s in sales_app.stream(inputs, {"recursion_limit": 20}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)