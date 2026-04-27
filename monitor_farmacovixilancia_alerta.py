import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS DE INVESTIGACIÓN MÉDICA ---

@tool
def social_patient_monitor(drug_name: str):
    """Busca testimonios de pacientes en foros, Reddit y grupos de apoyo sobre efectos secundarios."""
    search = DuckDuckGoSearchRun()
    query = f"{drug_name} forum patient experiences side effects 'started feeling' symptoms"
    return search.run(query)

@tool
def official_database_search(drug_name: str):
    """Busca menciones del fármaco en literatura técnica y reportes tipo VAERS o EudraVigilance."""
    search = DuckDuckGoSearchRun()
    # Simulamos búsqueda en registros oficiales vía web
    query = f"{drug_name} adverse events reports VAERS EudraVigilance clinical case studies"
    return search.run(query)

# --- 2. DEFINICIÓN DEL ESTADO ---
class PharmaSafetyState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. CONSTRUCTOR DE NODOS (Versión Robusta) ---
def create_agent_node(llm, tools, system_prompt, name):
    llm_with_tools = llm.bind_tools(tools)
    
    def node(state: PharmaSafetyState):
        # Refuerzo de instrucciones para evitar repeticiones (Anti-Eco)
        instruction = (
            f"\n\n[ROL ACTUAL]: {system_prompt}\n"
            "INSTRUCCIÓN: Analiza la información previa pero NO la repitas. "
            "Si el agente anterior encontró datos en foros, tú busca en bases oficiales o correlaciona. "
            "Si detectas un patrón de riesgo, descríbelo claramente."
        )
        
        messages = state["messages"] + [SystemMessage(content=instruction)]
        result = llm_with_tools.invoke(messages)
        result.name = name
        return {"messages": [result]}
    return node

# --- 4. PROMPTS DE ESPECIALIDAD ---

PATIENT_LISTENER_PROMPT = """Eres un Especialista en Escucha de Pacientes. Tu objetivo es identificar 
quejas subjetivas o síntomas recurrentes en lenguaje coloquial (ej: 'niebla mental', 'hormigueo') 
que los pacientes mencionan en foros tras usar el medicamento."""

MEDICAL_AUDITOR_PROMPT = """Eres un Auditor de Farmacovigilancia Clínica. Tu tarea es buscar 
evidencia técnica en reportes de bases de datos oficiales y estudios de casos. Busca si los 
síntomas coloquiales reportados por los pacientes ya están documentados científicamente."""

SAFETY_STRATEGIST_PROMPT = """Eres el Director de Seguridad de Producto. Debes comparar los 
reportes de pacientes con la evidencia clínica. Si hay una coincidencia de síntomas nuevos no 
listados en el prospecto, genera una 'ALERTA DE SEGURIDAD NIVEL 1' y sugiere pasos regulatorios."""

# --- 5. CONFIGURACIÓN DEL GRAFO ---

llm = ChatOllama(model="mistral", temperature=0)

# Nodos
patient_node = create_agent_node(llm, [social_patient_monitor], PATIENT_LISTENER_PROMPT, "patient_monitor")
medical_node = create_agent_node(llm, [official_database_search], MEDICAL_AUDITOR_PROMPT, "medical_auditor")
safety_node = create_agent_node(llm, [], SAFETY_STRATEGIST_PROMPT, "safety_director")

def manager_node(state: PharmaSafetyState):
    if not state["messages"] or len(state["messages"]) < 2:
        return {"next_agent": "patient_monitor"}
    
    last_actor = state["messages"][-1].name
    
    if last_actor == "patient_monitor":
        return {"next_agent": "medical_auditor"}
    if last_actor == "medical_auditor":
        return {"next_agent": "safety_director"}
    
    return {"next_agent": "FINISH"}

workflow = StateGraph(PharmaSafetyState)
workflow.add_node("manager", manager_node)
workflow.add_node("patient_monitor", patient_node)
workflow.add_node("medical_auditor", medical_node)
workflow.add_node("safety_director", safety_node)

workflow.set_entry_point("manager")

for node in ["patient_monitor", "medical_auditor", "safety_director"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "patient_monitor": "patient_monitor",
    "medical_auditor": "medical_auditor",
    "safety_director": "safety_director",
    "FINISH": END
})

app = workflow.compile()

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    medicamento = "Lisinopril" # Ejemplo de un fármaco común
    inputs = {"messages": [HumanMessage(content=f"Inicia monitorización de seguridad para el fármaco: {medicamento}")]}
    
    for s in app.stream(inputs, {"recursion_limit": 15}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)