# -*- coding: utf-8 -*-
"""
Orquestador principal. Junta: ExcelController + MotorDeVoz + Corrector +
VozOffline + UI (ui.py).

Flujo:
1. Se conecta al Excel abierto.
2. El maestro coloca el cursor en una celda y empieza a dictar numeros.
3. Cada numero reconocido se escribe y el cursor baja una fila.
4. Si el maestro reposiciona el cursor manualmente (otra columna, otra
   hoja), se detecta por polling de la seleccion y se reinicia el
   "ancla" de la corrida (para que 'repiteme' sepa desde donde repetir).
5. Comandos: "repiteme", "me equivoque en clave <numero>",
   "me equivoque con <nombre>".

LIMITACION REAL: el polling de seleccion tiene una latencia (intervalo
configurable, por defecto 300ms). Si el maestro dicta MUY rapido justo
despues de reposicionar el cursor, puede que la primera nota se escriba
en la celda vieja. Se puede bajar el intervalo a costa de mas uso de
CPU. Esto hay que probarlo y ajustarlo con hardware real.
"""

import re
import threading
import time
from typing import Optional

from excel_controller import ExcelController
from speech_engine import MotorDeVoz
from corrector import Corrector
from numeros_es import texto_a_numero, numero_a_texto
from tts import VozOffline


INTERVALO_POLLING_SEGUNDOS = 0.3


class Orquestador:
    def __init__(self, ruta_modelo_vosk: str, callback_ui=None):
        self.excel = ExcelController()
        self.corrector = Corrector(self.excel)
        self.voz = VozOffline()
        self.callback_ui = callback_ui or (lambda evento, datos: None)

        self.motor_voz = MotorDeVoz(ruta_modelo_vosk, self._on_texto_reconocido)

        self.estado = "esperando_conexion"
        self.referencia_correccion_pendiente: Optional[str] = None
        self.celda_esperada = None
        self._hilo_polling = None
        self._corriendo = False

    # ---------- conexion y ciclo de vida ----------

    def conectar_excel(self) -> bool:
        ok = self.excel.conectar()
        if ok:
            self.estado = "listo"
            self.callback_ui("conectado", {})
        else:
            self.callback_ui("sin_excel", {})
        return ok

    def iniciar(self, dispositivo_mic: Optional[int] = None):
        if not self.excel.hay_conexion():
            if not self.conectar_excel():
                return

        self._corriendo = True
        self._hilo_polling = threading.Thread(target=self._bucle_polling_seleccion, daemon=True)
        self._hilo_polling.start()

        self.motor_voz.iniciar(dispositivo=dispositivo_mic)  # bloqueante

    def detener(self):
        self._corriendo = False
        self.motor_voz.detener()

    # ---------- deteccion de reposicionamiento manual ----------

    def _bucle_polling_seleccion(self):
        while self._corriendo:
            try:
                if self.excel.hay_conexion():
                    hoja, fila, col = self.excel.celda_activa()
                    actual = (hoja, fila, col)
                    if self.celda_esperada is not None and actual != self.celda_esperada:
                        self._iniciar_nueva_corrida()
                    elif self.celda_esperada is None:
                        self._iniciar_nueva_corrida()
            except Exception:
                pass
            time.sleep(INTERVALO_POLLING_SEGUNDOS)

    def _iniciar_nueva_corrida(self):
        self.excel.iniciar_corrida()
        hoja, fila, col = self.excel.celda_activa()
        self.corrector.fijar_columna_en_dictado(col)
        self.celda_esperada = (hoja, fila, col)

        # refrescar vocabulario de voz con los textos de la hoja activa
        # (para reconocer nombres/claves al hacer correcciones)
        try:
            textos = self._extraer_textos_hoja_activa()
            self.motor_voz.actualizar_vocabulario(palabras_extra=textos)
        except Exception:
            pass

        self.callback_ui("nueva_corrida", {"hoja": hoja, "fila": fila, "col": col})

    def _extraer_textos_hoja_activa(self):
        sheet = self.excel.book.sheets.active
        usado = sheet.used_range
        if usado is None or usado.value is None:
            return []
        valores = usado.value
        if not isinstance(valores, list):
            valores = [[valores]]
        elif valores and not isinstance(valores[0], list):
            valores = [valores]
        textos = []
        for fila_vals in valores:
            for val in fila_vals:
                if isinstance(val, str) and val.strip():
                    textos.append(val.strip())
        return textos

    # ---------- interpretacion de lo dictado ----------

    def _on_texto_reconocido(self, texto: str):
        self.callback_ui("texto_reconocido", {"texto": texto})

        if self.estado == "esperando_valor_correccion":
            numero = texto_a_numero(texto)
            if numero is not None:
                self._aplicar_correccion_pendiente(numero)
            else:
                self.callback_ui("aviso", {
                    "mensaje": "Esperaba un numero para la correccion, no entendi. Repite el valor."
                })
            return

        if "repiteme" in texto or texto.strip() == "repite":
            self._repetir()
            return

        m = re.search(r"me equivoque (?:en clave|con|clave) (.+)", texto)
        if m:
            referencia = m.group(1).strip()
            self._iniciar_correccion(referencia)
            return

        numero = texto_a_numero(texto)
        if numero is not None:
            self.excel.escribir_siguiente(numero)
            hoja, fila, col = self.excel.celda_activa()
            self.celda_esperada = (hoja, fila, col)
            self.callback_ui("valor_escrito", {"valor": numero})
            return

        self.callback_ui("no_reconocido", {"texto": texto})

    def _iniciar_correccion(self, referencia: str):
        resultado = self.corrector.procesar_correccion(referencia)
        self.callback_ui("correccion", {"estado": resultado.estado, "mensaje": resultado.mensaje})

        if resultado.estado == "ok":
            self.referencia_correccion_pendiente = referencia
            self.estado = "esperando_valor_correccion"
            self.voz.decir("Dime el valor correcto")
        elif resultado.estado == "ambiguo":
            self.voz.decir("Encontre varias coincidencias, necesito que lo aclares en pantalla")
        else:
            self.voz.decir(f"No encontre {referencia} en el Excel")

    def _aplicar_correccion_pendiente(self, numero: int):
        resultado = self.corrector.procesar_correccion(
            self.referencia_correccion_pendiente, nuevo_valor=numero
        )
        self.callback_ui("correccion_aplicada", {"mensaje": resultado.mensaje})
        self.voz.decir("Listo, corregido")
        self.estado = "listo"
        self.referencia_correccion_pendiente = None

    def _repetir(self):
        valores = self.excel.valores_de_la_corrida_actual()
        if not valores:
            self.voz.decir("Todavia no hay nada que repetir")
            self.callback_ui("repeticion", {"valores": []})
            return

        texto_hablado = ", ".join(numero_a_texto(v) for _, _, v in valores)
        self.callback_ui("repeticion", {"valores": valores})
        self.voz.decir(texto_hablado)


if __name__ == "__main__":
    import sys
    ruta_modelo = sys.argv[1] if len(sys.argv) > 1 else "modelo_vosk_es"

    def on_evento(evento, datos):
        print(f"[{evento}] {datos}")

    orquestador = Orquestador(ruta_modelo, callback_ui=on_evento)
    if orquestador.conectar_excel():
        print("Conectado a Excel. Coloca el cursor en una celda y empieza a dictar.")
        orquestador.iniciar()
    else:
        print("No se encontro Excel abierto. Abre tu archivo y vuelve a intentar.")
