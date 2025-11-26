"""
Janela principal da aplicação.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional, Callable, Tuple
import cv2
import numpy as np
from PIL import Image, ImageTk
from src.config.config import Config
from src.data.gesto_repository import GestoRepository
from src.data.database import Database
from src.data.paciente_repository import PacienteRepository
from src.audio.audio_handler import AudioHandler


class MainWindow:
    """Janela principal da aplicação de reconhecimento de gestos."""
    
    def __init__(self, repositorio: Optional[GestoRepository] = None, db: Optional[Database] = None, 
                 paciente_repo: Optional[PacienteRepository] = None):
        """
        Inicializa a janela principal.
        
        Args:
            repositorio: Repositório de gestos. Se None, cria um novo.
            db: Instância do banco de dados. Se None, cria uma nova.
            paciente_repo: Repositório de pacientes. Se None, cria um novo.
        """
        self.root = tk.Tk()
        self.repositorio = repositorio or GestoRepository()
        self.db = db or Database()
        self.paciente_repo = paciente_repo or PacienteRepository(db=self.db)
        self.audio_handler = AudioHandler()
        self.gesto_atual = ()
        self.gesto_pendente: Optional[Tuple[tuple, str]] = None  # (chave, mensagem) aguardando confirmação
        self.callback_salvar: Optional[Callable] = None
        self.callback_enviar_gesto: Optional[Callable] = None  # Callback para enviar gesto via WebSocket
        self._restauracao_pendente = None  # ID do timer para cancelar restauração pendente
        self.paciente_atual_id: Optional[int] = None  # ID do paciente selecionado
        self.paciente_atual: Optional[dict] = None  # Dados do paciente selecionado
        self._pacientes_dict: dict = {}  # Mapeia índice do combobox para dados do paciente
        self.logo_photo = None  # Referência para a logo (evita garbage collection)
        self.window_icon = None  # Referência para o ícone da janela (evita garbage collection)
        
        self._configurar_janela()
        self._criar_widgets()
        self._atualizar_painel_gestos()
        
        # Agenda atualização periódica das configurações (a cada 5 segundos)
        self._atualizar_configuracoes_periodicamente()
    
    def _configurar_janela(self):
        """Configura propriedades da janela."""
        self.root.title(Config.WINDOW_TITLE)
        self.root.geometry(Config.WINDOW_SIZE)
        self.root.configure(bg='#f0f0f0')
        
        # Configura ícone da janela (logo)
        # Nota: O AppUserModelID é definido no main.py ANTES de criar a janela
        try:
            import platform
            if platform.system() == 'Windows' and Config.ICON_PATH.exists():
                # No Windows, usa arquivo .ico para melhor compatibilidade na barra de tarefas
                self.root.iconbitmap(str(Config.ICON_PATH))
            elif Config.LOGO_PATH.exists():
                # Em outros sistemas, usa PNG via iconphoto
                icon_img = Image.open(Config.LOGO_PATH)
                icon_img = icon_img.resize((32, 32), Image.Resampling.LANCZOS)
                self.window_icon = ImageTk.PhotoImage(icon_img)
                self.root.iconphoto(False, self.window_icon)
        except Exception as e:
            print(f"⚠️ Não foi possível carregar o ícone da janela: {e}")
    
    def _criar_widgets(self):
        """Cria os widgets da interface."""
        # Header com logo e título
        header_frame = tk.Frame(self.root, bg='white', relief=tk.FLAT)
        header_frame.pack(fill="x", pady=0)
        
        # Container interno do header
        header_content = tk.Frame(header_frame, bg='white')
        header_content.pack(fill="x", padx=20, pady=15)
        
        # Logo no header
        try:
            if Config.LOGO_PATH.exists():
                logo_img = Image.open(Config.LOGO_PATH)
                logo_img = logo_img.resize((70, 70), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = tk.Label(
                    header_content,
                    image=self.logo_photo,
                    bg='white'
                )
                logo_label.pack(side="left", padx=(0, 15))
        except Exception as e:
            print(f"⚠️ Não foi possível carregar a logo no header: {e}")
            # Se não conseguir carregar, não adiciona nada
        
        # Título no header
        title_frame = tk.Frame(header_content, bg='white')
        title_frame.pack(side="left", fill="y")
        
        title_label = tk.Label(
            title_frame,
            text="HELP AI - Pacientes",
            font=(Config.FONT_FAMILY, 24, "bold"),
            bg='white',
            fg='#1B4965'
        )
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(
            title_frame,
            text="Sistema de Reconhecimento de Gestos",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL),
            bg='white',
            fg='#666'
        )
        subtitle_label.pack(anchor="w")
        
        # Linha separadora
        separator = tk.Frame(header_frame, bg='#00B4D8', height=3)
        separator.pack(fill="x", pady=0)
        
        # Container principal com duas colunas
        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame superior: Seleção de paciente
        frame_selecao_paciente = tk.Frame(main_container, bg='#e0f7fa', relief=tk.RAISED, bd=2)
        frame_selecao_paciente.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            frame_selecao_paciente,
            text="👤 Paciente:",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL, "bold"),
            bg='#e0f7fa'
        ).pack(side="left", padx=10, pady=8)
        
        self.combo_paciente = ttk.Combobox(
            frame_selecao_paciente,
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL),
            state="readonly",
            width=40
        )
        self.combo_paciente.pack(side="left", padx=5, pady=8)
        self.combo_paciente.bind("<<ComboboxSelected>>", self._on_paciente_selecionado)
        
        # Botão para atualizar lista de pacientes
        btn_atualizar = tk.Button(
            frame_selecao_paciente,
            text="🔄 Atualizar",
            command=self._atualizar_lista_pacientes,
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL - 1),
            bg='#00B4D8',
            fg='white',
            relief=tk.FLAT,
            padx=10
        )
        btn_atualizar.pack(side="left", padx=5, pady=8)
        
        # Label de status do paciente selecionado
        self.label_paciente_status = tk.Label(
            frame_selecao_paciente,
            text="⚠️ Nenhum paciente selecionado",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL - 1),
            bg='#e0f7fa',
            fg='#f44336'
        )
        self.label_paciente_status.pack(side="right", padx=10, pady=8)
        
        # Carrega lista de pacientes
        self._atualizar_lista_pacientes()
        
        # Coluna esquerda: Vídeo e confirmação
        left_frame = tk.Frame(main_container, bg='#f0f0f0')
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        # Título do vídeo
        tk.Label(
            left_frame,
            text="📹 Visualização da Câmera",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_LARGE, "bold"),
            bg='#f0f0f0'
        ).pack(pady=5)
        
        # Canvas para vídeo
        self.canvas_video = tk.Canvas(
            left_frame,
            width=Config.VIDEO_WIDTH,
            height=Config.VIDEO_HEIGHT,
            bg='black',
            highlightthickness=2,
            highlightbackground='#333'
        )
        self.canvas_video.pack(pady=10)
        
        # Label de status da detecção (abaixo do vídeo)
        self.frame_status_deteccao = tk.Frame(left_frame, bg='#e3f2fd', relief=tk.GROOVE, bd=1)
        self.frame_status_deteccao.pack(fill="x", padx=5, pady=(0, 5))
        
        self.label_status_deteccao = tk.Label(
            self.frame_status_deteccao,
            text="👁️ Aguardando detecção...",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL, "bold"),
            bg='#e3f2fd',
            fg='#1565c0',
            pady=8
        )
        self.label_status_deteccao.pack(fill="x")
        
        # Painel de status do gesto detectado
        self.frame_status_gesto = tk.Frame(left_frame, bg='#e8f5e9', relief=tk.RAISED, bd=2)
        self.frame_status_gesto.pack(fill="x", pady=10, padx=5)
        
        self.label_gesto_detectado = tk.Label(
            self.frame_status_gesto,
            text="👋 Faça um gesto para começar\n\n💡 Dica: Abra a mão totalmente (🖐️) para enviar ou feche (✊) para cancelar",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL),
            bg='#e8f5e9',
            wraplength=600,
            justify=tk.CENTER
        )
        self.label_gesto_detectado.pack(pady=10)
        
        # Instruções
        self.label_instrucoes = tk.Label(
            left_frame,
            text="📌 Instruções:\n1. Faça um gesto com a mão\n2. Abra a mão totalmente (🖐️) para enviar\n3. Feche a mão (✊) para cancelar",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL - 1),
            bg='#f0f0f0',
            fg='#666',
            justify=tk.LEFT
        )
        self.label_instrucoes.pack(pady=5)
        
        # Coluna direita: Gestos disponíveis e configurações
        right_frame = tk.Frame(main_container, bg='#f0f0f0')
        right_frame.pack(side="right", fill="both", expand=False, padx=5)
        
        # Título dos gestos disponíveis
        titulo_frame = tk.Frame(right_frame, bg='#f0f0f0')
        titulo_frame.pack(fill="x", pady=5)
        
        tk.Label(
            titulo_frame,
            text="📋 Gestos Configurados",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_LARGE, "bold"),
            bg='#f0f0f0'
        ).pack(side="left")
        
        tk.Label(
            titulo_frame,
            text="🖐️ = Enviar | ✊ = Cancelar",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL - 1),
            bg='#f0f0f0',
            fg='#4caf50'
        ).pack(side="right", padx=5)
        
        # Frame scrollável para gestos
        frame_scroll = tk.Frame(right_frame, bg='#f0f0f0')
        frame_scroll.pack(fill="both", expand=True)
        
        scrollbar_gestos = tk.Scrollbar(frame_scroll)
        scrollbar_gestos.pack(side="right", fill="y")
        
        self.canvas_gestos = tk.Canvas(
            frame_scroll,
            width=300,
            height=400,
            bg='white',
            yscrollcommand=scrollbar_gestos.set
        )
        self.canvas_gestos.pack(side="left", fill="both", expand=True)
        scrollbar_gestos.config(command=self.canvas_gestos.yview)
        
        self.frame_gestos_cards = tk.Frame(self.canvas_gestos, bg='white')
        self.canvas_gestos.create_window((0, 0), window=self.frame_gestos_cards, anchor="nw")
        
        # Nota informativa sobre configuração
        info_frame = tk.Frame(right_frame, bg='#e0f7fa', relief=tk.FLAT, bd=1)
        info_frame.pack(fill="x", pady=10, padx=5)
        
        tk.Label(
            info_frame,
            text="ℹ️ As mensagens são configuradas pelo enfermeiro no portal web.",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL - 1),
            bg='#e0f7fa',
            fg='#1B4965',
            wraplength=280,
            justify=tk.CENTER
        ).pack(pady=8, padx=5)
    
    # Métodos de configuração removidos - agora feitos pelo portal do enfermeiro
    
    def atualizar_status_deteccao(self, estado: str, mensagem: str):
        """
        Atualiza o status de detecção da mão.
        
        Args:
            estado: Estado da detecção ('nenhuma', 'fechada', 'aberta', 'gesto').
            mensagem: Mensagem descritiva do estado.
        """
        try:
            # Cores para cada estado
            cores_estado = {
                'nenhuma': ('#e3f2fd', '#1565c0', '👁️'),  # Azul claro
                'fechada': ('#ffebee', '#c62828', '✊'),    # Vermelho claro
                'aberta': ('#e8f5e9', '#2e7d32', '🖐️'),   # Verde claro
                'gesto': ('#fff3e0', '#e65100', '👆')      # Laranja claro
            }
            
            cor_fundo, cor_texto, emoji = cores_estado.get(estado, cores_estado['nenhuma'])
            
            self.frame_status_deteccao.config(bg=cor_fundo)
            self.label_status_deteccao.config(
                text=f"{emoji} {mensagem}",
                bg=cor_fundo,
                fg=cor_texto
            )
        except Exception as e:
            print(f"Erro ao atualizar status de detecção: {e}")
    
    def atualizar_frame_video(self, frame_bgr):
        """
        Atualiza o frame de vídeo no canvas.
        
        Args:
            frame_bgr: Frame BGR do OpenCV.
        """
        try:
            # Redimensiona frame se necessário
            height, width = frame_bgr.shape[:2]
            if width != Config.VIDEO_WIDTH or height != Config.VIDEO_HEIGHT:
                frame_bgr = cv2.resize(frame_bgr, (Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT))
            
            # Converte BGR para RGB
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            
            # Converte para PIL Image
            image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(image=image)
            
            # Atualiza canvas
            self.canvas_video.create_image(0, 0, anchor=tk.NW, image=photo)
            self.canvas_video.image = photo  # Mantém referência
            
        except Exception as e:
            print(f"Erro ao atualizar frame de vídeo: {e}")
    
    def atualizar_gesto_atual(self, chave: tuple, mensagem: str):
        """
        Atualiza o gesto atual detectado e exibe mensagem.
        
        Args:
            chave: Chave do gesto detectado.
            mensagem: Mensagem associada ao gesto (pode conter instruções de confirmação).
        """
        self.gesto_atual = chave
        
        # Verifica se contém mensagem de confirmação (indicando que está aguardando)
        aguardando_confirmacao = "🖐️ Abra a mão totalmente" in mensagem or "✊ Feche a mão" in mensagem or "🖐️" in mensagem
        
        # Se gesto foi reconhecido (tem mensagem), mostra na tela
        if mensagem and not mensagem.startswith("Gesto não reconhecido") and not mensagem.startswith("⚠️"):
            # Extrai apenas a mensagem principal (remove instruções de confirmação se necessário)
            mensagem_principal = mensagem
            if "✅ Gesto Detectado!" in mensagem:
                # Formatação especial para mensagem de confirmação
                mensagem_principal = mensagem
            elif "\n\n" in mensagem:
                # Separa mensagem principal das instruções
                partes = mensagem.split("\n\n")
                if len(partes) > 0:
                    mensagem_principal = partes[0]
            
            self.gesto_pendente = (chave, mensagem_principal)
            
            # Verifica se é crítico
            is_critico = self.audio_handler.verificar_mensagem_critica(mensagem_principal)
            
            # Cores diferentes para aguardando confirmação
            if aguardando_confirmacao:
                cor_fundo = '#fff3e0'  # Laranja claro para aguardando
                cor_texto = '#e65100'
            elif is_critico:
                cor_fundo = '#ffebee'  # Vermelho claro para crítico
                cor_texto = '#c62828'
            else:
                cor_fundo = '#e8f5e9'  # Verde claro para normal
                cor_texto = '#2e7d32'
            
            emoji = '🔴' if is_critico else '⏳' if aguardando_confirmacao else '✅'
            
            self.frame_status_gesto.config(bg=cor_fundo)
            self.label_gesto_detectado.config(
                text=mensagem,  # Mostra a mensagem completa (incluindo instruções)
                bg=cor_fundo,
                fg=cor_texto,
                font=(Config.FONT_FAMILY, Config.FONT_SIZE_LARGE, "bold")
            )
            
            # Reproduz alerta se crítico
            if is_critico:
                self.audio_handler.reproduzir_alerta()
        else:
            # Gesto não reconhecido
            self.gesto_pendente = None
            self.frame_status_gesto.config(bg='#fff3e0')
            self.label_gesto_detectado.config(
                text=f"⚠️ {mensagem}\n\nTente fazer um gesto válido.",
                bg='#fff3e0',
                fg='#e65100',
                font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL)
            )
        
        # Atualiza destaque no painel de gestos
        self._destacar_gesto(chave)
    
    def mostrar_mensagem_temporaria(self, mensagem: str, tipo: str = "info", duracao_segundos: int = 3):
        """
        Mostra mensagem temporária na interface.
        
        Args:
            mensagem: Mensagem a exibir.
            tipo: Tipo da mensagem ('sucesso', 'erro', 'aviso', 'info').
            duracao_segundos: Duração em segundos para exibir a mensagem (padrão: 3).
        """
        cores = {
            'sucesso': ('#c8e6c9', '#2e7d32'),
            'erro': ('#ffcdd2', '#c62828'),
            'aviso': ('#fff9c4', '#f57f17'),
            'info': ('#e3f2fd', '#1565c0')
        }
        
        cor_fundo, cor_texto = cores.get(tipo, cores['info'])
        
        # Usa fonte maior para mensagens de sucesso (envio)
        tamanho_fonte = Config.FONT_SIZE_LARGE if tipo == 'sucesso' else Config.FONT_SIZE_NORMAL
        
        self.frame_status_gesto.config(bg=cor_fundo)
        self.label_gesto_detectado.config(
            text=mensagem,
            bg=cor_fundo,
            fg=cor_texto,
            font=(Config.FONT_FAMILY, tamanho_fonte, "bold")
        )
        
        # Cancela qualquer restauração pendente (com tratamento de erro seguro)
        if hasattr(self, '_restauracao_pendente') and self._restauracao_pendente is not None:
            try:
                self.root.after_cancel(self._restauracao_pendente)
            except (ValueError, AttributeError, TypeError):
                # Ignora erros se o timer já foi cancelado, não existe ou é inválido
                pass
        
        # Restaura após o tempo especificado (em milissegundos)
        self._restauracao_pendente = self.root.after(duracao_segundos * 1000, self._restaurar_status_padrao)
    
    def _restaurar_status_padrao(self):
        """Restaura o status padrão do painel."""
        self.frame_status_gesto.config(bg='#e8f5e9')
        self.label_gesto_detectado.config(
            text="👋 Faça um gesto para começar\n\n💡 Dica: Após detectar o gesto, abra a mão totalmente (🖐️) para enviar ou feche (✊) para cancelar",
            bg='#e8f5e9',
            fg='black',
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL)
        )
    
    def _destacar_gesto(self, chave: tuple):
        """Destaca o gesto detectado no painel de gestos."""
        # Remove destaque anterior
        for widget in self.frame_gestos_cards.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.config(bg='white', relief=tk.RAISED, bd=2, highlightthickness=0)
        
        # Conta quantos dedos estão estendidos
        num_dedos = len(chave) if chave else 0
        
        # Encontra o card correspondente e destaca (por número de dedos ou chave antiga)
        for widget in self.frame_gestos_cards.winfo_children():
            if isinstance(widget, tk.Frame):
                # Nova lógica: destaca por número de dedos
                if hasattr(widget, 'gesto_num_dedos') and widget.gesto_num_dedos == num_dedos:
                    widget.config(bg='#e0f7fa', relief=tk.RAISED, bd=4)
                    # Adiciona animação visual
                    widget.config(highlightbackground='#00B4D8', highlightthickness=2)
                    break
                # Fallback: lógica antiga por chave
                elif hasattr(widget, 'gesto_chave') and widget.gesto_chave == chave:
                    widget.config(bg='#e0f7fa', relief=tk.RAISED, bd=3)
                    break
    
    
    def _atualizar_painel_gestos(self):
        """Atualiza o painel visual de gestos disponíveis com configurações do enfermeiro."""
        # Limpa cards existentes
        for widget in self.frame_gestos_cards.winfo_children():
            widget.destroy()
        
        # Busca configurações simplificadas do banco (1, 2, 3, 4 dedos)
        configs_gestos = self.db.listar_config_gestos()
        configs_ativas = {c['num_dedos']: c['mensagem'] for c in configs_gestos if c.get('ativo', 1)}
        
        # Ícones para cada número de dedos
        icones_dedos = {
            1: "👆",
            2: "✌️",
            3: "🤟",
            4: "🖐️"
        }
        
        # Cores e ícones de prioridade
        cores_prioridade = {
            'baixa': ('#4caf50', '🟢', 'Baixa'),
            'normal': ('#ffc107', '🟡', 'Normal'),
            'alta': ('#ff9800', '🟠', 'Alta'),
            'urgente': ('#f44336', '🔴', 'Urgente')
        }
        
        if not configs_ativas:
            # Se não houver configurações, mostra mensagem
            tk.Label(
                self.frame_gestos_cards,
                text="⏳ Aguardando configuração...\n\nO enfermeiro ainda não configurou os gestos.\nAs mensagens aparecerão aqui quando configuradas.",
                font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL),
                bg='white',
                fg='gray',
                justify=tk.CENTER,
                wraplength=280
            ).pack(pady=20)
        else:
            # Exibe as configurações em ordem (1, 2, 3, 4)
            for num_dedos in sorted([d for d in configs_ativas.keys() if d in [1, 2, 3, 4]]):
                config = next((c for c in configs_gestos if c['num_dedos'] == num_dedos), None)
                mensagem = configs_ativas[num_dedos]
                prioridade = config.get('prioridade', 'normal') if config else 'normal'
                icone = icones_dedos.get(num_dedos, "👋")
                
                # Obtém cor e ícone da prioridade
                cor_prioridade, icone_prioridade, texto_prioridade = cores_prioridade.get(
                    prioridade, cores_prioridade['normal']
                )
                
                card = tk.Frame(
                    self.frame_gestos_cards,
                    bg='white',
                    relief=tk.RAISED,
                    bd=2,
                    padx=15,
                    pady=15
                )
                card.pack(fill="x", padx=5, pady=8)
                card.gesto_num_dedos = num_dedos  # Armazena número de dedos para destacar depois
                
                # Cabeçalho do card com ícone e número de dedos
                header_frame = tk.Frame(card, bg='white')
                header_frame.pack(fill="x", pady=(0, 8))
                
                tk.Label(
                    header_frame,
                    text=f"{icone} {num_dedos} Dedo{'s' if num_dedos > 1 else ''}",
                    font=(Config.FONT_FAMILY, Config.FONT_SIZE_LARGE, "bold"),
                    bg='white',
                    fg='#00B4D8'
                ).pack(side="left")
                
                tk.Label(
                    header_frame,
                    text=f"Solicitação {chr(64 + num_dedos)}",
                    font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL - 1),
                    bg='white',
                    fg='#666',
                    padx=10
                ).pack(side="left")
                
                # Badge de prioridade
                prioridade_frame = tk.Frame(card, bg=cor_prioridade, relief=tk.FLAT, bd=0)
                prioridade_frame.pack(anchor="e", pady=(0, 5))
                
                tk.Label(
                    prioridade_frame,
                    text=f"{icone_prioridade} {texto_prioridade}",
                    font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL - 2, "bold"),
                    bg=cor_prioridade,
                    fg='white',
                    padx=8,
                    pady=2
                ).pack()
                
                # Mensagem configurada
                tk.Label(
                    card,
                    text=f"💬 {mensagem}",
                    font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL),
                    bg='white',
                    wraplength=280,
                    justify=tk.LEFT,
                    fg='#333'
                ).pack(anchor="w", pady=(5, 10))
                
                # Instrução de envio
                instrucao_frame = tk.Frame(card, bg='#e8f5e9', relief=tk.FLAT, bd=1)
                instrucao_frame.pack(fill="x", pady=5)
                
                tk.Label(
                    instrucao_frame,
                    text="🖐️ Abra a mão totalmente para enviar  |  ✊ Feche para cancelar",
                    font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL - 2, "italic"),
                    bg='#e8f5e9',
                    fg='#2e7d32',
                    padx=5,
                    pady=3
                ).pack()
        
        # Atualiza scroll
        self.frame_gestos_cards.update_idletasks()
        self.canvas_gestos.config(scrollregion=self.canvas_gestos.bbox("all"))
    
    def _atualizar_configuracoes_periodicamente(self):
        """Atualiza as configurações de gestos periodicamente."""
        self._atualizar_painel_gestos()
        # Agenda próxima atualização em 5 segundos
        self.root.after(5000, self._atualizar_configuracoes_periodicamente)
    
    def _atualizar_lista_pacientes(self):
        """Atualiza a lista de pacientes no combobox."""
        try:
            # Lista todos os pacientes ativos (padrão) ou todos se não houver ativos
            pacientes = self.paciente_repo.listar_pacientes(apenas_ativos=True)
            
            # Se não houver pacientes ativos, tenta listar todos
            if not pacientes:
                pacientes = self.paciente_repo.listar_pacientes(apenas_ativos=False)
                print(f"⚠️ Nenhum paciente ativo encontrado. Listando todos os pacientes: {len(pacientes)} encontrado(s)")
            valores = []
            self._pacientes_dict = {}  # Mapeia índice do combobox para dados do paciente
            
            for idx, paciente in enumerate(pacientes):
                nome_display = f"{paciente['nome']} - Quarto {paciente['quarto'] or 'N/A'}"
                valores.append(nome_display)
                self._pacientes_dict[idx] = paciente
            
            self.combo_paciente['values'] = valores
            
            # Se não houver paciente selecionado e houver pacientes disponíveis, seleciona o primeiro
            if not self.paciente_atual_id and valores:
                self.combo_paciente.current(0)
                self._on_paciente_selecionado()
            elif not valores:
                self.combo_paciente.set("")
                self.label_paciente_status.config(
                    text="⚠️ Nenhum paciente cadastrado",
                    fg='#f44336'
                )
        except Exception as e:
            print(f"Erro ao atualizar lista de pacientes: {e}")
            self.label_paciente_status.config(
                text="❌ Erro ao carregar pacientes",
                fg='#f44336'
            )
    
    def _on_paciente_selecionado(self, event=None):
        """Callback quando um paciente é selecionado."""
        try:
            indice = self.combo_paciente.current()
            if indice >= 0 and indice in self._pacientes_dict:
                paciente = self._pacientes_dict[indice]
                self.paciente_atual_id = paciente['id']
                self.paciente_atual = paciente
                
                nome_display = f"{paciente['nome']} - Quarto {paciente['quarto'] or 'N/A'}"
                self.label_paciente_status.config(
                    text=f"✅ {nome_display}",
                    fg='#00B4D8'
                )
                print(f"✅ Paciente selecionado: {nome_display} (ID: {self.paciente_atual_id})")
            else:
                self.paciente_atual_id = None
                self.paciente_atual = None
                self.label_paciente_status.config(
                    text="⚠️ Nenhum paciente selecionado",
                    fg='#f44336'
                )
        except Exception as e:
            print(f"Erro ao selecionar paciente: {e}")
            self.paciente_atual_id = None
            self.paciente_atual = None
    
    def _obter_descricao_dedos(self, chave: tuple) -> str:
        """
        Retorna descrição legível dos dedos estendidos.
        
        Args:
            chave: Tupla com índices dos dedos.
            
        Returns:
            Descrição em texto.
        """
        nomes_dedos = {
            4: "Polegar",
            8: "Indicador",
            12: "Médio",
            16: "Anelar",
            20: "Mindinho"
        }
        
        descricoes = []
        for dedo in sorted(chave):
            if dedo in nomes_dedos:
                descricoes.append(nomes_dedos[dedo])
        
        if descricoes:
            return ", ".join(descricoes)
        return ""
    
    def verificar_e_reproduzir_alerta(self, mensagem: str):
        """
        Verifica se a mensagem é crítica e reproduz alerta se necessário.
        
        Args:
            mensagem: Mensagem a verificar.
        """
        if self.audio_handler.verificar_mensagem_critica(mensagem):
            self.audio_handler.reproduzir_alerta()
    
    def executar(self):
        """Inicia o loop principal da interface."""
        self.root.mainloop()
    
    def fechar(self):
        """Fecha a janela."""
        self.root.quit()
        self.root.destroy()

