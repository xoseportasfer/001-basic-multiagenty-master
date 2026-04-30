import os
import tempfile
import subprocess
import shutil
import stat
from typing import TypedDict, List
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END

class ComplianceState(TypedDict):
    repo_url: str
    code_base: str
    detected_risks: List[str]
    compliance_report: str
    matrix_md: str

llm = ChatOllama(model="mistral", temperature=0)

# --- NODO 1: Minería de Datos Sensibles ---
def compliance_miner_node(state: ComplianceState):
    print(f"\n[PASO 1]: Escaneando código en {state['repo_url']} en busca de PII (Datos Sensibles)...")
    temp_dir = tempfile.mkdtemp()
    code_content = ""
    try:
        subprocess.run(["git", "clone", "--depth", "1", state['repo_url'], temp_dir], check=True, capture_output=True)
        for root, _, files in os.walk(temp_dir):
            for f in files:
                if f.endswith((".py", ".env")):
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as file:
                        content = file.read()
                        # Etiquetamos claramente el inicio y fin de cada archivo
                        code_content += f"\n--- INICIO ARCHIVO: {f} ---\n{content[:1500]}\n--- FIN ARCHIVO: {f} ---\n"
    finally:
        shutil.rmtree(temp_dir, onerror=lambda func, path, _: os.chmod(path, stat.S_IWRITE) or func(path))
    
    return {"code_base": code_content}

# --- NODO 2: Auditor de Normativas (Versión Proactiva) ---
def regulation_auditor_node(state: ComplianceState):
    print("[PASO 2]: Ejecutando Auditoría de Privacidad y Cumplimiento...")
    prompt = f"""
    Eres un Data Privacy Officer (DPO). Analiza este código:
    {state['code_base']}
    
    INSTRUCCIONES:
    1. Si encuentras riesgos (ej. passwords en texto plano, emails sin validar), lístalos.
    2. Si NO encuentras riesgos, identifica qué medidas de seguridad SI existen (ej. "Usa hashing para passwords", "Usa esquemas para validar emails").
    3. No dejes el reporte vacío. Si el código es seguro, emite un 'Certificado de Cumplimiento Positivo'.
    
    Analiza bajo GDPR, PCI y HIPAA.
    """
    response = llm.invoke(prompt)
    return {"detected_risks": [response.content]}

# --- NODO 3: Generador de Matriz de Cumplimiento (Resiliente) ---
def compliance_matrix_node(state: ComplianceState):
    print("[PASO 3]: Generando Matriz de Cumplimiento (Certificación de Seguridad)...")
    
    # Prompt reforzado para evitar tablas vacías
    prompt = f"""
    Eres un Auditor Senior de Cumplimiento. Basado en el análisis:
    {state['detected_risks']}
    
    INSTRUCCIONES DE FORMATO:
    1. Genera una tabla Markdown obligatoriamente.
    2. Si se detectaron riesgos, lístalos.
    3. Si el análisis indica que el código es seguro, crea entradas que certifiquen las BUENAS PRÁCTICAS encontradas (ej. "Uso de Pydantic para validación", "Hashing de passwords detectado").
    4. Usa este formato:
    | Fichero | Hallazgo / Práctica | Normativa | Riesgo | Recomendación |
    | :--- | :--- | :--- | :--- | :--- |
    """
    
    response = llm.invoke(prompt)
    return {"matrix_md": response.content}

# --- Construcción del Grafo ---
builder = StateGraph(ComplianceState)
builder.add_node("miner", compliance_miner_node)
builder.add_node("auditor", regulation_auditor_node)
builder.add_node("matrix", compliance_matrix_node)

builder.add_edge(START, "miner")
builder.add_edge("miner", "auditor")
builder.add_edge("auditor", "matrix")
builder.add_edge("matrix", END)

compliance_ai = builder.compile()

if __name__ == "__main__":
    # Probamos con el repo de siempre (o el de FastAPI que tiene modelos de usuario)
    url = "https://github.com/xoseportasfer/xestor_reputacion_dixital"
    url = "https://github.com/nsidnev/fastapi-realworld-example-app"
    url = "https://github.com/digininja/DVWA"
    result = compliance_ai.invoke({"repo_url": url})
    print("\n" + "="*80 + "\n" + result["matrix_md"] + "\n" + "="*80)