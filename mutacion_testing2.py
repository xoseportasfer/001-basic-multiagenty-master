import os
import operator
import tempfile
import subprocess
import shutil
import stat
import warnings
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

# 1. Configuración inicial
warnings.filterwarnings("ignore")
load_dotenv()

# LLM: Usamos Mistral para el análisis de lógica
llm = ChatOllama(model="mistral", temperature=0)

class GlobalState(TypedDict):
    repo_url: str
    security_report: str
    mutation_report: str
    final_audit: str
    messages: Annotated[Sequence[BaseMessage], operator.add]

# 2. Herramienta de Ingesta adaptada para Python
@tool
def clone_and_scan_for_testing(repo_url: str) -> str:
    """Clona un repo y lee código/tests ignorando errores de codificación."""
    def remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    temp_dir = tempfile.mkdtemp()
    try:
        print(f"\n>>> [SISTEMA]: Accediendo a {repo_url}...")
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], 
                        check=True, capture_output=True, text=True)
        
        context = ""
        for root, dirs, filenames in os.walk(temp_dir):
            if '.git' in dirs: dirs.remove('.git')
            for f in filenames:
                if f.endswith('.py'):
                    # NOTA: Usamos 'errors=ignore' para evitar que el agente se distraiga con UTF-8
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as file:
                        tipo = "TEST" if "test" in f.lower() else "CÓDIGO"
                        context += f"\n--- TIPO: {tipo} | ARCHIVO: {f} ---\n"
                        context += file.read()[:1500] 
        
        return context if context else "No se encontraron archivos válidos."
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        shutil.rmtree(temp_dir, onerror=remove_readonly)

tools = [clone_and_scan_for_testing]

# 3. Definición del Estado
class MutationState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 4. Orquestador (Mutation Manager)
def mutation_manager_node(state: MutationState):
    # Si no hay mensajes, forzamos el inicio
    if len(state.get("messages", [])) == 0:
        return {"next": "mutador_logico"}
    
    last_msg = state["messages"][-1]
    
    # IMPORTANTE: Mistral a veces no pone el 'name' correctamente. 
    # Vamos a usar una lógica más segura:
    last_actor = getattr(last_msg, "name", None)

    if last_actor == "mutador_logico":
        return {"next": "ejecutor_de_tests"}
    elif last_actor == "ejecutor_de_tests":
        return {"next": "auditor_de_robustez"}
    elif last_actor == "auditor_de_robustez":
        return {"next": "FINISH"}
    
    # Por defecto, si se pierde, que vaya al mutador
    return {"next": "mutador_logico"}

def supervisor_node(state: GlobalState):
    # 1. Ejecutar Auditoría de Seguridad
    print("\n[SUPERVISOR]: Iniciando Auditoría de Seguridad (SAST)...")
    res_sec = app_sast_security.invoke({
        "messages": [HumanMessage(content=f"Auditoría completa para {state['repo_url']}")]
    })
    security_summary = res_sec["messages"][-1].content

    # 2. Ejecutar Auditoría de Robustez (Mutation)
    print("\n[SUPERVISOR]: Iniciando Auditoría de Robustez (Mutation Testing)...")
    res_mut = app_mutation.invoke({
        "messages": [HumanMessage(content=f"Análisis de mutación para {state['repo_url']}")]
    })
    mutation_summary = res_mut["messages"][-1].content

    return {
        "security_report": security_summary,
        "mutation_report": mutation_summary
    }

def final_reporter_node(state: GlobalState):
    prompt = f"""
    Eres el Chief QA & Security Officer. Cruza los siguientes informes:
    
    INFORME SEGURIDAD:
    {state['security_report']}
    
    INFORME MUTACIÓN:
    {state['mutation_report']}
    
    TAREA:
    Identifica si las áreas vulnerables encontradas en seguridad tienen tests robustos.
    Si el SAST encontró un fallo y el Mutation Testing dice 'SURVIVED' en esa área, 
    márcalo como RIESGO CRÍTICO (Vulnerabilidad no testeada).
    """
    
    response = llm.invoke(prompt)
    return {"final_audit": response.content}



# 5. Constructor de Nodos
def create_node(llm, tools_list, system_prompt, name):
    agent = create_react_agent(llm, tools=tools_list, prompt=system_prompt)
    def node(state: MutationState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 6. Prompts (Forzando lenguaje Python)
mutator_prompt = (
    "Eres un Ingeniero de QA. NO TE PREOCUPES POR LA CODIFICACIÓN UTF-8. "
    "Tu única misión es: 1. Elegir una función lógica. 2. Cambiar un operador (==, !=, <, >). "
    "3. Devolver el código mutado. Ignora cualquier error de caracteres extraños." \
    "No modifiques los nombres de las funciones de test. Modifica únicamente los operadores lógicos (<, >, ==, !=, if, else) "
    "dentro de las funciones de lógica de negocio (CÓDIGO) para intentar engañar a los ASSETRTS de los archivos de TEST."
)

executor_prompt = (
    "Analiza el código mutado de Python frente a sus tests. Si el error sería detectado por un 'assert', "
    "responde 'MUTATION KILLED'. Si el test pasaría a pesar del error, responde 'MUTATION SURVIVED'."
)

auditor_prompt = (
    "Evalúa la robustez de la suite de pruebas de Python basándote en el resultado anterior. "
    "Sugiere qué tests faltan para cubrir los valores límite (edge cases)."
)

# Nodos
mutator_node = create_node(llm, tools, mutator_prompt, "mutador_logico")
executor_node = create_node(llm, [], executor_prompt, "ejecutor_de_tests")
auditor_node = create_node(llm, [], auditor_prompt, "auditor_de_robustez")

# 7. Construcción del Grafo
workflow = StateGraph(MutationState)
workflow.add_node("manager", mutation_manager_node)
workflow.add_node("mutador_logico", mutator_node)
workflow.add_node("ejecutor_de_tests", executor_node)
workflow.add_node("auditor_de_robustez", auditor_node)

for n in ["mutador_logico", "ejecutor_de_tests", "auditor_de_robustez"]:
    workflow.add_edge(n, "manager")

workflow.add_conditional_edges("manager", lambda x: x["next"], {
    "mutador_logico": "mutador_logico",
    "ejecutor_de_tests": "ejecutor_de_tests",
    "auditor_de_robustez": "auditor_de_robustez",
    "FINISH": END
})

workflow.set_entry_point("manager")
app_mutation = workflow.compile()

# 8. Ejecución
if __name__ == "__main__":
    inputs = {
        "messages": [
            HumanMessage(content="Analiza el repositorio https://github.com/usuario/repo. Localiza una función lógica y realiza un test de mutación.")
        ],
        "original_code": "", # Ahora es responsabilidad del agente llenarlo
        "mutated_code": ""
    }
    
    print("--- INICIANDO DETECTOR DE MUTACIONES ---\n")
    for s in app_mutation.stream(inputs, {"recursion_limit": 15}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 60)