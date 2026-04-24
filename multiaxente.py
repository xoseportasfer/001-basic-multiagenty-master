import os
import operator
import warnings
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv, find_dotenv

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

# 1. Configuración
warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())

# LLM: Mistral
llm = ChatOllama(model="mistral", temperature=0)

# 2. Herramientas
tools = [TavilySearchResults(max_results=1)]

# 3. Estado
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

options = ["online_researcher", "blog_manager", "social_media_manager", "FINISH"]

# 4. El Manager (Lógica Híbrida)
def manager_node(state: AgentState):
    # Lógica de Raíles: Miramos quién fue el último en hablar
    if not state["messages"]:
        return {"next": "online_researcher"}
    
    last_msg = state["messages"][-1]
    # Identificamos al último actor por su nombre
    last_actor = getattr(last_msg, "name", None)

    # Si ya investigó, forzamos blog. Si ya escribió blog, forzamos social media.
    if last_actor == "online_researcher":
        return {"next": "blog_manager"}
    if last_actor == "blog_manager":
        return {"next": "social_media_manager"}
    if last_actor == "social_media_manager":
        return {"next": "FINISH"}
    
    return {"next": "online_researcher"}

# 5. Creador de Nodos mejorado
def create_agent_node(llm, tools, system_prompt, name):
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    
    def node(state: AgentState):
        result = agent.invoke(state)
        last_message = result["messages"][-1]
        # Devolvemos el mensaje con el 'name' para que el manager sepa quién habló
        return {
            "messages": [HumanMessage(content=last_message.content, name=name)],
        }
    return node

# Nodos con instrucciones SÚPER específicas
researcher_node = create_agent_node(llm, tools, "Eres investigador. Solo da puntos clave de Sartre. No redactes artículos.", "online_researcher")
blog_node = create_agent_node(llm, [], "Eres redactor. Crea un artículo de blog breve basado en la investigación.", "blog_manager")
social_node = create_agent_node(llm, [], "Eres experto en Twitter. Crea un tweet sobre el artículo anterior.", "social_media_manager")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

workflow.add_node("content_marketing_manager", manager_node)
workflow.add_node("online_researcher", researcher_node)
workflow.add_node("blog_manager", blog_node)
workflow.add_node("social_media_manager", social_node)

# Aristas
for member in ["online_researcher", "blog_manager", "social_media_manager"]:
    workflow.add_edge(member, "content_marketing_manager")

workflow.add_conditional_edges(
    "content_marketing_manager",
    lambda x: x["next"],
    {
        "online_researcher": "online_researcher",
        "blog_manager": "blog_manager",
        "social_media_manager": "social_media_manager",
        "FINISH": END
    }
)

workflow.set_entry_point("content_marketing_manager")
multiagent = workflow.compile()

# 7. Ejecución
if __name__ == "__main__":
    inputs = {"messages": [HumanMessage(content="Investiga el existencialismo en Sartre, haz un blog y un tweet.")]}
    for s in multiagent.stream(inputs, {"recursion_limit": 20}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            print(f"\n--- [TRANSICIÓN]: {node_name} ---")
            if "messages" in s[node_name]:
                print(s[node_name]["messages"][-1].content)
            else:
                print(s[node_name])