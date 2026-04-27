import operator
import json
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTA ---
@tool
def pubmed_recent_search(pathology: str):
    """Rastrea publicaciones recientes en PubMed."""
    search = DuckDuckGoSearchRun()
    query = f"site:pubmed.ncbi.nlm.nih.gov {pathology} clinical trial 2024 2025"
    return search.run(query)

# --- 2. ESTADO ---
class MedicalCuratorState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. NODOS REFORMATEADOS ---

def literature_scout_node(state: MedicalCuratorState):
    llm = ChatOllama(model="mistral", temperature=0).bind_tools([pubmed_recent_search])
    prompt = SystemMessage(content=(
        "Eres un Documentalista. Tu ÚNICA función es listar 3-5 estudios recientes. "
        "Para cada estudio indica: TÍTULO, REVISTA y LINK. No analices nada aún."
    ))
    # Solo enviamos el mensaje inicial para evitar ruido
    response = llm.invoke([prompt] + [state["messages"][0]])
    response.name = "literature_scout"
    return {"messages": [response]}

def insight_extractor_node(state: MedicalCuratorState):
    llm = ChatOllama(model="mistral", temperature=0)
    # Recuperamos lo que dijo el scout
    last_msg = state["messages"][-1].content
    
    prompt = SystemMessage(content=(
        "Eres un Analista de Datos Clínicos. Tu objetivo es convertir la lista anterior en un RESUMEN TÉCNICO. "
        "FORMATO OBLIGATORIO: \n"
        "- Hallazgo clave: (1 frase)\n"
        "- Dato numérico relevante: (ej. p-value, % de reducción)\n"
        "- Implicación clínica: (¿Qué significa para el médico?)\n"
        "PROHIBIDO: No repitas la lista original. Transfórmala en un análisis de impacto."
    ))
    
    response = llm.invoke([prompt, HumanMessage(content=f"Analiza estos datos: {last_msg}")])
    response.name = "insight_extractor"
    return {"messages": [response]}

def newsletter_editor_node(state: MedicalCuratorState):
    llm = ChatOllama(model="mistral", temperature=0)
    # Recuperamos el análisis técnico
    analysis = state["messages"][-1].content
    
    prompt = SystemMessage(content=(
        "Eres Editor de Newsletters Médicas. Tu misión es crear un boletín ELEGANTE y EJECUTIVO. "
        "Usa emojis, negritas y una estructura de 'Flash Informativo'. "
        "Crea un título atractivo y una sección de 'Sabías que...' basada en el análisis anterior. "
        "NO LISTES LOS ESTUDIOS, redacta una narrativa para el delegado médico."
    ))
    
    response = llm.invoke([prompt, HumanMessage(content=f"Redacta el boletín final basado en: {analysis}")])
    response.name = "newsletter_editor"
    return {"messages": [response]}

# --- 4. LÓGICA DE CONTROL ---

def manager_node(state: MedicalCuratorState):
    if len(state["messages"]) <= 1: return {"next_agent": "literature_scout"}
    last_actor = state["messages"][-1].name
    if last_actor == "literature_scout": return {"next_agent": "insight_extractor"}
    if last_actor == "insight_extractor": return {"next_agent": "newsletter_editor"}
    return {"next_agent": "FINISH"}

# --- 5. CONSTRUCCIÓN DEL GRAFO ---

workflow = StateGraph(MedicalCuratorState)
workflow.add_node("manager", manager_node)
workflow.add_node("literature_scout", literature_scout_node)
workflow.add_node("insight_extractor", insight_extractor_node)
workflow.add_node("newsletter_editor", newsletter_editor_node)

workflow.set_entry_point("manager")
workflow.add_edge("literature_scout", "manager")
workflow.add_edge("insight_extractor", "manager")
workflow.add_edge("newsletter_editor", "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "literature_scout": "literature_scout",
    "insight_extractor": "insight_extractor",
    "newsletter_editor": "newsletter_editor",
    "FINISH": END
})

app = workflow.compile()

# --- 6. PRUEBA ---
if __name__ == "__main__":
    inputs = {"messages": [HumanMessage(content="Patología: Hipercolesterolemia Familiar")]}
    for s in app.stream(inputs, {"recursion_limit": 10}):
        node_name = list(s.keys())[0]
        if node_name != "manager" and node_name != "__end__":
            print(f"\n--- {node_name.upper()} ---")
            print(s[node_name]["messages"][-1].content)