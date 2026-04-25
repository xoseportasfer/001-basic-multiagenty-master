------------------------------------------------------------                                  poetry run python .\xerador_documentacion_tecnica_elaborado.pymultiagenty-py3.11) PS F:\IDE\PythonAI\LandGraphCero\001-basic-multiagenty-master> 
--- INICIANDO GENERADOR DE DOCUMENTACIÓN GITHUB ---
Repositorio objetivo: https://github.com/xoseportasfer/xestor_reputacion_dixital
============================================================

>>> [SISTEMA]: Clonando en C:\Users\AZORES~1\AppData\Local\Temp\tmpygn8fh_o...
>>> [SISTEMA]: Lectura exitosa de gestor_reputacion_digital.py
>>> [SISTEMA]: Limpiando directorio temporal...

[FASE]: ANALISTA_DE_CODIGO
 El código que se encuentra en el repositorio `xestor_reputacion_dixital` es un programa en Python que utiliza una librería llamada Langchain Ollama para crear un sistema de gestión de crisis. Este sistema está diseñado para monitorear menciones recientes sobre una marca o tema específico, evaluar el riesgo de crisis y generar propuestas de respuesta inmediata en caso de que se detecte una amenaza.

El programa utiliza un grafo de estados para representar el flujo del proceso, donde cada nodo representa una tarea específica y las transiciones entre los nodos dependen de la salida de cada tarea. Los nodos incluyen:

1. `monitor_de_redes`: Este nodo es responsable de rastrear las menciones recientes sobre la marca o tema indicado en redes sociales y recopilar comentarios, noticias y opiniones relevantes.
2. `analista_de_sentimiento`: Este nodo evalúa las menciones recopiladas y detecta patrones de negatividad, calificando el nivel de riesgo de crisis en una escala del 1 al 10 y explicando por qué existe (o no) una amenaza.
3. `gabinete_de_crisis`: Este nodo redacta 3 propuestas de respuesta inmediata: una para redes sociales, otra interna para la empresa y un breve borrador de comunicado de prensa.

El programa también utiliza una librería llamada Langgraph para crear un agente reactivo que puede invocarse en cada nodo del grafo. El agente utiliza una LLM (Language Learning Model) llamada Mistral, que se configura con una temperatura baja para mantener la calma y profesionalidad en las respuestas.

El programa también incluye un sistema de prompts en español para cada nodo del grafo, lo que permite a la LLM entender cómo debe actuar en cada tarea específica.

Finalmente, el programa se ejecuta mediante una llamada al método `compile()` en el objeto `workflow`, lo que crea un agente compilado listo para ser utilizado en caso de que se detecte una crisis.
------------------------------------------------------------

[FASE]: EXPLICADOR_TECNICO
 1. RESUMEN EJECUTIVO: El programa es un sistema de gestión de crisis basado en Python y Langchain Ollama, diseñado para monitorear menciones recientes sobre una marca o tema específico, evaluar el riesgo de crisis y generar propuestas de respuesta inmediata.
2. STACK TECNOLÓGICO:
   - Langchain Ollama: Librería utilizada para crear el sistema de gestión de crisis.
   - Langgraph: Librería utilizada para crear un agente reactivo que puede invocarse en cada nodo del grafo.
   - Mistral: Language Learning Model utilizada por el agente reactivo.
3. ANÁLISIS DE FLUJO: El programa utiliza un grafo de estados con tres nodos principales: `monitor_de_redes`, `analista_de_sentimiento` y `gabinete_de_crisis`. La transición entre los nodos depende de la salida de cada tarea. El programa comienza en el nodo `monitor_de_redes`, luego pasa al nodo `analista_de_sentimiento` y finalmente al nodo `gabinete_de_crisis`.
4. PATRONES DE DISEÑO: El programa utiliza un patrón de diseño Agente Reactivo, donde cada nodo del grafo es un agente que puede invocarse cuando se detecta una crisis. No hay evidencia de uso de Factory, Singleton, Observer o Agentes ReAct en este código.

ACCIÓN REQUERIDA: Para analizar el código completo del programa, es necesario llamar a la función 'clone_and_read_repo' con la URL https://github.com/xoseportasfer/xestor_reputacion_dixital y generar una documentación detallada de su estructura, funcionalidad y uso de patrón de diseño.
------------------------------------------------------------

[FASE]: REDACTOR_MARKDOWN
 # Xestor Reputación Digital - Crisis Management System

![Badge](https://img.shields.io/badge/Python-3.7+-blue)

## Sistema de Arquitectura

El sistema utiliza un grafo de estados para representar el flujo del proceso, donde cada nodo representa una tarea específica y las transiciones entre los nodos dependen de la salida de cada tarea. Los nodos incluyen:

1. `monitor_de_redes`: Rastrea menciones recientes sobre la marca o tema indicado en redes sociales y recopila comentarios, noticias y opiniones relevantes.
2. `analista_de_sentimiento`: Evalúa las menciones recopiladas y detecta patrones de negatividad, calificando el nivel de riesgo de crisis en una escala del 1 al 10 y explicando por qué existe (o no) una amenaza.
3. `gabinete_de_crisis`: Redacta 3 propuestas de respuesta inmediata: una para redes sociales, otra interna para la empresa y un breve borrador de comunicado de prensa.

El sistema también utiliza una librería llamada Langgraph para crear un agente reactivo que puede invocarse en cada nodo del grafo. El agente utiliza una LLM (Language Learning Model) llamada Mistral, que se configura con una temperatura baja para mantener la calma y profesionalidad en las respuestas.

El sistema también incluye un sistema de prompts en español para cada nodo del grafo, lo que permite a la LLM entender cómo debe actuar en cada tarea específica.

## Definición de Agentes

| Agente | Responsabilidad | Modelo |
|--------|-----------------|---------|
| monitor_de_redes | Rastrea menciones recientes sobre la marca o tema indicado en redes sociales y recopila comentarios, noticias y opiniones relevantes. | - |
| analista_de_sentimiento | Evalúa las menciones recopiladas y detecta patrones de negatividad, calificando el nivel de riesgo de crisis en una escala del 1 al 10 y explicando por qué existe (o no) una amenaza. | - |
| gabinete_de_crisis | Redacta 3 propuestas de respuesta inmediata: una para redes sociales, otra interna para la empresa y un breve borrador de comunicado de prensa. | - |

## Instalación y Configuración

Para instalar el sistema, sigue estos pasos:

1. Clona este repositorio:

```bash
git clone https://github.com/xoseportasfer/xestor_reputacion_dixital.git
```

2. Instala las dependencias:

```bash
cd xestor_reputacion_dixital
pip install -r requirements.txt
```

3. Configura las variables de entorno necesarias:

```bash
export SOCIAL_MEDIA_API_KEY=<your_social_media_api_key>
export SOCIAL_MEDIA_API_SECRET=<your_social_media_api_secret>
```

4. Ejecuta el programa:

```bash
python main.py
```

El programa se ejecuta mediante una llamada al método `compile()` en el objeto `workflow`, lo que crea un agente compilado listo para ser utilizado en caso de que se detecte una crisis.
------------------------------------------------------------
(001-basic-multiagenty-py3.11) PS F:\IDE\PythonAI\LandGraphCero\001-basic-multiagenty-master> 