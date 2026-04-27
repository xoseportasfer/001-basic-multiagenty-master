import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS DE PROSPECCIÓN ---

@tool
def search_funding_news(sector: str):
    """Busca noticias recientes sobre rondas de inversión, startups financiadas o expansiones."""
    search = DuckDuckGoSearchRun()
    query = f"ronda financiación serie A B C {sector} expansión internacional noticias reciente"
    return search.run(query)

@tool
def find_legal_contact(company_name: str):
    """Busca quién es el responsable legal (CLO, General Counsel) o el CEO de una empresa."""
    search = DuckDuckGoSearchRun()
    query = f"{company_name} 'General Counsel' OR 'Chief Legal Officer' OR 'CEO' LinkedIn"
    return search.run(query)

# --- 2. DEFINICIÓN DEL ESTADO ---
class MAProspectorState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. CONSTRUCTOR DE NODOS (Manual & Robust) ---
def create_agent_node(llm, tools, system_prompt, name):
    llm_with_tools = llm.bind_tools(tools)
    
    def node(state: MAProspectorState):
        # Instrucción de refuerzo para que el agente sea un consultor senior
        instruction = (
            f"\n\n[SISTEMA]: {system_prompt}\n"
            "REGLA: No inventes datos. Si no encuentras el nombre exacto del contacto, "
            "dirígete al 'Responsable Legal' de forma genérica pero profesional."
        )
        
        messages = state["messages"] + [SystemMessage(content=instruction)]
        result = llm_with_tools.invoke(messages)
        result.name = name
        return {"messages": [result]}
    return node

# --- 4. PROMPTS DE LOS AGENTES ---

SIGNAL_DETECTOR_PROMPT = """Eres un Analista de Mercado M&A. Tu tarea es encontrar empresas 
que hayan recibido inversión recientemente o anunciado planes de expansión. Identifica el 
nombre de la empresa y la cuantía o tipo de operación."""

RECRUITER_PROMPT = """Eres un Investigador Corporativo. Una vez identificada la empresa, 
tu objetivo es encontrar quién toma las decisiones legales o el CEO. Busca nombres propios 
o estructuras del departamento legal en LinkedIn a través de los resultados de búsqueda."""

LEGAL_STRATEGIST_PROMPT = """Eres un Abogado Mercantil Senior. Tu tarea es redactar una 
invitación de conexión de LinkedIn altamente personalizada. Enfócate en cómo tu despacho 
puede ayudarles en la 'protección de la inversión' o 'compliance en nuevos mercados' 
tras su reciente éxito financiero. Tono: Ejecutivo, sofisticado y no intrusivo."""

# --- 5. CONFIGURACIÓN DEL GRAFO ---

llm = ChatOllama(model="mistral", temperature=0)

# Nodos
detector_node = create_agent_node(llm, [search_funding_news], SIGNAL_DETECTOR_PROMPT, "signal_detector")
research_node = create_agent_node(llm, [find_legal_contact], RECRUITER_PROMPT, "legal_researcher")
writer_node = create_agent_node(llm, [], LEGAL_STRATEGIST_PROMPT, "outreach_writer")

def manager_node(state: MAProspectorState):
    if not state["messages"] or len(state["messages"]) < 2:
        return {"next_agent": "signal_detector"}
    
    last_actor = state["messages"][-1].name
    
    if last_actor == "signal_detector":
        return {"next_agent": "legal_researcher"}
    if last_actor == "legal_researcher":
        return {"next_agent": "outreach_writer"}
    
    return {"next_agent": "FINISH"}

workflow = StateGraph(MAProspectorState)
workflow.add_node("manager", manager_node)
workflow.add_node("signal_detector", detector_node)
workflow.add_node("legal_researcher", research_node)
workflow.add_node("outreach_writer", writer_node)

workflow.set_entry_point("manager")

for node in ["signal_detector", "legal_researcher", "outreach_writer"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "signal_detector": "signal_detector",
    "legal_researcher": "legal_researcher",
    "outreach_writer": "outreach_writer",
    "FINISH": END
})

app = workflow.compile()

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    sector_objetivo = "Fintech en España"
    inputs = {"messages": [HumanMessage(content=f"Busca oportunidades de M&A en el sector: {sector_objetivo}")]}
    
    for s in app.stream(inputs, {"recursion_limit": 15}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)