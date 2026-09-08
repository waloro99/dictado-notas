; Script de Inno Setup. Genera el instalador final tipo "Siguiente, Siguiente,
; Instalar" que se le entrega al maestro. Se compila EN WINDOWS con Inno
; Setup (gratis): https://jrsoftware.org/isdl.php
;
; Uso:
;   1) Compilar primero el .exe con PyInstaller (ver dictado_notas.spec)
;   2) Abrir este archivo con Inno Setup Compiler y presionar Compile
;   3) Se genera Output\DictadoDeNotas_Setup.exe -- ese es el archivo
;      que se le manda al maestro. Un doble click y "Siguiente" tres
;      veces lo instala.

#define MyAppName "Dictado de Notas"
#define MyAppVersion "1.0"
#define MyAppExeName "DictadoDeNotas.exe"

[Setup]
AppId={{B7B2B6C1-4F2E-4C2B-9E1A-DICTADO0NOTAS}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=DictadoDeNotas_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un icono en el Escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "..\dist\DictadoDeNotas.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent
