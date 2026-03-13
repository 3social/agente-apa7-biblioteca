from openai import OpenAI

def analizar_trabajo(cuerpo, refs, contexto_manual, api_key):
    """Realiza el análisis experto usando el manual como base."""
    client = OpenAI(api_key=api_key)
    
    prompt_sistema = (
        "Eres un bibliotecario experto en APA 7ma edición. Genera un REPORTE DE FEEDBACK.\n"
        "Usa el manual oficial proporcionado para justificar tus correcciones.\n"
        "1. COHERENCIA: Citas en texto vs Referencias.\n"
        "2. FORMATO APA 7: Basado estrictamente en el manual.\n"
        "3. CORRECCIONES: Sé pedagógico y claro."
    )
    
    prompt_usuario = (
        f"--- REGLAS DEL MANUAL ---\n{contexto_manual}\n\n"
        f"--- TRABAJO DEL ALUMNO ---\nCUERPO:\n{cuerpo}\n\nREFS:\n{refs}"
    )
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": prompt_sistema},
                  {"role": "user", "content": prompt_usuario}]
    )
    return response.choices[0].message.content
