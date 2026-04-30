import os
import operator
import tempfile
import subprocess
import shutil
import stat
import warnings
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv

# Importaciones de LangChain / LangGraph
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

# 1. Configuración e Importaciones faltantes
warnings.filterwarnings("ignore")
load_dotenv()

# LLM optimizado para lógica
llm = ChatOllama(model="mistral", temperature=0)

@tool
def clone_and_scan_for_testing(repo_url: str) -> str:
    """Clona un repo para obtener el código fuente y sus tests para análisis de mutación."""
    def remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    temp_dir = tempfile.mkdtemp()
    try:
        print(f"\n>>> [SISTEMA]: Extrayendo código y tests de {repo_url}...")
        # Comando para clonar de forma superficial
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], 
                        check=True, capture_output=True, text=True)
        
        context = ""
        for root, dirs, filenames in os.walk(temp_dir):
            if '.git' in dirs: dirs.remove('.git')
            for f in filenames:
                if f.endswith('.py'):
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        tipo = "TEST" if "test" in f.lower() else "CÓDIGO"
                        context += f"\n--- TIPO: {tipo} | ARCHIVO: {f} ---\n"
                        context += file.read()[:1500] 
        
        return context if context else "No se encontraron archivos de Python o tests."
    except Exception as e:
        return f"Error en la fase de lectura: {str(e)}"
    finally:
        shutil.rmtree(temp_dir, onerror=remove_readonly)

# Lista de herramientas
tools = [clone_and_scan_for_testing]

# 2. Definición del Estado
class MutationState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    # Estos campos ayudan a que el agente mantenga memoria técnica
    original_code: str
    mutated_code: str

# 3. Lógica del Orquestador (Manager)
def mutation_manager_node(state: MutationState):
    if not state["messages"]:
        return {"next": "mutador_logico"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    if last_actor == "mutador_logico":
        return {"next": "ejecutor_de_tests"}
    if last_actor == "ejecutor_de_tests":
        return {"next": "auditor_de_robustez"}
    if last_actor == "auditor_de_robustez":
        return {"next": "FINISH"}
    
    return {"next": "mutador_logico"}

# 4. Prompts Especializados
mutator_prompt = (
    "Eres un Ingeniero de QA especializado en Mutation Testing. Tu tarea es introducir UN SOLO error sutil "
    "en el código original que se te proporciona. \n"
    "REGLA: Cambia un operador lógico (ej. de '>=' a '>'), un valor booleano o un retorno. "
    "Devuelve el CÓDIGO MUTADO COMPLETO dentro de bloques de código y explica brevemente qué cambiaste."
)

test_executor_prompt = (
    "Eres un Runtime de Tests. Tu función es comparar el código mutado con la suite de pruebas. "
    "Analiza lógicamente: ¿Los tests fallarían debido al error introducido? \n"
    "- Si los tests detectan el error y fallan, responde: 'MUTATION KILLED'.\n"
    "- Si los tests pasan a pesar del error, responde: 'MUTATION SURVIVED'.\n"
    "Justifica tu respuesta basándote en los asserts de los tests."
)

auditor_prompt = (
    "Eres un Auditor de Calidad de Software. Basándote en el resultado anterior, "
    "evalúa la robustez de la suite de pruebas. Si la mutación sobrevivió, sugiere el test que falta."
)

# 5. Constructor de Nodos Mejorado
def create_mutation_node(llm, tools_list, system_prompt, name):
    # IMPORTANTE: Pasamos las herramientas aquí para que puedan usarlas
    agent = create_react_agent(llm, tools=tools_list, prompt=system_prompt)
    def node(state: MutationState):
        result = agent.invoke(state)
        # Extraemos el contenido del último mensaje del agente react
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# Crear los nodos vinculando herramientas solo donde se necesitan
mutator_node = create_mutation_node(llm, tools, mutator_prompt, "mutador_logico")
executor_node = create_mutation_node(llm, [], test_executor_prompt, "ejecutor_de_tests")
auditor_node = create_mutation_node(llm, [], auditor_prompt, "auditor_de_robustez")

# 6. Construcción del Grafo
workflow = StateGraph(MutationState)

workflow.add_node("manager", mutation_manager_node)
workflow.add_node("mutador_logico", mutator_node)
workflow.add_node("ejecutor_de_tests", executor_node)
workflow.add_node("auditor_de_robustez", auditor_node)

for node_name in ["mutador_logico", "ejecutor_de_tests", "auditor_de_robustez"]:
    workflow.add_edge(node_name, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "mutador_logico": "mutador_logico",
        "ejecutor_de_tests": "ejecutor_de_tests",
        "auditor_de_robustez": "auditor_de_robustez",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
app_mutation = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    # 1. Cambiamos la URL por la que quieras auditar
    url_repo_real = "https://github.com/xoseportasfer/xestor_reputacion_dixital" 

    inputs = {
        "messages": [
            HumanMessage(content=(
                f"Usa la herramienta 'clone_and_scan_for_testing' para descargar el código "
                f"de este repositorio: {url_repo_real}. "
                "Después, elige un archivo de lógica y su correspondiente test para "
                "realizar una auditoría de mutación."
            ))
        ],
        # Dejamos estos vacíos para que el agente los llene con la herramienta
        "original_code": "" 
    }

    print("--- INICIANDO DETECTOR DE MUTACIONES ---\n")
    for s in app_mutation.stream(inputs, {"recursion_limit": 15}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)