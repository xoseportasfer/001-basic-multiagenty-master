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

# LLM: Mistral (Excelente para detectar patrones de seguridad y vulnerabilidades)
llm = ChatOllama(model="mistral", temperature=0)

# 2. Herramienta de Ingesta y Escaneo Inicial
@tool
def clone_and_scan_security(repo_url: str) -> str:
    """Clona un repositorio para realizar una auditoría de seguridad SAST."""
    def remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    temp_dir = tempfile.mkdtemp()
    try:
        print(f"\n>>> [SISTEMA]: Iniciando escaneo de seguridad en {repo_url}...")
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], 
                        check=True, capture_output=True, text=True)
        
        security_context = ""
        for root, dirs, filenames in os.walk(temp_dir):
            if '.git' in dirs: dirs.remove('.git')
            for f in filenames:
                # Escaneamos archivos de configuración y código
                if f.endswith(('.py', '.js', '.env', '.yaml', '.yml', '.json')):
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        security_context += f"\n--- ORIGEN: {f} ---\n"
                        security_context += file.read()[:2000] 
        
        return security_context if security_context else "No se encontró contenido para auditar."
    except Exception as e:
        return f"Error en la fase de clonación: {str(e)}"
    finally:
        shutil.rmtree(temp_dir, onerror=remove_readonly)

tools = [clone_and_scan_security]

# 3. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 4. Orquestador de Seguridad (Security Manager)
def security_manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "detector_de_secretos"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    if last_actor == "detector_de_secretos":
        return {"next": "analista_owasp"}
    if last_actor == "analista_owasp":
        return {"next": "redactor_de_parches"}
    if last_actor == "redactor_de_parches":
        return {"next": "FINISH"}
    
    return {"next": "detector_de_secretos"}

# 5. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 6. Prompts Especializados en Ciberseguridad

secret_detector_prompt = (
    "Eres un Especialista en Detección de Secretos. Tu función es llamar a 'clone_and_scan_security'. "
    "Busca patrones que indiquen claves de API expuestas, contraseñas hardcoded, tokens de acceso "
    "y certificados privados dentro del código y archivos de configuración. "
    "Reporta la ubicación exacta y el tipo de secreto encontrado."
)

owasp_analyst_prompt_generico = (
    "Eres un Auditor de Seguridad experto en OWASP Top 10. Analiza el código buscando vulnerabilidades como: "
    "Inyecciones (SQL, NoSQL), Autenticación rota, Exposición de datos sensibles, XSS y Deserialización insegura. "
    "Clasifica cada hallazgo por nivel de criticidad (Bajo, Medio, Alto, Crítico)."
)

owasp_analyst_prompt = (
    "Eres un Auditor de Seguridad Senior experto en Python y el ecosistema LangGraph. "
    "REGLA CRÍTICA: Estás analizando un repositorio de PYTHON. No lo confundas con PHP u otros lenguajes. "
    "Analiza el código buscando vulnerabilidades del OWASP Top 10 específicas de Python (como inyecciones en f-strings, "
    "uso inseguro de 'eval()', serialización con 'pickle', o manejo incorrecto de variables de entorno en .env). "
    "Identifica fallos en la lógica de los grafos de estado y clasifica cada hallazgo por criticidad."
)

patch_writer_prompt = (
    "Eres un Ingeniero de Remediación de Seguridad. Tu tarea es redactar el 'Security Report' final. "
    "Para cada vulnerabilidad encontrada, debes: \n"
    "1. Describir el riesgo.\n"
    "2. Proporcionar el PARCHE O CORRECCIÓN de código específica.\n"
    "3. Sugerir mejores prácticas para evitar que se repita.\n"
    "El informe debe ser técnico, conciso y seguir un formato de 'Security-as-Code'."
)

# Nodos
secret_node = create_node(llm, tools, secret_detector_prompt, "detector_de_secretos")
owasp_node = create_node(llm, [], owasp_analyst_prompt, "analista_owasp")
patch_node = create_node(llm, [], patch_writer_prompt, "redactor_de_parches")

# 7. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", security_manager_node)
workflow.add_node("detector_de_secretos", secret_node)
workflow.add_node("analista_owasp", owasp_node)
workflow.add_node("redactor_de_parches", patch_node)

for node_name in ["detector_de_secretos", "analista_owasp", "redactor_de_parches"]:
    workflow.add_edge(node_name, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "detector_de_secretos": "detector_de_secretos",
        "analista_owasp": "analista_owasp",
        "redactor_de_parches": "redactor_de_parches",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
app_sast_security = workflow.compile()

# 8. Ejecución
if __name__ == "__main__":
    url_repo = "https://github.com/xoseportasfer/xestor_reputacion_dixital" 
    
    inputs = {
        "messages": [
            HumanMessage(content=f"Realiza una auditoría de seguridad completa (SAST) en el repositorio: {url_repo}")
        ]
    }
    
    print(f"--- AGENTE DE EVALUACIÓN Y PREVENCIÓN DE CIBERSEGURIDAD (SAST) ---")
    
    for s in app_sast_security.stream(inputs, {"recursion_limit": 30}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)