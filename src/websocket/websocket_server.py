"""
Servidor WebSocket para notificações em tempo real.
"""

import asyncio
import json
import threading
from typing import Set, Dict, Any, Optional
import websockets
from websockets.server import WebSocketServerProtocol


class WebSocketServer:
    """Servidor WebSocket para enviar notificações para enfermeiros."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        Inicializa o servidor WebSocket.
        
        Args:
            host: Endereço do servidor (padrão: localhost).
            port: Porta do servidor (padrão: 8765).
        """
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.server: Optional[websockets.server.Serve] = None
        self.running = False
        self._lock = threading.Lock()
    
    async def _registrar_cliente(self, websocket: WebSocketServerProtocol):
        """Registra um novo cliente conectado."""
        with self._lock:
            self.clients.add(websocket)
        print(f"✅ Cliente conectado. Total de enfermeiros conectados: {len(self.clients)}")
    
    async def _remover_cliente(self, websocket: WebSocketServerProtocol):
        """Remove um cliente desconectado."""
        with self._lock:
            self.clients.discard(websocket)
        print(f"❌ Cliente desconectado. Total de enfermeiros conectados: {len(self.clients)}")
    
    async def _handler_connection(self, websocket: WebSocketServerProtocol):
        """
        Handler para conexões WebSocket.
        
        Args:
            websocket: Conexão WebSocket do cliente.
        """
        await self._registrar_cliente(websocket)
        try:
            # Mantém conexão aberta até cliente desconectar
            await websocket.wait_closed()
        finally:
            await self._remover_cliente(websocket)
    
    async def _broadcast_async(self, mensagem: Dict[str, Any]):
        """
        Envia mensagem para todos os clientes conectados (versão assíncrona).
        
        Args:
            mensagem: Dicionário com dados da mensagem.
        """
        if not self.clients:
            return
        
        mensagem_json = json.dumps(mensagem, ensure_ascii=False)
        desconectados = []
        
        # Copia lista de clientes para evitar problemas de concorrência
        with self._lock:
            clientes_copia = self.clients.copy()
        
        for client in clientes_copia:
            try:
                await client.send(mensagem_json)
            except Exception as e:
                print(f"Erro ao enviar mensagem para cliente: {e}")
                desconectados.append(client)
        
        # Remove clientes desconectados
        for client in desconectados:
            await self._remover_cliente(client)
    
    def broadcast(self, mensagem: Dict[str, Any]):
        """
        Envia mensagem para todos os clientes conectados (versão síncrona).
        
        Args:
            mensagem: Dicionário com dados da mensagem.
        """
        if not self.running:
            print("⚠️ WebSocket não está rodando. Mensagem não enviada.")
            return
        
        if not self.loop:
            print("⚠️ Loop do WebSocket não inicializado.")
            return
        
        if not self.loop.is_running():
            print("⚠️ Loop do WebSocket não está rodando.")
            return
        
        if not self.clients:
            print(f"⚠️ Nenhum cliente conectado ao WebSocket. Mensagem não enviada: {mensagem.get('mensagem', 'N/A')}")
            return
        
        try:
            # Envia mensagem assincronamente
            future = asyncio.run_coroutine_threadsafe(
                self._broadcast_async(mensagem),
                self.loop
            )
            # Aguarda um pouco para garantir que foi enviada
            future.result(timeout=1.0)
            print(f"📤 Mensagem enviada para {len(self.clients)} cliente(s): {mensagem.get('mensagem', 'N/A')}")
        except asyncio.TimeoutError:
            print(f"⏱️ Timeout ao enviar mensagem via WebSocket")
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem via WebSocket: {e}")
            import traceback
            traceback.print_exc()
    
    def _iniciar_servidor(self):
        """Inicia o servidor WebSocket em loop assíncrono."""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Cria função handler compatível que aceita websocket e path opcional
            async def handler(websocket, path=None):
                """Handler compatível que aceita websocket e path opcional."""
                await self._handler_connection(websocket)
            
            async def iniciar():
                try:
                    # Usa handler compatível
                    self.server = await websockets.serve(
                        handler,
                        self.host,
                        self.port,
                        ping_interval=20,
                        ping_timeout=10
                    )
                    print(f"🌐 Servidor WebSocket iniciado em ws://{self.host}:{self.port}")
                    print(f"📱 Abra o arquivo 'cliente_enfermeiro.html' no navegador para visualizar as notificações")
                    print(f"✅ Servidor pronto para receber conexões")
                    self.running = True
                except OSError as e:
                    if "Address already in use" in str(e) or "address is already in use" in str(e).lower():
                        print(f"⚠️ Porta {self.port} já está em uso. Tentando usar porta alternativa...")
                        # Tenta porta alternativa
                        self.port = self.port + 1
                        try:
                            self.server = await websockets.serve(
                                handler,
                                self.host,
                                self.port
                            )
                            print(f"🌐 Servidor WebSocket iniciado em ws://{self.host}:{self.port}")
                            print(f"📱 Atualize a URL no cliente_enfermeiro.html para ws://{self.host}:{self.port}")
                            self.running = True
                        except Exception as e2:
                            print(f"❌ Erro ao iniciar servidor WebSocket na porta alternativa: {e2}")
                            self.running = False
                    else:
                        print(f"❌ Erro ao iniciar servidor WebSocket: {e}")
                        import traceback
                        traceback.print_exc()
                        self.running = False
                except Exception as e:
                    print(f"❌ Erro ao iniciar servidor WebSocket: {e}")
                    import traceback
                    traceback.print_exc()
                    self.running = False
                    return
            
            self.loop.run_until_complete(iniciar())
            if self.running:
                self.loop.run_forever()
        except Exception as e:
            print(f"❌ Erro crítico ao iniciar servidor WebSocket: {e}")
            import traceback
            traceback.print_exc()
            self.running = False
    
    def iniciar(self):
        """
        Inicia o servidor WebSocket em thread separada.
        Deve ser chamado de uma thread, não bloqueia.
        """
        try:
            self._iniciar_servidor()
        except Exception as e:
            print(f"Erro ao iniciar servidor WebSocket: {e}")
            self.running = False
    
    def parar(self):
        """Para o servidor WebSocket."""
        self.running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        # Fecha todas as conexões
        if self.clients:
            for client in list(self.clients):
                try:
                    self.loop.call_soon_threadsafe(client.close)
                except:
                    pass
        
        print("🛑 Servidor WebSocket parado.")

