import re

# Mapa simple de sustituciones (clave en forma legible)
SUSTITUCIONES = {
    "xd": "X D",
    "wtf?": "watafac?",
    "wtf": "watafac",
    "omg": "o-em-ge",
    "porno": "nopor",
    "hitler": "señor del bigote",
}

def _flexible_pattern_for(token: str) -> str:
    """
    Crea un patrón regex que:
    - Permite cualquier cantidad de espacios entre letras (\s*)
    - Ignora mayúsculas/minúsculas al compilar
    - Asegura límites fuera de palabras con (?<!\w) ... (?!\w)
    token: texto simple como 'xd', 'wtf?', 'por no', etc.
    """
    # Normalizamos token: quitamos espacios extra en los extremos
    token = token.strip()

    parts = []
    for ch in token:
        if ch.isspace():
            # ya permitiremos espacios con \s* entre letras, así que lo ignoramos
            continue
        if re.match(r"\w", ch, re.UNICODE):
            # letra/dígito/underscore -> permitir espacios después
            parts.append(re.escape(ch) + r"\s*")
        else:
            # signo de puntuación (ej: '?', '!', '.') -> permitir espacios antes del signo
            parts.append(r"\s*" + re.escape(ch) + r"\s*")

    inner = "".join(parts)
    # quitamos el \s* final si existe para dejar el patrón más limpio
    inner = re.sub(r"\\s\*\Z", "", inner)

    # Delimitadores: que no haya carácter de palabra justo antes o después
    pattern = rf"(?<!\w)(?:{inner})(?!\w)"
    return pattern

def autocorregir_mensaje(texto: str) -> str:
    resultado = texto

    # Iteramos sustituciones. Compilamos cada patrón con IGNORECASE y UNICODE
    for token, reemplazo in SUSTITUCIONES.items():
        patron_flexible = _flexible_pattern_for(token)
        regex = re.compile(patron_flexible, flags=re.IGNORECASE | re.UNICODE)
        resultado = regex.sub(reemplazo, resultado)

    return resultado