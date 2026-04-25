import os
import functools
import operator
import warnings
import requests
from bs4 import BeautifulSoup
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv, find_dotenv

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun

# 1. Configuración
warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())

llm = ChatOllama(model="mistral", temperature=0)

# --- HERRAMIENTA PERSONALIZADA DE BEAUTIFULSOUP ---
@tool
def scrape_web_tool(url: str):
    """
    Extrae el contenido de texto de una URL específica. 
    Úsalo cuando tengas una URL de una licitación y necesites leer los detalles.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Eliminamos scripts y estilos para limpiar el texto
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
            
        text = soup.get_text(separator=' ')
        # Limpiamos espacios en blanco excesivos y limitamos a 3000 caracteres para el contexto del LLM
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return clean_text[:3000] 
    except Exception as e:
        return f"Error al leer la web: {e}"

# Lista de herramientas disponibles para los agentes
tools_list = [DuckDuckGoSearchRun(), scrape_web_tool]

# 3. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 4. Orquestador (Manager)
def manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "rastreador_licitaciones"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    if last_actor == "rastreador_licitaciones":
        return {"next": "analista_requisitos_tecnicos"}
    if last_actor == "analista_requisitos_tecnicos":
        return {"next": "evaluador_viabilidad_comercial"}
    if last_actor == "evaluador_viabilidad_comercial":
        return {"next": "FINISH"}
    
    return {"next": "rastreador_licitaciones"}

# 5. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 6. Prompts (Instrucciones para usar las herramientas)
rastreador_prompt = (
    "Eres un Rastreador de Licitaciones. Usa DuckDuckGo para encontrar concursos "
    "en España. Tu objetivo es encontrar las URLs de los anuncios en 'contrataciondelestado.es' "
    "o boletines oficiales. Pasa estas URLs al siguiente agente."
)

analista_prompt = (
    "Eres un Analista de Pliegos. Tienes la herramienta 'scrape_web_tool' para leer "
    "el contenido de las URLs que encontró el rastreador. Úsala para extraer requisitos "
    "obligatorios, solvencia técnica y presupuestos detallados."
)

evaluador_prompt = (
    "Eres un Evaluador de Viabilidad. Resume toda la información y emite un informe "
    "Go/No-Go fundamentado para la empresa."
)

# Nodos
rastreador_node = create_node(llm, tools_list, rastreador_prompt, "rastreador_licitaciones")
analista_node = create_node(llm, tools_list, analista_prompt, "analista_requisitos_tecnicos")
evaluador_node = create_node(llm, [], evaluador_prompt, "evaluador_viabilidad_comercial")

# 7. Construcción del Grafo
workflow = StateGraph(AgentState)
workflow.add_node("manager", manager_node)
workflow.add_node("rastreador_licitaciones", rastreador_node)
workflow.add_node("analista_requisitos_tecnicos", analista_node)
workflow.add_node("evaluador_viabilidad_comercial", evaluador_node)

for node in ["rastreador_licitaciones", "analista_requisitos_tecnicos", "evaluador_viabilidad_comercial"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "rastreador_licitaciones": "rastreador_licitaciones",
        "analista_requisitos_tecnicos": "analista_requisitos_tecnicos",
        "evaluador_viabilidad_comercial": "evaluador_viabilidad_comercial",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
tender_app = workflow.compile()

# 8. Ejecución
if __name__ == "__main__":
    sector_interes = "Licitaciones de Smart Cities y movilidad eléctrica en España"
    inputs = {"messages": [HumanMessage(content=f"Analiza profundamente las licitaciones actuales para: {sector_interes}")]}
    
    for s in tender_app.stream(inputs, {"recursion_limit": 30}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)