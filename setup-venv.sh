#!/bin/bash
# Script de setup do ambiente virtual Python para Linux/Mac

echo "========================================"
echo "Setup do Ambiente Virtual - ProjetoInova"
echo "========================================"
echo ""

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado! Instale Python 3.8 ou superior."
    exit 1
fi

echo "✅ Python encontrado"
python3 --version
echo ""

# Cria ambiente virtual
echo "🔨 Criando ambiente virtual..."
if [ -d "venv" ]; then
    echo "⚠️ Diretório 'venv' já existe. Removendo..."
    rm -rf venv
fi

python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Erro ao criar ambiente virtual."
    exit 1
fi

echo "✅ Ambiente virtual criado!"
echo ""

# Ativa o ambiente virtual e instala dependências
echo "📦 Instalando dependências..."
source venv/bin/activate

# Atualiza pip
python -m pip install --upgrade pip

# Instala dependências
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Erro ao instalar dependências."
    exit 1
fi

echo ""
echo "========================================"
echo "✅ Setup concluído com sucesso!"
echo "========================================"
echo ""
echo "Para ativar o ambiente virtual, execute:"
echo "  source venv/bin/activate"
echo ""
echo "Para executar a aplicação:"
echo "  python main.py"
echo ""

