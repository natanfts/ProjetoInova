# HELP AI - Sistema de Reconhecimento de Gestos para Pacientes

Sistema de reconhecimento de gestos de mão desenvolvido para auxiliar pacientes com mobilidade reduzida a solicitarem ajuda. Utiliza MediaPipe, OpenCV e interface gráfica Tkinter para o painel do paciente, e um painel web para enfermeiros monitorarem as solicitações em tempo real.

## 🎯 Sobre o Projeto

O **HELP AI** é uma solução tecnológica desenvolvida para ambientes hospitalares, permitindo que pacientes se comuniquem com a equipe de enfermagem através de gestos simples com as mãos. O sistema detecta gestos configuráveis (1 a 4 dedos) e envia notificações em tempo real para o painel do enfermeiro, facilitando o atendimento e melhorando a qualidade do cuidado ao paciente.

## 📁 Estrutura do Projeto

```
HELP-AI/
├── src/                          # Código fonte principal
│   ├── __init__.py              # Inicialização do pacote
│   ├── config/                  # Módulo de configuração
│   │   ├── __init__.py
│   │   └── config.py           # Configurações da aplicação
│   ├── data/                    # Módulo de gerenciamento de dados
│   │   ├── __init__.py
│   │   ├── database.py         # Gerenciamento SQLite
│   │   ├── gesto_repository.py # Repositório de gestos
│   │   └── paciente_repository.py # Repositório de pacientes
│   ├── gesture_detector/        # Módulo de detecção de gestos
│   │   ├── __init__.py
│   │   └── gesture_detector.py  # Detector usando MediaPipe
│   ├── audio/                   # Módulo de áudio
│   │   ├── __init__.py
│   │   └── audio_handler.py     # Reconhecimento de voz e alertas
│   ├── video/                   # Módulo de processamento de vídeo
│   │   ├── __init__.py
│   │   └── video_processor.py   # Processador de vídeo da câmera
│   ├── ui/                      # Módulo de interface gráfica
│   │   ├── __init__.py
│   │   └── main_window.py       # Janela principal Tkinter (Pacientes)
│   ├── websocket/               # Módulo WebSocket
│   │   ├── __init__.py
│   │   └── websocket_server.py  # Servidor WebSocket para notificações
│   └── http/                    # Módulo HTTP
│       ├── __init__.py
│       └── http_server.py       # Servidor HTTP para painel do enfermeiro
├── assets/                      # Arquivos estáticos
│   ├── logo.png                # Logo da aplicação HELP AI
│   └── README.md               # Documentação dos assets
├── cliente_enfermeiro.html     # Painel web do enfermeiro
├── main.py                     # Ponto de entrada da aplicação
├── requirements.txt            # Dependências do projeto
├── banco_dados.db             # Banco de dados SQLite (não versionado)
├── setup-venv.bat             # Script de setup do venv (Windows)
├── setup-venv.sh              # Script de setup do venv (Linux/Mac)
├── ativar-venv.bat            # Script para ativar venv (Windows)
├── ativar-venv.sh             # Script para ativar venv (Linux/Mac)
└── README.md                   # Este arquivo
```

## 🏗️ Arquitetura

A aplicação foi organizada seguindo o princípio de **Separação de Responsabilidades**:

- **`config/`**: Centraliza todas as configurações da aplicação
- **`data/`**: Gerencia persistência de dados (SQLite) - gestos, pacientes, histórico
- **`gesture_detector/`**: Lógica de detecção de gestos usando MediaPipe
- **`audio/`**: Funcionalidades de áudio (reconhecimento de voz, alertas)
- **`video/`**: Processamento de vídeo da câmera
- **`ui/`**: Interface gráfica Tkinter para pacientes
- **`websocket/`**: Servidor WebSocket para notificações em tempo real
- **`http/`**: Servidor HTTP para painel web do enfermeiro

### 🎨 Componentes Principais

1. **Painel do Paciente (Tkinter)**
   - Interface gráfica para o paciente
   - Visualização da câmera em tempo real
   - Detecção de gestos e confirmação visual
   - Seleção de paciente

2. **Painel do Enfermeiro (Web)**
   - Interface web responsiva (HTML/CSS/JavaScript)
   - Monitoramento de alertas em tempo real
   - Gerenciamento de pacientes
   - Configuração de gestos e mensagens
   - Histórico de solicitações

3. **Banco de Dados SQLite**
   - Armazena pacientes cadastrados
   - Configurações de gestos e mensagens
   - Histórico completo de solicitações
   - Suporte a prioridades (baixa, normal, alta, urgente)

## 🚀 Como Executar

### 📋 Pré-requisitos

#### Versão do Python
- **Python 3.11.0** (versão recomendada e testada)
- **Mínimo: Python 3.8** (compatibilidade limitada)
- ⚠️ **Importante**: 
  - Versões anteriores a 3.8 não são suportadas
  - Versões superiores a 3.11 (3.12+) podem apresentar incompatibilidades com MediaPipe
  - Recomenda-se usar **exatamente Python 3.11.0** para garantir compatibilidade total

#### Verificar Versão do Python

**Windows:**
```cmd
python --version
```

**Linux/Mac:**
```bash
python3 --version
```

Se não tiver Python instalado ou a versão for inferior a 3.8:
- **Download**: https://www.python.org/downloads/
- Durante a instalação, marque a opção **"Add Python to PATH"**

#### Outros Requisitos
- ✅ Câmera web conectada e funcionando
- ✅ Microfone (opcional, para reconhecimento de voz)
- ✅ Sistema operacional: Windows, Linux ou macOS
- ✅ Conexão com internet (apenas para instalação de dependências)

### 🔧 Preparação do Ambiente

**⚠️ IMPORTANTE**: Sempre use um ambiente virtual (venv) para isolar as dependências do projeto e evitar conflitos com outros projetos Python.

#### Opção 1: Setup Automático (Recomendado)

##### Windows:

1. **Criar e configurar o ambiente virtual:**
```cmd
setup-venv.bat
```
Este script irá:
- Verificar se Python está instalado
- Criar o ambiente virtual (`venv`)
- Instalar/atualizar o pip
- Instalar todas as dependências do `requirements.txt`

2. **Ativar o ambiente virtual:**
```cmd
ativar-venv.bat
```

Você saberá que o ambiente está ativo quando ver `(venv)` no início do prompt.

##### Linux/Mac:

1. **Dar permissão de execução aos scripts (primeira vez):**
```bash
chmod +x setup-venv.sh ativar-venv.sh
```

2. **Criar e configurar o ambiente virtual:**
```bash
./setup-venv.sh
```

3. **Ativar o ambiente virtual:**
```bash
source ativar-venv.sh
```

Ou manualmente:
```bash
source venv/bin/activate
```

Você saberá que o ambiente está ativo quando ver `(venv)` no início do prompt.

#### Opção 2: Setup Manual

Se preferir fazer manualmente ou os scripts não funcionarem:

1. **Criar ambiente virtual:**
```bash
# Windows
python -m venv venv

# Linux/Mac
python3 -m venv venv
```

2. **Ativar ambiente virtual:**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Atualizar pip (recomendado):**
```bash
python -m pip install --upgrade pip
```

4. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

**⏱️ Tempo estimado**: 2-5 minutos (dependendo da velocidade da internet)

### ▶️ Executar a Aplicação

Com o ambiente virtual ativado (você deve ver `(venv)` no prompt), execute:

```bash
python main.py
```

**Windows:**
```cmd
python main.py
```

**Linux/Mac:**
```bash
python3 main.py
```

### 🔍 Verificação do Setup

Após instalar as dependências, você pode verificar se tudo está correto:

```bash
# Verificar versão do Python
python --version

# Verificar se as dependências foram instaladas
pip list

# Verificar se o ambiente virtual está ativo
# (deve mostrar o caminho do venv)
where python    # Windows
which python    # Linux/Mac
```

## 📦 Dependências

### Requisitos do Sistema
- **Python**: 3.11.0 (recomendado e testado) / Mínimo: 3.8
  - ⚠️ Versões superiores a 3.11 podem ter incompatibilidades com MediaPipe
- **pip**: Versão mais recente (será atualizado automaticamente)

### Bibliotecas Python

As dependências estão listadas no arquivo `requirements.txt`. Principais:

- `opencv-python>=4.8.0` - Processamento de vídeo e captura de câmera
- `mediapipe>=0.10.0` - Detecção de gestos de mão
- `SpeechRecognition>=3.10.0` - Reconhecimento de voz
- `pygame>=2.5.0` - Reprodução de áudio (substitui playsound para melhor compatibilidade)
- `websockets>=11.0` - Notificações em tempo real via WebSocket
- `Pillow>=10.0.0` - Processamento de imagens

### Módulos Padrão do Python (não precisam instalação)
- `os`, `sys` - Operações do sistema
- `sqlite3` - Banco de dados SQLite (padrão do Python)
- `tkinter` - Interface gráfica (pode precisar instalação no Linux: `sudo apt-get install python3-tk`)
- `threading` - Execução paralela
- `asyncio` - Programação assíncrona

**Nota**: Todas as dependências serão instaladas automaticamente ao executar o script de setup (`setup-venv.bat` ou `setup-venv.sh`).

## 🎯 Funcionalidades

### 👤 Painel do Paciente
- ✅ Detecção de gestos de mão em tempo real (1-4 dedos)
- ✅ Visualização da câmera com feedback visual
- ✅ Sistema de confirmação:
  - 🖐️ Mão totalmente aberta (5 dedos) = Confirmar envio
  - ✊ Mão fechada (0 dedos) = Cancelar
- ✅ Seleção de paciente via dropdown
- ✅ Exibição de gestos configurados e suas mensagens
- ✅ Requisição de "hold" de 1.5s antes de ativar confirmação
- ✅ Sistema de cooldown para evitar envios múltiplos

### 👨‍⚕️ Painel do Enfermeiro
- ✅ Monitoramento de alertas em tempo real via WebSocket
- ✅ Cadastro e gerenciamento de pacientes
- ✅ Configuração de gestos e mensagens:
  - 1 dedo = Solicitação A
  - 2 dedos = Solicitação B
  - 3 dedos = Solicitação C
  - 4 dedos = Solicitação D
- ✅ Sistema de priorização (Baixa, Normal, Alta, Urgente)
- ✅ Histórico completo de solicitações
- ✅ Visualização filtrada por paciente
- ✅ Marcação de solicitações como resolvidas
- ✅ Interface web responsiva e moderna
- ✅ Sincronização automática entre alertas e histórico

### 🔧 Funcionalidades Técnicas
- ✅ Banco de dados SQLite para persistência
- ✅ Notificações em tempo real via WebSocket
- ✅ Servidor HTTP integrado (porta 8000)
- ✅ API REST para gerenciamento de dados
- ✅ Migração automática de dados antigos (CSV → SQLite)

## 🔧 Boas Práticas Implementadas

1. **Separação de Responsabilidades**: Cada módulo tem uma responsabilidade única
2. **Configuração Centralizada**: Todas as configurações em um único lugar
3. **Tratamento de Erros**: Try/except em operações críticas
4. **Type Hints**: Tipagem para melhor legibilidade e manutenção
5. **Docstrings**: Documentação em todos os módulos e classes
6. **Código Limpo**: Nomes descritivos e estrutura organizada
7. **Threading**: Processamento de vídeo em thread separada
8. **Callbacks**: Comunicação entre módulos via callbacks

## 📝 Notas Importantes

### ⚠️ Requisitos Críticos
- **Sempre ative o ambiente virtual antes de executar a aplicação**
- O banco de dados SQLite (`banco_dados.db`) é criado automaticamente se não existir
- A aplicação **requer acesso à câmera web** para funcionar
- **Python 3.11.0 é recomendado** - versões superiores (3.12+) podem ter incompatibilidades com MediaPipe

### 🎯 Funcionalidades do Sistema
- Gestos críticos (contendo palavras como "emergência", "pânico", "urgente") disparam alertas sonoros
- O servidor WebSocket é iniciado automaticamente na porta 8765
- Para visualizar as notificações dos enfermeiros, abra o arquivo `cliente_enfermeiro.html` no navegador
- Sistema de confirmação: **mão totalmente aberta** para confirmar envio, **mão fechada** para cancelar

### 🔧 Troubleshooting

**Problema: "Python não encontrado"**
- Verifique se Python está instalado: `python --version`
- Certifique-se de que Python foi adicionado ao PATH durante a instalação
- No Windows, reinstale Python marcando "Add Python to PATH"

**Problema: "pip não encontrado"**
- Atualize o pip: `python -m pip install --upgrade pip`
- Ou instale pip: `python -m ensurepip --upgrade`

**Problema: Erro ao instalar dependências**
- Certifique-se de que está usando Python 3.11.0 (recomendado) ou versões 3.8-3.11
- ⚠️ Versões superiores a 3.11 podem causar incompatibilidades com MediaPipe
- Atualize o pip antes de instalar: `pip install --upgrade pip`
- Tente instalar as dependências uma por uma para identificar o problema

**Problema: Câmera não funciona**
- Verifique se a câmera não está sendo usada por outro aplicativo
- No Windows, verifique as permissões de câmera nas configurações do sistema
- Teste a câmera com outro aplicativo primeiro

**Problema: WebSocket não conecta**
- Verifique se a porta 8765 não está sendo usada por outro processo
- Certifique-se de que o firewall não está bloqueando a porta
- Verifique se o servidor WebSocket iniciou corretamente (veja os logs no console)

**Problema: Painel do enfermeiro não carrega**
- Verifique se a porta 8000 não está sendo usada por outro processo
- Acesse manualmente: http://localhost:8000
- Verifique os logs do servidor HTTP no console

**Problema: Logo não aparece**
- Certifique-se de que o arquivo `assets/logo.png` existe
- Verifique se o servidor HTTP está servindo arquivos estáticos corretamente
- O sistema funciona mesmo sem a logo (ela será ocultada automaticamente)

## 🔧 Gerenciamento do Ambiente Virtual

### Desativar Ambiente Virtual

Quando terminar de trabalhar, você pode desativar o ambiente virtual:

```bash
# Windows/Linux/Mac
deactivate
```

### Reativar Ambiente Virtual

Sempre que voltar a trabalhar no projeto, reative o ambiente virtual:

**Windows:**
```cmd
ativar-venv.bat
# ou
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source ativar-venv.sh
# ou
source venv/bin/activate
```

### Reinstalar Dependências

Se houver problemas com as dependências, você pode reinstalá-las:

```bash
# Com o ambiente virtual ativado
pip install --upgrade pip
pip install --force-reinstall -r requirements.txt
```

### Remover Ambiente Virtual

Se precisar começar do zero:

```bash
# Desative o ambiente virtual primeiro
deactivate

# Remova a pasta venv
# Windows
rmdir /s venv

# Linux/Mac
rm -rf venv

# Depois, execute o setup novamente
```

