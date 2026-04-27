import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS DE VIGILANCIA CIENTÍFICA ---
search_tool = DuckDuckGoSearchRun()

# --- 2. ESTADO DEL GRAFO ---
class BiomarkerState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. NODOS DE AGENTES ESPECIALIZADOS ---

def omics_scout_node(state: BiomarkerState):
    """Rastrea estudios de alto rendimiento (NGS, espectrometría de masas)."""
    pathology = state["messages"][0].content
    # Buscamos estudios recientes de expresión diferencial
    query = f"recent proteomics genomics studies differential expression {pathology} 2024 2025"
    results = search_tool.run(query)
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres un Bioinformático experto en Ómicas. Tu misión es identificar genes, "
        "proteínas o metabolitos que aparezcan sobreexpresados o mutados en los estudios recientes. "
        "Lista los candidatos con mayor significación estadística (p-values bajos)."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Datos de búsqueda para {pathology}: {results}")])
    response.name = "omics_scout"
    return {"messages": [response]}

def clinical_correlator_node(state: BiomarkerState):
    """Evalúa si el biomarcador se correlaciona con la progresión o pronóstico."""
    candidates = state["messages"][-1].content
    pathology = state["messages"][0].content
    
    # Buscamos si esos candidatos tienen valor pronóstico (curvas Kaplan-Meier, etc.)
    query = f"prognostic value clinical correlation survival analysis {pathology} markers"
    results = search_tool.run(query)
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres un Patólogo Molecular. Analiza la lista de candidatos y verifica si "
        "existe evidencia de que su presencia se correlaciona con la agresividad de la "
        "enfermedad, la supervivencia del paciente o la respuesta al tratamiento."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Candidatos: {candidates}\nEvidencia clínica: {results}")])
    response.name = "clinical_correlator"
    return {"messages": [response]}

def rd_alert_node(state: BiomarkerState):
    """Genera la alerta estratégica para el equipo de I+D."""
    llm = ChatOllama(model="mistral", temperature=0)
    final_analysis = state["messages"][-1].content
    
    prompt = SystemMessage(content=(
        "Eres el Director de Diagnóstico de Precisión. Tu objetivo es emitir una ALERTA DE BIOMARCADOR. "
        "ESTRUCTURA DEL REPORTE: \n"
        "1. BIOMARCADOR IDENTIFICADO (Gen/Proteína)\n"
        "2. MECANISMO BIOLÓGICO (Por qué es relevante)\n"
        "3. APLICACIÓN COMERCIAL (¿Test de diagnóstico rápido? ¿Selección de pacientes para ensayos?)\n"
        "4. NIVEL DE PRIORIDAD (Baja, Media, Alta)."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Análisis final: {final_analysis}")])
    response.name = "rd_advisor"
    return {"messages": [response]}

# --- 4. LÓGICA DE CONTROL ---

def manager_node(state: BiomarkerState):
    if len(state["messages"]) <= 1: return {"next_agent": "omics_scout"}
    last_actor = state["messages"][-1].name
    if last_actor == "omics_scout": return {"next_agent": "clinical_correlator"}
    if last_actor == "clinical_correlator": return {"next_agent": "rd_advisor"}
    return {"next_agent": "FINISH"}

workflow = StateGraph(BiomarkerState)
workflow.add_node("manager", manager_node)
workflow.add_node("omics_scout", omics_scout_node)
workflow.add_node("clinical_correlator", clinical_correlator_node)
workflow.add_node("rd_advisor", rd_alert_node)

workflow.set_entry_point("manager")
workflow.add_edge("omics_scout", "manager")
workflow.add_edge("clinical_correlator", "manager")
workflow.add_edge("rd_advisor", "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "omics_scout": "omics_scout",
    "clinical_correlator": "clinical_correlator",
    "rd_advisor": "rd_advisor",
    "FINISH": END
})

app = workflow.compile()

if __name__ == "__main__":
    # Ejemplo con una patología compleja donde se buscan biomarcadores
    inputs_1 = {"messages": [HumanMessage(content="Cáncer de Páncreas (Adenocarcinoma)")]}
    inputs_2 = {"messages": [HumanMessage(content="Glioblastoma Multiforme (Biomarcadores de microambiente tumoral e inmunoterapia)")]}
    inputs = {"messages": [HumanMessage(content="MASH/NASH (Biomarcadores no invasivos de fibrosis hepática y resolución de esteatosis)")]}
    for s in app.stream(inputs, {"recursion_limit": 10}):
        node_name = list(s.keys())[0]
        if node_name != "manager" and node_name != "__end__":
            print(f"\n--- {node_name.upper()} ---")
            print(s[node_name]["messages"][-1].content)
            print("-" * 50)