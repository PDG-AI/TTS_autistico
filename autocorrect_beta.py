import re

# Diccionario de autocorrecciones
SUSTITUCIONES = {
    r"\bXD\b": "X D",
    r"\bxd\b": "x d",
    r"\bWTF\b": "watafac",
    r"\bwtf\b": "watafac",
    r"\bOMG\b": "o-em-ge",
    r"\bomg\b": "o-em-ge",
}

# Efectos disponibles
SFX = ["vineboom", "dross", "metalpipe"]


def autocorregir_mensaje(texto: str) -> str:
    # 1) Autocorrección
    resultado = texto
    for patron, reemplazo in SUSTITUCIONES.items():
        resultado = re.sub(patron, reemplazo, resultado, flags=re.IGNORECASE)

    # 2) Convertir [SFX:nombre] → <SFX:nombre>
    #    (para que no rompa el TTS)
    patron_sfx = r"\[SFX:(.*?)\]"
    resultado = re.sub(patron_sfx, lambda m: f"<SFX:{m.group(1).strip().lower()}>", resultado)
    resultado_procesado = procesar_sfx(resultado)
    return resultado_procesado

def procesar_sfx(texto):
    partes = texto.split("<SFX:")
    for i, parte in enumerate(partes):
        if i == 0:
            # Primera parte: solo texto normal
            yield ("texto", parte)
        else:
            # Ejemplo: "vineboom> resto del texto"
            nombre, resto = parte.split(">", 1)
            yield ("sfx", nombre)
            yield ("texto", resto)
