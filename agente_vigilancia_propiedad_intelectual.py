import operator
from typing import Annotated, Sequence, TypedDict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# --- 1. HERRAMIENTAS DE VIGILANCIA DIGITAL ---

@tool
def domain_social_scanner(brand_name: str):
    """Busca dominios sospechosos, perfiles falsos en redes y menciones de marca no autorizadas."""
    search = DuckDuckGoSearchRun()
    # Buscamos variaciones comunes y sitios de estafas
    queries = [
        f'"{brand_name}" official site -site:.com', # Busca posibles impostores
        f'"{brand_name}" scam OR fake OR counterfeit',
        f'"{brand_name}" instagram OR tiktok OR twitter profile'
    ]
    results = []
    for q in queries:
        results.append(search.run(q))
    return "\n".join(results)

@tool
def whois_simulated_lookup(domain_url: str):
    """Simula una consulta de propiedad de dominio para ver quién está detrás de la infracción."""
    # En un entorno real, aquí usarías una API de WHOIS
    search = DuckDuckGoSearchRun()
    return search.run(f"whois information for {domain_url}")

# --- 2. DEFINICIÓN DEL ESTADO ---
class IPProtectionState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# --- 3. CONSTRUCTOR DE NODOS ---
def create_agent_node(llm, tools, system_prompt, name):
    llm_with_tools = llm.bind_tools(tools)
    
    def node(state: IPProtectionState):
        instruction = (
            f"\n\n[ROL]: {system_prompt}\n"
            "OBJETIVO: Identificar infracciones de marca. Si encuentras un uso legítimo (ej. noticias), "
            "descártalo. Enfócate en suplantación de identidad o venta de falsificaciones."
        )
        messages = state["messages"] + [SystemMessage(content=instruction)]
        result = llm_with_tools.invoke(messages)
        result.name = name
        return {"messages": [result]}
    return node

# --- 4. PROMPTS DE LOS AGENTES ---

IP_WATCHMAN_PROMPT = """Eres un Especialista en Vigilancia Digital de Marcas. Tu misión es 
encontrar sitios web, dominios o perfiles en redes sociales que utilicen el nombre de la 
marca del cliente sin autorización, especialmente aquellos que parecen intentar confundir 
al consumidor (phishing o venta de productos falsos)."""

INFRINGEMENT_ANALYST_PROMPT = """Eres un Abogado de Propiedad Intelectual. Analiza los hallazgos 
del vigilante. Clasifica la infracción como: 
- BAJA: Uso en blogs o críticas. 
- MEDIA: Uso de logotipos sin permiso. 
- ALTA: Suplantación de identidad, venta de falsificaciones o dominios engañosos."""

LEGAL_ENFORCER_PROMPT = """Eres un Especialista en Litigios de IP. Tu tarea es redactar un 
'Requerimiento Extrajudicial de Cese y Desistimiento' (Cease and Desist Letter) formal y 
contundente. Incluye los fundamentos legales de protección de marca y exige la retirada 
inmediata del contenido bajo amenaza de acciones legales."""

# --- 5. CONFIGURACIÓN DEL GRAFO ---

llm = ChatOllama(model="mistral", temperature=0)

# Nodos
watchman_node = create_agent_node(llm, [domain_social_scanner], IP_WATCHMAN_PROMPT, "ip_watchman")
analyst_node = create_agent_node(llm, [whois_simulated_lookup], INFRINGEMENT_ANALYST_PROMPT, "ip_analyst")
enforcer_node = create_agent_node(llm, [], LEGAL_ENFORCER_PROMPT, "legal_enforcer")

def manager_node(state: IPProtectionState):
    if not state["messages"] or len(state["messages"]) < 2:
        return {"next_agent": "ip_watchman"}
    
    last_actor = state["messages"][-1].name
    
    if last_actor == "ip_watchman":
        return {"next_agent": "ip_analyst"}
    if last_actor == "ip_analyst":
        return {"next_agent": "legal_enforcer"}
    
    return {"next_agent": "FINISH"}

workflow = StateGraph(IPProtectionState)
workflow.add_node("manager", manager_node)
workflow.add_node("ip_watchman", watchman_node)
workflow.add_node("ip_analyst", analyst_node)
workflow.add_node("legal_enforcer", enforcer_node)

workflow.set_entry_point("manager")

for node in ["ip_watchman", "ip_analyst", "legal_enforcer"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges("manager", lambda x: x["next_agent"], {
    "ip_watchman": "ip_watchman",
    "ip_analyst": "ip_analyst",
    "legal_enforcer": "legal_enforcer",
    "FINISH": END
})

app = workflow.compile()

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    marca_a_proteger = "Zara"
    inputs = {"messages": [HumanMessage(content=f"Inicia vigilancia de marca para: {marca_a_proteger}")]}
    
    for s in app.stream(inputs, {"recursion_limit": 15}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 70)