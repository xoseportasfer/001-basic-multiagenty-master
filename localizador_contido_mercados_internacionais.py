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
from langchain_community.tools import DuckDuckGoSearchRun

# 1. Configuración
warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())

# LLM: Mistral (Excelente para matices lingüísticos y creatividad)
llm = ChatOllama(model="mistral", temperature=0)
search_tool = [DuckDuckGoSearchRun()]

# 2. Definición del Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# 3. Orquestador de Localización (Localization Manager)
def localization_manager_node(state: AgentState):
    if not state["messages"]:
        return {"next": "traductor_tecnico"}
    
    last_msg = state["messages"][-1]
    last_actor = getattr(last_msg, "name", None)

    # Flujo: Traducción -> Transcreación Cultural -> Optimización SEO Local
    if last_actor == "traductor_tecnico":
        return {"next": "especialista_en_transcreacion"}
    if last_actor == "especialista_en_transcreacion":
        return {"next": "analista_seo_local"}
    if last_actor == "analista_seo_local":
        return {"next": "FINISH"}
    
    return {"next": "traductor_tecnico"}

# 4. Constructor de Nodos
def create_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    def node(state: AgentState):
        result = agent.invoke(state)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)],
        }
    return node

# 5. Prompts Especializados (Marketing & Lingüística)

traductor_prompt = (
    "Eres un Traductor Técnico Profesional. Tu tarea es realizar una traducción precisa "
    "del contenido original al idioma destino, manteniendo la terminología técnica correcta "
    "pero sin intentar adaptar todavía el estilo cultural."
)

transcreador_prompt = (
    "Eres un Experto en Transcreación y Adaptación Cultural. Tu misión es ajustar el texto traducido "
    "para que resuene con la audiencia local. Cambia frases hechas, referencias culturales, "
    "unidades de medida y el tono (formal/informal) según las normas sociales del país destino. "
    "El objetivo es que el contenido parezca escrito originalmente por un nativo."
)

seo_local_prompt = (
    "Eres un Especialista en SEO Internacional. Usa DuckDuckGo para investigar las palabras clave "
    "más buscadas y las tendencias actuales en el país destino para el año 2026. "
    "Optimiza el contenido transcreado integrando estas keywords de forma natural para maximizar "
    "el alcance orgánico en buscadores locales."
)

# Nodos
traductor_node = create_node(llm, [], traductor_prompt, "traductor_tecnico")
transcreador_node = create_node(llm, [], transcreador_prompt, "especialista_en_transcreacion")
seo_node = create_node(llm, search_tool, seo_local_prompt, "analista_seo_local")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("manager", localization_manager_node)
workflow.add_node("traductor_tecnico", traductor_node)
workflow.add_node("especialista_en_transcreacion", transcreador_node)
workflow.add_node("analista_seo_local", seo_node)

for node in ["traductor_tecnico", "especialista_en_transcreacion", "analista_seo_local"]:
    workflow.add_edge(node, "manager")

workflow.add_conditional_edges(
    "manager",
    lambda x: x["next"],
    {
        "traductor_tecnico": "traductor_tecnico",
        "especialista_en_transcreacion": "especialista_en_transcreacion",
        "analista_seo_local": "analista_seo_local",
        "FINISH": END
    }
)

workflow.set_entry_point("manager")
localization_app = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    contenido_original = (
    "En Iberdrola, lideramos la transición hacia un modelo energético sostenible mediante soluciones personalizadas de consultoría. "
    "Nuestros expertos analizan tu perfil de consumo para implementar estrategias de eficiencia que garantizan un ahorro del 20% en tu factura eléctrica "
    "desde el primer mes, optimizando cada kilovatio hora mediante tecnología de redes inteligentes.\n\n"
    "No permitas que tu negocio pierda competitividad por costes energéticos obsoletos; es el momento de unirse a la revolución verde. "
    "Al elegir nuestras soluciones de autoconsumo fotovoltaico e hidrógeno verde, no solo reduces costes, sino que posicionas tu marca "
    "en la vanguardia de la descarbonización y el compromiso medioambiental global."
)
    mercado_destino = "Reino Unido (UK)"
    
    inputs = {"messages": [HumanMessage(content=f"Localiza este contenido para {mercado_destino}: {contenido_original}")]}
    
    print(f"--- LOCALIZADOR DE CONTENIDO PARA MERCADOS INTERNACIONALES ---")
    
    for s in localization_app.stream(inputs, {"recursion_limit": 25}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            if node_name != "manager":
                print(f"\n[FASE]: {node_name.upper()}")
                print(s[node_name]["messages"][-1].content)
                print("-" * 50)