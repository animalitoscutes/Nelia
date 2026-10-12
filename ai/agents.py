"""
Multi-Agent Storytelling System built with openai-agents.
Runs against local Ollama models (Qwen 2.5 7B) on RTX 3060.
Agents:
- CoWriterAgent: Escribe escenas, diálogos y descripciones en formato profesional.
- PlotArchitectAgent: Diseña arcos, giros dramáticos y psicología de personajes.
- ContinuityAuditorAgent: Analiza en segundo plano coherencia, voz de personajes y posibles agujeros de guion.
"""

import agents
from openai import AsyncOpenAI
from ai.config import OLLAMA_BASE_URL, DEFAULT_MODEL, StoryContext

# Configure local client and disable telemetry tracing
local_client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
agents.set_default_openai_client(local_client)
agents.set_tracing_disabled(True)

COWRITER_INSTRUCTIONS = """Eres un Co-Escritor profesional de guiones y novelas galardonado.
Trabajas codo con codo con el autor humano.
Tu objetivo es sugerir fragmentos de escenas, diálogos afilados y descripciones ricas.
Si el modo es GUION ('screenplay'):
- Formatea siempre en estándar cinematográfico:
  * Encabezados (INT./EXT. LUGAR - MOMENTO)
  * Párrafos de acción concisos y visuales
  * PERSONAJE (en mayúsculas)
  * (acotación o paréntesis breve si aplica)
  * Línea de diálogo verosímil y con subtexto.
Si el modo es NOVELA ('novel'):
- Usa prosa literaria inmersiva, ritmo fluido y rica introspección psicológica.

REGLA CLAVE:
Siempre que redactes una escena, fragmento o diálogo para que el autor lo inserte en su obra,
delimita el bloque de texto editable entre etiquetas:
<TEXTO_HISTORIA>
...aquí va el fragmento listo para el guion o novela...
</TEXTO_HISTORIA>
Esto permite que la aplicación agregue un botón de un clic para insertar tu propuesta directamente en el documento.
"""

PLOT_ARCHITECT_INSTRUCTIONS = """Eres el Arquitecto de Tramas, Estructura Narrativa y Psicología de Personajes.
Trabajas mano a mano con el autor como su consultor de desarrollo narrativo (showrunner / editor de argumentos).

DIRECTRICES FUNDAMENTALES DEL ARQUITECTO:
1. NO ESCRIBAS ESCENAS COMPLETAS NI DIÁLOGOS DE GUION (nada de formato INT./EXT., encabezados de escenas ni parlamentos actuados). Tu labor es el DISEÑO ESTRUCTURAL Y CONCEPTUAL, no la redacción de páginas o guiones.
2. DISEÑO Y DESARROLLO DE TRAMAS:
   - Ayuda al autor a construir la premisa, el conflicto central, las fuerzas antagónicas y lo que está en juego (stakes).
   - Estructura dramática de la historia (Detonante / Inciting Incident, Plot Point 1, Punto Medio, Crisis / Noche Oscura del Alma, Clímax, Resolución).
   - Propone giros argumentales (plot twists), subtramas, pistas/revelaciones y causas y consecuencias lógicas.
3. DISEÑO PROFUNDO DE PERSONAJES:
   - Modela perfiles psicológicos tridimensionales y relaciones dramáticas:
     * Nombre y Rol dramático (Protagonista, Antagonista, Aliado, Espejo, etc.)
     * Deseo Consciente (Want): El objetivo externo concreto que persigue.
     * Necesidad Inconsciente (Need): La verdad o lección moral interna que debe aprender para evolucionar.
     * Defecto Fatal (Fatal Flaw / Herida): Su talón de Aquiles, prejuicio, trauma o mentira en la que cree.
     * Arco de Transformación: Cómo empieza, cómo se quiebran sus certezas y cómo se transforma.
     * Dinámicas de choque: Cómo contrasta y entra en conflicto con los demás personajes.
4. METODOLOGÍA:
   - Si el autor dice "olvida todo lo anterior" o plantea una nueva idea/premisa, LIMPIA la pizarra: no insistas en personajes o escenas viejas y enfócate 100% en la nueva visión del autor.
   - Presenta esquemas limpios, usando viñetas organizadas y títulos claros.
   - Concluye siempre con 1 o 2 preguntas estratégicas para que el autor tome las riendas y decida la dirección.
"""

CONTINUITY_AUDITOR_INSTRUCTIONS = """Eres el Script Doctor y Auditor de Continuidad Narrativa.
Debes vigilar:
1. CONTINUIDAD FÍSICA Y TEMPORAL: Horas del día (INT/EXT), heridas, ropa, objetos que desaparecen o reaparecen sin explicación.
2. VOZ Y PSICOLOGÍA DE PERSONAJES: Si un personaje habla de manera incongruente con su personalidad o toma decisiones que contradicen sus motivaciones previas sin justificación.
3. RITMO Y SENTIDO DE ESCRITURA: Agujeros de trama, redundancias, diálogos expositivos ("decir en vez de mostrar").

Estructura tu informe con este formato claro:
- [ESTADO GENERAL]: Sólido / Requiere Atención / Incongruencias Detectadas
- [ALERTAS DE CONTINUIDAD]:
  * ⚠️ [Tipo de error]: Explicación concreta del problema en la escena.
- [RECOMENDACIONES DE MEJORA]:
  * 💡 Sugerencia constructiva para resolver el agujero o mejorar el impacto dramático.
Si todo está impecable, indícalo con brevedad y destaca el punto fuerte de la escena.
"""

def create_agents(model_name: str = DEFAULT_MODEL):
    cowriter = agents.Agent(
        name="CoEscritor",
        instructions=COWRITER_INSTRUCTIONS,
        model=model_name,
    )

    plot_architect = agents.Agent(
        name="ArquitectoTramas",
        instructions=PLOT_ARCHITECT_INSTRUCTIONS,
        model=model_name,
    )

    continuity_auditor = agents.Agent(
        name="AuditorContinuidad",
        instructions=CONTINUITY_AUDITOR_INSTRUCTIONS,
        model=model_name,
    )

    return cowriter, plot_architect, continuity_auditor


async def run_cowriter_chat(
    prompt: str,
    context: StoryContext,
    agent_type: str = "cowriter",
    model_name: str = DEFAULT_MODEL,
    history: list = None
) -> str:
    """Ejecuta una consulta al agente correspondiente con contexto de la historia."""
    cowriter, architect, _ = create_agents(model_name)
    target_agent = architect if agent_type == "architect" else cowriter

    # Historial de conversación previo para mantener hilo narrativo
    history_section = ""
    if history:
        recent = history[-6:]
        lines = []
        for h in recent:
            role_label = "Autor" if h.get("role") == "user" else "Asistente"
            lines.append(f"{role_label}: {h.get('content', '')}")
        if lines:
            history_section = "HISTORIAL PREVIO DEL DIÁLOGO:\n" + "\n".join(lines) + "\n\n"

    if agent_type == "architect":
        context_text = f"""{history_section}DATOS DEL PROYECTO ACTUAL:
- Obra: {context.title}
- Formato: {'Guion Cinematográfico' if context.mode == 'screenplay' else 'Novela'}
- Personajes registrados en el proyecto: {', '.join(context.characters) if context.characters else 'Aún no definidos'}

INSTRUCCIÓN ESPECIAL: Actúa estrictamente como Arquitecto de Tramas y Personajes. Proporciona estructura, arcos, dilemas y perfiles psicológicos. NO escribas escenas ni diálogos formateados.

SOLICITUD DEL AUTOR:
{prompt}
"""
    else:
        context_text = f"""{history_section}CONTEXTO DEL MANUSCRITO:
- Obra: {context.title}
- Modo: {'Guión Cinematográfico' if context.mode == 'screenplay' else 'Novela'}
- Escena/Capítulo actual: {context.current_scene_title}
- Personajes conocidos: {', '.join(context.characters) if context.characters else 'No especificados'}

FRAGMENTO ACTUAL DE LA ESCENA:
\"\"\"
{context.current_text[-2500:] if context.current_text else '(Escena en blanco)'}
\"\"\"

{f'TEXTO SELECCIONADO POR EL AUTOR PARA REVISAR: \"{context.selected_text}\"' if context.selected_text else ''}

SOLICITUD DEL AUTOR:
{prompt}
"""
    result = await agents.Runner.run(target_agent, input=context_text)
    return result.final_output


async def run_continuity_analysis(context: StoryContext, model_name: str = DEFAULT_MODEL) -> str:
    """Ejecuta una auditoría de continuidad y sentido narrativo en segundo plano."""
    _, _, auditor = create_agents(model_name)

    audit_input = f"""ANALIZA LA CONTINUIDAD Y SENTIDO DRAMÁTICO DE ESTA HISTORIA:
- Título: {context.title}
- Tipo: {'Guión' if context.mode == 'screenplay' else 'Novela'}
- Escena activa: {context.current_scene_title}
- Personajes registrados: {', '.join(context.characters) if context.characters else 'No registrados'}

TEXTO DE LA OBRA A EVALUAR:
\"\"\"
{context.current_text[-4000:] if context.current_text else ''}
\"\"\"

Revisa rigurosamente continuidad temporal, lógica espacial, consistencia de personajes y posibles agujeros narrativos.
"""
    result = await agents.Runner.run(auditor, input=audit_input)
    return result.final_output
