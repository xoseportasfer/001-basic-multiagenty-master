import os
import tempfile
import subprocess
import shutil
import stat
from typing import TypedDict
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END

class SecurityState(TypedDict):
    repo_url: str
    code_context: str       # Aquí guardaremos el código real encontrado
    security_payloads: str   
    validation_audit: str    
    final_report: str

llm = ChatOllama(model="mistral", temperature=0)

# --- NODO 1: Minería de Código (Extrae la lógica real) ---
def code_mining_node(state: SecurityState):
    print(f"\n[PASO 1]: Minando código en {state['repo_url']} para buscar vulnerabilidades...")
    temp_dir = tempfile.mkdtemp()
    content_summary = ""
    try:
        subprocess.run(["git", "clone", "--depth", "1", state['repo_url'], temp_dir], check=True, capture_output=True)
        for root, _, files in os.walk(temp_dir):
            for f in files:
                # Analizamos archivos de lógica y modelos
                if f.endswith(".py") and "test" not in f.lower():
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as file:
                        code = file.read()
                        # Solo guardamos archivos que manejen datos o lógica de negocio
                        if "class" in code or "def " in code:
                            content_summary += f"\n--- FICHERO: {f} ---\n{code}\n"
    finally:
        shutil.rmtree(temp_dir, onerror=lambda func, path, _: os.chmod(path, stat.S_IWRITE) or func(path))
    
    return {"code_context": content_summary if content_summary else "No se detectó código analizable."}

# --- NODO 2: Analista de Vulnerabilidades Específicas ---
def vulnerability_analyst_node(state: SecurityState):
    print("[PASO 2]: Analizando flujos de datos y generando payloads específicos...")
    prompt = f"""
    Analiza este código fuente y detecta dónde se reciben datos externos (inputs, JSON, argumentos de función).
    Para CADA punto detectado, genera un payload de inyección (SQLi o XSS) que sea específico para ese campo.
    
    CÓDIGO FUENTE:
    {state['code_context'][:6000]} 
    """
    response = llm.invoke(prompt)
    return {"security_payloads": response.content}

# --- NODO 3: Auditor de Defensas Reales ---
def defense_checker_node(state: SecurityState):
    print("[PASO 3]: Buscando sanitizadores y validadores en el código...")
    prompt = f"""
    Basado en el código analizado, ¿existen validaciones reales? 
    Busca: Pydantic models, transformaciones de tipos (int(), str()), o filtros.
    Si NO los hay, marca la vulnerabilidad como CRÍTICA.
    
    CÓDIGO:
    {state['code_context'][:6000]}
    """
    response = llm.invoke(prompt)
    return {"validation_audit": response.content}

# --- NODO 4: Reporte Ejecutivo ---
def security_reporter_node(state: SecurityState):
    print("[PASO 4]: Consolidando reporte final...")
    report = f"""
    # 🛡️ AUDITORÍA DE SEGURIDAD BASADA EN CÓDIGO REAL
    
    ## 🔍 ANÁLISIS DE ENTRADAS Y PAYLOADS ESPECÍFICOS
    {state['security_payloads']}
    
    ## 🛡️ EVALUACIÓN DE DEFENSAS EXISTENTES
    {state['validation_audit']}
    
    ---
    *Conclusión: Se han analizado los flujos de datos reales del repositorio para evitar falsos positivos y teoría genérica.*
    """
    return {"final_report": report}

# (La construcción del grafo se mantiene igual, cambiando los nombres de los nodos)
builder = StateGraph(SecurityState)
builder.add_node("miner", code_mining_node)
builder.add_node("analyst", vulnerability_analyst_node)
builder.add_node("checker", defense_checker_node)
builder.add_node("reporter", security_reporter_node)

builder.add_edge(START, "miner")
builder.add_edge("miner", "analyst")
builder.add_edge("analyst", "checker")
builder.add_edge("checker", "reporter")
builder.add_edge("reporter", END)

app_sec_v2 = builder.compile()

if __name__ == "__main__":
    url = "https://github.com/xoseportasfer/xestor_reputacion_dixital"
    url = "https://github.com/nsidnev/fastapi-realworld-example-app"
    result = app_sec_v2.invoke({"repo_url": url})
    print("\n" + "="*70 + "\n" + result["final_report"] + "\n" + "="*70)