import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS ---
search_tool = DuckDuckGoSearchRun()

# --- 2. ESTADO ---
class JourneyState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. NODOS DE AGENTES ---

def patient_data_scout(state: JourneyState):
    """Rastrea foros, comunidades y testimonios (simulado vía búsqueda)."""
    condition = state["messages"][0].content
    # Buscamos experiencias de pacientes reales, foros de salud y síntomas iniciales
    query = f"testimonios pacientes {condition} síntomas iniciales diagnóstico tiempo foros"
    results = search_tool.run(query)
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres un Analista de Datos de Pacientes. Tu función es extraer testimonios "
        "reales, anonimizarlos (eliminar nombres o datos personales) y resumir "
        "las quejas o vivencias más frecuentes durante la etapa previa al diagnóstico."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Datos recopilados: {results}")])
    response.name = "patient_scout"
    return {"messages": [response]}

def journey_mapper_node(state: JourneyState):
    """Mapea la línea de tiempo desde los síntomas hasta el tratamiento."""
    patient_insights = state["messages"][-1].content
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres un Antropólogo Médico. Basado en los testimonios, construye una línea de tiempo "
        "del recorrido del paciente. Identifica: \n"
        "1. Síntomas iniciales (a menudo ignorados).\n"
        "2. Primer contacto médico y diagnósticos erróneos frecuentes.\n"
        "3. Punto de diagnóstico definitivo.\n"
        "4. Inicio del tratamiento."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Insights: {patient_insights}")])
    response.name = "journey_mapper"
    return {"messages": [response]}

def drop_off_analyst_node(state: JourneyState):
    """Identifica puntos críticos de abandono y propone soluciones."""
    journey = state["messages"][-1].content
    
    llm = ChatOllama(model="mistral", temperature=0)
    prompt = SystemMessage(content=(
        "Eres Especialista en Patient Support Programs (PSP). Analiza el mapa del paciente e "
        "identifica el 'Punto de Abandono' (Drop-off point). \n"
        "¿Es por efectos secundarios? ¿Falta de información? ¿Dificultad de acceso? \n"
        "Propón una intervención (ej. App de soporte, línea 24/7, educación personalizada)."
    ))
    response = llm.invoke([prompt, HumanMessage(content=f"Mapa del paciente: {journey}")])
    response.name = "drop_off_analyst"
    return {"messages": [response]}

# --- 4. LÓGICA DE CONTROL ---

def manager_node(state: JourneyState):
    if len(state["messages"]) <= 1: return {"next_agent": "patient_scout"}
    last_actor = state["messages"][-1].name
    if last_actor == "patient_scout": return {"next_agent": "journey_mapper"}
    if last_actor == "journey_mapper": return {"next_agent": "drop_off_analyst"}
    return {"next_agent": "FINISH"}

workflow = StateGraph(JourneyState)
workflow.add_node("manager", manager_node)
workflow.add_node("patient_scout", patient_data_scout)
workflow.add_node("journey_mapper", journey_mapper_node)
workflow.add_node("drop_off_analyst", drop_off_analyst_node)

workflow.set_entry_point("manager")
workflow.add_edge("patient_scout", "manager")
workflow.add_edge("journey_mapper", "manager")
workflow.add_edge("drop_off_analyst", "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "patient_scout": "patient_scout",
    "journey_mapper": "journey_mapper",
    "drop_off_analyst": "drop_off_analyst",
    "FINISH": END
})

app = workflow.compile()

if __name__ == "__main__":
    # Ejemplo con una enfermedad de diagnóstico difícil o tratamiento crónico
    inputs_1 = {"messages": [HumanMessage(content="Esclerosis Múltiple")]}
    inputs_2 = {"messages": [HumanMessage(content="Endometriosis (desde el dolor pélvico inicial hasta la cirugía laparoscópica y tratamiento hormonal)")]}
    inputs = {"messages": [HumanMessage(content="Cáncer de mama con receptores hormonales positivos (adherencia al tratamiento adyuvante a largo plazo)")]}
    for s in app.stream(inputs, {"recursion_limit": 10}):
        node_name = list(s.keys())[0]
        if node_name != "manager" and node_name != "__end__":
            print(f"\n--- {node_name.upper()} ---")
            print(s[node_name]["messages"][-1].content)
            print("-" * 60)