import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

from langchain_core.messages import SystemMessage, AIMessage

# --- 1. HERRAMIENTAS ESPECIALIZADAS ---

@tool
def social_monitor_search(brand_name: str):
    """Rastrea menciones recientes de la marca en redes, foros y sitios de noticias."""
    search = DuckDuckGoSearchRun()
    # Buscamos menciones negativas o virales específicamente
    query = f'"{brand_name}" (scam OR fraud OR fake OR hate OR alert)'
    return search.run(query)

@tool
def fact_check_validator(claim: str):
    """Valida noticias virales contrastándolas con fuentes oficiales o sitios de fact-checking."""
    search = DuckDuckGoSearchRun()
    return search.run(f"fact check: {claim}")

# --- 2. DEFINICIÓN DEL ESTADO ---
class BrandSafetyState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. CONSTRUCTOR DE NODOS ---
"""
def create_agent_node(llm, tools, system_prompt, name):
    # Usamos state_modifier para compatibilidad con versiones actuales
    agent = create_react_agent(llm, tools=tools, state_modifier=system_prompt)
    
    def node(state: BrandSafetyState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node




def create_agent_node(llm, tools, system_prompt, name):
    # 1. Enlazamos las herramientas al modelo (esto permite que el LLM sepa que existen)
    llm_with_tools = llm.bind_tools(tools)
    
    def node(state: BrandSafetyState):
        # 2. Preparamos la lista de mensajes: Instrucciones + Historial acumulado
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        
        # 3. Llamamos al modelo
        response = llm_with_tools.invoke(messages)
        
        # 4. CRÍTICO: Asignamos el nombre del agente al mensaje de salida
        # Esto es lo que permite que tu 'manager_node' sepa quién respondió
        response.name = name
        
        return {
            "messages": [response]
        }
    return node
"""

def create_agent_node(llm, tools, system_prompt, name):
    llm_with_tools = llm.bind_tools(tools)
    
    def node(state: BrandSafetyState):
        # CAMBIO CLAVE: Ponemos las instrucciones al FINAL también para que no las olvide
        # Y le recordamos que NO debe repetir lo que dijeron los demás.
        last_message_content = state["messages"][-1].content
        
        instruction_refresher = (
            f"\n\nRECORDATORIO DE TU ROL: {system_prompt}\n"
            "NO repitas el análisis anterior. Enfócate ÚNICAMENTE en validar la veracidad "
            "y proponer la respuesta de PR. Si necesitas usar una herramienta, úsala ahora."
        )
        
        # Creamos un prompt donde el sistema habla justo antes de que el modelo decida
        messages = state["messages"] + [SystemMessage(content=instruction_refresher)]
        
        result = llm_with_tools.invoke(messages)
        result.name = name
        return {"messages": [result]}
    return node

# --- 4. PROMPTS DE LOS AGENTES ---

MONITOR_PROMPT = """Eres un Especialista en Escucha Social. Tu tarea es encontrar menciones 
emergentes sobre la marca. Busca especialmente picos de negatividad o rumores virales recientes 
y extrae el contenido principal de las quejas."""

BOT_DETECTOR_PROMPT = """Eres un Analista Forense Digital. Revisa las menciones encontradas 
buscando patrones de 'astroturfing': repetición exacta de frases, picos de actividad en 
horarios inusuales o lenguaje altamente inflamatorio que sugiera una campaña coordinada de bots."""

VERACITY_PROMPT = """Eres un Estratega de Comunicación y Fact-Checker. Tu misión es usar 
fact_check_validator para confirmar si las acusaciones son reales o desinformación. 
Propón una respuesta de Relaciones Públicas basada en la veracidad del contenido."""

# --- 5. CONFIGURACIÓN DEL SISTEMA ---

llm = ChatOllama(model="mistral", temperature=0)

# Nodos de agentes
monitor_node = create_agent_node(llm, [social_monitor_search], MONITOR_PROMPT, "social_monitor")
bot_node = create_agent_node(llm, [], BOT_DETECTOR_PROMPT, "bot_analyst") # Análisis lógico
veracity_node = create_agent_node(llm, [fact_check_validator], VERACITY_PROMPT, "pr_strategist")

# --- 6. ORQUESTADOR (MANAGER) ---

def manager_node(state: BrandSafetyState):
    if not state["messages"] or len(state["messages"]) < 2:
        return {"next_agent": "social_monitor"}
    
    last_msg = state["messages"][-1]
    
    if last_msg.name == "social_monitor":
        return {"next_agent": "bot_analyst"}
    if last_msg.name == "bot_analyst":
        return {"next_agent": "pr_strategist"}
    
    return {"next_agent": "FINISH"}

# --- 7. CONSTRUCCIÓN DEL GRAFO ---

workflow = StateGraph(BrandSafetyState)

workflow.add_node("manager", manager_node)
workflow.add_node("social_monitor", monitor_node)
workflow.add_node("bot_analyst", bot_node)
workflow.add_node("pr_strategist", veracity_node)

workflow.set_entry_point("manager")

for agent in ["social_monitor", "bot_analyst", "pr_strategist"]:
    workflow.add_edge(agent, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next_agent"],
    {
        "social_monitor": "social_monitor",
        "bot_analyst": "bot_analyst",
        "pr_strategist": "pr_strategist",
        "FINISH": END
    }
)

app = workflow.compile()

# --- 8. EJECUCIÓN ---
if __name__ == "__main__":
    inputs = {"messages": [HumanMessage(content="Analiza riesgos de desinformación para la marca 'EcoVolt' tras el rumor de incendio de baterías.")]}
    for s in app.stream(inputs, {"recursion_limit": 15}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)