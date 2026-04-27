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

# 1. Configuración
warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())

# LLM: Mistral (Excelente para análisis crítico y estructuración de negocios)
llm = ChatOllama(model="mistral", temperature=0)

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador de Inversión (Investment Manager)
def investment_manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "analista_de_deck"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Análisis de Deck -> Crítica de VC -> Narrativa Financiera
    if last_actor == "analista_de_deck":
        return {"next": "vc_critico"}
    if last_actor == "vc_critico":
        return {"next": "estratega_narrativo"}
    if last_actor == "estratega_narrativo":
        return {"next": "FINISH"}
    
    return {"next": "analista_de_deck"}

# 4. Constructor de Nodos
def create_node(llm, system_prompt, name):
    # En este caso no usamos herramientas externas para mantener el foco en el razonamiento del LLM
    agent = create_react_agent(llm, tools=[], prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts Especializados (Startups & VC)

analista_deck_prompt = (
    "Eres un Consultor de Startups experto. Tu tarea es analizar el Pitch Deck proporcionado. "
    "Extrae y resume: Problema, Solución, Tamaño de Mercado (TAM/SAM/SOM), Modelo de Negocio "
    "y Tracción actual. Identifica si la propuesta es clara o si hay lagunas de información."
)

vc_critico_prompt = (
    "Eres un Venture Capitalist de Nivel 1 (Tier 1 VC). Tu tono es escéptico y directo. "
    "Tu misión es encontrar fallos en la tesis de inversión. Haz preguntas difíciles sobre: "
    "barreras de entrada (moats), escalabilidad, unidad económica (LTV/CAC) y por qué este "
    "equipo es el adecuado. No seas amable; sé riguroso."
)

estratega_narrativo_prompt = (
    "Eres un Lead Technical Writer y Estratega Financiero. Tu tarea es recibir las críticas del VC "
    "y sugerir mejoras en la narrativa. Reformula los puntos débiles, sugiere cómo presentar los "
    "números para que sean más atractivos y diseña un 'storytelling' financiero que mitigue "
    "los riesgos percibidos por el inversor."
)

# Nodos
analista_node = create_node(llm, analista_deck_prompt, "analista_de_deck")
vc_node = create_node(llm, vc_critico_prompt, "vc_critico")
estratega_node = create_node(llm, estratega_narrativo_prompt, "estratega_narrativo")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", investment_manager_node)
workflow.add_node("analista_de_deck", analista_node)
workflow.add_node("vc_critico", vc_node)
workflow.add_node("estratega_narrativo", estratega_node)

for node in ["analista_de_deck", "vc_critico", "estratega_narrativo"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "analista_de_deck": "analista_de_deck",
        "vc_critico": "vc_critico",
        "estratega_narrativo": "estratega_narrativo",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
pitch_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    pitch_deck_contenido = (
    "Proyecto: HydroCrop. Solución: Sistemas de riego inteligente basados en IA que reducen el uso de agua en un 60%. "
    "Mercado: 2M de explotaciones agrícolas tecnificables. Tracción: Instalaciones en 10 viñedos de gran escala. "
    "Modelo: Venta directa + mantenimiento anual. Equipo: Agrónomos e ingenieros de IoT."
)
    
    inputs = {"messages": [HumanMessage(content=f"Revisa este Pitch Deck: {pitch_deck_contenido}")]}
    
    print(f"--- CONSULTOR DE PREPARACIÓN PARA INVERSIONES (PITCH DECK REVIEWER) ---")
    
    for s in pitch_app.stream(inputs, {"recursion_limit": 20}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)