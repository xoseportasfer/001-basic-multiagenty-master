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

# LLM: Mistral (Excelente para análisis semántico)
llm = ChatOllama(model="mistral", temperature=0.2)
search_tool = [TavilySearchResults(max_results=5)]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador de SEO (SEO Manager)
def manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "analista_competencia_seo"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Análisis de Competencia -> Auditoría de URL -> Recomendaciones
    if last_actor == "analista_competencia_seo":
        return {"next": "auditor_contenido_onpage"}
    if last_actor == "auditor_contenido_onpage":
        return {"next": "estratega_seo_copywriting"}
    if last_actor == "estratega_seo_copywriting":
        return {"next": "FINISH"}
    
    return {"next": "analista_competencia_seo"}

# 4. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts Especializados (Enfoque en Marketing Digital)
analista_competencia_prompt = (
    "Eres un Analista de SEO Competitivo. Tu misión es buscar las palabras clave por las que "
    "rankean los competidores del sector indicado. Identifica qué tipo de contenido les está "
    "funcionando (blogs, guías, herramientas) y extrae las keywords con mayor potencial de tráfico."
)

auditor_onpage_prompt = (
    "Eres un Auditor SEO Técnico. Tu tarea es analizar la URL proporcionada por el usuario "
    "(o el contenido descrito) para evaluar el uso de keywords, la estructura de encabezados (H1, H2, H3) "
    "y la calidad del contenido respecto a la intención de búsqueda del usuario."
)

copywriter_seo_prompt = (
    "Eres un Estratega de SEO Copywriting. Basándote en la competencia y la auditoría, "
    "sugiere cambios específicos: un Título SEO (Title Tag) optimizado, una Meta Descripción "
    "persuasiva y una nueva estructura de encabezados. Explica cómo estos cambios mejorarán el ranking."
)

# Nodos
analista_node = create_node(llm, search_tool, analista_competencia_prompt, "analista_competencia_seo")
auditor_node = create_node(llm, search_tool, auditor_onpage_prompt, "auditor_contenido_onpage")
copywriter_node = create_node(llm, [], copywriter_seo_prompt, "estratega_seo_copywriting")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", manager_node)
workflow.add_node("analista_competencia_seo", analista_node)
workflow.add_node("auditor_contenido_onpage", auditor_node)
workflow.add_node("estratega_seo_copywriting", copywriter_node)

for node in ["analista_competencia_seo", "auditor_contenido_onpage", "estratega_seo_copywriting"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "analista_competencia_seo": "analista_competencia_seo",
        "auditor_contenido_onpage": "auditor_contenido_onpage",
        "estratega_seo_copywriting": "estratega_seo_copywriting",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
seo_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    url_usuario = "https://www.tienda-de-bicicletas.com/montana"
    inputs = {"messages": [HumanMessage(content=f"Optimiza el SEO para esta web de bicicletas de montaña: {url_usuario}")]}
    
    print(f"--- Sistema Inteligente de Optimización SEO ---")
    print(f"Objetivo: {url_usuario}\n" + "="*50)
    
    for s in seo_app.stream(inputs, {"recursion_limit": 20}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)