import operator
import requests
from bs4 import BeautifulSoup
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS ---
search = DuckDuckGoSearchRun()

@tool
def get_sustainability_report(company_name: str):
    """Busca y extrae resúmenes de compromisos ESG e informes de sostenibilidad."""
    query = f"{company_name} sustainability report ESG goals emissions target"
    return search.run(query)

@tool
def search_environmental_records(company_name: str):
    """Busca datos reales, multas ambientales o reportes de emisiones de fuentes externas."""
    query = f"{company_name} environmental violations carbon emissions real data news"
    return search.run(query)

# --- 2. DEFINICIÓN DEL ESTADO ---
class GreenwashingState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. CONSTRUCTOR DE NODOS (Optimizado para evitar el 'Eco') ---
def create_agent_node(llm, tools, system_prompt, name):
    llm_with_tools = llm.bind_tools(tools)
    
    def node(state: GreenwashingState):
        # Tomamos el último mensaje para contexto, pero reforzamos la instrucción
        history = state["messages"]
        
        # Inyectamos una instrucción de "No repetición" técnica
        anti_echo_instruction = (
            f"\n\n[INSTRUCCIÓN DE ROL]: {system_prompt}\n"
            "IMPORTANTE: No repitas la información ya expuesta. Aporta valor nuevo "
            "basado en tu especialidad. Si ves datos contradictorios, menciónalos directamente."
        )
        
        full_prompt = history + [SystemMessage(content=anti_echo_instruction)]
        result = llm_with_tools.invoke(full_prompt)
        result.name = name
        return {"messages": [result]}
    return node

# --- 4. PROMPTS ESPECIALIZADOS ---

ESG_ANALYST_PROMPT = """Eres un Analista de Informes ESG. Tu misión es extraer las PROMESAS 
específicas de la empresa: ¿Qué porcentaje de reducción de emisiones prometen y para qué año? 
Sé muy concreto con las cifras encontradas en sus informes oficiales."""

DATA_AUDITOR_PROMPT = """Eres un Auditor de Datos Ambientales. Tu misión es buscar EVIDENCIAS 
EXTERNAS. Busca multas, reportes de ONGs o datos de emisiones reales que contradigan o 
maticen las promesas de la empresa. No analices todavía, solo presenta los hechos externos."""

INCONSISTENCY_DETECTOR_PROMPT = """Eres un Experto en Greenwashing y Riesgo Reputacional. 
Compara las promesas del Agente 1 con los hechos del Agente 2. 
Marca 'ALERTA DE GREENWASHING' si hay inconsistencias graves entre lo prometido y lo ejecutado. 
Sugiere acciones para mitigar el riesgo de sanción."""

# --- 5. CONFIGURACIÓN DEL GRAFO ---

llm = ChatOllama(model="mistral", temperature=0)

# Nodos
esg_node = create_agent_node(llm, [get_sustainability_report], ESG_ANALYST_PROMPT, "esg_analyst")
audit_node = create_agent_node(llm, [search_environmental_records], DATA_AUDITOR_PROMPT, "data_auditor")
detector_node = create_agent_node(llm, [], INCONSISTENCY_DETECTOR_PROMPT, "inconsistency_detector")

def manager_node(state: GreenwashingState):
    if not state["messages"] or len(state["messages"]) < 2:
        return {"next_agent": "esg_analyst"}
    last_actor = state["messages"][-1].name
    if last_actor == "esg_analyst":
        return {"next_agent": "data_auditor"}
    if last_actor == "data_auditor":
        return {"next_agent": "inconsistency_detector"}
    return {"next_agent": "FINISH"}

workflow = StateGraph(GreenwashingState)
workflow.add_node("manager", manager_node)
workflow.add_node("esg_analyst", esg_node)
workflow.add_node("data_auditor", audit_node)
workflow.add_node("inconsistency_detector", detector_node)

workflow.set_entry_point("manager")
for agent in ["esg_analyst", "data_auditor", "inconsistency_detector"]:
    workflow.add_edge(agent, "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "esg_analyst": "esg_analyst",
    "data_auditor": "data_auditor",
    "inconsistency_detector": "inconsistency_detector",
    "FINISH": END
})

app = workflow.compile()

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    #inputs = {"messages": [HumanMessage(content="Audita el posible Greenwashing de la empresa 'UltraOil Corp' respecto a su promesa de ser Net Zero en 2030.")]}
    inputs = {"messages": [HumanMessage(content="Analiza la estrategia Net Zero de Repsol. Contrasta su publicidad sobre 'combustibles 100% renovables' con sus datos de inversión real (CAPEX) en exploración de nuevos yacimientos de petróleo y gas. ")]}
    for s in app.stream(inputs, {"recursion_limit": 15}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)