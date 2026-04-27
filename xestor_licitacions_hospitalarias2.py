import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS ---
@tool
def search_hospital_tenders(medication_group: str):
    """Busca licitaciones activas."""
    search = DuckDuckGoSearchRun()
    return search.run(f"licitación hospitalaria {medication_group}")

# --- 2. ESTADO ---
class TenderState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. NODOS CORREGIDOS (Manejan la falta de respuesta de herramientas) ---

def tender_scout_node(state: TenderState):
    llm = ChatOllama(model="mistral", temperature=0)
    # Si la herramienta no devuelve texto, forzamos al modelo a darnos una respuesta textual
    prompt = SystemMessage(content=(
        "Eres un Especialista en Mercados Públicos. BUSCA Y LISTA 3 licitaciones ficticias "
        "pero realistas de hospitales españoles para el grupo terapéutico solicitado. "
        "Incluye: Hospital, Presupuesto y ID de licitación."
    ))
    # Importante: No bindeamos herramientas aquí para el prototipo si queremos ver texto directo
    response = llm.invoke([prompt] + [state["messages"][0]])
    response.name = "tender_scout"
    return {"messages": [response]}

def pricing_analyst_node(state: TenderState):
    llm = ChatOllama(model="mistral", temperature=0)
    # Recuperamos el input del scout
    last_context = state["messages"][-1].content
    
    prompt = SystemMessage(content=(
        "Eres Analista de Precios. Basado en las licitaciones anteriores, "
        "INVENTA un historial de adjudicación (ej. 'Año pasado se ganó a 45€/unidad'). "
        "Propón un precio de oferta un 5% menor."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Contexto: {last_context}")])
    response.name = "pricing_analyst"
    return {"messages": [response]}

def proposal_writer_node(state: TenderState):
    llm = ChatOllama(model="mistral", temperature=0)
    # Recuperamos el análisis de precios
    pricing_context = state["messages"][-1].content
    
    prompt = SystemMessage(content=(
        "Eres Redactor Técnico. Crea la propuesta final. "
        "USA LOS DATOS DE PRECIO Y HOSPITAL que te ha dado el analista. "
        "No uses 'X dólares', usa las cifras reales mencionadas anteriormente."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Datos: {pricing_context}")])
    response.name = "proposal_writer"
    return {"messages": [response]}

# --- 4. LÓGICA DE CONTROL (Sin cambios) ---

def manager_node(state: TenderState):
    if len(state["messages"]) <= 1: return {"next_agent": "tender_scout"}
    last_actor = state["messages"][-1].name
    if last_actor == "tender_scout": return {"next_agent": "pricing_analyst"}
    if last_actor == "pricing_analyst": return {"next_agent": "proposal_writer"}
    return {"next_agent": "FINISH"}

workflow = StateGraph(TenderState)
workflow.add_node("manager", manager_node)
workflow.add_node("tender_scout", tender_scout_node)
workflow.add_node("pricing_analyst", pricing_analyst_node)
workflow.add_node("proposal_writer", proposal_writer_node)

workflow.set_entry_point("manager")
workflow.add_edge("tender_scout", "manager")
workflow.add_edge("pricing_analyst", "manager")
workflow.add_edge("proposal_writer", "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "tender_scout": "tender_scout",
    "pricing_analyst": "pricing_analyst",
    "proposal_writer": "proposal_writer",
    "FINISH": END
})

app = workflow.compile()

if __name__ == "__main__":
    inputs = {"messages": [HumanMessage(content="Grupo: Inmunosupresores")]}
    for s in app.stream(inputs, {"recursion_limit": 10}):
        node_name = list(s.keys())[0]
        if node_name != "manager" and node_name != "__end__":
            print(f"\n--- {node_name.upper()} ---")
            print(s[node_name]["messages"][-1].content)