import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS DE INVESTIGACIÓN ---
search_tool = DuckDuckGoSearchRun()

# --- 2. ESTADO DEL GRAFO ---
class RepurposingState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. NODOS DE AGENTES ESPECIALIZADOS ---

def molecular_target_agent(state: RepurposingState):
    """Analiza dianas biológicas y mecanismos de acción del fármaco."""
    drug = state["messages"][0].content
    # Simulación de búsqueda en bases de datos tipo DrugBank o UniProt
    query = f"mecanismo de acción molecular y dianas biológicas de {drug} target proteins"
    results = search_tool.run(query)
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres un Biólogo Molecular. Tu tarea es identificar las proteínas diana y las vías "
        "metabólicas en las que actúa el fármaco. Busca otras enfermedades que compartan "
        "estas mismas dianas biológicas."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Datos moleculares de {drug}: {results}")])
    response.name = "molecular_expert"
    return {"messages": [response]}

def clinical_insight_agent(state: RepurposingState):
    """Busca 'efectos secundarios' que sugieran beneficios en otras patologías."""
    drug = state["messages"][0].content
    last_context = state["messages"][-1].content
    
    # Buscamos 'off-target effects' o beneficios inesperados en literatura
    query = f"unexpected clinical benefits or positive side effects of {drug} in clinical trials"
    results = search_tool.run(query)
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres un Farmacólogo Clínico. Analiza reportes de literatura médica buscando efectos "
        "secundarios 'positivos' o beneficios inesperados observados en pacientes. "
        "Ejemplo: Un fármaco para la hipertensión que mejora el crecimiento del cabello."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Contexto molecular: {last_context}\nEvidencia clínica: {results}")])
    response.name = "clinical_analyst"
    return {"messages": [response]}

def repurposing_strategist_node(state: RepurposingState):
    """Propone la nueva indicación terapéutica."""
    llm = ChatOllama(model="mistral", temperature=0)
    history = state["messages"][-1].content
    
    prompt = SystemMessage(content=(
        "Eres el Director de Estrategia de I+D. Basándote en el mecanismo molecular y la "
        "evidencia clínica, propón una NUEVA INDICACIÓN para el fármaco. "
        "ESTRUCTURA: \n"
        "1. NUEVA PATOLOGÍA PROPUESTA\n"
        "2. JUSTIFICACIÓN CIENTÍFICA (Dianas compartidas)\n"
        "3. EVIDENCIA DE APOYO (Observaciones clínicas)\n"
        "4. RIESGOS Y PRÓXIMOS PASOS (Fase II sugerida)."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Análisis acumulado: {history}")])
    response.name = "rd_director"
    return {"messages": [response]}

# --- 4. LÓGICA DE CONTROL ---

def manager_node(state: RepurposingState):
    if len(state["messages"]) <= 1: return {"next_agent": "molecular_expert"}
    last_actor = state["messages"][-1].name
    if last_actor == "molecular_expert": return {"next_agent": "clinical_analyst"}
    if last_actor == "clinical_analyst": return {"next_agent": "rd_director"}
    return {"next_agent": "FINISH"}

workflow = StateGraph(RepurposingState)
workflow.add_node("manager", manager_node)
workflow.add_node("molecular_expert", molecular_target_agent)
workflow.add_node("clinical_analyst", clinical_insight_agent)
workflow.add_node("rd_director", repurposing_strategist_node)

workflow.set_entry_point("manager")
workflow.add_edge("molecular_expert", "manager")
workflow.add_edge("clinical_analyst", "manager")
workflow.add_edge("rd_director", "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "molecular_expert": "molecular_expert",
    "clinical_analyst": "clinical_analyst",
    "rd_director": "rd_director",
    "FINISH": END
})

app = workflow.compile()

if __name__ == "__main__":
    # Ejemplo con Metformina (fármaco de diabetes con potencial en longevidad/cáncer)
    inputs_1 = {"messages": [HumanMessage(content="Metformina")]}
    inputs_2 = {"messages": [HumanMessage(content="Rapamicina")]}
    inputs = {"messages": [HumanMessage(content="Analiza el potencial de Reposicionamiento de la Hidroxicloroquina como adyuvante en Terapias Oncológicas y Resistencia a Quimioterapia")]}
    for s in app.stream(inputs, {"recursion_limit": 10}):
        node_name = list(s.keys())[0]
        if node_name != "manager" and node_name != "__end__":
            print(f"\n--- {node_name.upper()} ---")
            print(s[node_name]["messages"][-1].content)
            print("-" * 50)