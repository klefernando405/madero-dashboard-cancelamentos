@echo off
:: ============================================================
:: MADERO | Agendador de Upload para Google Drive
:: Executa o upload_drive.py todo dia às 09:00h
:: ============================================================
echo Configurando agendamento no Windows Task Scheduler...

:: Caminho do Python e do script
set PYTHON=C:\Users\M27812\Desktop\PROJETOS PYTHON\venv\Scripts\python.exe
set SCRIPT=c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos\upload_drive.py

:: Registra a tarefa agendada (com tratamento de aspas nativo do Windows)
schtasks /create /tn "Madero_Upload_Drive" ^
  /tr "\"%PYTHON%\" \"%SCRIPT%\"" ^
  /sc daily ^
  /st 09:00 ^
  /f

echo.
if %errorlevel% == 0 (
    echo [OK] Tarefa agendada com sucesso!
    echo      Nome: Madero_Upload_Drive
    echo      Horario: Todo dia as 09:00h
    echo      Script: %SCRIPT%
) else (
    echo [ERRO] Falha ao criar tarefa. Execute como Administrador.
)
echo.
pause
