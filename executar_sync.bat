@echo off
echo Iniciando Sincronizacao de Cancelamentos - Grupo Madero
echo Perfil: Auditoria Forense
echo.

cd /d "c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos"
"C:/Users/M27812/Desktop/PROJETOS PYTHON/venv/Scripts/python.exe" upload_drive.py

echo.
echo Sincronizacao (Upload para o Drive) concluida! Verifique o log upload_drive.log.
echo Finalizado em %date% %time%
pause
