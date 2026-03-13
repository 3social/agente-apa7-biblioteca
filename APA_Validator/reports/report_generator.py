import docx
import io

def generar_reporte_docx(feedback, nombre_archivo):
    """Crea un documento Word profesional con el feedback de la IA."""
    doc = docx.Document()
    doc.add_heading(f"Reporte de Revisión APA 7 - {nombre_archivo}", 0)
    
    # Separar el texto por líneas para añadir párrafos limpios
    for linea in feedback.split('\n'):
        if linea.strip():
            doc.add_paragraph(linea.strip())
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
