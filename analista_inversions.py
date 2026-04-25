import os
import functools
import operator
import warnings
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv, find_dotenv

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults

# 1. Configuración
warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())

# LLM: Mistral (Excelente para razonamiento lógico y financiero)
llm = ChatOllama(model="mistral", temperature=0)
search_tool = [TavilySearchResults(max_results=5)]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador Financiero (Investment Manager)
def manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "extractor_metricas_clave"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Métricas -> Sentimiento -> Recomendación
    if last_actor == "extractor_metricas_clave":
        return {"next": "analista_sentimiento_mercado"}
    if last_actor == "analista_sentimiento_mercado":
        return {"next": "comite_de_inversion"}
    if last_actor == "comite_de_inversion":
        return {"next": "FINISH"}
    
    return {"next": "extractor_metricas_clave"}

# 4. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts Especializados (Contexto FinTech)
extractor_prompt = (
    "Eres un Analista Cuantitativo. Tu misión es extraer indicadores financieros actuales "
    "de la empresa solicitada. Busca específicamente: P/E Ratio, Dividend Yield, "
    "Crecimiento de Ingresos (Revenue Growth) y Niveles de Deuda. "
    "Presenta los datos de forma limpia y numérica."
)

sentimiento_prompt = (
    "Eres un Analista de Sentimiento de Mercado. Busca noticias financieras de las últimas "
    "48 horas sobre la empresa. Clasifica el tono general como Positivo, Neutral o Negativo "
    "y destaca eventos clave (juicios, lanzamientos, cambios en el CEO) que puedan afectar la acción."
)

comite_prompt = (
    "Eres un Director de Inversiones. Basándote en las métricas cuantitativas y el sentimiento "
    "recibido, genera un informe final. Debe incluir: \n"
    "1. Recomendación clara (Comprar, Mantener o Vender).\n"
    "2. Justificación técnica.\n"
    "3. Análisis de Riesgos (qué podría salir mal).\n"
    "Sé conservador y profesional en tu juicio."
)

# Nodos
extractor_node = create_node(llm, search_tool, extractor_prompt, "extractor_metricas_clave")
sentimiento_node = create_node(llm, search_tool, sentimiento_prompt, "analista_sentimiento_mercado")
comite_node = create_node(llm, [], comite_prompt, "comite_de_inversion")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", manager_node)
workflow.add_node("extractor_metricas_clave", extractor_node)
workflow.add_node("analista_sentimiento_mercado", sentimiento_node)
workflow.add_node("comite_de_inversion", comite_node)

for node in ["extractor_metricas_clave", "analista_sentimiento_mercado", "comite_de_inversion"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "extractor_metricas_clave": "extractor_metricas_clave",
        "analista_sentimiento_mercado": "analista_sentimiento_mercado",
        "comite_de_inversion": "comite_de_inversion",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
finance_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    ticker = "Microsoft"
    inputs = {"messages": [HumanMessage(content=f"Realiza un análisis de inversión completo para: {ticker}")]}
    
    print(f"--- Sistema de Inteligencia Financiera Multi-Agente ---")
    print(f"Activo bajo análisis: {ticker}\n" + "="*50)
    
    for s in finance_app.stream(inputs, {"recursion_limit": 25}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)