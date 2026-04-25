
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

# LLM: Mistral (Excelente para análisis de requisitos y lógica)
llm = ChatOllama(model="mistral", temperature=0)
search_tool = [TavilySearchResults(max_results=6)]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador de Licitaciones (Tender Manager)
def manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "rastreador_licitaciones"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Rastreo -> Extracción de Requisitos -> Evaluación de Viabilidad
    if last_actor == "rastreador_licitaciones":
        return {"next": "analista_requisitos_tecnicos"}
    if last_actor == "analista_requisitos_tecnicos":
        return {"next": "evaluador_viabilidad_comercial"}
    if last_actor == "evaluador_viabilidad_comercial":
        return {"next": "FINISH"}
    
    return {"next": "rastreador_licitaciones"}

# 4. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts Especializados (Contexto B2G)
rastreador_prompt = (
    "Eres un Rastreador de Licitaciones Públicas. Tu tarea es buscar concursos públicos activos "
    "en boletines oficiales (como el BOE o plataformas de contratación) para el sector indicado. "
    "Identifica el objeto del contrato, el presupuesto base de licitación y la fecha límite de presentación."
)

analista_prompt = (
    "Eres un Analista de Pliegos Técnicos. Tu misión es desglosar la 'letra pequeña' de la licitación. "
    "Extrae: 1. Requisitos técnicos obligatorios, 2. Certificaciones ISO necesarias, "
    "3. Solvencia económica mínima y 4. Experiencia previa exigida (número de proyectos similares)."
)

evaluador_prompt = (
    "Eres un Evaluador de Viabilidad Comercial. Basándote en los requisitos extraídos y el perfil de "
    "nuestra empresa (asume que somos una empresa mediana de tecnología con 10 años de experiencia), "
    "determina si es viable presentarse. Genera un informe 'Go/No-Go' con los puntos fuertes y "
    "los riesgos detectados (bloqueos por certificaciones faltantes o presupuesto ajustado)."
)

# Nodos
rastreador_node = create_node(llm, search_tool, rastreador_prompt, "rastreador_licitaciones")
analista_node = create_node(llm, search_tool, analista_prompt, "analista_requisitos_tecnicos")
evaluador_node = create_node(llm, [], evaluador_prompt, "evaluador_viabilidad_comercial")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", manager_node)
workflow.add_node("rastreador_licitaciones", rastreador_node)
workflow.add_node("analista_requisitos_tecnicos", analista_node)
workflow.add_node("evaluador_viabilidad_comercial", evaluador_node)

for node in ["rastreador_licitaciones", "analista_requisitos_tecnicos", "evaluador_viabilidad_comercial"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "rastreador_licitaciones": "rastreador_licitaciones",
        "analista_requisitos_tecnicos": "analista_requisitos_tecnicos",
        "evaluador_viabilidad_comercial": "evaluador_viabilidad_comercial",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
tender_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    #sector_interes = "Servicios de ciberseguridad y auditoría de redes para administraciones públicas en España"
    sector_interes = "Licitaciones de sistemas inteligentes de gestión de tráfico, plataformas de ciudad inteligente (Smart Cities) y flotas de transporte público eléctrico en España."
    inputs = {"messages": [HumanMessage(content=f"Busca y analiza licitaciones para: {sector_interes}")]}
    
    print(f"--- Sistema Inteligente de Licitaciones B2G ---")
    print(f"Sector objetivo: {sector_interes}\n" + "="*50)
    
    for s in tender_app.stream(inputs, {"recursion_limit": 25}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)