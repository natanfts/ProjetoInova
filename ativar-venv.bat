@echo off
REM Script rápido para ativar o ambiente virtual no Windows

if not exist venv (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute 'setup-venv.bat' primeiro para criar o ambiente.
    pause
    exit /b 1
)

echo ✅ Ativando ambiente virtual...
call venv\Scripts\activate.bat
echo ✅ Ambiente virtual ativado!
echo.
echo Você pode agora executar:
echo   python main.py
echo.

