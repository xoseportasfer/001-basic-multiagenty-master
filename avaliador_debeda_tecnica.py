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

# LLM: Mistral (Excelente para detectar patrones y olores de código / code smells)
llm = ChatOllama(model="mistral", temperature=0)

# 2. Herramientas (Mantenemos la lógica de clonación pero enfocada a calidad)
@tool
def clone_and_scan_repo(repo_url: str) -> str:
    """Clona un repositorio para realizar un escaneo de calidad de código."""
    def remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    temp_dir = tempfile.mkdtemp()
    try:
        print(f"\n>>> [SISTEMA]: Descargando código fuente para auditoría...")
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], 
                        check=True, capture_output=True, text=True)
        
        all_content = ""
        for root, dirs, filenames in os.walk(temp_dir):
            if '.git' in dirs: dirs.remove('.git')
            for f in filenames:
                if f.endswith(('.py', '.js', '.ts', '.java')):
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        # Añadimos el nombre del archivo para que el agente sepa qué está auditando
                        all_content += f"\n--- ARCHIVO: {f} ---\n"
                        all_content += file.read()[:1500] # Fragmentos para evitar saturación
        
        return all_content if all_content else "No se encontró código fuente analizable."
    except Exception as e:
        return f"Error en el escaneo: {str(e)}"
    finally:
        shutil.rmtree(temp_dir, onerror=remove_readonly)

tools = [clone_and_scan_repo]

# 3. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 4. Orquestador de Calidad (Quality Manager)
def quality_manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "auditor_de_codigo"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    if last_actor == "auditor_de_codigo":
        return {"next": "analista_de_deuda"}
    if last_actor == "analista_de_deuda":
        return {"next": "estratega_refactorizacion"}
    if last_actor == "estratega_refactorizacion":
        return {"next": "FINISH"}
    
    return {"next": "auditor_de_codigo"}

# 5. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 6. Prompts Especializados en Deuda Técnica

auditor_prompt = (
    "Eres un Auditor de Código Estático. Tu función es llamar a 'clone_and_scan_repo'. "
    "Tu objetivo es identificar 'Code Smells' (malos olores), funciones demasiado largas, "
    "falta de comentarios técnicos, variables mal nombradas y lógica duplicada. "
    "Entrega un listado de hallazgos brutos encontrados en el código."
)

analista_prompt = (
    "Eres un Experto en QA y Deuda Técnica. Tu tarea es categorizar los hallazgos del Auditor. "
    "Debes identificar:\n"
    "1. DEUDA TÉCNICA: Código difícil de mantener o desactualizado.\n"
    "2. COMPLEJIDAD CICLOMÁTICA: Funciones con demasiadas ramificaciones.\n"
    "3. DEFICIENCIAS DE DOCUMENTACIÓN: Áreas donde la lógica es oscura y no hay docstrings.\n"
    "Sé crítico y técnico."
)

estratega_prompt = (
    "Eres un CTO / Arquitecto de Software. Tu misión es crear un 'Plan de Refactorización Priorizado'. "
    "Basándote en el análisis anterior, genera un informe para el equipo de desarrollo que incluya:\n"
    "- MATRIZ DE PRIORIDAD: Qué arreglar primero basándose en Riesgo vs. Esfuerzo.\n"
    "- RECOMENDACIONES TÉCNICAS: Sugiere patrones de diseño (ej. simplificar con Strategy, extraer a servicios).\n"
    "- ESTIMACIÓN DE RIESGO: Qué partes del sistema podrían romperse al refactorizar.\n"
    "Termina con una hoja de ruta para el próximo Sprint de mantenimiento."
)

# Nodos
auditor_node = create_node(llm, tools, auditor_prompt, "auditor_de_codigo")
analista_node = create_node(llm, [], analista_prompt, "analista_de_deuda")
estratega_node = create_node(llm, [], estratega_prompt, "estratega_refactorizacion")

# 7. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", quality_manager_node)
workflow.add_node("auditor_de_codigo", auditor_node)
workflow.add_node("analista_de_deuda", analista_node)
workflow.add_node("estratega_refactorizacion", estratega_node)

for node_name in ["auditor_de_codigo", "analista_de_deuda", "estratega_refactorizacion"]:
    workflow.add_edge(node_name, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "auditor_de_codigo": "auditor_de_codigo",
        "analista_de_deuda": "analista_de_deuda",
        "estratega_refactorizacion": "estratega_refactorizacion",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
app_quality_audit = workflow.compile()

# 8. Ejecución
if __name__ == "__main__":
    url_repo = "https://github.com/xoseportasfer/xestor_reputacion_dixital" 
    
    inputs = {
        "messages": [
            HumanMessage(content=f"Audita la calidad y deuda técnica del repositorio: {url_repo}")
        ]
    }
    
    print(f"--- INICIANDO AUDITORÍA DE CALIDAD DE SOFTWARE ---")
    print(f"Objetivo: {url_repo}")
    print("="*60)
    
    for s in app_quality_audit.stream(inputs, {"recursion_limit": 30}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)