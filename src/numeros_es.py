# -*- coding: utf-8 -*-
"""
Conversion de numeros hablados en espanol (0-100) a enteros, y generacion
del vocabulario cerrado que se le pasa a Vosk como gramatica restringida.

Diseño: el maestro dicta notas de 0 a 100, enteros. El reconocimiento de
voz es mucho mas confiable si se le restringe a un vocabulario cerrado
(gramatica) en vez de dejarlo abierto. Por eso este modulo tiene dos
responsabilidades:

1) texto_a_numero(): interpretar lo que Vosk devolvio como texto.
2) generar_vocabulario_numeros(): generar TODAS las frases validas de
   0 a 100 para construir esa gramatica cerrada.

NOTA IMPORTANTE (limitacion real, no maquillada):
Vosk normalmente devuelve el texto ya en palabras sueltas separadas por
espacio (ej. "treinta y cinco"), no combina "veintidos" como una sola
palabra a menos que el modelo la reconozca asi. Este parser acepta AMBAS
formas para no fallar por eso.
"""

from typing import Optional, List

UNIDADES = {
    "cero": 0, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4,
    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
}

DIEZ_A_QUINCE = {
    "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14,
    "quince": 15,
}

DIECI = {
    "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
}

VEINTI = {
    "veinte": 20, "veintiuno": 21, "veintiun": 21, "veintidos": 22,
    "veintitres": 23, "veinticuatro": 24, "veinticinco": 25,
    "veintiseis": 26, "veintisiete": 27, "veintiocho": 28,
    "veintinueve": 29,
}

DECENAS = {
    "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
    "setenta": 70, "ochenta": 80, "noventa": 90,
}

CIEN = {"cien": 100, "ciento": 100}


def _quitar_tildes(s: str) -> str:
    tabla = str.maketrans("áéíóúÁÉÍÓÚñÑ", "aeiouAEIOUnN")
    return s.translate(tabla)


def texto_a_numero(texto: str) -> Optional[int]:
    """
    Convierte una frase hablada en espanol (0-100) a entero.
    Devuelve None si no se pudo interpretar (para que quien llama
    decida pedir que se repita, en vez de asumir un valor).
    """
    if texto is None:
        return None

    t = _quitar_tildes(texto.strip().lower())
    t = t.replace("-", " ")
    palabras = [p for p in t.split(" ") if p]

    if not palabras:
        return None

    # Digito ya numerico ("24", "0", "100") - por si Vosk devuelve numero
    if len(palabras) == 1 and palabras[0].isdigit():
        val = int(palabras[0])
        return val if 0 <= val <= 100 else None

    # Un solo token de palabra
    if len(palabras) == 1:
        p = palabras[0]
        if p in UNIDADES:
            return UNIDADES[p]
        if p in DIEZ_A_QUINCE:
            return DIEZ_A_QUINCE[p]
        if p in DIECI:
            return DIECI[p]
        if p in VEINTI:
            return VEINTI[p]
        if p in DECENAS:
            return DECENAS[p]
        if p in CIEN:
            return CIEN[p]
        return None

    # "treinta y cinco", "cuarenta y dos", "ochenta y ocho"
    if len(palabras) == 3 and palabras[1] == "y":
        base = palabras[0]
        unidad = palabras[2]
        if base in DECENAS and unidad in UNIDADES:
            return DECENAS[base] + UNIDADES[unidad]
        return None

    # "cien" a veces se dicta como "ciento" solo (ya cubierto arriba)
    return None


def generar_vocabulario_numeros() -> List[str]:
    """
    Genera la lista de TODAS las frases validas de 0 a 100, tal como se
    dictarian, para usarlas como gramatica cerrada en Vosk
    (KaldiRecognizer con SetGrammar). Restringir el vocabulario es lo que
    realmente sube la precision en dictado rapido de numeros aislados.
    """
    frases = set()

    for palabra in UNIDADES:
        frases.add(palabra)
    for palabra in DIEZ_A_QUINCE:
        frases.add(palabra)
    for palabra in DIECI:
        frases.add(palabra)
    for palabra in VEINTI:
        frases.add(palabra)
    for palabra in DECENAS:
        frases.add(palabra)
        for unidad, _ in UNIDADES.items():
            if unidad in ("cero",):
                continue
            frases.add(f"{palabra} y {unidad}")
    for palabra in CIEN:
        frases.add(palabra)

    return sorted(frases)


def extraer_numeros(texto: str) -> List[int]:
    """
    Extrae TODOS los numeros que aparezcan en una frase reconocida, en
    el orden en que aparecen.

    Por que existe: en dictado rapido, el reconocedor de voz a veces
    agrupa varias palabras-numero dichas seguidas en un solo resultado
    (ej. 'cinco cinco', 'diez diez diez') en vez de devolver una por
    una. Con solo texto_a_numero() esos casos se perdian por completo
    (se marcaban como 'no entendido' y no se escribia nada). Esta
    funcion recupera todos los numeros validos que aparezcan, en
    orden, e ignora palabras sueltas que no sean numeros en vez de
    descartar todo el resultado.
    """
    if not texto:
        return []

    t = _quitar_tildes(texto.strip().lower()).replace("-", " ")
    palabras = [p for p in t.split(" ") if p]

    resultado = []
    i = 0
    while i < len(palabras):
        # intentar primero un compuesto de 3 palabras ("treinta y cinco")
        if i + 2 < len(palabras) and palabras[i + 1] == "y":
            compuesto = f"{palabras[i]} y {palabras[i + 2]}"
            numero = texto_a_numero(compuesto)
            if numero is not None:
                resultado.append(numero)
                i += 3
                continue
        # si no, una palabra suelta (o digito)
        numero = texto_a_numero(palabras[i])
        if numero is not None:
            resultado.append(numero)
        i += 1

    return resultado


def numero_a_texto(n: int) -> str:
    """Convierte un entero 0-100 a su forma hablada (para el TTS de 'repiteme')."""
    if n == 0:
        return "cero"
    if n == 100:
        return "cien"
    for dic in (UNIDADES, DIEZ_A_QUINCE, DIECI, VEINTI):
        for palabra, val in dic.items():
            if val == n and palabra not in ("una", "veintiun"):
                return palabra
    if n > 20:
        decena = (n // 10) * 10
        unidad = n % 10
        for palabra, val in DECENAS.items():
            if val == decena:
                if unidad == 0:
                    return palabra
                for u_pal, u_val in UNIDADES.items():
                    if u_val == unidad and u_pal != "una":
                        return f"{palabra} y {u_pal}"
    return str(n)