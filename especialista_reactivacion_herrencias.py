import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS DE INVESTIGACIÓN PATRIMONIAL ---

@tool
def search_probate_announcements(region: str):
    """Busca edictos judiciales, anuncios de herencias abintestato o fincas en investigación en boletines oficiales."""
    search = DuckDuckGoSearchRun()
    # Buscamos términos legales que indican herencias "atascadas"
    query = f"site:boe.es '{region}' 'herencia abintestato' OR 'llamamiento a herederos' OR 'finca en investigación'"
    return search.run(query)

@tool
def search_property_details(reference_info: str):
    """Busca información pública sobre la ubicación o el estado de fincas mencionadas en edictos."""
    search = DuckDuckGoSearchRun()
    query = f"información catastral o ubicación de {reference_info}"
    return search.run(query)

# --- 2. DEFINICIÓN DEL ESTADO ---
class InheritanceState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. CONSTRUCTOR DE NODOS ---
def create_agent_node(llm, tools, system_prompt, name):
    llm_with_tools = llm.bind_tools(tools)
    
    def node(state: InheritanceState):
        instruction = (
            f"\n\n[SISTEMA - ROL]: {system_prompt}\n"
            "INSTRUCCIÓN: Actúa con máxima ética y rigor legal. No especules. "
            "Si los datos del boletín son parciales, indícalo como un 'Caso a validar'."
        )
        messages = state["messages"] + [SystemMessage(content=instruction)]
        result = llm_with_tools.invoke(messages)
        result.name = name
        return {"messages": [result]}
    return node

# --- 4. PROMPTS DE LOS AGENTES ---

PROBATE_FINDER_PROMPT = """Eres un Investigador de Boletines Oficiales. Tu tarea es encontrar edictos 
donde la administración busque a herederos desconocidos o anuncie fincas que han pasado a estar 
en investigación por falta de dueño conocido en una región específica."""

ASSET_EVALUATOR_PROMPT = """Eres un Perito Judicial y Patrimonial. Tu misión es analizar los 
datos de la propiedad o herencia encontrados. Estima el valor potencial de la cuantía (si es una 
finca urbana, rústica o una masa hereditaria) y evalúa la viabilidad de la reclamación legal."""

LEGAL_COMMUNICATOR_PROMPT = """Eres un Abogado Especialista en Sucesiones. Tu tarea es redactar 
una carta informativa (no comercial agresiva, sino de asesoramiento) dirigida a posibles interesados 
o para uso interno del despacho. Explica los derechos sucesorios sobre el caso detectado y los 
pasos para evitar que el Estado se apropie del bien (abintestato)."""

# --- 5. CONFIGURACIÓN DEL GRAFO ---

llm = ChatOllama(model="mistral", temperature=0)

# Nodos
finder_node = create_agent_node(llm, [search_probate_announcements], PROBATE_FINDER_PROMPT, "probate_finder")
evaluator_node = create_agent_node(llm, [search_property_details], ASSET_EVALUATOR_PROMPT, "asset_evaluator")
communicator_node = create_agent_node(llm, [], LEGAL_COMMUNICATOR_PROMPT, "legal_communicator")

def manager_node(state: InheritanceState):
    if not state["messages"] or len(state["messages"]) < 2:
        return {"next_agent": "probate_finder"}
    
    last_actor = state["messages"][-1].name
    
    if last_actor == "probate_finder":
        return {"next_agent": "asset_evaluator"}
    if last_actor == "asset_evaluator":
        return {"next_agent": "legal_communicator"}
    
    return {"next_agent": "FINISH"}

workflow = StateGraph(InheritanceState)
workflow.add_node("manager", manager_node)
workflow.add_node("probate_finder", finder_node)
workflow.add_node("asset_evaluator", evaluator_node)
workflow.add_node("legal_communicator", communicator_node)

workflow.set_entry_point("manager")

for node in ["probate_finder", "asset_evaluator", "legal_communicator"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "probate_finder": "probate_finder",
    "asset_evaluator": "asset_evaluator",
    "legal_communicator": "legal_communicator",
    "FINISH": END
})

app = workflow.compile()

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    region_busqueda = "Cataluña"
    inputs = {"messages": [HumanMessage(content=f"Busca edictos de herencias sin reclamar en: {region_busqueda}")]}
    
    for s in app.stream(inputs, {"recursion_limit": 15}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 70)