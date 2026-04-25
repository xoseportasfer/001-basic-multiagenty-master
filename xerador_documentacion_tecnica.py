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
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

# 1. Configuración
warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())

# LLM: Mistral (Excelente para entender lógica de código)
llm = ChatOllama(model="mistral", temperature=0)

# 2. Herramienta personalizada para leer archivos locales
@tool
def read_source_code(file_path: str) -> str:
    """Lee el contenido de un archivo de código fuente local."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            return content[:4000] # Limitamos para no saturar el contexto
    except Exception as e:
        return f"Error al leer el archivo: {e}"
    
@tool
def clone_and_read_repo(repo_url: str) -> str:
    """Clona un repo y devuelve el código fuente. Maneja errores de permisos en Windows."""
    
    # Función interna para forzar el borrado de archivos de solo lectura (especial para Windows)
    def remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    temp_dir = tempfile.mkdtemp()
    try:
        print(f"\n>>> [SISTEMA]: Clonando en {temp_dir}...")
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], 
                       check=True, capture_output=True, text=True)
        
        source_files = []
        for root, dirs, filenames in os.walk(temp_dir):
            if '.git' in dirs: dirs.remove('.git') # Ignorar carpeta git
            for f in filenames:
                if f.endswith(('.py', '.js', '.ts', '.java')):
                    source_files.append(os.path.join(root, f))

        if not source_files:
            return "No se encontraron archivos de código."

        with open(source_files[0], "r", encoding="utf-8") as f:
            content = f.read()
            
        print(f">>> [SISTEMA]: Lectura exitosa de {os.path.basename(source_files[0])}")
        return f"CONTENIDO DEL REPOSITORIO (Archivo: {os.path.basename(source_files[0])}):\n\n{content[:4000]}"

    except Exception as e:
        return f"Error en la herramienta: {str(e)}"
    finally:
        # CAMBIO CLAVE: Usamos onerror para limpiar archivos bloqueados por Windows/Git
        print(f">>> [SISTEMA]: Limpiando directorio temporal...")
        shutil.rmtree(temp_dir, onerror=remove_readonly)

tools = [read_source_code, clone_and_read_repo]

# 3. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 4. Manager de Documentación (Orquestador DevOps)
def manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "analista_de_codigo"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Análisis de Código -> Explicación de Lógica -> Generación de Markdown
    if last_actor == "analista_de_codigo":
        return {"next": "explicador_tecnico"}
    if last_actor == "explicador_tecnico":
        return {"next": "redactor_markdown"}
    if last_actor == "redactor_markdown":
        return {"next": "FINISH"}
    
    return {"next": "analista_de_codigo"}

# 5. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    # Asegúrate de pasar 'tools' aquí
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 6. Prompts Especializados (En Español)

analista_prompt = (
    "Eres un Analista de Código. Tu ÚNICA función es llamar a 'clone_and_read_repo'. "
    "Cuando recibas la respuesta, entrégala tal cual al siguiente agente. "
    "NO analices el código de la función de clonación, analiza el código que la función RECOGIÓ de internet."
)

explicador_prompt = (
    "Eres un Explicador Técnico. Basándote en la estructura extraída, explica la lógica "
    "detrás de cada función y cómo interactúan los componentes. Enfócate en el 'por qué' "
    "se hizo así y no solo en lo que hace el código."
)

redactor_prompt = (
    "Eres un Redactor de Documentación Markdown. Toma el análisis y las explicaciones "
    "para generar un archivo README.md profesional. Incluye secciones de: Descripción, "
    "Arquitectura, Funciones Principales y Ejemplo de Uso. Usa un formato limpio y elegante."
)

# Nodos
analista_node = create_node(llm, tools, analista_prompt, "analista_de_codigo")
explicador_node = create_node(llm, [], explicador_prompt, "explicador_tecnico")
redactor_node = create_node(llm, [], redactor_prompt, "redactor_markdown")

# 7. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", manager_node)
workflow.add_node("analista_de_codigo", analista_node)
workflow.add_node("explicador_tecnico", explicador_node)
workflow.add_node("redactor_markdown", redactor_node)

for node_name in ["analista_de_codigo", "explicador_tecnico", "redactor_markdown"]:
    workflow.add_edge(node_name, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "analista_de_codigo": "analista_de_codigo",
        "explicador_tecnico": "explicador_tecnico",
        "redactor_markdown": "redactor_markdown",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
#app_devops = workflow.compile()
app_github_doc = workflow.compile()

# 8. Ejecución corregida para Repositorios de GitHub
if __name__ == "__main__":
    url_repo = "https://github.com/xoseportasfer/xestor_reputacion_dixital" 
    
    # Mensaje imperativo para forzar el uso de la herramienta
    inputs = {
        "messages": [
            HumanMessage(content=f"ACCIÓN REQUERIDA: Llama a la función 'clone_and_read_repo' con la URL {url_repo}. Analiza el código que devuelva la función y genera la documentación.")
        ]
    }
    
    print(f"--- INICIANDO GENERADOR DE DOCUMENTACIÓN GITHUB ---")
    print(f"Repositorio objetivo: {url_repo}")
    print("="*60)
    
    # Iniciamos el flujo del grafo
    for s in app_github_doc.stream(inputs, {"recursion_limit": 30}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                # Extraemos el contenido del último mensaje generado por el agente en esa fase
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)