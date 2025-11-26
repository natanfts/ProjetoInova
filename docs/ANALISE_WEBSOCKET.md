# 📡 Análise: Implementação de WebSocket para Notificação de Enfermeiros

## 📋 Resumo Executivo

Esta análise avalia a viabilidade de implementar WebSocket para notificar enfermeiros em tempo real sempre que um paciente fizer um gesto reconhecido pelo sistema.

**Conclusão**: ✅ **VIÁVEL** - A arquitetura atual está bem estruturada e permite integração de WebSocket sem grandes refatorações.

---

## 🏗️ Arquitetura Atual

### Fluxo de Detecção Atual

```
VideoProcessor → detecta gesto → callback → MainWindow → atualiza UI
                                      ↓
                              AudioHandler (alerta sonoro)
```

### Pontos de Integração Identificados

1. **`main.py` - linha 27**: Função `on_gesto_detectado()`
   - **Localização ideal**: Aqui já temos acesso a `chave`, `mensagem` e `indice_mao`
   - **Vantagem**: Ponto centralizado onde todas as informações estão disponíveis

2. **`VideoProcessor._loop_video()` - linha 73**: Callback de gesto
   - **Alternativa**: Poderia enviar diretamente do processador de vídeo
   - **Desvantagem**: Menos contexto sobre o paciente

---

## 🎯 Arquitetura Proposta com WebSocket

### Opção 1: Cliente WebSocket (Recomendada)

```
┌─────────────────┐
│  Aplicação      │
│  (Cliente)      │───WebSocket───►┌─────────────────┐
│                 │                │  Servidor       │
│  VideoProcessor │                │  WebSocket      │───► Enfermeiros
│  ↓              │                │  (Broker)       │     (Múltiplos)
│  on_gesto_      │                │                 │
│  detectado()    │                └─────────────────┘
└─────────────────┘
```

**Vantagens:**
- ✅ Separação de responsabilidades
- ✅ Escalável (múltiplos pacientes → servidor → múltiplos enfermeiros)
- ✅ Servidor pode gerenciar autenticação/autorização
- ✅ Facilita adicionar persistência/histórico

### Opção 2: Servidor WebSocket Integrado

```
┌─────────────────────────────────┐
│  Aplicação (Servidor + Cliente) │
│                                 │
│  VideoProcessor                 │
│  ↓                              │
│  WebSocketServer ──────────────► Enfermeiros
│  (thread separada)              │
└─────────────────────────────────┘
```

**Vantagens:**
- ✅ Mais simples (tudo em uma aplicação)
- ✅ Menos infraestrutura

**Desvantagens:**
- ❌ Menos escalável
- ❌ Mistura responsabilidades
- ❌ Mais difícil gerenciar múltiplos pacientes

---

## 📦 Dependências Necessárias

### Opção 1: Cliente WebSocket (Python)

```python
# Biblioteca recomendada
websockets>=11.0  # Para servidor WebSocket em Python
# OU
websocket-client>=1.6.0  # Para cliente WebSocket em Python
```

### Opção 2: Servidor WebSocket Integrado

```python
# Opções de servidor WebSocket em Python:
websockets>=11.0  # Async/await, moderno
# OU
python-socketio>=5.10.0  # Mais recursos (rooms, namespaces)
# OU
fastapi[websockets]>=0.100.0  # Se quiser API REST também
```

### Opção 3: Servidor WebSocket Separado (Node.js/Outro)

```javascript
// Exemplo com Node.js
socket.io>=4.0.0
// OU
ws>=8.0.0
```

---

## 🔌 Estrutura de Mensagem WebSocket

### Formato JSON Proposto

```json
{
  "tipo": "gesto_detectado",
  "timestamp": "2024-01-15T14:30:45.123Z",
  "paciente": {
    "id": "PAC001",
    "nome": "João Silva",
    "quarto": "201"
  },
  "gesto": {
    "chave": [4, 8, 12],
    "dedos_estendidos": [4, 8, 12],
    "mensagem": "Preciso de ajuda urgente.🆘",
    "indice_mao": 0
  },
  "prioridade": "alta",  // baseado em palavras-chave críticas
  "status": "pendente"   // pendente, visualizado, atendido
}
```

### Tipos de Mensagens

1. **`gesto_detectado`**: Novo gesto detectado
2. **`gesto_atualizado`**: Status do gesto atualizado (visualizado/atendido)
3. **`heartbeat`**: Mantém conexão ativa
4. **`paciente_conectado`**: Paciente conectou ao sistema
5. **`paciente_desconectado`**: Paciente desconectou

---

## 🎨 Pontos de Integração no Código Atual

### 1. Criar Módulo `src/websocket/`

```
src/websocket/
├── __init__.py
├── websocket_client.py    # Cliente WebSocket
└── websocket_server.py    # Servidor WebSocket (se opção 2)
```

### 2. Modificar `main.py`

**Localização**: Linha 27-40 (função `on_gesto_detectado`)

**Mudança necessária**:
```python
# ANTES
def on_gesto_detectado(chave, dedos_estendidos, indice_mao):
    mensagem = repositorio.obter_mensagem(chave)
    # ... código atual ...

# DEPOIS (conceitual, não implementado ainda)
def on_gesto_detectado(chave, dedos_estendidos, indice_mao):
    mensagem = repositorio.obter_mensagem(chave)
    # ... código atual ...
    
    # NOVO: Enviar via WebSocket
    websocket_client.enviar_gesto({
        'chave': chave,
        'mensagem': mensagem,
        'indice_mao': indice_mao,
        'timestamp': datetime.now().isoformat()
    })
```

### 3. Adicionar Configuração

**Arquivo**: `src/config/config.py`

**Novas configurações necessárias**:
```python
# WebSocket
WEBSOCKET_ENABLED = False  # Flag para habilitar/desabilitar
WEBSOCKET_SERVER_URL = "ws://localhost:8765"
WEBSOCKET_SERVER_PORT = 8765
WEBSOCKET_RECONNECT_INTERVAL = 5  # segundos
WEBSOCKET_TIMEOUT = 30  # segundos

# Informações do paciente (será necessário adicionar)
PACIENTE_ID = None  # Configurar por paciente
PACIENTE_NOME = None
PACIENTE_QUARTO = None
```

---

## 🔒 Considerações de Segurança

### 1. Autenticação
- **Problema**: Enfermeiros precisam se autenticar
- **Solução**: Token JWT ou autenticação no handshake WebSocket

### 2. Autorização
- **Problema**: Nem todos os enfermeiros devem ver todos os pacientes
- **Solução**: Rooms/Namespaces por quarto/área

### 3. Criptografia
- **Problema**: Dados sensíveis de saúde (LGPD/HIPAA)
- **Solução**: WSS (WebSocket Secure) com TLS/SSL

### 4. Rate Limiting
- **Problema**: Prevenir spam de gestos
- **Solução**: Debounce/throttle na detecção de gestos

---

## ⚡ Desafios e Soluções

### Desafio 1: Gestos Duplicados

**Problema**: O mesmo gesto pode ser detectado múltiplas vezes por segundo.

**Solução**:
- Implementar debounce (esperar X segundos antes de enviar novamente)
- Adicionar timestamp do último gesto enviado
- Comparar gesto atual com último enviado

**Localização**: `on_gesto_detectado()` ou `WebSocketClient`

### Desafio 2: Conexão Perdida

**Problema**: WebSocket pode desconectar (rede instável).

**Solução**:
- Implementar reconexão automática
- Fila de mensagens não enviadas (opcional)
- Log de eventos para auditoria

### Desafio 3: Múltiplos Pacientes

**Problema**: Como identificar qual paciente fez o gesto?

**Solução**:
- Adicionar ID do paciente na configuração
- Cada instância da aplicação = 1 paciente
- Servidor gerencia múltiplas conexões

### Desafio 4: Performance

**Problema**: WebSocket não deve bloquear detecção de gestos.

**Solução**:
- Enviar em thread separada (async)
- Usar fila de mensagens
- Não aguardar confirmação do servidor

---

## 📊 Fluxo de Dados Proposto

```
1. VideoProcessor detecta gesto
   ↓
2. on_gesto_detectado() é chamado
   ↓
3. Verifica se gesto mudou (debounce)
   ↓
4. Prepara mensagem JSON
   ↓
5. WebSocketClient.enviar() [async/não-bloqueante]
   ↓
6. Servidor WebSocket recebe
   ↓
7. Servidor valida e autentica
   ↓
8. Servidor distribui para enfermeiros conectados
   ↓
9. Enfermeiros recebem notificação em tempo real
```

---

## 🧪 Estratégia de Implementação

### Fase 1: Preparação (Sem mudanças no código)
- ✅ Definir estrutura de mensagens
- ✅ Escolher biblioteca WebSocket
- ✅ Definir servidor WebSocket (próprio ou externo)

### Fase 2: Módulo WebSocket
- Criar `src/websocket/websocket_client.py`
- Implementar conexão e reconexão
- Implementar envio de mensagens

### Fase 3: Integração
- Modificar `main.py` para usar WebSocketClient
- Adicionar configurações em `config.py`
- Adicionar tratamento de erros

### Fase 4: Servidor (se necessário)
- Criar servidor WebSocket
- Implementar autenticação
- Implementar distribuição para enfermeiros

### Fase 5: Testes
- Testar conexão/desconexão
- Testar múltiplos gestos
- Testar múltiplos enfermeiros
- Testar performance

---

## 💡 Recomendações

### Arquitetura Recomendada

**Opção Híbrida**: Cliente WebSocket + Servidor Separado

**Justificativa**:
1. ✅ Separação clara de responsabilidades
2. ✅ Escalável (múltiplos pacientes, múltiplos enfermeiros)
3. ✅ Facilita manutenção
4. ✅ Permite adicionar recursos futuros (histórico, dashboard, etc.)

### Biblioteca Recomendada

**Python Cliente**: `websocket-client` ou `websockets`
- `websocket-client`: Síncrono, mais simples
- `websockets`: Assíncrono, mais moderno

**Servidor**: `FastAPI` com WebSockets ou `Socket.IO`
- FastAPI: Moderno, rápido, boa documentação
- Socket.IO: Mais recursos (rooms, namespaces)

### Configuração Inicial

1. **Modo Desenvolvimento**: WebSocket opcional (flag `WEBSOCKET_ENABLED`)
2. **Servidor Local**: Para testes (`ws://localhost:8765`)
3. **Servidor Produção**: Configurável via variáveis de ambiente

---

## 📈 Escalabilidade

### Cenário Atual
- 1 paciente → 1 aplicação → WebSocket → N enfermeiros

### Cenário Futuro
- N pacientes → N aplicações → Servidor WebSocket → M enfermeiros
- Servidor pode:
  - Agrupar por quarto/área
  - Priorizar gestos críticos
  - Manter histórico
  - Dashboard em tempo real

---

## 🔍 Pontos de Atenção

1. **Thread Safety**: WebSocket deve ser thread-safe (usar locks ou async)
2. **Memory Leaks**: Fechar conexões adequadamente
3. **Error Handling**: Não quebrar aplicação se WebSocket falhar
4. **Logging**: Registrar eventos importantes (gestos enviados, erros)
5. **Testing**: Testar com servidor offline, conexão instável

---

## 📝 Próximos Passos (Quando Implementar)

1. Decidir arquitetura (cliente vs servidor integrado)
2. Escolher biblioteca WebSocket
3. Criar módulo `src/websocket/`
4. Adicionar configurações em `config.py`
5. Modificar `main.py` para integrar WebSocket
6. Criar servidor WebSocket (se necessário)
7. Implementar debounce para evitar duplicatas
8. Adicionar tratamento de erros robusto
9. Testar em ambiente de desenvolvimento
10. Documentar API WebSocket

---

## ✅ Conclusão

A implementação de WebSocket é **totalmente viável** e se encaixa bem na arquitetura atual. A estrutura modular facilita a adição sem grandes refatorações.

**Complexidade**: Média
**Tempo estimado**: 2-3 dias de desenvolvimento
**Impacto**: Alto (melhora significativa na comunicação)

**Recomendação**: Prosseguir com a implementação seguindo a Opção 1 (Cliente WebSocket + Servidor Separado).

