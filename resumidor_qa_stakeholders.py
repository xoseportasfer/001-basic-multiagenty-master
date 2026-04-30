import os
import operator
import tempfile
import subprocess
import shutil
import stat
from typing import TypedDict, Annotated, Sequence
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END

# 1. Definición del Estado
class QAState(TypedDict):
    repo_url: str
    repo_content: str       # Contenido de código y tests extraídos
    metrics: str
    executive_report: str

llm = ChatOllama(model="mistral", temperature=0.1)

# --- HERRAMIENTA: Clonador y Extractor ---
@tool
def clone_and_extract_for_qa(repo_url: str) -> str:
    """Clona un repo y extrae un resumen del código y tests para el reporte."""
    def remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    temp_dir = tempfile.mkdtemp()
    try:
        print(f"\n>>> [SISTEMA]: Accediendo a {repo_url}...")
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], 
                        check=True, capture_output=True, text=True)
        
        summary = ""
        for root, dirs, filenames in os.walk(temp_dir):
            if '.git' in dirs: dirs.remove('.git')
            for f in filenames:
                if f.endswith(('.py', '.test.py', 'pytest.ini')):
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as file:
                        summary += f"\nFICHERO: {f}\n{file.read()[:500]}\n" # Fragmentos para métricas
        return summary if summary else "No se encontró código Python."
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        shutil.rmtree(temp_dir, onerror=remove_readonly)

# --- NODO 1: Analista de Repositorio ---
def repo_analyzer_node(state: QAState):
    print("[PASO 1]: Extrayendo información del repositorio...")
    # Ejecutamos la herramienta manualmente para simplificar el flujo
    content = clone_and_extract_for_qa.invoke(state['repo_url'])
    
    prompt = f"""
    Eres un Analista de QA. Basado en este código y estructura de tests, estima:
    1. Densidad de tests (¿Hay muchos o pocos tests para el código visto?).
    2. Cobertura lógica visual (¿Se prueban casos críticos?).
    3. Complejidad técnica.
    
    CÓDIGO EXTRAÍDO:
    {content[:5000]}
    """
    response = llm.invoke(prompt)
    return {"repo_content": content, "metrics": response.content}

# --- NODO 2: Redactor para Stakeholders ---
def stakeholder_reporter_node(state: QAState):
    print("[PASO 2]: Traduciendo hallazgos para perfiles no técnicos...")
    prompt = f"""
    Eres un Product Manager. Traduce este análisis técnico en un reporte de salud del proyecto.
    Usa el sistema de semáforos:
    🔴 Crítico: Falta de tests o código inestable.
    🟡 Precaución: Cobertura parcial.
    🟢 Estable: Buena suite de pruebas.
    
    ANÁLISIS TÉCNICO:
    {state['metrics']}
    """
    response = llm.invoke(prompt)
    return {"executive_report": response.content}

# --- 2. Construcción del Grafo ---
builder = StateGraph(QAState)

builder.add_node("analista_repo", repo_analyzer_node)
builder.add_node("redactor_jefes", stakeholder_reporter_node)

builder.add_edge(START, "analista_repo")
builder.add_edge("analista_repo", "redactor_jefes")
builder.add_edge("redactor_jefes", END)

app_qa_github = builder.compile()

# --- 3. Ejecución Real ---
if __name__ == "__main__":
    # URL del repositorio a analizar
    target_repo = "https://github.com/xoseportasfer/xestor_reputacion_dixital"

    print(f"--- INICIANDO RESUMIDOR DE QA PARA: {target_repo} ---")
    
    inputs = {"repo_url": target_repo}
    
    for output in app_qa_github.stream(inputs):
        for key, value in output.items():
            if key == "redactor_jefes":
                print("\n" + "="*50)
                print("📢 REPORTE EJECUTIVO PARA STAKEHOLDERS")
                print("="*50)
                print(value["executive_report"])
            else:
                print(f"✓ Fase {key.upper()} completada.")