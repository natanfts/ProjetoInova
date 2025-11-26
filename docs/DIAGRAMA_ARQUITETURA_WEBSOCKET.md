# 🏗️ Diagrama de Arquitetura - WebSocket

## Arquitetura Atual vs Proposta

### 🔵 Arquitetura Atual (Sem WebSocket)

```
┌─────────────────────────────────────────┐
│         Aplicação Desktop               │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │   VideoProcessor                  │  │
│  │   (Thread de vídeo)              │  │
│  │   ↓ detecta gesto                │  │
│  └───────────┬───────────────────────┘  │
│              │                          │
│              ↓ callback                 │
│  ┌───────────────────────────────────┐  │
│  │   main.py                         │  │
│  │   on_gesto_detectado()            │  │
│  │   ↓                               │  │
│  │   • Busca mensagem                │  │
│  │   • Atualiza UI                   │  │
│  │   • Reproduz alerta (se crítico)  │  │
│  └───────────────────────────────────┘  │
│              │                          │
│              ↓                          │
│  ┌───────────────────────────────────┐  │
│  │   MainWindow (Tkinter)            │  │
│  │   • Exibe gesto atual             │  │
│  │   • Lista gestos salvos           │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 🟢 Arquitetura Proposta (Com WebSocket)

```
┌─────────────────────────────────────────────────────────────┐
│              Aplicação Desktop (Paciente)                   │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │   VideoProcessor                                      │ │
│  │   (Thread de vídeo)                                  │ │
│  │   ↓ detecta gesto                                    │ │
│  └───────────┬───────────────────────────────────────────┘ │
│              │                                              │
│              ↓ callback                                     │
│  ┌───────────────────────────────────────────────────────┐ │
│  │   main.py                                            │ │
│  │   on_gesto_detectado()                               │ │
│  │   ↓                                                  │ │
│  │   • Busca mensagem                                   │ │
│  │   • Atualiza UI                                      │ │
│  │   • Reproduz alerta (se crítico)                     │ │
│  │   • 🆕 Envia via WebSocket                           │ │
│  └───────────┬───────────────────────────────────────────┘ │
│              │                                              │
│              ↓                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │   WebSocketClient                                    │ │
│  │   • Conecta ao servidor                              │ │
│  │   • Envia mensagem JSON                             │ │
│  │   • Gerencia reconexão                              │ │
│  └───────────┬───────────────────────────────────────────┘ │
└──────────────┼──────────────────────────────────────────────┘
               │
               │ WebSocket (WSS)
               │
               ↓
┌──────────────────────────────────────────────────────────────┐
│              Servidor WebSocket                              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   WebSocket Server                                  │  │
│  │   • Recebe mensagens de pacientes                  │  │
│  │   • Valida autenticação                            │  │
│  │   • Gerencia rooms (quartos/áreas)                 │  │
│  │   • Distribui para enfermeiros                     │  │
│  └───────────┬──────────────────────────────────────────┘  │
│              │                                              │
│              ↓ broadcast                                    │
└──────────────┼──────────────────────────────────────────────┘
               │
               │ WebSocket (WSS)
               │
       ┌───────┴───────┬───────────────┬───────────────┐
       ↓               ↓               ↓               ↓
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│Enfermeiro│   │Enfermeiro│   │Enfermeiro│   │Enfermeiro│
│   App    │   │   App    │   │   App    │   │   App    │
│(Mobile/  │   │(Mobile/  │   │(Mobile/  │   │(Mobile/  │
│ Desktop) │   │ Desktop) │   │ Desktop) │   │ Desktop) │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
```

## Fluxo Detalhado de Mensagem

```
┌─────────────────────────────────────────────────────────────┐
│ PASSO 1: Detecção                                           │
│                                                             │
│  VideoProcessor detecta gesto                               │
│  → chave: (4, 8, 12)                                       │
│  → dedos_estendidos: [4, 8, 12]                            │
│  → indice_mao: 0                                           │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ PASSO 2: Processamento Local                                │
│                                                             │
│  on_gesto_detectado(chave, dedos_estendidos, indice_mao)   │
│  ↓                                                          │
│  • Busca mensagem no repositório                           │
│    → mensagem: "Preciso de ajuda urgente.🆘"              │
│  • Atualiza UI                                             │
│  • Verifica se é crítico                                   │
│    → prioridade: "alta"                                     │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ PASSO 3: Preparação da Mensagem                             │
│                                                             │
│  WebSocketClient.preparar_mensagem()                       │
│  ↓                                                          │
│  {                                                          │
│    "tipo": "gesto_detectado",                              │
│    "timestamp": "2024-01-15T14:30:45.123Z",                │
│    "paciente": {                                            │
│      "id": "PAC001",                                        │
│      "nome": "João Silva",                                  │
│      "quarto": "201"                                        │
│    },                                                       │
│    "gesto": {                                               │
│      "chave": [4, 8, 12],                                  │
│      "mensagem": "Preciso de ajuda urgente.🆘",            │
│      "indice_mao": 0                                        │
│    },                                                       │
│    "prioridade": "alta"                                     │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ PASSO 4: Envio (Não-bloqueante)                             │
│                                                             │
│  WebSocketClient.enviar(mensagem)                          │
│  ↓ [Thread separada ou async]                              │
│  • Serializa JSON                                           │
│  • Envia via WebSocket                                      │
│  • Não aguarda resposta (fire-and-forget)                  │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ PASSO 5: Servidor Recebe                                    │
│                                                             │
│  WebSocket Server                                           │
│  ↓                                                          │
│  • Valida mensagem                                          │
│  • Verifica autenticação                                    │
│  • Identifica room/quarto                                   │
│  • Adiciona ao histórico (opcional)                        │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ PASSO 6: Distribuição                                       │
│                                                             │
│  WebSocket Server.broadcast()                               │
│  ↓                                                          │
│  • Encontra enfermeiros no mesmo room                      │
│  • Envia mensagem para cada enfermeiro                     │
│  • Registra status: "enviado"                              │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ PASSO 7: Enfermeiros Recebem                                │
│                                                             │
│  App Enfermeiro (Mobile/Desktop)                           │
│  ↓                                                          │
│  • Recebe mensagem WebSocket                               │
│  • Exibe notificação push                                  │
│  • Atualiza lista de alertas                               │
│  • Reproduz som (se crítico)                               │
│  • Envia confirmação de recebimento                        │
└─────────────────────────────────────────────────────────────┘
```

## Estrutura de Módulos Proposta

```
src/
├── websocket/                    # 🆕 NOVO MÓDULO
│   ├── __init__.py
│   ├── websocket_client.py       # Cliente WebSocket
│   │   ├── WebSocketClient
│   │   │   ├── conectar()
│   │   │   ├── desconectar()
│   │   │   ├── enviar_gesto()
│   │   │   ├── _reconectar()
│   │   │   └── _enviar_mensagem()
│   │   └── MensagemGesto         # Classe de dados
│   │
│   └── websocket_server.py       # Servidor (se necessário)
│       └── WebSocketServer
│
├── config/
│   └── config.py                 # ✏️ ADICIONAR
│       ├── WEBSOCKET_ENABLED
│       ├── WEBSOCKET_SERVER_URL
│       ├── PACIENTE_ID
│       └── PACIENTE_NOME
│
└── ... (outros módulos existentes)
```

## Integração no main.py

```python
# main.py (conceitual - não implementado)

def main():
    # ... código existente ...
    
    # 🆕 NOVO: Inicializar WebSocket Client
    websocket_client = None
    if Config.WEBSOCKET_ENABLED:
        websocket_client = WebSocketClient(
            server_url=Config.WEBSOCKET_SERVER_URL,
            paciente_id=Config.PACIENTE_ID
        )
        websocket_client.conectar()
    
    # Callback modificado
    def on_gesto_detectado(chave, dedos_estendidos, indice_mao):
        mensagem = repositorio.obter_mensagem(chave)
        
        # ... código existente (UI, alerta) ...
        
        # 🆕 NOVO: Enviar via WebSocket
        if websocket_client and mensagem:
            websocket_client.enviar_gesto(
                chave=chave,
                mensagem=mensagem,
                indice_mao=indice_mao,
                prioridade='alta' if audio_handler.verificar_mensagem_critica(mensagem) else 'normal'
            )
    
    # ... resto do código ...
    
    # 🆕 NOVO: Fechar conexão ao sair
    if websocket_client:
        websocket_client.desconectar()
```

## Cenários de Uso

### Cenário 1: Paciente Único, Múltiplos Enfermeiros

```
Paciente (Quarto 201)
    ↓
Servidor WebSocket
    ↓
├─→ Enfermeiro A (Área 2)
├─→ Enfermeiro B (Área 2)
└─→ Enfermeiro C (Plantão)
```

### Cenário 2: Múltiplos Pacientes, Múltiplos Enfermeiros

```
Paciente 1 (Quarto 201) ─┐
Paciente 2 (Quarto 202) ─┤
Paciente 3 (Quarto 203) ─┼─→ Servidor WebSocket
                         │
                         ├─→ Enfermeiro A (Área 2)
                         ├─→ Enfermeiro B (Área 2)
                         └─→ Enfermeiro C (Plantão)
```

### Cenário 3: Gestos Críticos com Prioridade

```
Gesto Crítico Detectado
    ↓
Servidor identifica prioridade "alta"
    ↓
├─→ Notificação Push Urgente
├─→ Som de Alerta
└─→ Dashboard atualiza com destaque vermelho
```

## Tratamento de Erros

```
┌─────────────────────────────────────────┐
│  Tentativa de Envio                     │
└───────────────┬─────────────────────────┘
                │
        ┌───────┴───────┐
        │               │
    Sucesso?        Erro?
        │               │
        ↓               ↓
┌───────────────┐  ┌──────────────────┐
│ Mensagem      │  │ Verifica tipo    │
│ Enviada       │  │ de erro          │
└───────────────┘  └──────┬───────────┘
                           │
                  ┌────────┴────────┐
                  │                  │
            Conexão            Outro Erro
            Perdida?                │
                  │                  │
            ┌─────┴─────┐            │
            │           │            │
          Sim          Não          │
            │           │            │
            ↓           ↓            ↓
    ┌───────────┐ ┌──────────┐ ┌──────────┐
    │Tenta      │ │Log erro  │ │Log erro  │
    │reconectar │ │e continua│ │e continua│
    └───────────┘ └──────────┘ └──────────┘
```

## Performance e Otimizações

### Debounce de Gestos

```
Gesto Detectado (t=0s)
    ↓
Enviado via WebSocket
    ↓
Gesto Detectado Novamente (t=0.5s)
    ↓
❌ IGNORADO (mesmo gesto, < 2s)
    ↓
Gesto Diferente Detectado (t=3s)
    ↓
✅ ENVIADO (gesto diferente)
```

### Threading

```
Thread Principal (UI)
    │
    ├─→ VideoProcessor (Thread separada)
    │       │
    │       └─→ on_gesto_detectado()
    │               │
    │               └─→ WebSocketClient.enviar()
    │                       │
    │                       └─→ Thread/Async (não bloqueia)
    │
    └─→ MainWindow.mainloop()
```

