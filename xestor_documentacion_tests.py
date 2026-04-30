import os
import operator
import tempfile
import subprocess
import shutil
import stat
from typing import TypedDict, Annotated, Sequence
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import StateGraph, START, END

# 1. Definición del Estado del Grafo
class DocState(TypedDict):
    repo_url: str
    test_analysis: str      # Análisis de la lógica de los tests
    readme_update: str      # Propuesta de texto para el README/Wiki
    flowchart_mermaid: str  # Código Mermaid.js para diagramas de flujo
    final_report: str

llm = ChatOllama(model="mistral", temperature=0.2)

# --- NODO 1: Analista de Lógica de Tests ---
def test_logic_analyzer_node(state: DocState):
    print(f"\n[PASO 1]: Analizando cambios y lógica en {state['repo_url']}...")
    
    # Simulación de extracción de código (usando la lógica de clonación anterior)
    # Aquí el agente identifica qué hace cada test.
    prompt = f"Analiza los tests del repositorio {state['repo_url']}. " \
             "Explica la intención de cada test y qué flujos de negocio valida."
    
    response = llm.invoke(prompt)
    return {"test_analysis": response.content}

# --- NODO 2: Redactor de Documentación (README/Wiki) ---
def documentation_writer_node(state: DocState):
    print("[PASO 2]: Actualizando documentación técnica (README/Wiki)...")
    prompt = f"""
    Eres un Technical Writer. Basado en este análisis:
    {state['test_analysis']}
    
    Genera una sección '### Guía de Pruebas' para un README.md. 
    Debe ser clara, concisa y explicar cómo funcionan los tests para un nuevo desarrollador.
    """
    response = llm.invoke(prompt)
    return {"readme_update": response.content}

# --- NODO 3: Arquitecto de Diagramas (Mermaid.js) ---
def diagram_architect_node(state: DocState):
    print("[PASO 3]: Generando diagramas de flujo actualizados...")
    prompt = f"""
    Basado en la lógica de estos tests:
    {state['test_analysis']}
    
    Genera un diagrama de flujo en formato Mermaid.js (graph TD) que represente 
    el flujo de validación del software. Solo devuelve el código del diagrama.
    """
    response = llm.invoke(prompt)
    return {"flowchart_mermaid": response.content}

# --- NODO 4: Consolidador de Documentación ---
def doc_consolidator_node(state: DocState):
    print("[PASO 4]: Consolidando paquete de documentación...")
    report = f"""
    # 📑 PAQUETE DE ACTUALIZACIÓN DE DOCUMENTACIÓN
    
    ## 📝 README / WIKI SUGERIDO
    {state['readme_update']}
    
    ## 📊 DIAGRAMA DE FLUJO (Mermaid)
    ```mermaid
    {state['flowchart_mermaid']}
    ```
    
    ---
    *Valor: Documentación sincronizada con la lógica real de los tests.*
    """
    return {"final_report": report}

# --- 2. Construcción del Grafo ---
builder = StateGraph(DocState)

builder.add_node("analista", test_logic_analyzer_node)
builder.add_node("redactor", documentation_writer_node)
builder.add_node("arquitecto", diagram_architect_node)
builder.add_node("consolidador", doc_consolidator_node)

builder.add_edge(START, "analista")
builder.add_edge("analista", "redactor")
builder.add_edge("redactor", "arquitecto")
builder.add_edge("arquitecto", "consolidador")
builder.add_edge("consolidador", END)

app_docs = builder.compile()

# --- 3. Ejecución ---
if __name__ == "__main__":
    url = "https://github.com/xoseportasfer/xestor_reputacion_dixital"
    result = app_docs.invoke({"repo_url": url})
    print("\n" + "="*60)
    print(result["final_report"])
    print("="*60)