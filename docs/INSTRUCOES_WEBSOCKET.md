# 📡 Instruções de Uso - WebSocket

## 🚀 Como Usar o Sistema com WebSocket

### 1. Instalar Dependências

Primeiro, instale a nova dependência:

```bash
pip install -r requirements.txt
```

Ou apenas:

```bash
pip install websockets>=11.0
```

### 2. Executar a Aplicação do Paciente

Execute a aplicação normalmente:

```bash
python main.py
```

Você verá uma mensagem no console indicando que o servidor WebSocket foi iniciado:

```
🌐 Servidor WebSocket iniciado em ws://localhost:8765
📱 Abra o arquivo 'cliente_enfermeiro.html' no navegador para visualizar as notificações
✅ Cliente conectado. Total de enfermeiros conectados: 1
```

### 3. Abrir o Painel dos Enfermeiros

Abra o arquivo `cliente_enfermeiro.html` no seu navegador:

- **Windows**: Clique duas vezes no arquivo ou arraste para o navegador
- **Linux/Mac**: Abra com `firefox cliente_enfermeiro.html` ou `chrome cliente_enfermeiro.html`

Você verá a interface com:
- Status de conexão (verde = conectado)
- Lista de alertas em tempo real
- Contador de alertas recebidos

### 4. Testar o Sistema

1. **Faça um gesto na câmera** da aplicação do paciente
2. **Observe** a notificação aparecer instantaneamente no painel do enfermeiro
3. **Abra múltiplas abas** do navegador para simular múltiplos enfermeiros
4. **Todos receberão** as notificações simultaneamente

## 🎯 Funcionalidades

### Notificações em Tempo Real
- Quando um paciente faz um gesto, todos os enfermeiros conectados recebem uma notificação instantaneamente

### Priorização
- Gestos críticos (com palavras como "urgente", "emergência", "pânico") aparecem em **vermelho** com destaque
- Gestos normais aparecem em **azul**

### Interface Visual
- Design moderno e responsivo
- Animações suaves quando novos alertas chegam
- Som de alerta para gestos críticos

### Reconexão Automática
- Se a conexão cair, o sistema tenta reconectar automaticamente
- Até 5 tentativas de reconexão

## ⚙️ Configurações

As configurações podem ser alteradas em `src/config/config.py`:

```python
# Configurações WebSocket
WEBSOCKET_ENABLED = True          # Habilitar/desabilitar WebSocket
WEBSOCKET_HOST = "localhost"      # Endereço do servidor
WEBSOCKET_PORT = 8765              # Porta do servidor

# Informações do paciente
PACIENTE_ID = "PAC001"
PACIENTE_NOME = "João Silva"
PACIENTE_QUARTO = "201"
```

## 🎓 Para Apresentação

### Demonstração Sugerida:

1. **Inicie a aplicação do paciente**
   - Mostre a detecção de gestos funcionando

2. **Abra o painel do enfermeiro**
   - Abra `cliente_enfermeiro.html` no navegador
   - Mostre o status "Conectado ✅"

3. **Faça um gesto**
   - Faça um gesto na câmera
   - **Imediatamente** a notificação aparece no painel
   - Destaque a velocidade da comunicação

4. **Demonstre múltiplos enfermeiros**
   - Abra várias abas do navegador
   - Mostre que todos recebem simultaneamente

5. **Demonstre gestos críticos**
   - Faça um gesto com mensagem crítica (ex: "Preciso de ajuda urgente")
   - Mostre o destaque vermelho e o som de alerta

## 🔧 Solução de Problemas

### WebSocket não conecta

1. Verifique se a aplicação do paciente está rodando
2. Verifique se a porta 8765 não está sendo usada por outro programa
3. Verifique o console da aplicação para mensagens de erro

### Notificações não aparecem

1. Verifique se o gesto está salvo no sistema (aparece na lista de gestos)
2. Verifique o console do navegador (F12) para erros
3. Verifique se o status mostra "Conectado ✅"

### Erro ao instalar websockets

```bash
# Tente atualizar o pip primeiro
pip install --upgrade pip
pip install websockets>=11.0
```

## 📝 Formato das Mensagens

As mensagens enviadas via WebSocket seguem este formato:

```json
{
  "tipo": "gesto",
  "paciente": "João Silva - Quarto 201",
  "mensagem": "Preciso de ajuda urgente.🆘",
  "prioridade": "alta",
  "timestamp": "14:30:45"
}
```

## ✅ Checklist para Apresentação

- [ ] Aplicação do paciente funcionando
- [ ] Servidor WebSocket iniciado (mensagem no console)
- [ ] Painel do enfermeiro aberto e conectado
- [ ] Teste de gesto normal funcionando
- [ ] Teste de gesto crítico funcionando (destaque vermelho)
- [ ] Teste com múltiplas abas (múltiplos enfermeiros)
- [ ] Som de alerta funcionando para gestos críticos

---

**Boa sorte na apresentação! 🎉**

