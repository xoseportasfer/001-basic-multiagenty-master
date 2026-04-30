import os
import tempfile
import subprocess
import shutil
import stat
from typing import TypedDict
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END

class QAState(TypedDict):
    repo_url: str
    discovered_tests: str 
    metrics: str
    executive_report: str

llm = ChatOllama(model="mistral", temperature=0)

# --- NODO 1: Inspector de Código ---
def code_inspector_node(state: QAState):
    print(f"\n[PASO 1]: Clonando e inspeccionando código en {state['repo_url']}...")
    def remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    temp_dir = tempfile.mkdtemp()
    extracted_content = ""
    try:
        subprocess.run(["git", "clone", "--depth", "1", state['repo_url'], temp_dir], check=True, capture_output=True)
        for root, _, files in os.walk(temp_dir):
            for f in files:
                if "test" in f.lower() and f.endswith(".py"):
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as file:
                        extracted_content += f"\n--- ARCHIVO: {f} ---\n{file.read()}\n"
    finally:
        shutil.rmtree(temp_dir, onerror=remove_readonly)
    return {"discovered_tests": extracted_content}

# --- NODO 2: Analista (Genera listado y simula resultados) ---
def technical_analyst_node(state: QAState):
    print("[PASO 2]: Evaluando tests y simulando resultados...")
    prompt = f"""
    Analiza estos tests y genera un informe técnico detallado:
    1. Lista cada función de test encontrada.
    2. Evalúa si pasaría o fallaría basándote en la lógica del código (Simulación).
    3. Cuenta: Total de tests, Estimados como PASSED, Estimados como FAILED.

    CONTENIDO DE LOS TESTS:
    {state['discovered_tests']}
    """
    response = llm.invoke(prompt)
    return {"metrics": response.content}

# --- NODO 3: Redactor Ejecutivo (Incluye Resumen Final) ---
def stakeholder_reporter_node(state: QAState):
    print("[PASO 3]: Redactando Reporte Ejecutivo Final...")
    prompt = f"""
    Eres un Product Manager. Genera un reporte final con este orden exacto:
    
    1. 📊 RESUMEN DE RESULTADOS:
       - Total de Tests: [Número]
       - ✅ Pasados: [Número]
       - ❌ Fallidos: [Número]
       - 📈 Cobertura Estimada: [Porcentaje]

    2. 📋 LISTADO DETALLADO DE TESTS:
       (Genera una tabla con: Nombre del Test | Resultado Estimado | Descripción)

    3. 💡 RECOMENDACIONES DE NEGOCIO.

    DATOS TÉCNICOS:
    {state['metrics']}
    """
    response = llm.invoke(prompt)
    return {"executive_report": response.content}

# Construcción del Grafo
builder = StateGraph(QAState)
builder.add_node("inspector", code_inspector_node)
builder.add_node("analista", technical_analyst_node)
builder.add_node("redactor", stakeholder_reporter_node)
builder.add_edge(START, "inspector")
builder.add_edge("inspector", "analista")
builder.add_edge("analista", "redactor")
builder.add_edge("redactor", END)
app_qa_final = builder.compile()

if __name__ == "__main__":
    url = "https://github.com/xoseportasfer/xestor_reputacion_dixital"
    result = app_qa_final.invoke({"repo_url": url})
    print("\n" + "="*70 + "\n" + result["executive_report"] + "\n" + "="*70)