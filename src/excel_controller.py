# -*- coding: utf-8 -*-
"""
Control de Excel EN VIVO via COM (xlwings, que envuelve pywin32).

IMPORTANTE: este modulo SOLO funciona en Windows con Microsoft Excel
instalado. No se puede probar en Linux. xlwings se conecta a la
instancia de Excel que el maestro ya tiene abierta -- no procesa un
archivo cerrado.

Requiere: pip install xlwings pywin32
"""

import xlwings as xw
from typing import Optional, Tuple, List


class ExcelController:
    def __init__(self):
        self.app = None
        self.book = None
        self.anchor_sheet = None   # hoja donde inicio la ultima "corrida" de dictado
        self.anchor_row = None     # fila donde inicio esa corrida
        self.anchor_col = None     # columna donde inicio esa corrida
        self.valores_corrida: List[Tuple[int, int, int]] = []  # (fila, col, valor)

    def conectar(self) -> bool:
        """
        Se conecta al Excel que el usuario ya tiene abierto.
        No abre ni crea ningun archivo -- por diseno, para que funcione
        con CUALQUIER formato de Excel que el maestro ya tenga.
        """
        try:
            if len(xw.apps) == 0:
                return False
            self.app = xw.apps.active
            self.book = self.app.books.active
            return self.book is not None
        except Exception:
            return False

    def hay_conexion(self) -> bool:
        try:
            return self.book is not None and self.book.app is not None
        except Exception:
            return False

    def celda_activa(self):
        """Devuelve (nombre_hoja, fila, columna) de la celda seleccionada AHORA MISMO."""
        hoja = self.book.app.selection.sheet
        celda = self.book.app.selection
        return hoja.name, celda.row, celda.column

    def iniciar_corrida(self):
        """
        Marca el punto de partida de una nueva serie de dictado.
        Se llama la primera vez que el maestro empieza a dictar despues
        de reposicionar el cursor.
        """
        hoja, fila, col = self.celda_activa()
        self.anchor_sheet = hoja
        self.anchor_row = fila
        self.anchor_col = col
        self.valores_corrida = []

    def escribir_siguiente(self, valor: int):
        """
        Escribe 'valor' en la celda actual y mueve el cursor una fila
        hacia abajo, como si el maestro estuviera llenando de arriba
        hacia abajo.
        """
        hoja, fila, col = self.celda_activa()
        sheet = self.book.sheets[hoja]
        sheet.range((fila, col)).value = valor
        self.valores_corrida.append((fila, col, valor))
        # mover el puntero una fila abajo
        sheet.range((fila + 1, col)).select()

    def buscar_por_texto(self, texto_buscado: str, solo_hoja_activa: bool = True):
        """
        Busca 'texto_buscado' (clave o nombre) en las celdas de la hoja
        activa (o de todo el libro). Devuelve una lista de coincidencias
        [(nombre_hoja, fila, columna, valor_celda), ...] para que quien
        llama decida que hacer si hay mas de una.

        NOTA: esto es busqueda de texto plano/insensible a mayusculas.
        No intenta "adivinar" cual columna es "clave" o "nombre" -- busca
        en todas las celdas usadas, porque no hay formato fijo de Excel.
        """
        coincidencias = []
        texto_buscado_norm = texto_buscado.strip().lower()

        hojas = [self.book.sheets.active] if solo_hoja_activa else list(self.book.sheets)

        for sheet in hojas:
            usado = sheet.used_range
            if usado is None:
                continue
            valores = usado.value
            if valores is None:
                continue
            # normalizar a matriz de filas
            if not isinstance(valores, list):
                valores = [[valores]]
            elif valores and not isinstance(valores[0], list):
                valores = [valores]

            fila_base = usado.row
            col_base = usado.column

            for i, fila_vals in enumerate(valores):
                for j, val in enumerate(fila_vals):
                    if val is None:
                        continue
                    if str(val).strip().lower() == texto_buscado_norm:
                        coincidencias.append(
                            (sheet.name, fila_base + i, col_base + j, val)
                        )

        return coincidencias

    def ir_a_celda(self, nombre_hoja: str, fila: int, columna: int):
        sheet = self.book.sheets[nombre_hoja]
        sheet.activate()
        sheet.range((fila, columna)).select()

    def valor_en(self, nombre_hoja: str, fila: int, columna: int):
        sheet = self.book.sheets[nombre_hoja]
        return sheet.range((fila, columna)).value

    def escribir_en(self, nombre_hoja: str, fila: int, columna: int, valor: int):
        sheet = self.book.sheets[nombre_hoja]
        sheet.range((fila, columna)).value = valor

    def valores_de_la_corrida_actual(self):
        """Para 'repiteme': devuelve lo dictado desde el ancla hasta ahora."""
        return list(self.valores_corrida)
