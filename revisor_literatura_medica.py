import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS DE VIGILANCIA CIENTÍFICA ---

@tool
def pubmed_recent_search(pathology: str):
    """Rastrea las publicaciones más recientes de los últimos 7 días en PubMed y journals médicos."""
    search = DuckDuckGoSearchRun()
    # Forzamos la búsqueda de estudios recientes y significativos
    query = f"site:pubmed.ncbi.nlm.nih.gov {pathology} 'last 7 days' clinical trial OR meta-analysis"
    return search.run(query)

# --- 2. DEFINICIÓN DEL ESTADO ---
class MedicalCuratorState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. CONSTRUCTOR DE NODOS ---
def create_agent_node(llm, tools, system_prompt, name):
    llm_with_tools = llm.bind_tools(tools)
    
    def node(state: MedicalCuratorState):
        instruction = (
            f"\n\n[ROL ACTUAL]: {system_prompt}\n"
            "INSTRUCCIÓN: Filtra el ruido. Céntrate en cambios en guías clínicas, "
            "nuevos datos de eficacia o alertas de seguridad. Si el estudio es pequeño o poco relevante, descártalo."
        )
        messages = state["messages"] + [SystemMessage(content=instruction)]
        result = llm_with_tools.invoke(messages)
        result.name = name
        return {"messages": [result]}
    return node

# --- 4. PROMPTS DE LOS AGENTES (Flujo MSL) ---

LITERATURE_SCOUT_PROMPT = """Eres un Documentalista Científico. Tu misión es localizar los 
estudios más recientes y de mayor impacto (Ensayos Fase III, Meta-análisis) publicados en la 
última semana sobre la patología indicada. Identifica el título y el DOI o link."""

INSIGHT_EXTRACTOR_PROMPT = """Eres un Analista de Datos Clínicos. Tu tarea es leer los resultados 
encontrados y extraer los 'Key Insights': ¿Qué cambia este estudio respecto a lo que ya sabíamos? 
Extrae datos numéricos (p-value, HR, reducción de riesgo) y la conclusión principal."""

NEWSLETTER_EDITOR_PROMPT = """Eres un Editor de Publicaciones Médicas para MSLs. Tu objetivo es 
redactar un boletín semanal técnico, conciso y elegante. Usa una estructura de: 
1. Titular impactante, 2. Resumen ejecutivo, 3. Relevancia para el MSL (qué decir en la próxima visita médica)."""

# --- 5. CONFIGURACIÓN DEL GRAFO ---

llm = ChatOllama(model="mistral", temperature=0)

# Nodos
scout_node = create_agent_node(llm, [pubmed_recent_search], LITERATURE_SCOUT_PROMPT, "literature_scout")
insight_node = create_agent_node(llm, [], INSIGHT_EXTRACTOR_PROMPT, "insight_extractor")
editor_node = create_agent_node(llm, [], NEWSLETTER_EDITOR_PROMPT, "newsletter_editor")

def manager_node(state: MedicalCuratorState):
    if not state["messages"] or len(state["messages"]) < 2:
        return {"next_agent": "literature_scout"}
    
    last_actor = state["messages"][-1].name
    
    if last_actor == "literature_scout":
        return {"next_agent": "insight_extractor"}
    if last_actor == "insight_extractor":
        return {"next_agent": "newsletter_editor"}
    
    return {"next_agent": "FINISH"}

workflow = StateGraph(MedicalCuratorState)
workflow.add_node("manager", manager_node)
workflow.add_node("literature_scout", scout_node)
workflow.add_node("insight_extractor", insight_node)
workflow.add_node("newsletter_editor", editor_node)

workflow.set_entry_point("manager")

for node in ["literature_scout", "insight_extractor", "newsletter_editor"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "literature_scout": "literature_scout",
    "insight_extractor": "insight_extractor",
    "newsletter_editor": "newsletter_editor",
    "FINISH": END
})

app = workflow.compile()

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    #patologia = "Mieloma Múltiple Refractario"
    patologia = "Hipercolesterolemia Familiar con riesgo cardiovascular persistente"
    inputs = {"messages": [HumanMessage(content=f"Genera el boletín de novedades científicas para: {patologia}")]}
    
    for s in app.stream(inputs, {"recursion_limit": 15}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)