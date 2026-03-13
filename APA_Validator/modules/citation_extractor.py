import docx
import io

def extraer_secciones(file_bytes):
    """Separa el cuerpo del texto de la lista de referencias."""
    doc = docx.Document(io.BytesIO(file_bytes))
    cuerpo, refs = [], []
    en_refs = False
    marcas = ["referencias", "bibliografía", "lista de referencias", "obras citadas"]
    
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t: continue
        if t.lower().replace(":", "") in marcas:
            en_refs = True
            continue
        if en_refs:
            refs.append(t)
        else:
            cuerpo.append(t)
            
    return "\n".join(cuerpo), "\n".join(refs)
