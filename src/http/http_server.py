"""
Servidor HTTP simples para servir o painel do enfermeiro.
"""

import http.server
import socketserver
import threading
import webbrowser
import time
import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs


class HTTPHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP customizado para servir o painel do enfermeiro."""
    
    def __init__(self, *args, html_path: Optional[Path] = None, db=None, **kwargs):
        self.html_path = html_path
        self.db = db
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Responde a requisições GET."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/' or parsed_path.path == '/cliente_enfermeiro.html':
            # Serve o arquivo HTML do painel
            if self.html_path and self.html_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(self.html_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'404 - Arquivo nao encontrado')
        elif parsed_path.path.startswith('/assets/'):
            # Serve arquivos estáticos da pasta assets
            base_dir = self.html_path.parent if self.html_path else Path('.')
            file_path = base_dir / parsed_path.path.lstrip('/')
            
            if file_path.exists() and file_path.is_file():
                # Determina o tipo MIME baseado na extensão
                ext = file_path.suffix.lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.svg': 'image/svg+xml',
                    '.gif': 'image/gif',
                    '.ico': 'image/x-icon',
                    '.css': 'text/css',
                    '.js': 'application/javascript'
                }
                content_type = mime_types.get(ext, 'application/octet-stream')
                
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'404 - Arquivo nao encontrado')
        elif parsed_path.path == '/api/config_gestos':
            # API: Lista configurações de gestos
            if self.db:
                try:
                    configs = self.db.listar_config_gestos()
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(configs, ensure_ascii=False).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(json.dumps({'erro': str(e)}).encode('utf-8'))
            else:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'Database not available')
        elif parsed_path.path == '/api/pacientes':
            # API: Lista pacientes
            if self.db:
                try:
                    # Obtém parâmetro apenas_ativos da query string
                    query_params = parse_qs(parsed_path.query)
                    apenas_ativos = query_params.get('apenas_ativos', ['true'])[0].lower() == 'true'
                    
                    pacientes = self.db.listar_pacientes(apenas_ativos=apenas_ativos)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(pacientes, ensure_ascii=False).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({'erro': str(e)}).encode('utf-8'))
            else:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'Database not available')
        elif parsed_path.path == '/api/historico':
            # API: Lista histórico de solicitações
            if self.db:
                try:
                    query_params = parse_qs(parsed_path.query)
                    paciente_id = query_params.get('paciente_id', [None])[0]
                    status = query_params.get('status', [None])[0]
                    
                    # Converte paciente_id para int se fornecido
                    paciente_id_int = int(paciente_id) if paciente_id and paciente_id.isdigit() else None
                    
                    # Busca histórico (com filtro opcional por paciente_id e status)
                    historico = self.db.listar_solicitacoes(
                        paciente_id=paciente_id_int,
                        status=status,
                        limit=None  # Sem limite para retornar todos
                    )
                    
                    # Formata o histórico para o frontend
                    historico_formatado = []
                    for h in historico:
                        paciente_nome = h.get('paciente_nome', 'Paciente Desconhecido')
                        paciente_quarto = h.get('paciente_quarto', '')
                        paciente_texto = f"{paciente_nome}"
                        if paciente_quarto:
                            paciente_texto += f" - Quarto {paciente_quarto}"
                        
                        historico_formatado.append({
                            'id': h.get('id'),
                            'paciente': paciente_texto,
                            'paciente_id': h.get('paciente_id'),
                            'mensagem': h.get('mensagem', ''),
                            'prioridade': h.get('prioridade', 'normal'),
                            'status': h.get('status', 'pendente'),
                            'timestamp': h.get('data_solicitacao', ''),
                            'data_solicitacao': h.get('data_solicitacao', ''),
                            'data_resolucao': h.get('data_resolucao', ''),
                            'observacoes': h.get('observacoes', '')
                        })
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(historico_formatado, ensure_ascii=False).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({'erro': str(e)}).encode('utf-8'))
            else:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'Database not available')
        else:
            # Para outros arquivos, usa comportamento padrão
            super().do_GET()
    
    def do_POST(self):
        """Responde a requisições POST."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/config_gestos':
            # API: Salva configuração de gesto
            if not self.db:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'Database not available')
                return
            
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                num_dedos = data.get('num_dedos')
                mensagem = data.get('mensagem')
                prioridade = data.get('prioridade', 'normal')
                
                if num_dedos not in [1, 2, 3, 4] or not mensagem:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({'erro': 'Dados inválidos'}).encode('utf-8'))
                    return
                
                if prioridade not in ['baixa', 'normal', 'alta', 'urgente']:
                    prioridade = 'normal'
                
                sucesso = self.db.salvar_config_gesto(num_dedos, mensagem, prioridade)
                
                if sucesso:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'sucesso': True}).encode('utf-8'))
                else:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(json.dumps({'erro': 'Erro ao salvar'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'erro': str(e)}).encode('utf-8'))
        elif parsed_path.path == '/api/pacientes':
            # API: Cria novo paciente
            if not self.db:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'Database not available')
                return
            
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                nome = data.get('nome')
                if not nome:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({'erro': 'Nome é obrigatório'}).encode('utf-8'))
                    return
                
                paciente_id = self.db.criar_paciente(
                    nome=nome,
                    quarto=data.get('quarto'),
                    cpf=data.get('cpf'),
                    telefone=data.get('telefone'),
                    observacoes=data.get('observacoes')
                )
                
                # Busca o paciente criado para retornar
                paciente = self.db.obter_paciente(paciente_id)
                
                if paciente:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'sucesso': True, 'paciente': paciente}, ensure_ascii=False).encode('utf-8'))
                else:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({'erro': 'Erro ao criar paciente'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'erro': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_PUT(self):
        """Responde a requisições PUT para atualizar status de solicitação."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/historico':
            # API: Atualiza status de solicitação no histórico
            if not self.db:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'Database not available')
                return
            
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    put_data = self.rfile.read(content_length)
                    data = json.loads(put_data.decode('utf-8'))
                    
                    solicitacao_id = data.get('id')
                    status = data.get('status')
                    
                    if not solicitacao_id or not status:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json; charset=utf-8')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({'erro': 'ID e status são obrigatórios'}).encode('utf-8'))
                        return
                    
                    observacoes = data.get('observacoes')
                    sucesso = self.db.atualizar_status_solicitacao(solicitacao_id, status, observacoes)
                    
                    if sucesso:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json; charset=utf-8')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({'sucesso': True}).encode('utf-8'))
                    else:
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json; charset=utf-8')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({'erro': 'Erro ao atualizar status'}).encode('utf-8'))
                else:
                    self.send_response(400)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'erro': 'Corpo da requisição vazio'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'erro': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
    
    def do_OPTIONS(self):
        """Responde a requisições OPTIONS (CORS)."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suprime logs do servidor HTTP para não poluir o console."""
        pass  # Remove logs desnecessários


class HTTPServer:
    """Servidor HTTP para servir o painel do enfermeiro."""
    
    def __init__(self, port: int = 8000, html_path: Optional[Path] = None, db=None):
        """
        Inicializa o servidor HTTP.
        
        Args:
            port: Porta do servidor HTTP (padrão: 8000).
            html_path: Caminho para o arquivo HTML. Se None, tenta encontrar automaticamente.
            db: Instância do banco de dados para APIs.
        """
        self.port = port
        self.html_path = html_path or self._encontrar_html()
        self.db = db
        self.server: Optional[socketserver.TCPServer] = None
        self.running = False
        self._thread: Optional[threading.Thread] = None
    
    def _encontrar_html(self) -> Optional[Path]:
        """Tenta encontrar o arquivo cliente_enfermeiro.html."""
        # Tenta no diretório raiz do projeto
        caminhos_possiveis = [
            Path(__file__).parent.parent.parent / 'cliente_enfermeiro.html',
            Path.cwd() / 'cliente_enfermeiro.html',
        ]
        
        for caminho in caminhos_possiveis:
            if caminho.exists():
                return caminho
        
        return None
    
    def _iniciar_servidor(self):
        """Inicia o servidor HTTP em thread separada."""
        try:
            # Cria handler customizado com o caminho do HTML e banco de dados
            def handler_factory(*args, **kwargs):
                return HTTPHandler(*args, html_path=self.html_path, db=self.db, **kwargs)
            
            self.server = socketserver.TCPServer(("", self.port), handler_factory)
            self.server.allow_reuse_address = True
            self.running = True
            
            print(f"🌐 Servidor HTTP iniciado em http://localhost:{self.port}")
            print(f"📱 Painel do enfermeiro disponível em http://localhost:{self.port}")
            
            # Aguarda um pouco antes de abrir o navegador
            time.sleep(0.5)
            
            # Abre o navegador automaticamente
            try:
                webbrowser.open(f'http://localhost:{self.port}')
                print(f"✅ Navegador aberto automaticamente")
            except Exception as e:
                print(f"⚠️ Não foi possível abrir o navegador automaticamente: {e}")
                print(f"   Abra manualmente: http://localhost:{self.port}")
            
            # Inicia o servidor
            self.server.serve_forever()
        except OSError as e:
            if "Address already in use" in str(e) or "address is already in use" in str(e).lower():
                print(f"⚠️ Porta {self.port} já está em uso. Tentando porta alternativa...")
                self.port = self.port + 1
                try:
                    self.server = socketserver.TCPServer(("", self.port), handler_factory)
                    self.server.allow_reuse_address = True
                    self.running = True
                    print(f"🌐 Servidor HTTP iniciado em http://localhost:{self.port}")
                    webbrowser.open(f'http://localhost:{self.port}')
                except Exception as e2:
                    print(f"❌ Erro ao iniciar servidor HTTP na porta alternativa: {e2}")
                    self.running = False
            else:
                print(f"❌ Erro ao iniciar servidor HTTP: {e}")
                self.running = False
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor HTTP: {e}")
            import traceback
            traceback.print_exc()
            self.running = False
    
    def iniciar(self):
        """
        Inicia o servidor HTTP em thread separada.
        Não bloqueia a execução.
        """
        if self.html_path and not self.html_path.exists():
            print(f"⚠️ Arquivo HTML não encontrado: {self.html_path}")
            print("   Servidor HTTP não será iniciado.")
            return
        
        if not self.html_path:
            print("⚠️ Arquivo cliente_enfermeiro.html não encontrado.")
            print("   Servidor HTTP não será iniciado.")
            return
        
        self._thread = threading.Thread(target=self._iniciar_servidor, daemon=True)
        self._thread.start()
        
        # Aguarda um pouco para garantir que o servidor iniciou
        time.sleep(0.3)
    
    def parar(self):
        """Para o servidor HTTP."""
        self.running = False
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
                print("🛑 Servidor HTTP parado.")
            except Exception as e:
                print(f"⚠️ Erro ao parar servidor HTTP: {e}")

