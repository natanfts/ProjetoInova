"""
Configurações da aplicação.
"""

import os
from pathlib import Path


class Config:
    """Gerencia as configurações da aplicação."""
    
    # Diretórios
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR
    
    # Arquivos
    CSV_PATH = DATA_DIR / 'dados.csv'  # Mantido para compatibilidade/migração
    DB_PATH = DATA_DIR / 'banco_dados.db'  # Banco de dados SQLite
    EXPORT_PATH = DATA_DIR / 'gestos_exportados.txt'
    ALERT_SOUND_PATH = DATA_DIR / 'alerta.mp3'
    LOGO_PATH = DATA_DIR / 'assets' / 'logo.png'  # Logo da aplicação
    ICON_PATH = DATA_DIR / 'assets' / 'logo.ico'  # Ícone da aplicação (Windows)
    
    # Configurações de vídeo
    CAMERA_INDEX = 0
    
    # Configurações de reconhecimento de voz
    LANGUAGE = 'pt-BR'
    
    # Configurações da interface
    WINDOW_TITLE = "HELP AI - Pacientes"
    WINDOW_SIZE = "1000x700"
    FONT_FAMILY = "Arial"
    FONT_SIZE_NORMAL = 12
    FONT_SIZE_LARGE = 14
    FONT_SIZE_XLARGE = 16
    
    # Configurações de vídeo na interface
    VIDEO_WIDTH = 640
    VIDEO_HEIGHT = 480
    VIDEO_FPS = 30
    
    # Mostrar janela OpenCV separada (False = apenas na interface Tkinter)
    SHOW_OPENCV_WINDOW = False
    
    # Palavras-chave para alertas críticos
    CRITICAL_KEYWORDS = ['emergência', 'pânico', 'urgente']
    
    # Configurações WebSocket
    # Permite sobrescrever via variáveis de ambiente
    import platform
    # No Windows, usa localhost por padrão; no Linux pode usar 0.0.0.0
    _default_host = '0.0.0.0' if platform.system() != 'Windows' else 'localhost'
    WEBSOCKET_ENABLED = os.getenv('WEBSOCKET_ENABLED', 'True').lower() in ('true', '1', 'yes')
    WEBSOCKET_HOST = os.getenv('WEBSOCKET_HOST', _default_host)
    WEBSOCKET_PORT = int(os.getenv('WEBSOCKET_PORT', '8765'))
    
    # Configurações Servidor HTTP (para painel do enfermeiro)
    HTTP_ENABLED = os.getenv('HTTP_ENABLED', 'True').lower() in ('true', '1', 'yes')
    HTTP_PORT = int(os.getenv('HTTP_PORT', '8000'))
    HTML_PATH = DATA_DIR / 'cliente_enfermeiro.html'
    
    # Informações do paciente (configurar conforme necessário)
    PACIENTE_ID = "PAC001"
    PACIENTE_NOME = "João Silva"
    PACIENTE_QUARTO = "201"
    
    # Gesto de confirmação/envio (joia = polegar + indicador formando círculo)
    # Representado como (4, 8) - polegar e indicador
    GESTO_JOIA_CONFIRMACAO = (4, 8)
    
    # Debounce para evitar envios múltiplos do mesmo gesto
    DEBOUNCE_TEMPO_SEGUNDOS = 2  # Aguarda 2 segundos antes de aceitar o mesmo gesto novamente
    
    @classmethod
    def ensure_data_file_exists(cls):
        """Garante que o arquivo CSV existe."""
        if not cls.CSV_PATH.exists():
            cls.CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(cls.CSV_PATH, 'w', encoding='utf-8') as f:
                f.write('dedos,mensagem\n')

