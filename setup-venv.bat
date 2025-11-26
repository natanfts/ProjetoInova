@echo off
REM Script de setup do ambiente virtual Python para Windows

echo ========================================
echo Setup do Ambiente Virtual - ProjetoInova
echo ========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado! Instale Python 3.8 ou superior.
    echo    Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version
echo.

REM Cria ambiente virtual
echo 🔨 Criando ambiente virtual...
if exist venv (
    echo ⚠️ Diretório 'venv' já existe. Removendo...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo ❌ Erro ao criar ambiente virtual.
    pause
    exit /b 1
)

echo ✅ Ambiente virtual criado!
echo.

REM Ativa o ambiente virtual e instala dependências
echo 📦 Instalando dependências...
call venv\Scripts\activate.bat

REM Atualiza pip
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ⚠️ Aviso: Erro ao atualizar pip (continuando...)
)

REM Instala dependências
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Erro ao instalar dependências.
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ Setup concluído com sucesso!
echo ========================================
echo.
echo Para ativar o ambiente virtual, execute:
echo   venv\Scripts\activate.bat
echo.
echo Para executar a aplicação:
echo   python main.py
echo.
pause

