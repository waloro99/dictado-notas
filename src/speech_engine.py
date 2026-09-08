# -*- coding: utf-8 -*-
"""
Reconocimiento de voz continuo, offline, en espanol, usando Vosk con
GRAMATICA RESTRINGIDA (vocabulario cerrado).

Por que gramatica restringida: dictar numeros aislados rapido es un
escenario dificil para cualquier motor de voz. Restringir lo que el
modelo puede "escuchar" a un conjunto cerrado de palabras validas
(numeros 0-100 + comandos + nombres/claves de la hoja activa) mejora
mucho la precision comparado con reconocimiento de vocabulario abierto.

LIMITACION REAL: esto no es magia. Si el maestro dicta sin NINGUNA
pausa entre numero y numero, el reconocedor va a fusionar palabras y
va a fallar. Este sistema requiere una pausa breve (silencio) entre
cada numero para poder segmentar -- eso es una restriccion de la
tecnologia de reconocimiento de voz en general, no un defecto de este
programa en particular.

Requiere: pip install vosk sounddevice
Requiere ademas descargar un modelo Vosk en espanol, por ejemplo:
  https://alphacephei.com/vosk/models -> vosk-model-small-es-0.42
"""

import json
import queue
from typing import Callable, List, Optional

import sounddevice as sd
from vosk import Model, KaldiRecognizer

from numeros_es import generar_vocabulario_numeros

COMANDOS = [
    "repiteme", "repite", "me equivoque", "corrige", "cambia",
    "pausa", "detente", "continua", "clave", "con",
]


class MotorDeVoz:
    def __init__(self, ruta_modelo: str, on_texto: Callable[[str], None],
                 sample_rate: int = 16000):
        self.ruta_modelo = ruta_modelo
        self.on_texto = on_texto
        self.sample_rate = sample_rate
        self.modelo = Model(ruta_modelo)
        self.cola_audio: "queue.Queue[bytes]" = queue.Queue()
        self.stream: Optional[sd.RawInputStream] = None
        self.reconocedor: Optional[KaldiRecognizer] = None
        self.activo = False

    def _callback_audio(self, indata, frames, time, status):
        self.cola_audio.put(bytes(indata))

    def actualizar_vocabulario(self, palabras_extra: Optional[List[str]] = None):
        """
        Reconstruye la gramatica cerrada del reconocedor. Se llama cada
        vez que el maestro cambia de columna/hoja, para incluir los
        nombres o claves de esa columna como vocabulario reconocible
        (asi 'me equivoque con Barrios Edson' tiene chance real de
        reconocerse, en vez de vocabulario abierto).
        """
        vocabulario = set(generar_vocabulario_numeros())
        vocabulario.update(COMANDOS)
        if palabras_extra:
            for palabra in palabras_extra:
                for token in str(palabra).lower().split():
                    vocabulario.add(token)

        gramatica = json.dumps(sorted(vocabulario), ensure_ascii=False)
        self.reconocedor = KaldiRecognizer(self.modelo, self.sample_rate, gramatica)
        self.reconocedor.SetWords(True)

    def iniciar(self, dispositivo: Optional[int] = None):
        if self.reconocedor is None:
            self.actualizar_vocabulario()

        self.activo = True
        self.stream = sd.RawInputStream(
            samplerate=self.sample_rate, blocksize=4000, dtype="int16",
            channels=1, device=dispositivo, callback=self._callback_audio,
        )
        self.stream.start()
        self._bucle_reconocimiento()

    def detener(self):
        self.activo = False
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def _bucle_reconocimiento(self):
        while self.activo:
            try:
                data = self.cola_audio.get(timeout=0.5)
            except queue.Empty:
                continue

            if self.reconocedor.AcceptWaveform(data):
                resultado = json.loads(self.reconocedor.Result())
                texto = resultado.get("text", "").strip()
                if texto:
                    self.on_texto(texto)

    @staticmethod
    def listar_microfonos():
        return sd.query_devices()
