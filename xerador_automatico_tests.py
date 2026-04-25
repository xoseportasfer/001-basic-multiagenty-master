import os
import functools
import operator
import warnings
import shutil
import subprocess
import tempfile
import stat
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv, find_dotenv

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

# 1. Configuración
warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())

# LLM: Mistral (Excelente para lógica y generación de sintaxis de testing)
llm = ChatOllama(model="mistral", temperature=0)

# 2. Herramientas de Ingesta de Código
@tool
def fetch_logic_for_testing(repo_url: str) -> str:
    """Clona un repositorio y extrae las funciones principales para generar pruebas."""
    def remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    temp_dir = tempfile.mkdtemp()
    try:
        print(f"\n>>> [SISTEMA]: Extrayendo lógica para generación de tests...")
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], 
                        check=True, capture_output=True, text=True)
        
        logic_context = ""
        for root, dirs, filenames in os.walk(temp_dir):
            if '.git' in dirs: dirs.remove('.git')
            for f in filenames:
                if f.endswith(('.py', '.js', '.ts')): # Foco en Python/JS
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        logic_context += f"\n# ARCHIVO: {f}\n"
                        logic_context += file.read()[:2000] 
        
        return logic_context if logic_context else "No se detectó lógica procesable."
    except Exception as e:
        return f"Error en la ingesta: {str(e)}"
    finally:
        shutil.rmtree(temp_dir, onerror=remove_readonly)

tools = [fetch_logic_for_testing]

# 3. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 4. Orquestador de Testing (Test Manager)
def test_manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "analista_de_funcionalidad"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    if last_actor == "analista_de_funcionalidad":
        return {"next": "arquitecto_de_casos_limite"}
    if last_actor == "arquitecto_de_casos_limite":
        return {"next": "desarrollador_de_pruebas"}
    if last_actor == "desarrollador_de_pruebas":
        return {"next": "FINISH"}
    
    return {"next": "analista_de_funcionalidad"}

# 5. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 6. Prompts para el Ciclo TDD

analista_func_prompt = (
    "Eres un Analista de Sistemas. Tu función es llamar a 'fetch_logic_for_testing'. "
    "Debes identificar las funciones clave, sus parámetros de entrada y los valores de retorno esperados. "
    "Define el 'Contrato de Software' de cada función detectada para que el siguiente agente sepa qué probar."
)

edge_cases_prompt = (
    "Eres un Ingeniero de QA especializado en Casos Límite (Edge Cases). "
    "Basándote en la funcionalidad descrita, diseña una lista de escenarios de prueba:\n"
    "1. Casos felices (Happy Path).\n"
    "2. Entradas nulas, vacías o tipos de datos incorrectos.\n"
    "3. Límites numéricos (desbordamientos, negativos).\n"
    "4. Fallos de red o excepciones esperadas.\n"
    "Tu salida debe ser una lista lógica, no código todavía."
)

developer_test_prompt = (
    "Eres un Desarrollador Senior de Software experto en Pytest (Python) y Jest (JS). "
    "Tu tarea es transformar los casos de prueba en SCRIPTS REALES Y EJECUTABLES. "
    "Usa 'fixtures', 'mocks' para dependencias externas y aserciones claras. "
    "Estructura el código de prueba de forma profesional y limpia. "
    "Empieza directamente con el código de los tests."
)

# Nodos
analista_node = create_node(llm, tools, analista_func_prompt, "analista_de_funcionalidad")
edge_node = create_node(llm, [], edge_cases_prompt, "arquitecto_de_casos_limite")
dev_test_node = create_node(llm, [], developer_test_prompt, "desarrollador_de_pruebas")

# 7. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", test_manager_node)
workflow.add_node("analista_de_funcionalidad", analista_node)
workflow.add_node("arquitecto_de_casos_limite", edge_node)
workflow.add_node("desarrollador_de_pruebas", dev_test_node)

for node_name in ["analista_de_funcionalidad", "arquitecto_de_casos_limite", "desarrollador_de_pruebas"]:
    workflow.add_edge(node_name, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "analista_de_funcionalidad": "analista_de_funcionalidad",
        "arquitecto_de_casos_limite": "arquitecto_de_casos_limite",
        "desarrollador_de_pruebas": "desarrollador_de_pruebas",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
app_tdd_gen = workflow.compile()

# 8. Ejecución
if __name__ == "__main__":
    url_repo = "https://github.com/xoseportasfer/xestor_reputacion_dixital" 
    
    inputs = {
        "messages": [
            HumanMessage(content=f"Genera una suite completa de pruebas unitarias para el repositorio: {url_repo}")
        ]
    }
    
    print(f"--- GENERADOR AUTÓNOMO DE PRUEBAS (TDD-AGENT) ---")
    
    for s in app_tdd_gen.stream(inputs, {"recursion_limit": 30}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)