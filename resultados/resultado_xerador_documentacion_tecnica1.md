(001-basic-multiagenty-py3.11) PS F:\IDE\PythonAI\LandGraphCero\001-basic-multiagenty-master> poetry run python .\xerador_documentacion_tecnica.py
--- INICIANDO GENERADOR DE DOCUMENTACIÓN GITHUB ---
Repositorio objetivo: https://github.com/xoseportasfer/xestor_reputacion_dixital
============================================================

>>> [SISTEMA]: Clonando en C:\Users\AZORES~1\AppData\Local\Temp\tmpelf24_ns...
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
 El código que se encuentra en el repositorio `xestor_reputacion_dixital` es un programa en Python diseñado para crear un sistema de gestión de crisis utilizando la librería Langchain Ollama. La función `clone_and_read_repo` que se llama con la URL https://github.com/xoseportasfer/xestor_reputacion_dixital clona el repositorio y lee su contenido para extraer el código del programa de gestión de crisis.

El sistema de gestión de crisis está diseñado para monitorear menciones recientes sobre una marca o tema específico, evaluar el riesgo de crisis y generar propuestas de respuesta inmediata en caso de que se detecte una amenaza. El programa utiliza un grafo de estados para representar el flujo del proceso, donde cada nodo representa una tarea específica y las transiciones entre los nodos dependen de la salida de cada tarea.

El grafo de estados incluye tres nodos principales: `monitor_de_redes`, `analista_de_sentimiento` y `gabinete_de_crisis`. El nodo `monitor_de_redes` rastrea las menciones recientes sobre la marca o tema indicado en redes sociales y recopila comentarios, noticias y opiniones relevantes. El nodo `analista_de_sentimiento` evalúa las menciones recopiladas y detecta patrones de negatividad, calificando el nivel de riesgo de crisis en una escala del 1 al 10 y explicando por qué existe (o no) una amenaza. El nodo `gabinete_de_crisis` redacta 3 propuestas de respuesta inmediata: una para redes sociales, otra interna para la empresa y un breve borrador de comunicado de prensa.

El programa también utiliza una librería llamada Langgraph para crear un agente reactivo que puede invocarse en cada nodo del grafo. El agente utiliza una LLM (Language Learning Model) llamada Mistral, que se configura con una temperatura baja para mantener la calma y profesionalidad en las respuestas. Además, el programa incluye un sistema de prompts en español para cada nodo del grafo, lo que permite a la LLM entender cómo debe actuar en cada tarea específica.

Finalmente, el programa se ejecuta mediante una llamada al método `compile()` en el objeto `workflow`, lo que crea un agente compilado listo para ser utilizado en caso de que se detecte una crisis.

La lógica detrás del diseño del sistema es la siguiente:

1. El programa utiliza un grafo de estados para representar el flujo del proceso, lo que permite a los usuarios ver y controlar fácilmente cada tarea en el proceso de gestión de crisis.
2. La utilización de una LLM (Language Learning Model) como Mistral permite al sistema entender y responder a las menciones recopiladas sobre la marca o tema indicado, manteniendo una calma y profesionalidad en las respuestas.
3. El uso de un agente reactivo que puede invocarse en cada nodo del grafo permite al sistema reaccionar rápidamente a las menciones recopiladas sobre la marca o tema indicado, generando propuestas de respuesta inmediata en caso de que se detecte una amenaza.
4. El uso de un sistema de prompts en español permite al sistema entender cómo debe actuar en cada tarea específica, lo que facilita la comunicación entre el sistema y los usuarios.
5. La creación de un agente compilado listo para ser utilizado en caso de que se detecte una crisis permite al sistema reaccionar rápidamente a las menciones recopiladas sobre la marca o tema indicado, generando propuestas de respuesta inmediata en caso de que se detecte una amenaza.

En resumen, el programa es un sistema de gestión de crisis diseñado para monitorear menciones recientes sobre una marca o tema específico, evaluar el riesgo de crisis y generar propuestas de respuesta inmediata en caso de que se detecte una amenaza. El programa utiliza un grafo de estados, una LLM (Language Learning Model) llamada Mistral, un agente reactivo, un sistema de prompts en español y un agente compilado listo para ser utilizado en caso de que se detecte una crisis.
------------------------------------------------------------

[FASE]: REDACTOR_MARKDOWN
 # README.md

## Descripción

Este proyecto contiene un programa en Python diseñado para crear un sistema de gestión de crisis utilizando la librería Langchain Ollama. El sistema está diseñado para monitorear menciones recientes sobre una marca o tema específico, evaluar el riesgo de crisis y generar propuestas de respuesta inmediata en caso de que se detecte una amenaza.

## Arquitectura

El programa utiliza un grafo de estados para representar el flujo del proceso, donde cada nodo representa una tarea específica y las transiciones entre los nodos dependen de la salida de cada tarea. Los nodos incluyen:

1. `monitor_de_redes`: Este nodo es responsable de rastrear las menciones recientes sobre la marca o tema indicado en redes sociales y recopilar comentarios, noticias y opiniones relevantes.
2. `analista_de_sentimiento`: Este nodo evalúa las menciones recopiladas y detecta patrones de negatividad, calificando el nivel de riesgo de crisis en una escala del 1 al 10 y explicando por qué existe (o no) una amenaza.
3. `gabinete_de_crisis`: Este nodo redacta 3 propuestas de respuesta inmediata: una para redes sociales, otra interna para la empresa y un breve borrador de comunicado de prensa.

El programa también utiliza una librería llamada Langgraph para crear un agente reactivo que puede invocarse en cada nodo del grafo. El agente utiliza una LLM (Language Learning Model) llamada Mistral, que se configura con una temperatura baja para mantener la calma y profesionalidad en las respuestas.

El programa incluye un sistema de prompts en español para cada nodo del grafo, lo que permite a la LLM entender cómo debe actuar en cada tarea específica.

## Funciones Principales

1. Monitorear menciones recientes sobre una marca o tema específico en redes sociales y recopilar comentarios, noticias y opiniones relevantes.
2. Evaluar el riesgo de crisis y calificarlo en una escala del 1 al 10.
3. Generar propuestas de respuesta inmediata en caso de que se detecte una amenaza.
4. Utilizar un agente reactivo para invocarse en cada nodo del grafo y reaccionar rápidamente a las menciones recopiladas sobre la marca o tema indicado.
5. Entender cómo debe actuar en cada tarea específica gracias al sistema de prompts en español.
6. Crear un agente compilado listo para ser utilizado en caso de que se detecte una crisis.

## Ejemplo de Uso

Para utilizar el programa, primero se necesita clonar el repositorio y luego ejecutar el código del programa de gestión de crisis mediante una llamada al método `compile()` en el objeto `workflow`. El sistema estará listo para ser utilizado en caso de que se detecte una crisis.

El programa también puede personalizarse ajustando los prompts en español y configurando la LLM (Language Learning Model) llamada Mistral según sea necesario.
------------------------------------------------------------