# 📡 Análise Simplificada: WebSocket para Trabalho de Faculdade

## 🎯 Objetivo

Implementar WebSocket de forma **simples e direta** para demonstrar notificação de enfermeiros em tempo real quando um paciente fizer um gesto.

**Foco**: Funcionalidade para apresentação, não escalabilidade empresarial.

---

## ✅ Solução Recomendada: Servidor WebSocket Integrado

### Por que esta opção?

- ✅ **Mais simples**: Tudo em uma aplicação Python
- ✅ **Fácil de demonstrar**: Um único executável
- ✅ **Rápido de implementar**: 1-2 dias
- ✅ **Perfeito para apresentação**: Funciona offline, sem configuração complexa

### Arquitetura Simplificada

```
┌─────────────────────────────────────────────┐
│     Aplicação Desktop (Paciente)           │
│                                             │
│  VideoProcessor                             │
│    ↓ detecta gesto                          │
│  on_gesto_detectado()                       │
│    ↓                                         │
│  WebSocketServer (thread separada)         │
│    ↓                                         │
│  Broadcast para todos conectados            │
└───────────────┬─────────────────────────────┘
                │
                │ WebSocket (ws://localhost:8765)
                │
        ┌───────┴───────┐
        │               │
┌───────────────┐ ┌───────────────┐
│  Cliente Web  │ │  Cliente Web  │
│  (Enfermeiro) │ │  (Enfermeiro) │
│  Navegador    │ │  Navegador    │
└───────────────┘ └───────────────┘
```

**Vantagem**: Enfermeiros acessam via navegador web (não precisa instalar nada!)

---

## 📦 Dependências Mínimas

Apenas **1 biblioteca adicional**:

```python
websockets>=11.0
```

Adicionar ao `requirements.txt`:
```
websockets>=11.0
```

---

## 🏗️ Estrutura de Implementação

### Novo Módulo: `src/websocket/`

```
src/websocket/
├── __init__.py
└── websocket_server.py    # Servidor WebSocket simples
```

### Modificações Necessárias

1. **`src/config/config.py`**: Adicionar configurações
   ```python
   WEBSOCKET_ENABLED = True
   WEBSOCKET_PORT = 8765
   PACIENTE_ID = "PAC001"
   PACIENTE_NOME = "João Silva"
   PACIENTE_QUARTO = "201"
   ```

2. **`main.py`**: Adicionar servidor WebSocket
   - Iniciar servidor em thread separada
   - Enviar mensagem quando gesto detectado

3. **Cliente Web**: Criar `cliente_enfermeiro.html`
   - Página HTML simples com JavaScript
   - Conecta via WebSocket
   - Exibe notificações em tempo real

---

## 📝 Formato de Mensagem Simplificado

```json
{
  "tipo": "gesto",
  "paciente": "João Silva - Quarto 201",
  "mensagem": "Preciso de ajuda urgente.🆘",
  "prioridade": "alta",
  "timestamp": "14:30:45"
}
```

---

## 🎨 Interface do Cliente (Enfermeiro)

### Página Web Simples

- **Título**: "Central de Notificações - Enfermeiros"
- **Lista de alertas**: Cards com gestos recebidos
- **Atualização em tempo real**: Novos gestos aparecem automaticamente
- **Destaque para críticos**: Cor vermelha para gestos urgentes
- **Som de notificação**: Beep quando recebe gesto crítico

### Exemplo Visual

```
┌─────────────────────────────────────┐
│  Central de Notificações           │
│  Status: Conectado ✅               │
├─────────────────────────────────────┤
│  🔴 URGENTE                         │
│  João Silva - Quarto 201            │
│  "Preciso de ajuda urgente.🆘"     │
│  14:30:45                          │
├─────────────────────────────────────┤
│  ⚪ Normal                          │
│  João Silva - Quarto 201            │
│  "Estou bem, obrigado.👍"          │
│  14:25:12                          │
└─────────────────────────────────────┘
```

---

## 🔧 Implementação Passo a Passo

### Passo 1: Criar Servidor WebSocket

**Arquivo**: `src/websocket/websocket_server.py`

```python
import asyncio
import websockets
import json
from typing import Set

class WebSocketServer:
    def __init__(self, port=8765):
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
    
    async def registrar_cliente(self, websocket):
        self.clients.add(websocket)
        print(f"Cliente conectado. Total: {len(self.clients)}")
    
    async def remover_cliente(self, websocket):
        self.clients.discard(websocket)
        print(f"Cliente desconectado. Total: {len(self.clients)}")
    
    async def broadcast(self, mensagem):
        if self.clients:
            mensagem_json = json.dumps(mensagem)
            desconectados = []
            for client in self.clients.copy():
                try:
                    await client.send(mensagem_json)
                except:
                    desconectados.append(client)
            for client in desconectados:
                await self.remover_cliente(client)
    
    async def servidor(self, websocket, path):
        await self.registrar_cliente(websocket)
        try:
            await websocket.wait_closed()
        finally:
            await self.remover_cliente(websocket)
    
    def iniciar(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        start_server = websockets.serve(self.servidor, "localhost", self.port)
        loop.run_until_complete(start_server)
        print(f"Servidor WebSocket iniciado em ws://localhost:{self.port}")
        loop.run_forever()
```

### Passo 2: Integrar no main.py

**Modificação**: Adicionar servidor e enviar mensagens

```python
# No início do main()
websocket_server = WebSocketServer(port=8765)
thread_websocket = threading.Thread(target=websocket_server.iniciar, daemon=True)
thread_websocket.start()

# Na função on_gesto_detectado()
def on_gesto_detectado(chave, dedos_estendidos, indice_mao):
    mensagem = repositorio.obter_mensagem(chave)
    # ... código existente ...
    
    # NOVO: Enviar via WebSocket
    if mensagem:
        prioridade = "alta" if audio_handler.verificar_mensagem_critica(mensagem) else "normal"
        websocket_server.broadcast({
            "tipo": "gesto",
            "paciente": f"{Config.PACIENTE_NOME} - Quarto {Config.PACIENTE_QUARTO}",
            "mensagem": mensagem,
            "prioridade": prioridade,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
```

### Passo 3: Criar Cliente Web

**Arquivo**: `cliente_enfermeiro.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>Central de Notificações - Enfermeiros</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .alerta { border: 1px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .urgente { background-color: #ffebee; border-color: #f44336; }
        .normal { background-color: #e3f2fd; border-color: #2196f3; }
        .status { padding: 10px; margin-bottom: 20px; border-radius: 5px; }
        .conectado { background-color: #4caf50; color: white; }
        .desconectado { background-color: #f44336; color: white; }
    </style>
</head>
<body>
    <h1>Central de Notificações - Enfermeiros</h1>
    <div id="status" class="status desconectado">Desconectado</div>
    <div id="alertas"></div>

    <script>
        const ws = new WebSocket('ws://localhost:8765');
        const alertasDiv = document.getElementById('alertas');
        const statusDiv = document.getElementById('status');

        ws.onopen = () => {
            statusDiv.textContent = 'Conectado ✅';
            statusDiv.className = 'status conectado';
        };

        ws.onclose = () => {
            statusDiv.textContent = 'Desconectado ❌';
            statusDiv.className = 'status desconectado';
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const alerta = document.createElement('div');
            alerta.className = `alerta ${data.prioridade === 'alta' ? 'urgente' : 'normal'}`;
            alerta.innerHTML = `
                <strong>${data.prioridade === 'alta' ? '🔴 URGENTE' : '⚪ Normal'}</strong><br>
                <strong>Paciente:</strong> ${data.paciente}<br>
                <strong>Mensagem:</strong> ${data.mensagem}<br>
                <strong>Horário:</strong> ${data.timestamp}
            `;
            alertasDiv.insertBefore(alerta, alertasDiv.firstChild);
            
            if (data.prioridade === 'alta') {
                // Som de alerta
                const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OSfTQ8MUKfj8LZjHAY4kdfyzHksBSR3x/DdkEAKFF606euoVRQKRp/g8r5sIQUqgc7y2Yk2CBtpvfDkn00PDFCn4/C2YxwGOJHX8sx5LAUkd8fw3ZBAC');
                audio.play().catch(() => {});
            }
        };
    </script>
</body>
</html>
```

---

## 🎯 Funcionalidades para Demonstração

### Durante a Apresentação

1. **Abrir aplicação do paciente**
   - Inicia detecção de gestos
   - Servidor WebSocket inicia automaticamente

2. **Abrir página web do enfermeiro**
   - Abrir `cliente_enfermeiro.html` no navegador
   - Mostrar status "Conectado ✅"

3. **Fazer gesto na câmera**
   - Gesto aparece na aplicação do paciente
   - **Imediatamente** aparece na página do enfermeiro
   - Se for crítico, destaque vermelho + som

4. **Demonstrar múltiplos enfermeiros**
   - Abrir várias abas do navegador
   - Todos recebem notificações simultaneamente

---

## ⚡ Vantagens desta Abordagem

✅ **Simples**: Apenas 1 biblioteca adicional  
✅ **Rápido**: Implementação em 1-2 dias  
✅ **Fácil de demonstrar**: Funciona localmente, sem configuração  
✅ **Visual**: Interface web moderna  
✅ **Funcional**: Todas as funcionalidades necessárias  
✅ **Profissional**: WebSocket é tecnologia moderna e relevante  

---

## 📋 Checklist de Implementação

- [ ] Adicionar `websockets>=11.0` ao `requirements.txt`
- [ ] Criar `src/websocket/websocket_server.py`
- [ ] Adicionar configurações em `config.py`
- [ ] Modificar `main.py` para iniciar servidor
- [ ] Modificar `on_gesto_detectado()` para enviar mensagens
- [ ] Criar `cliente_enfermeiro.html`
- [ ] Testar conexão e envio de mensagens
- [ ] Testar múltiplos clientes simultâneos
- [ ] Preparar demonstração para apresentação

---

## 🎓 Pontos para Apresentação

### O que destacar:

1. **Tecnologia Moderna**: WebSocket para comunicação em tempo real
2. **Arquitetura**: Separação cliente-servidor
3. **Funcionalidade**: Notificações instantâneas
4. **Interface**: Web responsiva e intuitiva
5. **Escalabilidade**: Suporta múltiplos enfermeiros simultaneamente

### Demonstração Sugerida:

1. Mostrar aplicação do paciente funcionando
2. Mostrar página web do enfermeiro conectada
3. Fazer gesto → mostrar notificação aparecendo instantaneamente
4. Abrir múltiplas abas → mostrar broadcast funcionando
5. Fazer gesto crítico → mostrar destaque e som

---

## 🚀 Tempo Estimado

- **Desenvolvimento**: 1-2 dias
- **Testes**: 0.5 dia
- **Preparação para apresentação**: 0.5 dia

**Total**: ~2-3 dias

---

## ✅ Conclusão

Esta solução simplificada é **perfeita para trabalho de faculdade**:

- ✅ Implementação rápida
- ✅ Fácil de demonstrar
- ✅ Todas as funcionalidades necessárias
- ✅ Tecnologia moderna e relevante
- ✅ Visualmente impressionante

**Recomendação**: Implementar esta solução simplificada para a apresentação.

