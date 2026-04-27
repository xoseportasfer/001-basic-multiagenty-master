import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS DE INTELIGENCIA ESTRATÉGICA ---

@tool
def clinical_trials_monitor(competitor_name: str):
    """Busca ensayos clínicos activos de un competidor en ClinicalTrials.gov y otras bases."""
    search = DuckDuckGoSearchRun()
    # Buscamos fases de ensayos clínicos (Phase II, Phase III) que indican proximidad al mercado
    query = f"site:clinicaltrials.gov '{competitor_name}' Phase 3 clinical trial results"
    return search.run(query)

@tool
def patent_office_search(competitor_name: str):
    """Rastrea solicitudes de patentes recientes y fechas de expiración de fármacos clave."""
    search = DuckDuckGoSearchRun()
    query = f"'{competitor_name}' drug patent expiration dates orange book FDA"
    return search.run(query)

# --- 2. DEFINICIÓN DEL ESTADO ---
class PharmaPipelineState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. CONSTRUCTOR DE NODOS ---
def create_agent_node(llm, tools, system_prompt, name):
    llm_with_tools = llm.bind_tools(tools)
    
    def node(state: PharmaPipelineState):
        instruction = (
            f"\n\n[ROL ACTUAL]: {system_prompt}\n"
            "INSTRUCCIÓN: Aporta datos técnicos específicos (fases de ensayos, años de expiración). "
            "No te limites a generalidades. Si detectas un lanzamiento inminente, subráyalo."
        )
        messages = state["messages"] + [SystemMessage(content=instruction)]
        result = llm_with_tools.invoke(messages)
        result.name = name
        return {"messages": [result]}
    return node

# --- 4. PROMPTS DE LOS AGENTES ---

PIPELINE_AGENT_PROMPT = """Eres un Analista de Ensayos Clínicos. Tu misión es rastrear en qué 
fase se encuentran los fármacos en desarrollo de la competencia. Identifica moléculas en 
Fase 3, ya que son las que representan una amenaza comercial a corto plazo (1-3 años)."""

PATENT_AGENT_PROMPT = """Eres un Especialista en Propiedad Intelectual Farmacéutica. Tu tarea 
es identificar cuándo vencen las patentes de los productos estrella de la competencia o si 
han solicitado extensiones. Esto es clave para predecir la entrada de genéricos."""

STRATEGIC_ANALYST_PROMPT = """Eres el Director de Estrategia Comercial. Cruza la información 
de los agentes anteriores. Genera un reporte de 'Amenaza de Genéricos' y 'Lanzamientos Inminentes'. 
Calcula el riesgo de pérdida de cuota de mercado para nuestra empresa."""

# --- 5. CONFIGURACIÓN DEL GRAFO ---

llm = ChatOllama(model="mistral", temperature=0)

# Nodos
pipeline_node = create_agent_node(llm, [clinical_trials_monitor], PIPELINE_AGENT_PROMPT, "pipeline_analyst")
patent_node = create_agent_node(llm, [patent_office_search], PATENT_AGENT_PROMPT, "patent_expert")
strategy_node = create_agent_node(llm, [], STRATEGIC_ANALYST_PROMPT, "strategic_director")

def manager_node(state: PharmaPipelineState):
    if not state["messages"] or len(state["messages"]) < 2:
        return {"next_agent": "pipeline_analyst"}
    
    last_actor = state["messages"][-1].name
    
    if last_actor == "pipeline_analyst":
        return {"next_agent": "patent_expert"}
    if last_actor == "patent_expert":
        return {"next_agent": "strategic_director"}
    
    return {"next_agent": "FINISH"}

workflow = StateGraph(PharmaPipelineState)
workflow.add_node("manager", manager_node)
workflow.add_node("pipeline_analyst", pipeline_node)
workflow.add_node("patent_expert", patent_node)
workflow.add_node("strategic_director", strategy_node)

workflow.set_entry_point("manager")

for node in ["pipeline_analyst", "patent_expert", "strategic_director"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "pipeline_analyst": "pipeline_analyst",
    "patent_expert": "patent_expert",
    "strategic_director": "strategic_director",
    "FINISH": END
})

app = workflow.compile()

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    competidor = "AstraZeneca"
    inputs = {"messages": [HumanMessage(content=f"Analiza el pipeline y amenazas de patentes para: {competidor}")]}
    
    for s in app.stream(inputs, {"recursion_limit": 15}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 70)