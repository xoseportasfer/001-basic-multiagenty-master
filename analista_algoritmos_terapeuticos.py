import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS ---
search_tool = DuckDuckGoSearchRun()

# --- 2. ESTADO ---
class GuideState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. NODOS DE AGENTES ---

def guide_watcher_node(state: GuideState):
    """Vigila actualizaciones en NICE, NCCN, ESMO o ASCO."""
    drug_context = state["messages"][0].content
    # Buscamos actualizaciones recientes en guías de referencia
    query = f"recent updates clinical guidelines NICE NCCN ESMO {drug_context} 2025 2026"
    results = search_tool.run(query)
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres un Especialista en Asuntos Regulatorios. Tu misión es detectar si ha habido una "
        "actualización en las guías de tratamiento (NICE, NCCN, etc.) para la patología indicada. "
        "Identifica qué fármacos se mencionan y en qué orden de preferencia (Líneas de tratamiento)."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Resultados de búsqueda: {results}")])
    response.name = "guide_watcher"
    return {"messages": [response]}

def algorithm_analyst_node(state: GuideState):
    """Analiza la posición relativa del fármaco (Subida/Bajada)."""
    last_context = state["messages"][-1].content
    # Buscamos el estándar de cuidado anterior para comparar
    query = f"standard of care history for {state['messages'][0].content} previous guidelines"
    history = search_tool.run(query)
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres un Analista de Estrategia Médica. Compara la guía actual con el estándar anterior. "
        "Determina si el fármaco de interés ha: \n"
        "A) Subido (ej. de 2ª línea a 1ª línea).\n"
        "B) Bajado (ej. ahora se prefiere otro competidor).\n"
        "C) Mantenido su posición pero con nuevas restricciones o combinaciones."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Nueva Guía: {last_context}\nHistorial: {history}")])
    response.name = "algorithm_analyst"
    return {"messages": [response]}

def sales_strategist_node(state: GuideState):
    """Genera el 'Sales Pitch' ajustado para el equipo comercial."""
    analysis = state["messages"][-1].content
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres Director Comercial Pharma. Basado en el cambio de la guía, redacta una alerta urgente "
        "para los visitadores médicos (Sales Reps). \n"
        "ESTRUCTURA: \n"
        "1. TITULAR: (Ej: ¡NICE nos posiciona como tratamiento de elección!)\n"
        "2. CAMBIO CLAVE: (Resumen de la guía en 2 frases).\n"
        "3. NUEVO MENSAJE PARA EL MÉDICO: (Qué decir en la visita).\n"
        "4. MANEJO DE OBJECIONES: (Si la guía nos perjudica, ¿cómo defender el producto?)."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Análisis técnico: {analysis}")])
    response.name = "sales_strategist"
    return {"messages": [response]}

# --- 4. LÓGICA DE CONTROL ---

def manager_node(state: GuideState):
    if len(state["messages"]) <= 1: return {"next_agent": "guide_watcher"}
    last_actor = state["messages"][-1].name
    if last_actor == "guide_watcher": return {"next_agent": "algorithm_analyst"}
    if last_actor == "algorithm_analyst": return {"next_agent": "sales_strategist"}
    return {"next_agent": "FINISH"}

workflow = StateGraph(GuideState)
workflow.add_node("manager", manager_node)
workflow.add_node("guide_watcher", guide_watcher_node)
workflow.add_node("algorithm_analyst", algorithm_analyst_node)
workflow.add_node("sales_strategist", sales_strategist_node)

workflow.set_entry_point("manager")
workflow.add_edge("guide_watcher", "manager")
workflow.add_edge("algorithm_analyst", "manager")
workflow.add_edge("sales_strategist", "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "guide_watcher": "guide_watcher",
    "algorithm_analyst": "algorithm_analyst",
    "sales_strategist": "sales_strategist",
    "FINISH": END
})

app = workflow.compile()

if __name__ == "__main__":
    # Ejemplo con un fármaco de alta competición
    inputs_1 = {"messages": [HumanMessage(content="Pembrolizumab en Cáncer de Pulmón")]}
    inputs_2 = {"messages": [HumanMessage(content="Analiza el impacto de la llegada de biosimilares de Bevacizumab en las guías de la ESMO para Cáncer Colorrectal")]}
    inputs = {"messages": [HumanMessage(content="Analiza las últimas recomendaciones del NICE para Terapias CAR-T en Linfoma")]}
    for s in app.stream(inputs, {"recursion_limit": 10}):
        node_name = list(s.keys())[0]
        if node_name != "manager" and node_name != "__end__":
            print(f"\n--- {node_name.upper()} ---")
            print(s[node_name]["messages"][-1].content)
            print("-" * 60)