"""
Gerenciador de funcionalidades de áudio.
"""

import threading
from typing import Optional
import speech_recognition as sr
import pygame
from pathlib import Path
from src.config.config import Config


class AudioHandler:
    """Gerencia reconhecimento de voz e alertas sonoros."""
    
    def __init__(self, language: str = None, alert_sound_path: Optional[Path] = None):
        """
        Inicializa o gerenciador de áudio.
        
        Args:
            language: Idioma para reconhecimento de voz (padrão: pt-BR).
            alert_sound_path: Caminho para arquivo de alerta sonoro.
        """
        self.language = language or Config.LANGUAGE
        self.alert_sound_path = alert_sound_path or Config.ALERT_SOUND_PATH
        self.recognizer = sr.Recognizer()
        # Inicializa pygame mixer para reprodução de áudio
        try:
            pygame.mixer.init()
        except:
            pass  # Se falhar, continua sem áudio
    
    def reconhecer_voz(self) -> Optional[str]:
        """
        Reconhece fala do microfone.
        
        Returns:
            Texto reconhecido ou None em caso de erro.
        """
        try:
            with sr.Microphone() as source:
                # Ajusta para ruído ambiente
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            texto = self.recognizer.recognize_google(audio, language=self.language)
            return texto
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"Erro ao acessar serviço de reconhecimento: {e}")
            return None
        except Exception as e:
            print(f"Erro inesperado no reconhecimento de voz: {e}")
            return None
    
    def reproduzir_alerta(self):
        """
        Reproduz um alerta sonoro em thread separada.
        """
        if self.alert_sound_path.exists():
            def _reproduzir():
                try:
                    pygame.mixer.music.load(str(self.alert_sound_path))
                    pygame.mixer.music.play()
                    # Aguarda até terminar a reprodução
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                except Exception as e:
                    print(f"Erro ao reproduzir alerta: {e}")
            
            threading.Thread(target=_reproduzir, daemon=True).start()
    
    def verificar_mensagem_critica(self, mensagem: str) -> bool:
        """
        Verifica se uma mensagem contém palavras-chave críticas.
        
        Args:
            mensagem: Mensagem a verificar.
            
        Returns:
            True se a mensagem é crítica, False caso contrário.
        """
        mensagem_lower = mensagem.lower()
        return any(keyword in mensagem_lower for keyword in Config.CRITICAL_KEYWORDS)

