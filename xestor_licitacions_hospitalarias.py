import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS DE LICITACIÓN ---

@tool
def search_hospital_tenders(medication_group: str):
    """Busca licitaciones activas en plataformas de contratación para grupos de medicamentos."""
    search = DuckDuckGoSearchRun()
    # Buscamos en la plataforma de contratación del sector público (España como ejemplo)
    query = f"site:contrataciondelestado.es licitación suministro medicamentos {medication_group} hospital"
    return search.run(query)

@tool
def analyze_historical_prices(tender_id: str):
    """Busca adjudicaciones previas para estimar el precio de mercado y la competencia."""
    search = DuckDuckGoSearchRun()
    query = f"formalización contrato suministro medicamentos adjudicación {tender_id} precio unitario"
    return search.run(query)

# --- 2. DEFINICIÓN DEL ESTADO ---
class TenderState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. NODOS DE AGENTES ---

def tender_scout_node(state: TenderState):
    llm = ChatOllama(model="mistral", temperature=0).bind_tools([search_hospital_tenders])
    prompt = SystemMessage(content=(
        "Eres un Especialista en Mercados Públicos. Tu función es identificar licitaciones "
        "abiertas, extrayendo: Hospital, Presupuesto Base y Fecha Límite de presentación."
    ))
    response = llm.invoke([prompt] + [state["messages"][0]])
    response.name = "tender_scout"
    return {"messages": [response]}

def pricing_analyst_node(state: TenderState):
    llm = ChatOllama(model="mistral", temperature=0).bind_tools([analyze_historical_prices])
    last_msg = state["messages"][-1].content
    prompt = SystemMessage(content=(
        "Eres un Analista de Precios (Market Access). Basado en la licitación encontrada, "
        "investiga precios de adjudicación anteriores. Tu objetivo es sugerir un precio "
        "competitivo que maximice el margen sin quedar fuera por precio excesivo."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Analiza precios para: {last_msg}")])
    response.name = "pricing_analyst"
    return {"messages": [response]}

def proposal_writer_node(state: TenderState):
    llm = ChatOllama(model="mistral", temperature=0)
    context = state["messages"][-1].content
    prompt = SystemMessage(content=(
        "Eres un Redactor de Licitaciones Técnicas. Debes redactar la propuesta técnica. "
        "FORMATO OBLIGATORIO: \n"
        "1. RESUMEN DE LA OFERTA: (Enfoque en calidad y logística)\n"
        "2. CUMPLIMIENTO DE PLIEGOS: (Menciona certificaciones GMP, ISO y cadena de frío)\n"
        "3. VALOR AÑADIDO: (Programas de soporte al paciente o sostenibilidad)\n"
        "4. PRECIO SUGERIDO: (Basado en el análisis previo)."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Genera propuesta basada en: {context}")])
    response.name = "proposal_writer"
    return {"messages": [response]}

# --- 4. GRAFO Y LÓGICA ---

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

# --- 5. EJECUCIÓN ---
if __name__ == "__main__":
    inputs = {"messages": [HumanMessage(content="Grupo terapéutico: Inmunosupresores para trasplante renal")]}
    for s in app.stream(inputs, {"recursion_limit": 10}):
        node_name = list(s.keys())[0]
        if node_name != "manager" and node_name != "__end__":
            print(f"\n--- {node_name.upper()} ---")
            print(s[node_name]["messages"][-1].content)