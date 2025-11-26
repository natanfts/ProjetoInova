#!/bin/bash
# Script rápido para ativar o ambiente virtual no Linux/Mac

if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado!"
    echo "Execute './setup-venv.sh' primeiro para criar o ambiente."
    exit 1
fi

echo "✅ Ativando ambiente virtual..."
source venv/bin/activate
echo "✅ Ambiente virtual ativado!"
echo ""
echo "Você pode agora executar:"
echo "  python main.py"
echo ""

