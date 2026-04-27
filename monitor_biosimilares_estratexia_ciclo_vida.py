import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. CONFIGURACIÓN DE HERRAMIENTAS ---
search_tool = DuckDuckGoSearchRun()

# --- 2. ESTADO DEL GRAFO ---
class EvergreeningState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. NODOS DE LOS AGENTES ---

def competitive_scout_node(state: EvergreeningState):
    """Busca competidores desarrollando biosimilares en pipelines públicos."""
    drug_name = state["messages"][0].content
    query = f"biosimilar pipeline development {drug_name} competitors clinical trials 2025 2026"
    results = search_tool.run(query)
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres un Analista de Inteligencia Competitiva. Tu objetivo es identificar qué empresas "
        "están desarrollando versiones biosimilares del fármaco mencionado. "
        "Reporta el nombre de la empresa y la fase de desarrollo (Fase I, III, etc.)."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Resultados de búsqueda: {results}")])
    response.name = "competitive_scout"
    return {"messages": [response]}

def patent_analyst_node(state: EvergreeningState):
    """Analiza la 'jungla de patentes' y busca huecos de protección."""
    drug_name = state["messages"][0].content
    prev_info = state["messages"][-1].content
    query = f"{drug_name} secondary patents formulation dosage subcutaneous delivery expiration"
    results = search_tool.run(query)
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres un Abogado de Patentes Farmacéuticas. Analiza las patentes secundarias existentes "
        "del fármaco original (formulaciones, combinaciones, pautas de dosis). "
        "Identifica cuándo caduca la última capa de protección y si hay amenazas inmediatas."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Fármaco: {drug_name}\nDatos patentes: {results}")])
    response.name = "patent_analyst"
    return {"messages": [response]}

def lifecycle_strategist_node(state: EvergreeningState):
    """Propone mejoras (Evergreening) para retener a los pacientes."""
    llm = ChatOllama(model="mistral", temperature=0)
    context = state["messages"][-1].content
    
    prompt = SystemMessage(content=(
        "Eres el Director de Estrategia de Ciclo de Vida (LCM). Tu misión es proponer una táctica "
        "de 'Evergreening' para neutralizar a los biosimilares. \n"
        "ESTRATEGIA SUGERIDA: \n"
        "1. CAMBIO DE FORMULACIÓN (Ej: de Intravenoso a Subcutáneo).\n"
        "2. NUEVA COMBINACIÓN (FDC - Fixed Dose Combination).\n"
        "3. DISPOSITIVO PROPIETARIO (Ej: Autoinyector inteligente).\n"
        "4. JUSTIFICACIÓN COMERCIAL (Por qué el paciente/médico se quedará con nosotros)."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Contexto competitivo y legal: {context}")])
    response.name = "lcm_director"
    return {"messages": [response]}

# --- 4. LÓGICA DE CONTROL ---

def manager_node(state: EvergreeningState):
    if len(state["messages"]) <= 1: return {"next_agent": "competitive_scout"}
    last_actor = state["messages"][-1].name
    if last_actor == "competitive_scout": return {"next_agent": "patent_analyst"}
    if last_actor == "patent_analyst": return {"next_agent": "lcm_director"}
    return {"next_agent": "FINISH"}

workflow = StateGraph(EvergreeningState)
workflow.add_node("manager", manager_node)
workflow.add_node("competitive_scout", competitive_scout_node)
workflow.add_node("patent_analyst", patent_analyst_node)
workflow.add_node("lcm_director", lifecycle_strategist_node)

workflow.set_entry_point("manager")
workflow.add_edge("competitive_scout", "manager")
workflow.add_edge("patent_analyst", "manager")
workflow.add_edge("lcm_director", "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "competitive_scout": "competitive_scout",
    "patent_analyst": "patent_analyst",
    "lcm_director": "lcm_director",
    "FINISH": END
})

app = workflow.compile()

if __name__ == "__main__":
    # Humira (Adalimumab) es el caso de estudio perfecto para biosimilares
    inputs_1 = {"messages": [HumanMessage(content="Humira (Adalimumab)")]}
    inputs_2 = {"messages": [HumanMessage(content="Dupilumab (Estrategia de expansión de indicaciones y protección de mercado pediátrico)")]}
    inputs = {"messages": [HumanMessage(content="Daratumumab (Transición de IV a SC y patentes de co-formulación con hialuronidasa)")]}
    for s in app.stream(inputs, {"recursion_limit": 10}):
        node_name = list(s.keys())[0]
        if node_name != "manager" and node_name != "__end__":
            print(f"\n--- {node_name.upper()} ---")
            print(s[node_name]["messages"][-1].content)
            print("-" * 60)