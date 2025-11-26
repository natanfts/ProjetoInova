"""
ProjetoInova - Sistema de Reconhecimento de Gestos
Ponto de entrada principal da aplicação.
"""

import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent))

from src.ui.main_window import MainWindow
from src.video.video_processor import VideoProcessor
from src.data.gesto_repository import GestoRepository
from src.data.paciente_repository import PacienteRepository
from src.data.database import Database
from src.audio.audio_handler import AudioHandler
from src.websocket.websocket_server import WebSocketServer
from src.http.http_server import HTTPServer
from src.config.config import Config


def main():
    """Função principal da aplicação."""
    websocket_server = None
    ultimo_gesto_enviado = None
    ultimo_tempo_envio = 0
    
    # No Windows, define AppUserModelID ANTES de criar qualquer janela
    # Isso faz o ícone personalizado aparecer na barra de tarefas
    try:
        import platform
        if platform.system() == 'Windows':
            import ctypes
            app_id = 'HelpAI.Pacientes.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception as e:
        print(f"⚠️ Não foi possível definir AppUserModelID: {e}")
    
    try:
        # Inicializa banco de dados
        db = Database()
        
        # Inicializa componentes
        repositorio = GestoRepository(db=db)
        paciente_repo = PacienteRepository(db=db)
        audio_handler = AudioHandler()
        janela = MainWindow(repositorio=repositorio, db=db, paciente_repo=paciente_repo)
        
        # Obtém ou cria paciente padrão
        paciente_id = None
        paciente = None
        if Config.PACIENTE_ID and Config.PACIENTE_ID.startswith("PAC"):
            # Tenta obter paciente existente ou cria novo
            try:
                # Busca por nome e quarto
                pacientes = paciente_repo.listar_pacientes()
                for p in pacientes:
                    if p['nome'] == Config.PACIENTE_NOME and p['quarto'] == Config.PACIENTE_QUARTO:
                        paciente = p
                        paciente_id = p['id']
                        break
                
                if not paciente:
                    # Cria novo paciente
                    paciente_id = paciente_repo.criar_paciente(
                        nome=Config.PACIENTE_NOME,
                        quarto=Config.PACIENTE_QUARTO
                    )
                    paciente = paciente_repo.obter_paciente(paciente_id)
                    print(f"✅ Paciente cadastrado: {Config.PACIENTE_NOME} (ID: {paciente_id})")
                else:
                    print(f"✅ Paciente encontrado: {paciente['nome']} (ID: {paciente_id})")
            except Exception as e:
                print(f"⚠️ Erro ao obter/criar paciente: {e}")
                print("   Aplicação continuará sem associar gestos a pacientes.")
        
        # Inicializa servidor WebSocket se habilitado
        websocket_server = None
        if Config.WEBSOCKET_ENABLED:
            try:
                websocket_server = WebSocketServer(
                    host=Config.WEBSOCKET_HOST,
                    port=Config.WEBSOCKET_PORT
                )
                thread_websocket = threading.Thread(
                    target=websocket_server.iniciar,
                    daemon=True
                )
                thread_websocket.start()
                # Aguarda um pouco para o servidor iniciar
                time.sleep(0.5)
                print(f"✅ WebSocket habilitado. Enfermeiros podem conectar em ws://{Config.WEBSOCKET_HOST}:{Config.WEBSOCKET_PORT}")
            except Exception as e:
                print(f"⚠️ Erro ao iniciar WebSocket: {e}")
                import traceback
                traceback.print_exc()
                print("   Aplicação continuará sem WebSocket.")
                websocket_server = None
        
        # Inicializa servidor HTTP para painel do enfermeiro
        http_server = None
        if Config.HTTP_ENABLED:
            try:
                http_server = HTTPServer(
                    port=Config.HTTP_PORT,
                    html_path=Config.HTML_PATH,
                    db=db
                )
                http_server.iniciar()
            except Exception as e:
                print(f"⚠️ Erro ao iniciar servidor HTTP: {e}")
                import traceback
                traceback.print_exc()
                print("   Aplicação continuará sem servidor HTTP.")
                http_server = None
        
        # Callback para frames de vídeo (atualiza interface)
        def on_frame_processado(frame_bgr):
            """Callback chamado para cada frame processado."""
            janela.atualizar_frame_video(frame_bgr)
        
        # Callback para estado da mão (atualiza label de status)
        def on_estado_mao(estado, mensagem):
            """Callback chamado para atualizar o estado de detecção da mão."""
            try:
                # Usa after para garantir atualização thread-safe na UI
                janela.root.after(0, lambda: janela.atualizar_status_deteccao(estado, mensagem))
            except Exception as e:
                pass  # Ignora erros durante fechamento da janela
        
        # Variáveis para controle de gestos e estado
        ultimo_gesto_valido = None  # Último gesto válido armazenado para envio
        aguardando_confirmacao = False  # Estado de espera por confirmação ou cancelamento
        ultimo_tempo_envio_completo = 0  # Timestamp do último envio completo (para cooldown)
        COOLDOWN_APOS_ENVIO_SEGUNDOS = 4.0  # Período de cooldown após envio (evita múltiplos envios e detecção do mesmo gesto)
        ultimo_gesto_enviado_para_cooldown = None  # Último gesto enviado (para ignorar o mesmo gesto por mais tempo)
        
        # Sistema de "hold" (manter gesto) - requer que o gesto seja mantido por alguns segundos
        gesto_em_hold = None  # Gesto atual sendo segurado
        tempo_inicio_hold = 0  # Timestamp de quando começou a segurar o gesto
        TEMPO_MINIMO_HOLD_SEGUNDOS = 1.5  # Tempo mínimo que o gesto deve ser mantido para ser considerado válido
        
        # Callback para quando um gesto é detectado
        def on_gesto_detectado(chave, dedos_estendidos, indice_mao):
            nonlocal ultimo_gesto_valido, aguardando_confirmacao, ultimo_tempo_envio_completo, ultimo_gesto_enviado_para_cooldown
            nonlocal gesto_em_hold, tempo_inicio_hold
            
            # CRÍTICO: Cooldown após envio - ignora TODOS os gestos por alguns segundos após enviar
            # Isso evita que o mesmo gesto seja detectado novamente quando a mão ainda está levantada
            tempo_atual_cooldown = time.time()
            tempo_desde_ultimo_envio = tempo_atual_cooldown - ultimo_tempo_envio_completo
            
            if tempo_desde_ultimo_envio < COOLDOWN_APOS_ENVIO_SEGUNDOS:
                # Ainda está em período de cooldown - ignora completamente qualquer gesto
                return
            
            # CRÍTICO: Se for o mesmo gesto que foi enviado recentemente, ignora por mais tempo
            # Isso evita que manter a mão na mesma posição após enviar seja detectado como novo gesto
            if ultimo_gesto_enviado_para_cooldown == chave and tempo_desde_ultimo_envio < COOLDOWN_APOS_ENVIO_SEGUNDOS * 2:
                # É o mesmo gesto enviado - ignora por período maior
                return
            
            # CRÍTICO: Ignora gestos vazios (mão fechada) - usado APENAS para cancelamento
            # Mão fechada nunca deve ser tratada como gesto válido
            if not chave or len(chave) == 0:
                return
            
            # Valida que todos os índices são válidos (4, 8, 12, 16, 20)
            # Ignora gestos com índices inválidos (como 0)
            indices_validos = {4, 8, 12, 16, 20}
            if not all(d in indices_validos for d in chave):
                return  # Ignora gestos com índices inválidos
            
            # CRÍTICO: Ignora mão totalmente aberta (4, 8, 12, 16, 20) - usada APENAS para confirmação/envio
            # Mão totalmente aberta nunca deve ser tratada como gesto válido
            if chave == (4, 8, 12, 16, 20):
                return
            
            # CRÍTICO: Valida que o gesto tem 1-4 dedos (compatível com configurações)
            num_dedos = len(chave)
            if num_dedos not in [1, 2, 3, 4]:
                # Ignora gestos com 0 ou 5+ dedos (mão fechada ou totalmente aberta)
                return
            
            # CRÍTICO: Valida ANTES de processar se o padrão de dedos está correto
            # Padrões válidos:
            # 1 dedo: apenas (8) - indicador
            # 2 dedos: apenas (8, 12) - indicador + médio
            # 3 dedos: apenas (8, 12, 16) - indicador + médio + anelar
            # 4 dedos: apenas (8, 12, 16, 20) - indicador + médio + anelar + mínimo
            padroes_validos = {
                1: (8,),
                2: (8, 12),
                3: (8, 12, 16),
                4: (8, 12, 16, 20)
            }
            
            # Ordena a chave para comparação
            chave_ordenada = tuple(sorted(chave))
            padrao_esperado = padroes_validos.get(num_dedos)
            
            if padrao_esperado is None or chave_ordenada != padrao_esperado:
                # Gesto não corresponde ao padrão esperado - ignora silenciosamente
                # (ex: (4, 8) não é válido, apenas (8, 12) é válido para 2 dedos)
                # Reseta hold se estava segurando um gesto
                gesto_em_hold = None
                tempo_inicio_hold = 0
                return
            
            # Se já estiver aguardando confirmação, ignora novos gestos
            if aguardando_confirmacao:
                return
            
            # Obtém mensagem - a validação do padrão de dedos já foi feita acima
            mensagem = repositorio.obter_mensagem(chave)
            
            if not mensagem:
                # Se não encontrou mensagem mesmo com padrão válido, pode não estar configurada
                print(f"⚠️ Gesto válido {chave} ({num_dedos} dedo(s)) detectado, mas sem mensagem configurada. Configure no painel do enfermeiro.")
                # Ignora silenciosamente (usuário pode configurar a mensagem depois)
                # Reseta hold também
                gesto_em_hold = None
                tempo_inicio_hold = 0
                return
            
            # SISTEMA DE HOLD: Requer que o gesto seja mantido por alguns segundos antes de entrar em confirmação
            tempo_atual_hold = time.time()
            
            # Se é o mesmo gesto que está sendo segurado, verifica se já passou o tempo mínimo
            if gesto_em_hold == chave:
                tempo_decorrido_hold = tempo_atual_hold - tempo_inicio_hold
                
                if tempo_decorrido_hold >= TEMPO_MINIMO_HOLD_SEGUNDOS:
                    # Gesto foi mantido por tempo suficiente - entra em modo de confirmação
                    # Armazena gesto válido
                    ultimo_gesto_valido = (chave, dedos_estendidos, indice_mao)
                    
                    # Ativa estado de aguardando confirmação
                    aguardando_confirmacao = True
                    processador_video.aguardando_confirmacao = True
                    
                    # Reseta hold
                    gesto_em_hold = None
                    tempo_inicio_hold = 0
                    
                    # Mostra gesto detectado e solicita confirmação
                    mensagem_exibida = f"✅ Gesto Detectado!\n\n{mensagem}\n\n🖐️ Abra a mão totalmente para enviar\n✊ Feche a mão para cancelar"
                    janela.atualizar_gesto_atual(chave, mensagem_exibida)
                    
                    print(f"📝 Gesto detectado: {chave} = {mensagem}")
                    print("⏳ Aguardando confirmação... (🖐️ mão aberta para enviar ou ✊ mão fechada para cancelar)")
                else:
                    # Ainda está segurando o gesto, mas não passou tempo suficiente
                    # Não faz nada, apenas continua segurando
                    tempo_restante = TEMPO_MINIMO_HOLD_SEGUNDOS - tempo_decorrido_hold
                    # Não loga para não poluir o console, mas pode exibir na UI se necessário
                    pass
            else:
                # É um gesto diferente ou novo gesto - inicia novo hold
                gesto_em_hold = chave
                tempo_inicio_hold = tempo_atual_hold
                print(f"⏳ Segurando gesto {chave}... ({TEMPO_MINIMO_HOLD_SEGUNDOS}s necessário)")
        
        # Variáveis para controle de envio
        ultimo_gesto_enviado = None
        ultimo_tempo_envio = 0
        
        # Função auxiliar para restaurar estado padrão após enviar/cancelar
        def restaurar_estado_padrao():
            """Restaura o estado padrão da interface após enviar ou cancelar."""
            nonlocal aguardando_confirmacao, gesto_em_hold, tempo_inicio_hold
            aguardando_confirmacao = False
            processador_video.aguardando_confirmacao = False
            # Reseta hold também
            gesto_em_hold = None
            tempo_inicio_hold = 0
            # O método _restaurar_status_padrao será chamado automaticamente após a mensagem temporária
        
        # Callback para mão fechada (cancelamento)
        def on_mao_fechada_detectada():
            """Cancela o envio e volta a detectar novos gestos."""
            nonlocal aguardando_confirmacao, ultimo_gesto_valido, gesto_em_hold, tempo_inicio_hold
            
            if aguardando_confirmacao:
                # Cancela e volta ao estado inicial
                aguardando_confirmacao = False
                processador_video.aguardando_confirmacao = False
                ultimo_gesto_valido = None
                
                # Reseta hold também
                gesto_em_hold = None
                tempo_inicio_hold = 0
                
                # Mostra feedback de cancelamento
                janela.mostrar_mensagem_temporaria("❌ Envio cancelado\n\nVocê pode fazer um novo gesto.", "aviso", duracao_segundos=3)
                print("❌ Envio cancelado. Aguardando novo gesto...")
                
                # Restaura estado padrão após exibir mensagem
                janela.root.after(3500, restaurar_estado_padrao)
            elif gesto_em_hold is not None:
                # Não está aguardando confirmação, mas está segurando um gesto - cancela o hold
                print(f"✊ Mão fechada detectada! Cancelando hold do gesto {gesto_em_hold}...")
                gesto_em_hold = None
                tempo_inicio_hold = 0
        
        # Callback para mão totalmente aberta (confirmação/envio)
        def on_mao_aberta_detectada(gesto_info):
            """Envia o gesto quando mão totalmente aberta é detectada durante aguardando confirmação."""
            nonlocal ultimo_gesto_enviado, ultimo_tempo_envio, ultimo_gesto_valido, aguardando_confirmacao, ultimo_tempo_envio_completo, ultimo_gesto_enviado_para_cooldown
            
            # CRÍTICO: Cooldown após envio - ignora mão totalmente aberta por alguns segundos após enviar
            tempo_atual_cooldown = time.time()
            if tempo_atual_cooldown - ultimo_tempo_envio_completo < COOLDOWN_APOS_ENVIO_SEGUNDOS:
                # Ainda está em período de cooldown - ignora
                return
            
            # Só processa se estiver aguardando confirmação
            if not aguardando_confirmacao:
                return
            
            if not ultimo_gesto_valido:
                print("⚠️ Mão totalmente aberta detectada, mas nenhum gesto válido foi armazenado.")
                return
            
            chave, dedos_estendidos, indice_mao = ultimo_gesto_valido
            mensagem = repositorio.obter_mensagem(chave)
            
            if not mensagem:
                print(f"⚠️ Erro: gesto {chave} não tem mensagem associada.")
                return
            
            # Debounce: evita envios múltiplos do mesmo gesto
            tempo_atual = time.time()
            if (ultimo_gesto_enviado == chave and 
                tempo_atual - ultimo_tempo_envio < Config.DEBOUNCE_TEMPO_SEGUNDOS):
                return
            
            # Envia via WebSocket e salva no histórico
            if websocket_server and websocket_server.running:
                prioridade = "alta" if audio_handler.verificar_mensagem_critica(mensagem) else "normal"
                
                # Obtém prioridade da configuração do gesto (se disponível)
                try:
                    config_gesto = db.obter_config_gesto(len(chave))
                    if config_gesto and config_gesto.get('prioridade'):
                        prioridade_config = config_gesto['prioridade']
                        # Mapeia prioridades: baixa/normal -> normal, alta/urgente -> alta
                        if prioridade_config in ['alta', 'urgente']:
                            prioridade = 'alta'
                        elif prioridade_config == 'baixa':
                            prioridade = 'normal'  # Mantém compatibilidade com sistema antigo
                except Exception as e:
                    print(f"⚠️ Erro ao obter prioridade da configuração: {e}")
                
                # Obtém paciente selecionado na interface ou usa fallback
                paciente_id_para_envio = janela.paciente_atual_id if janela.paciente_atual_id else paciente_id
                paciente_para_envio = janela.paciente_atual if janela.paciente_atual else paciente
                
                # Salva no histórico do banco de dados
                if paciente_id_para_envio:
                    try:
                        solicitacao_id = db.criar_solicitacao(
                            paciente_id=paciente_id_para_envio,
                            dedos=chave,
                            mensagem=mensagem,
                            prioridade=prioridade
                        )
                        print(f"📝 Solicitação salva no histórico (ID: {solicitacao_id})")
                    except Exception as e:
                        print(f"⚠️ Erro ao salvar solicitação no histórico: {e}")
                
                # Envia via WebSocket
                if paciente_para_envio:
                    nome_paciente = paciente_para_envio.get('nome', Config.PACIENTE_NOME)
                    quarto_paciente = paciente_para_envio.get('quarto', Config.PACIENTE_QUARTO)
                elif paciente:
                    nome_paciente = paciente.get('nome', Config.PACIENTE_NOME)
                    quarto_paciente = paciente.get('quarto', Config.PACIENTE_QUARTO)
                else:
                    nome_paciente = Config.PACIENTE_NOME
                    quarto_paciente = Config.PACIENTE_QUARTO
                
                # Obtém data completa da solicitação para sincronização
                timestamp_completo = datetime.now().isoformat()
                
                websocket_server.broadcast({
                    "tipo": "gesto",
                    "solicitacao_id": solicitacao_id if 'solicitacao_id' in locals() else None,
                    "paciente_id": paciente_id_para_envio,
                    "paciente": f"{nome_paciente} - Quarto {quarto_paciente}",
                    "mensagem": mensagem,
                    "prioridade": prioridade,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "timestamp_iso": timestamp_completo,  # Timestamp completo para sincronização
                    "dedos": list(chave)
                })
                
                # Atualiza controle de debounce
                ultimo_gesto_enviado = chave
                ultimo_tempo_envio = tempo_atual
                
                # Desativa estado de aguardando confirmação
                aguardando_confirmacao = False
                processador_video.aguardando_confirmacao = False
                ultimo_gesto_valido = None
                
                # CRÍTICO: Ativa cooldown após envio para evitar múltiplos envios acidentais
                ultimo_tempo_envio_completo = time.time()
                ultimo_gesto_enviado_para_cooldown = chave  # Armazena o gesto enviado para cooldown estendido
                
                # CRÍTICO: Reseta timestamp de mão aberta no processador para forçar novo período de debounce
                processador_video.ultimo_tempo_mao_aberta = 0
                
                # Feedback visual de sucesso
                emoji_prioridade = "🔴" if prioridade == "alta" else "✅"
                mensagem_feedback = f"{emoji_prioridade} MENSAGEM ENVIADA COM SUCESSO!\n\n{mensagem}\n\n👍 O enfermeiro foi notificado"
                janela.mostrar_mensagem_temporaria(mensagem_feedback, "sucesso", duracao_segundos=5)
                
                # Restaura estado padrão após exibir mensagem
                janela.root.after(5500, restaurar_estado_padrao)
                
                print(f"📤 Gesto enviado: {mensagem} (Prioridade: {prioridade})")
                print("✅ Estado resetado. Aguardando novo gesto...")
                print(f"⏳ Cooldown ativado por {COOLDOWN_APOS_ENVIO_SEGUNDOS}s (gestos ignorados) e {COOLDOWN_APOS_ENVIO_SEGUNDOS * 2}s para o mesmo gesto")
            else:
                janela.mostrar_mensagem_temporaria("⚠️ WebSocket não conectado. Verifique a conexão.", "erro", duracao_segundos=3)
                print("⚠️ WebSocket não está rodando. Não foi possível enviar.")
        
        # Inicializa processador de vídeo
        processador_video = VideoProcessor(
            callback_gesto=on_gesto_detectado,
            callback_frame=on_frame_processado,
            callback_mao_aberta=on_mao_aberta_detectada,
            callback_mao_fechada=on_mao_fechada_detectada,
            callback_estado_mao=on_estado_mao
        )
        processador_video.iniciar()
        
        # Executa interface gráfica
        janela.executar()
        
        # Limpa recursos ao fechar
        processador_video.parar()
        if websocket_server:
            websocket_server.parar()
        if http_server:
            http_server.parar()
        
    except KeyboardInterrupt:
        print("\nAplicação interrompida pelo usuário.")
    except Exception as e:
        print(f"Erro ao executar aplicação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
