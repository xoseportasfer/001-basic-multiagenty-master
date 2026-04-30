import os
import ast
import tempfile
import subprocess
import shutil
from typing import TypedDict, List
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END

# --- Configuración do Estado ---
class DocAuditState(TypedDict):
    repo_url: str
    function_pairs: List[dict]
    discrepancy_report: str
    final_output: str

llm = ChatOllama(model="mistral", temperature=0)

# --- NODO 1: Extractor Mejorado ---
def pair_extractor_node(state: DocAuditState):
    print(f"\n[PASO 1]: Buscando funciones en {state['repo_url']}...")
    temp_dir = tempfile.mkdtemp()
    pairs = []
    try:
        subprocess.run(["git", "clone", "--depth", "1", state['repo_url'], temp_dir], check=True, capture_output=True)
        for root, _, files in os.walk(temp_dir):
            for f in files:
                if f.endswith(".py"):
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as file:
                        source = file.read()
                        try:
                            tree = ast.parse(source)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    # Intentamos sacar docstring O las primeras líneas de comentarios
                                    docstring = ast.get_docstring(node)
                                    if not docstring:
                                        # Si no hay docstring, buscamos comentarios manuales arriba (simplificado)
                                        docstring = "Sin docstring formal (Revisar comentarios #)"
                                    
                                    pairs.append({
                                        "file": f,
                                        "name": node.name,
                                        "docstring": docstring,
                                        "body": ast.unparse(node)
                                    })
                        except: continue
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    return {"function_pairs": pairs}


# --- NODO 2: Analista de Veracidade (O "Detector de Mentiras") ---
def truth_analyst_node(state: DocAuditState):
    print(f"[PASO 2]: Comparando intención vs. implementación en {len(state['function_pairs'])} funcións...")
    report = ""
    for func in state['function_pairs']:
        prompt = f"""
        Eres un revisor de código senior. Compara o DOCSTRING co CÓDIGO REAL.
        
        FUNCIÓN: {func['name']}
        DOCSTRING: {func['docstring']}
        CÓDIGO:
        {func['body']}
        
        VERDICTO:
        1. ¿O docstring describe fielmente o que fai o código?
        2. ¿Hai parámetros ou retornos mencionados que non existen ou viceversa?
        3. Clasifica como: [VERAZ], [DESACTUALIZADO] ou [MENTIRA DETECTADA].
        """
        response = llm.invoke(prompt)
        report += f"\n--- Función: {func['name']} ({func['file']}) ---\n{response.content}\n"
    
    return {"discrepancy_report": report}

# --- NODO 3: Generador de Informe (Anti-Alucinaciones) ---
def executive_reporter_node(state: DocAuditState):
    if not state['function_pairs']:
        return {"final_output": "❌ NO SE ENCONTRARON FUNCIONES CON DOCSTRINGS. El repositorio parece no seguir el estándar de documentación de Python (PEP 257)."}

    print("[PASO 3]: Xerando informe de integridade documental...")
    prompt = f"""
    Resume este análisis: {state['discrepancy_report']}
    Si no hay discrepancias, felicita al programador. 
    NO inventes funciones que no están en el texto anterior.
    """
    response = llm.invoke(prompt)
    return {"final_output": response.content}

# --- Construcción do Grafo ---
builder = StateGraph(DocAuditState)
builder.add_node("extractor", pair_extractor_node)
builder.add_node("analyst", truth_analyst_node)
builder.add_node("reporter", executive_reporter_node)

builder.add_edge(START, "extractor")
builder.add_edge("extractor", "analyst")
builder.add_edge("analyst", "reporter")
builder.add_edge("reporter", END)

doc_auditor = builder.compile()

if __name__ == "__main__":
    url = "https://github.com/xoseportasfer/xestor_reputacion_dixital"
    result = doc_auditor.invoke({"repo_url": url})
    print("\n" + "="*80)
    print("📋 INFORME DE AUDITORÍA DE COMENTARIOS")
    print("="*80)
    print(result["final_output"])