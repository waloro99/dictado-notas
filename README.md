# Dictado de Notas — estado real del proyecto

## Qué SÍ está probado
`src/numeros_es.py` (conversión de números hablados en español 0-100) está
verificado con casos de prueba reales, incluyendo compuestos ("treinta y
cinco") y round-trip completo 0-100. Esta parte funciona tal como está.

## Qué NO está probado (y por qué)
Todo lo demás depende de Windows + Microsoft Excel instalado + micrófono
real, ninguno de los cuales existe en el entorno donde escribí este
código. Concretamente, sin probar en hardware real:

- `excel_controller.py` — la conexión COM con Excel vía `xlwings`
- `speech_engine.py` — el reconocimiento de voz real con Vosk y micrófono
- La detección de que el maestro reposicionó el cursor manualmente
  (polling de selección, `main.py`)
- La latencia real entre "reposicionar cursor" y "empezar a dictar"

Esto **no es opcional probarlo** — es la parte más incierta de todo el
proyecto. Antes de dárselo a un maestro real, alguien tiene que sentarse
con Excel abierto, un micrófono, y dictar de verdad para calibrar.

## Requisito no negociable: pausas entre números
Ningún motor de reconocimiento de voz segmenta bien números dictados
totalmente pegados sin ninguna pausa ("unodostrescuatro" sin espacios
audibles). El sistema necesita una pausa breve (silencio de unos
cientos de milisegundos) entre cada número. Si en la práctica el maestro
dicta sin ninguna pausa, hay que ajustar expectativa — no hay truco de
software que arregle eso.

## Cómo compilar el .exe (elige una opción)

### Opción A — sin tu propia PC con Windows (recomendada)
1. Descarga el modelo Vosk en español: https://alphacephei.com/vosk/models
   (`vosk-model-small-es-0.42`), descomprímelo en una carpeta llamada
   `modelo_vosk_es/` dentro de este proyecto.
2. Sube esta carpeta completa a un repositorio de GitHub.
3. El workflow en `.github/workflows/build.yml` corre solo (usa runners
   gratuitos de Windows de GitHub Actions) y deja el instalador listo
   para descargar en la pestaña "Actions" del repositorio, como artifact.

### Opción B — con una PC Windows 11 a mano
1. `pip install -r requirements.txt` (en Windows)
2. Descargar el modelo Vosk español y ponerlo en `modelo_vosk_es/`
3. `pyinstaller build/dictado_notas.spec`
4. Abrir `installer/instalador.iss` con Inno Setup (gratis) y compilar
5. Queda `installer/Output/DictadoDeNotas_Setup.exe` — ese es el archivo
   que se instala con doble click + "Siguiente" x3, sin conocimiento
   técnico.

## Cómo se usa (una vez instalado)
1. Abrir el Excel del maestro (cualquier formato, no requiere plantilla)
2. Abrir "Dictado de Notas"
3. Presionar "Conectar con Excel abierto"
4. Colocar el cursor en la celda donde empieza a dictar
5. Presionar "Iniciar dictado" y empezar a decir los números, uno por uno,
   con una pausa breve entre cada uno
6. Para corregir: "me equivoqué en clave 24" o "me equivoqué con
   Barrios Edson", y luego decir el valor correcto
7. Para escuchar/ver lo dictado desde donde empezó esa columna:
   "repíteme"
8. Para dictar otra columna u otra hoja: simplemente hacer click en la
   nueva celda con el mouse y seguir dictando — el programa detecta el
   cambio solo

## Lo que sigue después de esto (no está incluido todavía)
- Ajuste fino de precisión con grabaciones reales de un maestro
- Manejo de acentos regionales guatemaltecos si el modelo pequeño de
  Vosk no los reconoce bien (en ese caso, cambiar a
  `vosk-model-es-0.42`, el modelo completo, ~1.4 GB — más preciso, más
  pesado)
- Icono y firma del instalador (ahora mismo el .exe no está firmado
  digitalmente, Windows puede mostrar una advertencia de SmartScreen
  la primera vez — es normal para software no firmado, no es un error)
