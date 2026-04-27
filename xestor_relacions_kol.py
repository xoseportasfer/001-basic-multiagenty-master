import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS DE PROSPECCIÓN CIENTÍFICA ---

@tool
def search_scientific_publications(doctor_name: str):
    """Busca artículos en PubMed, ResearchGate o Google Scholar del médico especificado."""
    search = DuckDuckGoSearchRun()
    # Buscamos publicaciones recientes para medir actividad actual
    query = f"site:pubmed.ncbi.nlm.nih.gov '{doctor_name}' recent publications research"
    return search.run(query)

@tool
def search_congress_activity(doctor_name: str):
    """Rastrea la participación del médico en congresos, simposios o como ponente (Speaker)."""
    search = DuckDuckGoSearchRun()
    query = f"'{doctor_name}' speaker congress presentation symposium 2024 2025"
    return search.run(query)

# --- 2. DEFINICIÓN DEL ESTADO ---
class KOLRelationshipState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. CONSTRUCTOR DE NODOS (Arquitectura Anti-Repetición) ---
def create_agent_node(llm, tools, system_prompt, name):
    llm_with_tools = llm.bind_tools(tools)
    
    def node(state: KOLRelationshipState):
        instruction = (
            f"\n\n[ROL ACTUAL]: {system_prompt}\n"
            "INSTRUCCIÓN: Aporta nombres de revistas, títulos de estudios o nombres de congresos. "
            "Evita repetir lo que otros agentes hayan listado. Si no hay datos, indica 'Baja visibilidad'."
        )
        messages = state["messages"] + [SystemMessage(content=instruction)]
        result = llm_with_tools.invoke(messages)
        result.name = name
        return {"messages": [result]}
    return node

# --- 4. PROMPTS DE ESPECIALIDAD (MSL) ---

SCIENTIFIC_SCOUT_PROMPT = """Eres un Analista de Literatura Biomédica. Tu misión es identificar 
la producción científica reciente de un experto. Busca temas recurrentes, número de citas (si es posible) 
y si el experto actúa como autor principal (First Author) en áreas de interés terapéutico."""

CONGRESS_ANALYST_PROMPT = """Eres un Gestor de Eventos Médicos. Tu tarea es analizar la influencia 
pública del experto. ¿Es un ponente habitual en congresos internacionales? ¿Lidera grupos de trabajo 
en sociedades médicas? Su visibilidad en eventos determina su capacidad de influencia."""

STRATEGIC_MSL_PROMPT = """Eres un Medical Science Liaison (MSL) Senior. Tu misión es evaluar 
la afinidad del KOL con nuestra nueva línea de investigación. Sugiere si es el candidato ideal 
para liderar un estudio clínico o ser 'Advisory Board member' basándote en su rigor científico 
y su red de influencia actual."""

# --- 5. CONFIGURACIÓN DEL GRAFO ---

llm = ChatOllama(model="mistral", temperature=0)

# Nodos
scout_node = create_agent_node(llm, [search_scientific_publications], SCIENTIFIC_SCOUT_PROMPT, "scientific_scout")
congress_node = create_agent_node(llm, [search_congress_activity], CONGRESS_ANALYST_PROMPT, "congress_analyst")
msl_node = create_agent_node(llm, [], STRATEGIC_MSL_PROMPT, "msl_strategist")

def manager_node(state: KOLRelationshipState):
    if not state["messages"] or len(state["messages"]) < 2:
        return {"next_agent": "scientific_scout"}
    
    last_actor = state["messages"][-1].name
    
    if last_actor == "scientific_scout":
        return {"next_agent": "congress_analyst"}
    if last_actor == "congress_analyst":
        return {"next_agent": "msl_strategist"}
    
    return {"next_agent": "FINISH"}

workflow = StateGraph(KOLRelationshipState)
workflow.add_node("manager", manager_node)
workflow.add_node("scientific_scout", scout_node)
workflow.add_node("congress_analyst", congress_node)
workflow.add_node("msl_strategist", msl_node)

workflow.set_entry_point("manager")

for node in ["scientific_scout", "congress_analyst", "msl_strategist"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "scientific_scout": "scientific_scout",
    "congress_analyst": "congress_analyst",
    "msl_strategist": "msl_strategist",
    "FINISH": END
})

app = workflow.compile()

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    nombre_experto = "Dr. Antoni Castells" # Ejemplo de KOL en Gastroenterología
    #area_estudio = "Oncología Colorrectal"
    area_estudio = "Agonistas del Receptor GLP-1 en Diabetes y Obesidad"
    inputs = {"messages": [HumanMessage(content=f"Evalúa al KOL {nombre_experto} para liderar un estudio en {area_estudio}")]}    
    
    for s in app.stream(inputs, {"recursion_limit": 15}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 70)