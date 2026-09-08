# -*- coding: utf-8 -*-
"""
Ventana simple (Tkinter) para el maestro: un boton de Iniciar/Detener,
el estado actual, y un registro de lo ultimo dictado. Pensada para ser
usable sin ninguna capacitacion previa.
"""

import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from main import Orquestador


class VentanaPrincipal:
    def __init__(self, ruta_modelo_vosk: str):
        self.cola_eventos = queue.Queue()
        self.orquestador = Orquestador(ruta_modelo_vosk, callback_ui=self._encolar_evento)
        self.hilo_voz = None

        self.root = tk.Tk()
        self.root.title("Dictado de Notas")
        self.root.geometry("480x420")
        self.root.resizable(False, False)

        self._construir_widgets()
        self.root.after(150, self._procesar_eventos)

    def _construir_widgets(self):
        marco = ttk.Frame(self.root, padding=16)
        marco.pack(fill="both", expand=True)

        self.lbl_estado = ttk.Label(marco, text="Sin conectar a Excel", font=("Segoe UI", 13, "bold"))
        self.lbl_estado.pack(anchor="w")

        self.lbl_celda = ttk.Label(marco, text="")
        self.lbl_celda.pack(anchor="w", pady=(4, 12))

        botones = ttk.Frame(marco)
        botones.pack(fill="x", pady=(0, 12))

        self.btn_conectar = ttk.Button(botones, text="Conectar con Excel abierto", command=self._conectar)
        self.btn_conectar.pack(side="left", padx=(0, 8))

        self.btn_iniciar = ttk.Button(botones, text="Iniciar dictado", command=self._iniciar, state="disabled")
        self.btn_iniciar.pack(side="left", padx=(0, 8))

        self.btn_detener = ttk.Button(botones, text="Detener", command=self._detener, state="disabled")
        self.btn_detener.pack(side="left")

        ttk.Label(marco, text="Ultimo reconocido:").pack(anchor="w")
        self.lbl_ultimo = ttk.Label(marco, text="-", font=("Segoe UI", 11))
        self.lbl_ultimo.pack(anchor="w", pady=(0, 12))

        ttk.Label(marco, text="Registro:").pack(anchor="w")
        self.txt_log = tk.Text(marco, height=12, state="disabled")
        self.txt_log.pack(fill="both", expand=True)

    def _log(self, mensaje: str):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", mensaje + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _encolar_evento(self, evento, datos):
        self.cola_eventos.put((evento, datos))

    def _procesar_eventos(self):
        try:
            while True:
                evento, datos = self.cola_eventos.get_nowait()
                self._manejar_evento(evento, datos)
        except queue.Empty:
            pass
        self.root.after(150, self._procesar_eventos)

    def _manejar_evento(self, evento, datos):
        if evento == "conectado":
            self.lbl_estado.configure(text="Conectado a Excel")
            self.btn_iniciar.configure(state="normal")
        elif evento == "sin_excel":
            messagebox.showwarning("Excel no encontrado", "Abre tu archivo de Excel y coloca el cursor en una celda, luego presiona Conectar de nuevo.")
        elif evento == "nueva_corrida":
            self.lbl_celda.configure(text=f"Dictando desde: hoja '{datos['hoja']}', fila {datos['fila']}, columna {datos['col']}")
        elif evento == "texto_reconocido":
            self.lbl_ultimo.configure(text=datos["texto"])
        elif evento == "valor_escrito":
            self._log(f"Escrito: {datos['valor']}")
        elif evento == "no_reconocido":
            self._log(f"No entendido: '{datos['texto']}'")
        elif evento == "correccion":
            self._log(f"Correccion: {datos['mensaje']}")
        elif evento == "correccion_aplicada":
            self._log(datos["mensaje"])
        elif evento == "repeticion":
            valores = ", ".join(str(v) for _, _, v in datos["valores"])
            self._log(f"Repitiendo: {valores}")
        elif evento == "aviso":
            self._log(datos["mensaje"])

    def _conectar(self):
        self.orquestador.conectar_excel()

    def _iniciar(self):
        self.btn_iniciar.configure(state="disabled")
        self.btn_detener.configure(state="normal")
        self.hilo_voz = threading.Thread(target=self.orquestador.iniciar, daemon=True)
        self.hilo_voz.start()
        self.lbl_estado.configure(text="Escuchando...")

    def _detener(self):
        self.orquestador.detener()
        self.btn_iniciar.configure(state="normal")
        self.btn_detener.configure(state="disabled")
        self.lbl_estado.configure(text="Detenido")

    def ejecutar(self):
        self.root.mainloop()


if __name__ == "__main__":
    import os
    ruta_modelo = os.environ.get("MODELO_VOSK", "modelo_vosk_es")
    ventana = VentanaPrincipal(ruta_modelo)
    ventana.ejecutar()
