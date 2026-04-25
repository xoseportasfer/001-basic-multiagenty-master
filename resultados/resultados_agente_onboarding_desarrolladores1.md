--- AGENTE DE ONBOARDING PARA DESARROLLADORES ---

>>> [SISTEMA]: Explorando repositorio para Onboarding...

[FASE]: MAPEADOR_DE_ESTRUCTURA
 Este es un guía de onboarding para un nuevo desarrollador en el proyecto de gestión de reputación digital ubicado en GitHub en `https://github.com/xoseportasfer/xestor_reputacion_dixital`.

**Estructura del Proyecto:**
```bash
tmp09i884x7/
    .ipynb_checkpoints/
    001_basic_multiagenty/
    tests/
```
El proyecto principal se encuentra en la carpeta `001_basic_multiagenty`.

**Contenido de gestor\_reputacion\_digital.py:**
- Configuración: Carga de variables de entorno y configuración del modelo LLM (Language Learning Model) Mistral con una temperatura baja para mantener la calma y profesionalidad en las respuestas.
- Definición del Estado: Clase `AgentState` que representa el estado actual del agente, incluyendo mensajes y la próxima acción a tomar.
- Manager de Comunicación (Orquestador de Crisis): Función `manager_node(state: AgentState)` que determina la siguiente acción a tomar en función del último mensaje recibido.

**Contenido de pyproject.toml:**
- Configuración del proyecto, incluyendo dependencias y build system.

**Contenido de README.md:**
- Información general sobre el proyecto.

**Contenido de resultados\_analisis\_fuentes2.py:**
- Ejemplo de cómo se utiliza el agente para analizar una fuente específica (Karl Popper tolerance paradox analysis).

**Contenido de schemas.py:**
- Definición de modelos Pydantic para las solicitudes y respuestas del frontend.

**Contenido de __init__.py:**
- Archivo vacío.
------------------------------------------------------------

[FASE]: ANALISTA_DE_PUNTOS_ENTRADA
 En este proyecto, el punto de entrada principal se encuentra en la carpeta `001_basic_multiagenty` con el archivo `gestor_reputacion_digital.py`. El código comienza su ejecución al cargar el módulo principal y llama a la función `manager_node(state: AgentState)`, que se encuentra en este mismo archivo.

No hay rutas de API o nodos principales del grafo de agentes definidos en este proyecto, ya que parece ser una implementación inicial de un sistema de gestión de reputación digital basado en agentes inteligentes.

La información fluye a través del sistema de la siguiente manera:
1. El usuario envía una solicitud al frontend (no se proporciona código para el frontend en este repositorio).
2. El frontend procesa la solicitud y la envía al módulo `gestor_reputacion_digital.py`.
3. El módulo `gestor_reputacion_digital.py` analiza el estado actual del agente y determina la siguiente acción a tomar mediante la función `manager_node(state: AgentState)`.
4. El agente realiza la acción determinada y devuelve una respuesta al frontend.
5. El frontend procesa la respuesta y la envía de regreso al usuario.

Para un nuevo desarrollador, aquí hay algunas recomendaciones para comenzar con el proyecto:
1. Comprender la estructura del proyecto y los archivos principales (`gestor_reputacion_digital.py`, `pyproject.toml`, `README.md`, etc.).
2. Leer el código de `gestor_reputacion_digital.py` para entender cómo funciona el sistema de agentes inteligentes y cómo se determina la siguiente acción a tomar.
3. Investigar sobre el modelo LLM Mistral utilizado en este proyecto y cómo se configura para mantener la calma y profesionalidad en las respuestas.
4. Explorar el archivo `schemas.py` para entender cómo están definidos los modelos Pydantic para las solicitudes y respuestas del frontend.
5. Si se desea agregar nuevas funcionalidades al proyecto, es recomendable comenzar con pequeños cambios y pruebas antes de aplicarlos en el código principal.
------------------------------------------------------------

[FASE]: REDACTOR_GUIA_BIENVENIDA
 # ¡HOLA MUNDO!: Cómo ejecutar el proyecto por primera vez

Para ejecutar el proyecto, siga estos pasos:

1. Clona el repositorio desde GitHub en tu máquina local utilizando el siguiente comando:
```bash
git clone https://github.com/xoseportasfer/xestor_reputacion_dixital.git
```
2. Navega hasta la carpeta del proyecto:
```bash
cd xestor_reputacion_dixital
```
3. Instala las dependencias necesarias utilizando el siguiente comando:
```bash
pip install -r requirements.txt
```
4. Ejecuta el proyecto con el siguiente comando:
```bash
python 001_basic_multiagenty/gestor_reputacion_digital.py
```

# MAPA DEL TESORO: Qué archivos debe abrir el desarrollador para entender la lógica central

El punto de entrada principal se encuentra en la carpeta `001_basic_multiagenty` con el archivo `gestor_reputacion_digital.py`. El código comienza su ejecución al cargar el módulo principal y llama a la función `manager_node(state: AgentState)`, que se encuentra en este mismo archivo.

# PRIMEROS PASOS: Sugiere una pequeña modificación o 'issue' ficticio para que empiece a tocar el código

Una buena manera de comenzar a trabajar con el proyecto es creando un nuevo agente que tenga comportamientos diferentes al actual. Puedes crear un nuevo archivo `mis_agentes.py` en la carpeta `001_basic_multiagenty` y definir una nueva clase `MiAgente` que herede de `AgentState`. Modifica el comportamiento del agente mediante la función `manager_node(state: AgentState)`.

# ARQUITECTURA: Breve explicación del flujo principal

El flujo principal del proyecto se resume en los siguientes pasos:
1. El usuario envía una solicitud al frontend (no se proporciona código para el frontend en este repositorio).
2. El frontend procesa la solicitud y la envía al módulo `gestor_reputacion_digital.py`.
3. El módulo `gestor_reputacion_digital.py` analiza el estado actual del agente y determina la siguiente acción a tomar mediante la función `manager_node(state: AgentState)`.
4. El agente realiza la acción determinada y devuelve una respuesta al frontend.
5. El frontend procesa la respuesta y la envía de regreso al usuario.
------------------------------------------------------------