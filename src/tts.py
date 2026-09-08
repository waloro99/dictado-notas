# -*- coding: utf-8 -*-
"""
Texto a voz OFFLINE via pyttsx3 (usa SAPI5 de Windows por debajo).

LIMITACION REAL: si Windows no tiene una voz en espanol instalada,
esto habla en la voz por defecto (probablemente ingles). No hay forma
de garantizar una voz en espanol sin que el usuario la instale desde
Configuracion > Hora e idioma > Voz, en Windows 11. Por eso 'repiteme'
SIEMPRE muestra tambien en pantalla (ver ui.py) -- no depende solo
de esto.

Requiere: pip install pyttsx3
"""

import pyttsx3


class VozOffline:
    def __init__(self):
        self.motor = pyttsx3.init()
        self._preferir_voz_espanol()

    def _preferir_voz_espanol(self):
        for voz in self.motor.getProperty("voices"):
            nombre = (voz.name or "").lower()
            idioma = "".join(str(l).lower() for l in (voz.languages or []))
            if "spanish" in nombre or "español" in nombre or "es-" in idioma or "es_" in idioma:
                self.motor.setProperty("voice", voz.id)
                return
        # si no hay voz en espanol instalada, se queda con la voz por defecto

    def decir(self, texto: str):
        self.motor.say(texto)
        self.motor.runAndWait()
