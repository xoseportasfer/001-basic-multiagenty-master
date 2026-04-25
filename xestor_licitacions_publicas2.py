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
# --- CAMBIO DE LIBRERÍA ---
from langchain_community.tools import DuckDuckGoSearchRun

# 1. Configuración
warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())

llm = ChatOllama(model="mistral", temperature=0)

# 2. Definición de la herramienta gratuita
# DuckDuckGo no necesita API KEY
search_tool = [DuckDuckGoSearchRun()]

# 3. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 4. Orquestador (Manager) - Se mantiene igual
def manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "rastreador_licitaciones"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    if last_actor == "rastreador_licitaciones":
        return {"next": "analista_requisitos_tecnicos"}
    if last_actor == "analista_requisitos_tecnicos":
        return {"next": "evaluador_viabilidad_comercial"}
    if last_actor == "evaluador_viabilidad_comercial":
        return {"next": "FINISH"}
    
    return {"next": "rastreador_licitaciones"}

# 5. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 6. Prompts (Ajustado para DuckDuckGo)
rastreador_prompt = (
    "Eres un experto en búsqueda de licitaciones. Usa DuckDuckGo para encontrar concursos "
    "públicos en España. Sé muy específico buscando en 'contrataciondelestado.es' o 'boe.es'. "
    "Extrae el nombre de la licitación, el organismo y el presupuesto si está disponible."
)

# ... (El resto de prompts se mantienen igual)
analista_prompt = "Eres un Analista de Pliegos Técnicos. Extrae requisitos obligatorios y solvencia técnica."
evaluador_prompt = "Eres un Evaluador de Viabilidad. Genera un informe Go/No-Go basado en los datos encontrados."

# Nodos
rastreador_node = create_node(llm, search_tool, rastreador_prompt, "rastreador_licitaciones")
analista_node = create_node(llm, search_tool, analista_prompt, "analista_requisitos_tecnicos")
evaluador_node = create_node(llm, [], evaluador_prompt, "evaluador_viabilidad_comercial")

# 7. Grafo (Idéntico al anterior)
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

# 8. Ejecución
if __name__ == "__main__":
    sector_interes = "Licitaciones de Smart Cities y movilidad eléctrica en España"
    inputs = {"messages": [HumanMessage(content=f"Busca y analiza licitaciones para: {sector_interes}")]}
    
    print(f"--- Ejecutando con DuckDuckGo (Free) ---")
    
    for s in tender_app.stream(inputs, {"recursion_limit": 25}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)