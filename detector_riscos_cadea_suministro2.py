import operator
import requests
import warnings
from bs4 import BeautifulSoup
from typing import Annotated, Sequence, TypedDict

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

# Ignorar warnings de deprecación para limpieza de consola
warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- 1. HERRAMIENTAS ---
search = DuckDuckGoSearchRun()

@tool
def get_web_content(url: str):
    """Extrae el texto relevante de una URL específica para analizar noticias."""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        return clean_text[:4000]
    except Exception as e:
        return f"Error al acceder a la URL: {e}"

@tool
def geopolitic_search(query: str):
    """Busca en DuckDuckGo noticias sobre eventos geopolíticos y logística."""
    return search.run(query)

@tool
def check_provider_finance(provider_name: str):
    """Analiza la salud financiera y credit score de un proveedor."""
    # Simulación de respuesta financiera
    return f"Informe para {provider_name}: Liquidez bajo mínimos, riesgo de impago aumentado."

# --- 2. DEFINICIÓN DEL ESTADO ---
class SupplyChainState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. CONSTRUCTOR DE NODOS (Versión Actualizada) ---
def create_agent_node(llm, tools, system_prompt, name):
    # Usamos state_modifier en lugar de prompt para cumplir con la v1.0+ de LangGraph
    #agent = create_react_agent(llm, tools=tools, state_modifier=system_prompt)
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    
    def node(state: SupplyChainState):
        result = agent.invoke(state)
        # Retornamos el mensaje con el nombre del agente para que el manager sepa quién habló
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# --- 4. CONFIGURACIÓN DE AGENTES ---
llm = ChatOllama(model="mistral", temperature=0)

GEO_PROMPT = (
    "Eres un Analista Geopolítico. Tu flujo de trabajo es: "
    "1. Usa geopolitic_search para encontrar noticias sobre huelgas o cierres. "
    "2. Si hay una URL, usa get_web_content. "
    "3. Reporta el impacto (1-10)."
)

FINANCE_PROMPT = "Eres un Auditor Financiero. Evalúa la solvencia de proveedores con check_provider_finance."

STRATEGIST_PROMPT = "Eres Jefe de Logística. Diseña rutas de escape basadas en los reportes previos."

# Creación de los nodos
geo_node = create_agent_node(llm, [geopolitic_search, get_web_content], GEO_PROMPT, "geo_analyst")
fin_node = create_agent_node(llm, [check_provider_finance], FINANCE_PROMPT, "finance_analyst")
strat_node = create_agent_node(llm, [], STRATEGIST_PROMPT, "supply_strategist")

# --- 5. ORQUESTADOR (MANAGER) ---
def manager_node(state: SupplyChainState):
    if not state["messages"] or len(state["messages"]) < 2:
        return {"next_agent": "geo_analyst"}
    
    last_msg = state["messages"][-1]
    
    if last_msg.name == "geo_analyst":
        return {"next_agent": "finance_analyst"}
    if last_msg.name == "finance_analyst":
        return {"next_agent": "supply_strategist"}
    
    return {"next_agent": "FINISH"}

# --- 6. CONSTRUCCIÓN DEL GRAFO ---
workflow = StateGraph(SupplyChainState)

workflow.add_node("manager", manager_node)
workflow.add_node("geo_analyst", geo_node)
workflow.add_node("finance_analyst", fin_node)
workflow.add_node("supply_strategist", strat_node)

workflow.set_entry_point("manager")

for node_name in ["geo_analyst", "finance_analyst", "supply_strategist"]:
    workflow.add_edge(node_name, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next_agent"],
    {
        "geo_analyst": "geo_analyst",
        "finance_analyst": "finance_analyst",
        "supply_strategist": "supply_strategist",
        "FINISH": END
    }
)

app = workflow.compile()

# --- 7. EJECUCIÓN ---
if __name__ == "__main__":
    inputs = {"messages": [HumanMessage(content="Audita a NeonGas Ukraine, único proveedor de gas neón para nuestros láseres de precisión, bajo el contexto de conflicto activo.")]}
    for s in app.stream(inputs, {"recursion_limit": 15}):
        if "__end__" not in s:
            print(s)
            print("-" * 50)