import os
import functools
import operator
import requests
import warnings
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup

# LangChain & LangGraph
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
# Importación moderna y robusta para Tavily

from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

# 1. Configuración inicial
warnings.filterwarnings("ignore", category=SyntaxWarning)
_ = load_dotenv(find_dotenv())

# LLM: Usamos Mistral vía Ollama
# Asegúrate de que Ollama esté corriendo y tengas el modelo: ollama pull mistral
llm = ChatOllama(model="mistral", temperature=0)

# 2. Herramientas
@tool
def process_search_tool(url: str) -> str:
    """Parse web content with BeautifulSoup."""
    try:
        response = requests.get(url=url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        # Limitamos el texto para no saturar el contexto de Mistral
        return soup.get_text()[:2000] 
    except Exception as e:
        return f"Error leyendo la URL: {e}"

# Lista de herramientas (Requiere TAVILY_API_KEY en .env)
tools = [TavilySearchResults(max_results=1), process_search_tool]

# 3. Definición del Estado
class AgentState(TypedDict):
    # El historial se acumula gracias a operator.add
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

content_marketing_team = ["online_researcher", "blog_manager", "social_media_manager"]
options = ["FINISH"] + content_marketing_team

class Router(TypedDict):
    """Esquema de salida estructurada para el enrutador."""
    next: str

# 4. El Manager (Lógica de control corregida)
manager_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a content marketing manager overseeing: {team}. "
               "Decide who acts next or FINISH. You must ONLY output the name of the role."),
    MessagesPlaceholder(variable_name="messages"),
    ("system", "Who should act next? Select one of: {options}. Do not explain your choice."),
]).partial(options=str(options), team=", ".join(content_marketing_team))

def manager_node(state: AgentState):
    # Obligamos a Mistral a devolver JSON con la clave "next"
    chain = (manager_prompt | llm.with_structured_output(Router))
    
    try:
        result = chain.invoke(state)
        # VALIDACIÓN CRÍTICA: Si Mistral devuelve algo que no es un nodo, evitamos el KeyError
        if result["next"] not in options:
            # Si se equivoca, por defecto lo mandamos al investigador
            return {"next": "online_researcher"}
        return {"next": result["next"]}
    except Exception:
        # En caso de fallo en el formato JSON, forzamos una ruta segura
        return {"next": "online_researcher"}

# 5. Creación de Nodos de Agentes
def create_agent_node(llm, tools, system_prompt, name):
    # create_react_agent es el estándar moderno en LangGraph
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    
    def node(state):
        result = agent.invoke(state)
        last_message = result["messages"][-1]
        return {
            "messages": [HumanMessage(content=last_message.content, name=name)],
        }
    return node

#researcher_node = create_agent_node(llm, tools, "You are a researcher. Search info and summarize it.", "online_researcher")
researcher_node = create_agent_node(llm, tools, "Eres un investigador. Tu ÚNICA función es buscar datos y resumirlos. NO escribas artículos de blog ni tweets. Pasa solo los datos crudos.", "online_researcher")
blog_node = create_agent_node(llm, tools, "You are a blog editor. Create an article from research.", "blog_manager")
social_node = create_agent_node(llm, tools, "You are a social media expert. Create a tweet from the article.", "social_media_manager")

# 6. Construcción del Grafo
workflow = StateGraph(AgentState)

# Agregar nodos
workflow.add_node("content_marketing_manager", manager_node)
workflow.add_node("online_researcher", researcher_node)
workflow.add_node("blog_manager", blog_node)
workflow.add_node("social_media_manager", social_node)

# Los trabajadores siempre informan al manager al terminar
for member in content_marketing_team:
    workflow.add_edge(member, "content_marketing_manager")

# El manager decide el flujo condicionalmente
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
    inputs = {
        "messages": [
            #HumanMessage(content="Investiga sobre 'Agentic Behavior', escribe un artículo de blog y luego un tweet.")
            HumanMessage(content="Investiga sobre 'El existencialismo en Sartre', escribe un artículo de blog y luego un tweet.")
        ]
    }
    
    for s in multiagent.stream(inputs, {"recursion_limit": 25}):
        if "__end__" not in s:
            node_name = list(s.keys())[0]
            print(f"\n--- [NODO]: {node_name} ---")
            # Mostramos el contenido de forma más limpia
            content = s[node_name].get("messages", [{}])[-1].content if "messages" in s[node_name] else s[node_name]
            print(content)
            print("-" * 40)