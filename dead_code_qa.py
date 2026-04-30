import os
import tempfile
import subprocess
import shutil
import stat
from typing import TypedDict, List
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END

class ZombieState(TypedDict):
    repo_url: str
    source_catalog: str    # Lista de todas las funciones definidas
    usage_analysis: str    # Análisis de dónde se usan (o no)
    pr_proposal: str       # Propuesta de limpieza
    final_report: str

llm = ChatOllama(model="mistral", temperature=0)

# --- NODO 1: Catalogador de Funciones ---
def function_cataloger_node(state: ZombieState):
    print(f"\n[PASO 1]: Mapeando todas las definiciones de funciones en {state['repo_url']}...")
    temp_dir = tempfile.mkdtemp()
    catalog = ""
    try:
        subprocess.run(["git", "clone", "--depth", "1", state['repo_url'], temp_dir], check=True, capture_output=True)
        for root, _, files in os.walk(temp_dir):
            for f in files:
                if f.endswith(".py") and "test" not in f.lower():
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as file:
                        lines = file.readlines()
                        catalog += f"\nARCHIVO: {f}\n"
                        for line in lines:
                            if line.strip().startswith("def "):
                                catalog += line.strip() + "\n"
    finally:
        shutil.rmtree(temp_dir, onerror=lambda func, path, _: os.chmod(path, stat.S_IWRITE) or func(path))
    
    return {"source_catalog": catalog}

# --- NODO 2: Analista de Referencias (Buscador de Zombis con Certeza) ---
def reference_analyzer_node(state: ZombieState):
    print("[PASO 2]: Ejecutando Auditoría de Referencias Cruzadas (Certeza Alta)...")
    prompt = f"""
    Eres un optimizador de código de élite. Analiza este catálogo de funciones:
    {state['source_catalog']}
    
    CRITERIOS DE ELIMINACIÓN (ZOMBIE):
    1. La función está definida (`def`) pero su nombre no aparece en ninguna otra línea del catálogo.
    2. Son funciones de utilidad que no están integradas en el grafo principal.
    3. NO uses un lenguaje ambiguo como "parece ser" o "no se puede decir". 
    
    INSTRUCCIÓN: Genera una lista definitiva de funciones que DEBEN ser revisadas para eliminación inmediata.
    Si una función no tiene llamadas internas visibles, márcala como 'ZOMBIE CONFIRMADO'.
    """
    response = llm.invoke(prompt)
    return {"usage_analysis": response.content}

# --- NODO 3: Redactor de PR (Formato de Impacto) ---
def pr_generator_node(state: ZombieState):
    print("[PASO 3]: Redactando Pull Request de Limpieza Técnica...")
    prompt = f"""
    Basado en el análisis de funciones muertas:
    {state['usage_analysis']}
    
    Genera un Pull Request profesional con esta estructura:
    - RESUMEN: Cuántas funciones se eliminan y cuántas líneas de código se ahorran (estimado).
    - LISTA NEGRA: Nombre de la función y archivo.
    - BENEFICIO TÉCNICO: Por qué esto mejora la salud del repo.
    """
    response = llm.invoke(prompt)
    return {"pr_proposal": response.content}

# --- NODO 4: Consolidador de Reporte ---
def cleanup_reporter_node(state: ZombieState):
    print("[PASO 4]: Consolidando reporte de optimización...")
    report = f"""
    # 🧟 REPORTE DEL CAZADOR DE ZOMBIS
    
    ## 🔍 ANÁLISIS DE CÓDIGO MUERTO
    {state['usage_analysis']}
    
    ## 🚀 PROPUESTA DE PULL REQUEST
    {state['pr_proposal']}
    
    ---
    *Valor: Mantener el repositorio limpio reduce la carga cognitiva del equipo y la superficie de error.*
    """
    return {"final_report": report}

# --- Construcción del Grafo ---
builder = StateGraph(ZombieState)
builder.add_node("cataloger", function_cataloger_node)
builder.add_node("analyzer", reference_analyzer_node)
builder.add_node("generator", pr_generator_node)
builder.add_node("reporter", cleanup_reporter_node)

builder.add_edge(START, "cataloger")
builder.add_edge("cataloger", "analyzer")
builder.add_edge("analyzer", "generator")
builder.add_edge("generator", "reporter")
builder.add_edge("reporter", END)

app_zombie = builder.compile()

if __name__ == "__main__":
    url = "https://github.com/xoseportasfer/xestor_reputacion_dixital"
    result = app_zombie.invoke({"repo_url": url})
    print("\n" + "="*70 + "\n" + result["final_report"] + "\n" + "="*70)