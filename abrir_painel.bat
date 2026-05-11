@echo off
title Painel de Cancelamentos Madero
echo ==================================================
echo   INICIANDO O PAINEL DE CANCELAMENTOS - MADERO
echo ==================================================
echo.
echo Por favor, mantenha esta janela preta aberta. 
echo Se fechar, o painel vai parar de funcionar no navegador!
echo.
echo O navegador deve abrir automaticamente em alguns segundos...
echo.

cd /d "c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos"
"C:\Users\M27812\Desktop\PROJETOS PYTHON\venv\Scripts\python.exe" -m streamlit run dashboard_app.py
