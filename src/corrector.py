# -*- coding: utf-8 -*-
"""
Logica de correccion por texto: "me equivoque en clave 24" o
"me equivoque con Barrios Edson".

Diseno: busca el texto en la hoja activa. Si hay una sola coincidencia,
ubica esa fila y pide (por voz/pantalla) el valor correcto para la
MISMA COLUMNA que se estaba dictando. Si hay mas de una coincidencia,
NO ADIVINA -- pregunta cual es, porque adivinar mal aqui significa
corromper la nota de otro alumno.
"""

from typing import Optional, List, Tuple
from excel_controller import ExcelController


class ResultadoCorreccion:
    def __init__(self, estado: str, mensaje: str,
                 coincidencias: Optional[List[Tuple]] = None):
        self.estado = estado          # "ok" | "ambiguo" | "no_encontrado"
        self.mensaje = mensaje
        self.coincidencias = coincidencias or []


class Corrector:
    def __init__(self, excel: ExcelController):
        self.excel = excel
        self.columna_en_dictado: Optional[int] = None

    def fijar_columna_en_dictado(self, columna: int):
        self.columna_en_dictado = columna

    def procesar_correccion(self, texto_referencia: str,
                             nuevo_valor: Optional[int] = None) -> ResultadoCorreccion:
        coincidencias = self.excel.buscar_por_texto(
            texto_referencia, solo_hoja_activa=True
        )

        if len(coincidencias) == 0:
            # si no aparece en la hoja activa, se intenta en todo el libro
            coincidencias = self.excel.buscar_por_texto(
                texto_referencia, solo_hoja_activa=False
            )

        if len(coincidencias) == 0:
            return ResultadoCorreccion(
                "no_encontrado",
                f"No encontre '{texto_referencia}' en el Excel."
            )

        if len(coincidencias) > 1:
            return ResultadoCorreccion(
                "ambiguo",
                f"Encontre {len(coincidencias)} coincidencias de "
                f"'{texto_referencia}'. Necesito que me digas cual fila.",
                coincidencias,
            )

        hoja, fila, _col_encontrada, _valor = coincidencias[0]

        if self.columna_en_dictado is None:
            return ResultadoCorreccion(
                "ambiguo",
                "Encontre la fila pero no se en que columna estabas dictando.",
                coincidencias,
            )

        if nuevo_valor is None:
            return ResultadoCorreccion(
                "ok",
                f"Encontre la fila en '{hoja}'. Dime el valor correcto.",
                coincidencias,
            )

        self.excel.escribir_en(hoja, fila, self.columna_en_dictado, nuevo_valor)
        return ResultadoCorreccion(
            "ok",
            f"Corregido: fila de '{texto_referencia}' ahora tiene {nuevo_valor}.",
            coincidencias,
        )
