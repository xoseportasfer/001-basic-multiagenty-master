import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. CONFIGURACIÓN DE LA HERRAMIENTA ---
search_tool = DuckDuckGoSearchRun()

# --- 2. ESTADO ---
class TenderState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. NODOS CON DATOS REALES ---

def tender_scout_node(state: TenderState):
    """Agente que busca licitaciones REALES usando DuckDuckGo."""
    user_input = state["messages"][0].content
    # Realizamos la búsqueda real fuera del LLM para asegurar datos frescos
    query = f"licitación pública hospitalaria España suministros medicamentos {user_input} 2024 2025"
    search_results = search_tool.run(query)
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres un Especialista en Mercados Públicos. Basado en los RESULTADOS DE BÚSQUEDA REALES que te proporciono, "
        "identifica y resume las licitaciones vigentes. Si no hay licitaciones claras, "
        "indica que no se encontraron procesos abiertos hoy."
    ))
    
    # Le pasamos los resultados de la búsqueda al LLM para que los procese
    response = llm.invoke([prompt, HumanMessage(content=f"RESULTADOS DE INTERNET: {search_results}")])
    response.name = "tender_scout"
    return {"messages": [response]}

def pricing_analyst_node(state: TenderState):
    """Analiza precios buscando en el histórico de adjudicaciones reales."""
    last_context = state["messages"][-1].content
    # Buscamos precios históricos reales
    query = f"precio adjudicación licitación medicamentos suministros históricos España"
    price_data = search_tool.run(query)
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres Analista de Precios. Basado en el contexto de licitaciones y estos DATOS DE PRECIOS REALES de internet, "
        "propón una estrategia de puja. No inventes, usa las referencias encontradas."
    ))
    
    response = llm.invoke([prompt, HumanMessage(content=f"DATOS DE PRECIOS: {price_data}\n\nCONTEXTO: {last_context}")])
    response.name = "pricing_analyst"
    return {"messages": [response]}

def proposal_writer_node(state: TenderState):
    """Redacta la propuesta final usando los datos reales de los nodos anteriores."""
    llm = ChatOllama(model="mistral", temperature=0)
    context = state["messages"][-1].content
    
    prompt = SystemMessage(content=(
        "Eres Redactor Técnico. Genera la propuesta final profesional. "
        "USA EXCLUSIVAMENTE los nombres de hospitales y precios reales obtenidos por los agentes previos. "
        "Estructura el documento para presentación oficial."
    ))
    
    response = llm.invoke([prompt, HumanMessage(content=f"Contexto acumulado: {context}")])
    response.name = "proposal_writer"
    return {"messages": [response]}

# --- 4. LÓGICA DEL GRAFO (Igual que antes) ---

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
    # Prueba con un grupo real como 'Pembrolizumab' o 'Inmunoglobulinas'
    #inputs = {"messages": [HumanMessage(content="Suministro de Inmunoglobulinas hospitalarias")]}
    inputs = {"messages": [HumanMessage(content="Suministro de Pembrolizumab y Nivolumab para servicios de oncología hospitalaria")]}
    for s in app.stream(inputs, {"recursion_limit": 10}):
        node_name = list(s.keys())[0]
        if node_name != "manager" and node_name != "__end__":
            print(f"\n--- {node_name.upper()} ---")
            print(s[node_name]["messages"][-1].content)
            print("-" * 50)