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

# LLM: Mistral (Excelente para síntesis y explicación de flujos)
llm = ChatOllama(model="mistral", temperature=0)

# 2. Herramienta de Ingesta Inteligente
@tool
def clone_and_explore_repo(repo_url: str) -> str:
    """Clona un repositorio y realiza una exploración inicial de la estructura y archivos clave."""
    def remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    temp_dir = tempfile.mkdtemp()
    try:
        print(f"\n>>> [SISTEMA]: Explorando repositorio para Onboarding...")
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], 
                        check=True, capture_output=True, text=True)
        
        repo_context = ""
        # 1. Mapear estructura de directorios
        structure = []
        for root, dirs, files in os.walk(temp_dir):
            if '.git' in dirs: dirs.remove('.git')
            level = root.replace(temp_dir, '').count(os.sep)
            indent = ' ' * 4 * level
            structure.append(f"{indent}{os.path.basename(root)}/")
        
        repo_context += "ESTRUCTURA DEL PROYECTO:\n" + "\n".join(structure[:30]) + "\n"

        # 2. Leer archivos críticos de identidad y entrada
        critical_files = ['README.md', 'requirements.txt', 'main.py', 'app.py', 'manage.py', 'pyproject.toml']
        for root, _, filenames in os.walk(temp_dir):
            for f in filenames:
                if f in critical_files or f.endswith('.py'):
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        repo_context += f"\n--- CONTENIDO DE: {f} ---\n"
                        repo_context += file.read()[:1500] 
        
        return repo_context if repo_context else "Repositorio vacío o sin archivos Python."
    except Exception as e:
        return f"Error en la exploración: {str(e)}"
    finally:
        shutil.rmtree(temp_dir, onerror=remove_readonly)

tools = [clone_and_explore_repo]

# 3. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 4. Orquestador de Bienvenida (Onboarding Manager)
def onboarding_manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "mapeador_de_estructura"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    if last_actor == "mapeador_de_estructura":
        return {"next": "analista_de_puntos_entrada"}
    if last_actor == "analista_de_puntos_entrada":
        return {"next": "redactor_guia_bienvenida"}
    if last_actor == "redactor_guia_bienvenida":
        return {"next": "FINISH"}
    
    return {"next": "mapeador_de_estructura"}

# 5. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 6. Prompts para Onboarding (Foco en Python/LangGraph)

mapeador_prompt = (
    "Eres un Arquitecto de Onboarding. Tu función es llamar a 'clone_and_explore_repo'. "
    "Analiza la estructura de carpetas y archivos. Identifica si es un proyecto de LangGraph, "
    "FastAPI, Flask o un script puro. Resume el stack tecnológico principal."
)

analista_puntos_prompt = (
    "Eres un Analista Técnico. Tu tarea es encontrar los 'Entry Points' del código. "
    "Busca dónde se inicia la ejecución (ej: 'app.run()', 'workflow.compile()', 'if __name__ == \"__main__\"'). "
    "Identifica las rutas de API (si las hay) o los nodos principales del grafo de agentes. "
    "Explica cómo fluye la información a grandes rasgos."
)

redactor_guia_prompt = (
    "Eres un Mentor de Desarrolladores. Tu misión es redactar la 'Guía de Bienvenida del Desarrollador'. "
    "Estructura el documento así:\n"
    "1. HOLA MUNDO: Cómo ejecutar el proyecto por primera vez.\n"
    "2. MAPA DEL TESORO: Qué archivos debe abrir el desarrollador para entender la lógica central.\n"
    "3. PRIMEROS PASOS: Sugiere una pequeña modificación o 'issue' ficticio para que empiece a tocar el código.\n"
    "4. ARQUITECTURA: Breve explicación del flujo principal.\n"
    "Usa un tono acogedor, profesional y muy técnico. RECUERDA: El proyecto es PYTHON."
)

# Nodos
mapeador_node = create_node(llm, tools, mapeador_prompt, "mapeador_de_estructura")
analista_node = create_node(llm, [], analista_puntos_prompt, "analista_de_puntos_entrada")
redactor_node = create_node(llm, [], redactor_guia_prompt, "redactor_guia_bienvenida")

# 7. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", onboarding_manager_node)
workflow.add_node("mapeador_de_estructura", mapeador_node)
workflow.add_node("analista_de_puntos_entrada", analista_node)
workflow.add_node("redactor_guia_bienvenida", redactor_node)

for node_name in ["mapeador_de_estructura", "analista_de_puntos_entrada", "redactor_guia_bienvenida"]:
    workflow.add_edge(node_name, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "mapeador_de_estructura": "mapeador_de_estructura",
        "analista_de_puntos_entrada": "analista_de_puntos_entrada",
        "redactor_guia_bienvenida": "redactor_guia_bienvenida",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
app_onboarding = workflow.compile()

# 8. Ejecución
if __name__ == "__main__":
    url_repo = "https://github.com/xoseportasfer/xestor_reputacion_dixital" 
    
    inputs = {
        "messages": [
            HumanMessage(content=f"Genera una guía de onboarding completa para un nuevo desarrollador en: {url_repo}")
        ]
    }
    
    print(f"--- AGENTE DE ONBOARDING PARA DESARROLLADORES ---")
    
    for s in app_onboarding.stream(inputs, {"recursion_limit": 30}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)