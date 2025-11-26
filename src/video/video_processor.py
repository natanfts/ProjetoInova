"""
Processador de vídeo para detecção de gestos.
"""

import cv2
import threading
import time
from typing import Callable, Optional
import mediapipe as mp
from src.gesture_detector.gesture_detector import GestureDetector
from src.config.config import Config


class VideoProcessor:
    """Processa vídeo da câmera e detecta gestos."""

    def __init__(self, camera_index: int = None, callback_gesto: Optional[Callable] = None, callback_frame: Optional[Callable] = None, callback_mao_aberta: Optional[Callable] = None, callback_mao_fechada: Optional[Callable] = None, callback_estado_mao: Optional[Callable] = None):
        """
        Inicializa o processador de vídeo.

        Args:
            camera_index: Índice da câmera (padrão: 0).
            callback_gesto: Função chamada quando um gesto é detectado.
                            Recebe (chave, dedos_estendidos, indice_mao) como argumentos.
            callback_frame: Função chamada para cada frame processado.
                            Recebe (frame_bgr) como argumento.
            callback_mao_aberta: Função chamada quando mão totalmente aberta é detectada (confirmação/envio).
            callback_mao_fechada: Função chamada quando mão fechada é detectada (cancelamento).
            callback_estado_mao: Função chamada a cada frame para atualizar estado da mão.
                                 Recebe (estado: str, detalhes: str) como argumentos.
        """
        self.camera_index = camera_index or Config.CAMERA_INDEX
        self.callback_gesto = callback_gesto
        self.callback_frame = callback_frame
        self.callback_mao_aberta = callback_mao_aberta
        self.callback_mao_fechada = callback_mao_fechada
        self.callback_estado_mao = callback_estado_mao
        self.cap: Optional[cv2.VideoCapture] = None
        self.detector = GestureDetector()
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.show_opencv_window = Config.SHOW_OPENCV_WINDOW
        # Armazena último gesto para envio com mão aberta
        self.ultimo_gesto_detectado = None

        # Estado de aguardando confirmação (controlado externamente)
        self.aguardando_confirmacao = False

        # Debounce para evitar múltiplas chamadas do callback com o mesmo gesto
        self.ultimo_gesto_chamado = None  # Último gesto que chamou o callback
        self.ultimo_tempo_callback = 0  # Timestamp da última chamada do callback
        # Aguarda 0.5s antes de chamar callback novamente com o mesmo gesto
        self.DEBOUNCE_CALLBACK_SEGUNDOS = 0.5

        # Debounce para detecção de mão fechada (cancelamento)
        self.ultimo_tempo_mao_fechada = 0  # Timestamp da última detecção de mão fechada
        # Aguarda 0.3s antes de detectar mão fechada novamente
        self.DEBOUNCE_MAO_FECHADA_SEGUNDOS = 0.3

        # Debounce para detecção de mão totalmente aberta (confirmação)
        self.ultimo_tempo_mao_aberta = 0  # Timestamp da última detecção de mão aberta
        # Aguarda 1.5s antes de detectar mão aberta novamente (aumentado para evitar múltiplos envios)
        self.DEBOUNCE_MAO_ABERTA_SEGUNDOS = 1.5
        # Timestamp da última vez que detectou mão totalmente aberta (5 dedos)
        self.ultima_deteccao_mao_aberta_completa = 0
        # Janela de tempo para ignorar gestos de 4 dedos após detectar mão totalmente aberta (aumentado para evitar falsos positivos)
        self.WINDOW_IGNORAR_4_DEDOS_SEGUNDOS = 5.0
        # Contador de detecções consecutivas de mão totalmente aberta
        self.contador_deteccoes_mao_aberta = 0
        # Flag para indicar se mão totalmente aberta foi detectada recentemente
        self.ultima_deteccao_mao_aberta = False
        # Timestamp da última vez que mão totalmente aberta foi detectada
        self.tempo_deteccao_mao_aberta = 0
        # Janela de tempo para ignorar gestos de 4 dedos após detectar mão totalmente aberta
        self.WINDOW_MAO_ABERTA_SEGUNDOS = 2.0

    def iniciar(self):
        """Inicia a captura de vídeo."""
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Não foi possível abrir a câmera {self.camera_index}")

        self.running = True
        self.thread = threading.Thread(target=self._loop_video, daemon=True)
        self.thread.start()

    def _loop_video(self):
        """Loop principal de processamento de vídeo."""
        while self.running:
            if self.cap is None:
                break

            success, img = self.cap.read()
            if not success:
                break

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            result = self.detector.processar_frame(img_rgb)

            if result.multi_hand_landmarks:
                # Há mão(s) detectada(s)
                for idx, hand_landmarks in enumerate(result.multi_hand_landmarks):
                    # Desenha landmarks na imagem
                    self.mp_draw.draw_landmarks(
                        img,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS
                    )

                    # CRÍTICO: Detecta gesto PRIMEIRO para contar dedos antes de verificar estados especiais
                    chave_temp, dedos_estendidos_temp = self.detector.detectar_gesto(
                        hand_landmarks.landmark
                    )
                    num_dedos_detectados = len(chave_temp) if chave_temp else 0

                    # CRÍTICO: Verifica mão fechada ANTES de qualquer outra coisa
                    # Mão fechada tem PRIORIDADE MÁXIMA quando está aguardando confirmação
                    # Mão fechada (nenhum ou muito poucos dedos) = cancelamento
                    # NÃO deve ser tratada como gesto válido, apenas para cancelamento
                    is_mao_fechada = self.detector.detectar_mao_fechada(
                        hand_landmarks.landmark)

                    # CRÍTICO: Se estiver aguardando confirmação e detectar mão fechada,
                    # cancela IMEDIATAMENTE sem verificar nada mais
                    if is_mao_fechada and self.aguardando_confirmacao:
                        tempo_atual = time.time()
                        tempo_suficiente_mao_fechada = tempo_atual - \
                            self.ultimo_tempo_mao_fechada >= self.DEBOUNCE_MAO_FECHADA_SEGUNDOS

                        if self.callback_mao_fechada and tempo_suficiente_mao_fechada:
                            print("✊ Mão fechada detectada! Cancelando envio...")
                            self.callback_mao_fechada()
                            self.ultimo_tempo_mao_fechada = tempo_atual

                        # Notifica estado da mão (sem desenhar no frame)
                        if self.callback_estado_mao:
                            self.callback_estado_mao(
                                "fechada", f"Mão {idx+1}: ✊ MÃO FECHADA (Cancelando...)")

                        # PULA processamento como gesto normal quando é mão fechada
                        continue

                    # CRÍTICO: Só verifica mão totalmente aberta se forem EXATAMENTE 5 dedos
                    # E apenas se estiverem os 5 dedos corretos: (4, 8, 12, 16, 20)
                    # IMPORTANTE: Só verifica se NÃO for mão fechada
                    is_mao_aberta = False
                    if not is_mao_fechada and num_dedos_detectados == 5:
                        # Verifica se são os 5 dedos corretos
                        dedos_esperados = {4, 8, 12, 16, 20}
                        dedos_detectados_set = set(
                            chave_temp) if chave_temp else set()

                        if dedos_detectados_set == dedos_esperados:
                            # Só então verifica se é realmente mão totalmente aberta
                            # (com validação rigorosa do polegar)
                            is_mao_aberta = self.detector.detectar_mao_totalmente_aberta(
                                hand_landmarks.landmark)
                        else:
                            # Tem 5 dedos, mas não são os corretos - não é mão totalmente aberta
                            print(
                                f"🔍 [DEBUG] 5 dedos detectados, mas não são os corretos: {chave_temp} != {dedos_esperados}")
                            is_mao_aberta = False
                    else:
                        # Menos de 5 dedos ou mão fechada - definitivamente não é mão totalmente aberta
                        is_mao_aberta = False

                    # Processa mão fechada quando NÃO está aguardando confirmação (só para exibição)
                    if is_mao_fechada:
                        # Mão fechada detectada - usado APENAS para cancelar envio
                        # Só cancela se estiver aguardando confirmação e passou tempo suficiente
                        tempo_atual = time.time()
                        tempo_suficiente_mao_fechada = tempo_atual - \
                            self.ultimo_tempo_mao_fechada >= self.DEBOUNCE_MAO_FECHADA_SEGUNDOS

                        if self.callback_mao_fechada and self.aguardando_confirmacao and tempo_suficiente_mao_fechada:
                            print("✊ Mão fechada detectada! Cancelando envio...")
                            self.callback_mao_fechada()
                            self.ultimo_tempo_mao_fechada = tempo_atual

                        # Notifica estado da mão (sem desenhar no frame)
                        if self.callback_estado_mao:
                            texto = f"Mão {idx+1}: ✊ MÃO FECHADA"
                            if self.aguardando_confirmacao:
                                texto += " (Cancelando...)"
                            self.callback_estado_mao("fechada", texto)

                        # PULA processamento como gesto normal quando é mão fechada
                        continue

                    # Usa os valores já detectados acima
                    chave = chave_temp
                    dedos_estendidos = dedos_estendidos_temp

                    # DEBUG: Log para entender o que está sendo detectado
                    if chave:
                        num_dedos_detectados = len(chave)
                        print(
                            f"🔍 [DEBUG] Gestos detectados: {chave} ({num_dedos_detectados} dedos) | is_mao_aberta={is_mao_aberta}")

                    # CRÍTICO: Só considera mão totalmente aberta se EXATAMENTE 5 dedos forem detectados
                    # IMPORTANTE: Verifica PRIMEIRO se são 5 dedos, DEPOIS verifica se é mão totalmente aberta
                    # Se tiver 4 dedos ou menos, processa como gesto normal (não é mão totalmente aberta)
                    num_dedos = len(chave) if chave else 0

                    # Força is_mao_aberta = False se não forem 5 dedos (evita falsos positivos)
                    if num_dedos != 5:
                        is_mao_aberta = False

                    # CRÍTICO: Se detectou 5 dedos (independentemente de validação), atualiza timestamp
                    # Isso garante que gestos de 4 dedos detectados depois sejam ignorados
                    # IMPORTANTE: Atualiza SEMPRE que detectar 5 dedos, mesmo que não esteja aguardando confirmação
                    if num_dedos == 5:
                        dedos_detectados_set_5 = set(chave) if chave else set()
                        dedos_corretos_5 = {4, 8, 12, 16, 20}
                        if dedos_detectados_set_5 == dedos_corretos_5:
                            # Detectou os 5 dedos corretos - atualiza timestamp para ignorar gestos de 4 dedos
                            self.ultima_deteccao_mao_aberta_completa = time.time()
                            self.contador_deteccoes_mao_aberta += 1  # Incrementa contador
                            print(
                                f"🔍 [DEBUG] Timestamp atualizado: mão totalmente aberta detectada (5 dedos) - contador: {self.contador_deteccoes_mao_aberta}")
                    else:
                        # Se não detectou 5 dedos, reseta contador após alguns frames sem detecção
                        # (não reseta imediatamente para evitar resetar entre detecções intermitentes)
                        if self.contador_deteccoes_mao_aberta > 0 and num_dedos < 4:
                            self.contador_deteccoes_mao_aberta = 0

                    if num_dedos == 5 and is_mao_aberta:
                        # Mão totalmente aberta detectada (EXATAMENTE 5 dedos confirmados) - usado APENAS para confirmação/envio
                        # NÃO processa como gesto normal e NÃO armazena como gesto detectado

                        # VALIDAÇÃO FINAL: Verifica se os dedos detectados são exatamente os corretos
                        dedos_corretos = {4, 8, 12, 16, 20}
                        dedos_detectados_set = set(chave) if chave else set()

                        if dedos_detectados_set != dedos_corretos:
                            # Tem 5 dedos, mas não são os corretos - ignora
                            print(
                                f"🔍 [DEBUG] MÃO TOTALMENTE ABERTA REJEITADA: {chave} não corresponde a {dedos_corretos}")
                            is_mao_aberta = False
                            # Continua processando como gesto normal
                        else:
                            print(
                                f"🔍 [DEBUG] MÃO TOTALMENTE ABERTA CONFIRMADA: {chave} ({num_dedos} dedos)")

                            # Debounce: evita múltiplas detecções de mão aberta
                            tempo_atual = time.time()

                            # CRÍTICO: Se ultimo_tempo_mao_aberta for 0, significa que acabou de resetar
                            # Neste caso, inicializa com tempo atual menos o debounce para permitir primeira detecção
                            if self.ultimo_tempo_mao_aberta == 0:
                                self.ultimo_tempo_mao_aberta = tempo_atual - self.DEBOUNCE_MAO_ABERTA_SEGUNDOS

                            tempo_suficiente_mao_aberta = tempo_atual - \
                                self.ultimo_tempo_mao_aberta >= self.DEBOUNCE_MAO_ABERTA_SEGUNDOS

                            # CRÍTICO: Atualiza timestamp de detecção de mão totalmente aberta SEMPRE que detectar
                            # Isso será usado para ignorar gestos de 4 dedos logo após detectar mão totalmente aberta
                            # IMPORTANTE: Atualiza tanto quando está aguardando confirmação quanto quando não está
                            self.ultima_deteccao_mao_aberta_completa = tempo_atual

                            # Chama callback de confirmação apenas se estiver aguardando confirmação e passou tempo suficiente
                            if self.callback_mao_aberta and self.aguardando_confirmacao:
                                if tempo_suficiente_mao_aberta:
                                    # Passa None como gesto_info - o callback do main.py usará ultimo_gesto_valido
                                    print(
                                        f"✅ Mão totalmente aberta detectada (5 dedos)! Confirmando envio...")
                                    # Passa None, o callback usa ultimo_gesto_valido do main.py
                                    self.callback_mao_aberta(None)
                                    self.ultimo_tempo_mao_aberta = tempo_atual
                                # else: ainda está em período de debounce - não faz nada
                            elif not self.aguardando_confirmacao:
                                # Mão totalmente aberta detectada mas não está aguardando confirmação
                                # Isso significa que a pessoa está apenas mostrando a mão aberta sem querer fazer gesto
                                # Atualiza timestamp para ignorar gestos de 4 dedos que possam ser detectados depois
                                # Não faz nada além de atualizar o timestamp (já feito acima)
                                pass

                            # Notifica estado da mão (sem desenhar no frame)
                            if self.callback_estado_mao:
                                texto = f"Mão {idx+1}: 🖐️ MÃO ABERTA (5 dedos)"
                                if self.aguardando_confirmacao:
                                    texto += " (Confirmando...)"
                                else:
                                    texto += " (Faça um gesto primeiro)"
                                self.callback_estado_mao("aberta", texto)

                            # PULA processamento como gesto normal quando é mão totalmente aberta
                            continue

                    # Se chegou aqui, não é mão totalmente aberta - continua processando como gesto normal

                    # CRÍTICO: Se estiver aguardando confirmação, ignora TODOS os gestos normais
                    # Durante confirmação, apenas mão fechada (cancelar) ou mão totalmente aberta (enviar) são aceitos
                    # Qualquer outro gesto deve ser completamente ignorado ANTES de processar
                    if self.aguardando_confirmacao:
                        # Ignora completamente qualquer gesto normal enquanto aguarda confirmação
                        continue

                    # CRÍTICO: Ignora mão totalmente aberta (4, 8, 12, 16, 20) mesmo que detectada como gesto normal
                    # Isso garante que mão totalmente aberta nunca seja tratada como um gesto reconhecido
                    # Mão totalmente aberta = confirmação/envio, não é um gesto válido
                    if chave == (4, 8, 12, 16, 20):
                        continue

                    # CRÍTICO: Ignora gestos de 4 dedos quando mão totalmente aberta foi detectada neste mesmo frame ou recentemente
                    # Quando a mão está totalmente aberta, às vezes detecta 4 dedos primeiro (sem o polegar)
                    # e trata como gesto válido. Isso causa falsos positivos.
                    if chave == (8, 12, 16, 20):
                        # Se detectou mão totalmente aberta neste mesmo frame, ignora o gesto de 4 dedos
                        if is_mao_aberta:
                            print(
                                f"🔍 [DEBUG] Ignorando gesto de 4 dedos - mão totalmente aberta detectada no mesmo frame (falso positivo)")
                            continue

                        # Se houve múltiplas detecções de mão totalmente aberta recentemente, ignora gestos de 4 dedos completamente
                        # Isso evita falsos positivos quando a pessoa está apenas mostrando a mão aberta
                        if self.contador_deteccoes_mao_aberta >= 5:  # Se detectou mão totalmente aberta várias vezes
                            print(
                                f"🔍 [DEBUG] Ignorando gesto de 4 dedos - mão totalmente aberta detectada {self.contador_deteccoes_mao_aberta} vezes recentemente (provável mão apenas aberta)")
                            continue

                        # Se detectou mão totalmente aberta recentemente, ignora gestos de 4 dedos por um período
                        tempo_atual_check = time.time()
                        tempo_desde_mao_aberta = tempo_atual_check - \
                            self.ultima_deteccao_mao_aberta_completa

                        if tempo_desde_mao_aberta < self.WINDOW_IGNORAR_4_DEDOS_SEGUNDOS and self.ultima_deteccao_mao_aberta_completa > 0:
                            # Gesto de 4 dedos detectado logo após mão totalmente aberta - ignora (provável falso positivo)
                            print(
                                f"🔍 [DEBUG] Ignorando gesto de 4 dedos - detectado {tempo_desde_mao_aberta:.2f}s após mão totalmente aberta (falso positivo provável)")
                            continue

                    # CRÍTICO: Verifica novamente se é mão fechada (fallback caso a detecção anterior não tenha pego)
                    # IMPORTANTE: Mão fechada = 0 dedos, não 1 dedo!
                    # 1 dedo (indicador) é um COMANDO VÁLIDO, não mão fechada
                    # Esta verificação só acontece quando NÃO está aguardando confirmação (já verificamos acima)
                    if not chave or len(chave) == 0:
                        # Mão fechada detectada (0 dedos) - apenas para exibição quando não está aguardando confirmação
                        # Não faz nada aqui, apenas exibe na imagem
                        continue

                    # Armazena último gesto detectado (apenas gestos válidos, não joia)
                    # O callback de gesto será responsável por validar se tem mensagem antes de armazenar
                    self.ultimo_gesto_detectado = (
                        chave, dedos_estendidos, idx)

                    # Debounce: evita chamar callback repetidamente com o mesmo gesto
                    tempo_atual = time.time()
                    gesto_mudou = self.ultimo_gesto_chamado != chave
                    tempo_suficiente = tempo_atual - \
                        self.ultimo_tempo_callback >= self.DEBOUNCE_CALLBACK_SEGUNDOS

                    # Só chama callback se o gesto mudou ou passou tempo suficiente
                    if self.callback_gesto and (gesto_mudou or tempo_suficiente):
                        self.callback_gesto(chave, dedos_estendidos, idx)
                        self.ultimo_gesto_chamado = chave
                        self.ultimo_tempo_callback = tempo_atual

                    # Notifica estado da mão com gesto detectado (sem desenhar no frame)
                    if self.callback_estado_mao:
                        num_dedos = len(chave) if chave else 0
                        self.callback_estado_mao(
                            "gesto", f"Mão {idx+1}: {num_dedos} dedo(s) detectado(s)")
            else:
                # Nenhuma mão detectada
                if self.callback_estado_mao:
                    self.callback_estado_mao(
                        "nenhuma", "Nenhuma mão detectada - posicione a mão na frente da câmera")

            # Chama callback de frame se fornecido (para exibir na UI)
            if self.callback_frame:
                try:
                    self.callback_frame(img.copy())
                except Exception as e:
                    print(f"Erro ao chamar callback de frame: {e}")

            # Mostra janela OpenCV apenas se configurado
            if self.show_opencv_window:
                cv2.imshow("Detecção de Gestos", img)

                # Verifica se ESC foi pressionado
                if cv2.waitKey(1) & 0xFF == 27:
                    self.parar()
                    break
            else:
                # Pequeno delay para não sobrecarregar CPU
                time.sleep(1.0 / Config.VIDEO_FPS)

    def parar(self):
        """Para a captura de vídeo e libera recursos."""
        self.running = False

        if self.cap:
            self.cap.release()

        if self.show_opencv_window:
            cv2.destroyAllWindows()
        self.detector.liberar()

    def aguardar_finalizacao(self):
        """Aguarda a thread de vídeo finalizar."""
        if self.thread and self.thread.is_alive():
            self.thread.join()
