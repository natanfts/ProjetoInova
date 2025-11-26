"""
Detector de gestos usando MediaPipe.
"""

import math
from typing import Tuple, List, Optional
import mediapipe as mp


class GestureDetector:
    """Detecta gestos de mão usando MediaPipe."""
    
    # Índices dos dedos no MediaPipe
    INDICES_DEDOS = {
        'polegar': 4,
        'indicador': 8,
        'medio': 12,
        'anelar': 16,
        'mindinho': 20
    }
    
    # Pontos de referência para cada dedo
    PONTOS_REFERENCIA = {
        8: 6,   # Indicador
        12: 10, # Médio
        16: 14, # Anelar
        20: 18  # Mindinho
    }
    
    def __init__(self):
        """Inicializa o detector de gestos."""
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def detectar_dedos_estendidos(self, landmarks) -> List[int]:
        """
        Detecta quais dedos estão estendidos.
        
        Args:
            landmarks: Lista de landmarks da mão do MediaPipe.
            
        Returns:
            Lista de índices dos dedos estendidos.
        """
        dedos_estendidos = []
        
        # Verifica dedos (exceto polegar) - comparação vertical
        # Se a ponta do dedo (y menor) está acima da base, o dedo está estendido
        for dedo_topo, dedo_base in self.PONTOS_REFERENCIA.items():
            if landmarks[dedo_topo].y < landmarks[dedo_base].y:
                dedos_estendidos.append(dedo_topo)
        
        # Verifica polegar com lógica mais rigorosa
        # O polegar precisa estar CLARAMENTE estendido, não apenas parcialmente
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        wrist = landmarks[0]
        
        # Calcula distâncias
        dist_tip_ip = math.sqrt((thumb_tip.x - thumb_ip.x)**2 + (thumb_tip.y - thumb_ip.y)**2)
        dist_ip_mcp = math.sqrt((thumb_ip.x - thumb_mcp.x)**2 + (thumb_ip.y - thumb_mcp.y)**2)
        dist_tip_wrist = math.sqrt((thumb_tip.x - wrist.x)**2 + (thumb_tip.y - wrist.y)**2)
        dist_mcp_wrist = math.sqrt((thumb_mcp.x - wrist.x)**2 + (thumb_mcp.y - wrist.y)**2)
        
        # CRITÉRIO RIGOROSO: O polegar está estendido APENAS se:
        # 1. A distância entre ponta e articulação intermediária for significativa (ponta afastada)
        # 2. A ponta do polegar está mais distante do punho que a articulação MCP
        # Isso garante que o polegar está REALMENTE estendido, não apenas parcialmente dobrado
        
        # Verifica se a ponta está significativamente afastada da articulação
        thumb_extended = dist_tip_ip > dist_ip_mcp * 0.7  # Pelo menos 70% da distância entre articulações
        
        # Verifica se a ponta está mais afastada do punho que a base do polegar
        thumb_extended = thumb_extended and (dist_tip_wrist > dist_mcp_wrist * 1.1)  # Pelo menos 10% mais distante
        
        # Verificação adicional: comparação vertical/horizontal baseada na orientação da mão
        # Se a ponta do polegar está acima ou mais à direita (dependendo da orientação), está estendido
        if thumb_extended:
            # Verifica também se a ponta está realmente separada da mão (não dobrada sobre os outros dedos)
            index_mcp = landmarks[5]  # Base do indicador
            dist_thumb_index = math.sqrt((thumb_tip.x - index_mcp.x)**2 + (thumb_tip.y - index_mcp.y)**2)
            
            # Se o polegar está muito próximo do indicador, pode estar dobrado
            thumb_extended = dist_thumb_index > dist_ip_mcp * 1.5
        
        if thumb_extended:
            dedos_estendidos.append(4)
        
        return dedos_estendidos
    
    def detectar_mao_totalmente_aberta(self, landmarks) -> bool:
        """
        Detecta se a mão está totalmente aberta (todos os 5 dedos estendidos).
        Usado para confirmação/envio de gestos.
        
        Args:
            landmarks: Lista de landmarks da mão do MediaPipe.
            
        Returns:
            True se EXATAMENTE todos os 5 dedos estiverem estendidos, False caso contrário.
        """
        try:
            dedos_estendidos = self.detectar_dedos_estendidos(landmarks)
            num_dedos = len(dedos_estendidos)
            
            # CRÍTICO: Mão totalmente aberta = EXATAMENTE 5 dedos
            if num_dedos != 5:
                # DEBUG: Log quando não são 5 dedos
                if num_dedos > 0:  # Evita spam quando não há dedos
                    print(f"🔍 [DEBUG] detectar_mao_totalmente_aberta: {num_dedos} dedos detectados ({dedos_estendidos}) - NÃO é mão totalmente aberta")
                return False
            
            # CRÍTICO: Verifica se são EXATAMENTE os 5 dedos corretos
            dedos_detectados_set = set(dedos_estendidos)
            dedos_necessarios = {4, 8, 12, 16, 20}
            
            # Primeiro verifica se tem todos os dedos necessários
            if dedos_detectados_set != dedos_necessarios:
                return False
            
            # VALIDAÇÃO EXTRA: Verifica se o polegar está REALMENTE estendido
            # Não confia apenas na detecção básica - faz verificação adicional rigorosa
            thumb_tip = landmarks[4]
            thumb_ip = landmarks[3]
            thumb_mcp = landmarks[2]
            wrist = landmarks[0]
            
            # Verifica se o polegar está claramente estendido
            dist_tip_ip = math.sqrt((thumb_tip.x - thumb_ip.x)**2 + (thumb_tip.y - thumb_ip.y)**2)
            dist_ip_mcp = math.sqrt((thumb_ip.x - thumb_mcp.x)**2 + (thumb_ip.y - thumb_mcp.y)**2)
            dist_tip_wrist = math.sqrt((thumb_tip.x - wrist.x)**2 + (thumb_tip.y - wrist.y)**2)
            dist_mcp_wrist = math.sqrt((thumb_mcp.x - wrist.x)**2 + (thumb_mcp.y - wrist.y)**2)
            
            # Validação RIGOROSA do polegar: precisa estar CLARAMENTE estendido
            # Evita falsos positivos quando apenas 4 dedos estão levantados mas o polegar aparece intermitentemente
            # Requer que o polegar esteja pelo menos 50% estendido (mais rigoroso)
            thumb_extended_enough = (
                dist_tip_ip > dist_ip_mcp * 0.5 and  # Pelo menos 50% da distância entre articulações E
                dist_tip_wrist > dist_mcp_wrist * 0.9  # Pelo menos 90% da distância da base
            )
            
            if not thumb_extended_enough:
                print(f"🔍 [DEBUG] MÃO TOTALMENTE ABERTA REJEITADA: polegar completamente dobrado (tip_ip={dist_tip_ip/dist_ip_mcp:.2f}x, tip_wrist={dist_tip_wrist/dist_mcp_wrist:.2f}x)")
                return False
            
            # Log de confirmação com detalhes do polegar
            print(f"🔍 [DEBUG] Polegar validado para mão totalmente aberta: tip_ip={dist_tip_ip/dist_ip_mcp:.2f}x, tip_wrist={dist_tip_wrist/dist_mcp_wrist:.2f}x")
            
            is_aberta = True
            print(f"🔍 [DEBUG] MÃO TOTALMENTE ABERTA confirmada: {dedos_estendidos} (5 dedos)")
            return is_aberta
        except Exception as e:
            # Em caso de erro, retorna False
            print(f"⚠️ Erro em detectar_mao_totalmente_aberta: {e}")
            return False
    
    def detectar_mao_fechada(self, landmarks) -> bool:
        """
        Detecta se a mão está fechada (nenhum dedo estendido ou apenas o polegar parcialmente).
        Usado para cancelamento de gestos.
        
        IMPORTANTE: 1 dedo (indicador, médio, etc.) é um COMANDO VÁLIDO, não mão fechada.
        Apenas 0 dedos ou apenas polegar parcialmente estendido = mão fechada.
        
        Args:
            landmarks: Lista de landmarks da mão do MediaPipe.
            
        Returns:
            True se a mão estiver fechada (0 dedos ou apenas polegar parcialmente), False caso contrário.
        """
        try:
            dedos_estendidos = self.detectar_dedos_estendidos(landmarks)
            num_dedos = len(dedos_estendidos)
            
            # Mão fechada = 0 dedos estendidos
            if num_dedos == 0:
                return True
            
            # Se tiver 1 dedo, verifica se é realmente mão fechada ou um comando válido
            # 1 dedo pode ser um comando válido (indicador, médio, etc.)
            # Só considera mão fechada se for APENAS o polegar E ele estiver parcialmente estendido
            if num_dedos == 1:
                # Se for apenas o polegar, verifica se está realmente estendido ou parcialmente
                if 4 in dedos_estendidos:
                    thumb_tip = landmarks[4]
                    thumb_ip = landmarks[3]
                    thumb_mcp = landmarks[2]
                    
                    # Calcula distâncias
                    dist_tip_ip = math.sqrt((thumb_tip.x - thumb_ip.x)**2 + (thumb_tip.y - thumb_ip.y)**2)
                    dist_ip_mcp = math.sqrt((thumb_ip.x - thumb_mcp.x)**2 + (thumb_ip.y - thumb_mcp.y)**2)
                    
                    # Se a distância entre ponta e articulação for muito pequena, é mão fechada
                    if dist_tip_ip < dist_ip_mcp * 0.5:
                        return True
                    # Se o polegar estiver claramente estendido, não é mão fechada (é um gesto válido)
                    return False
                else:
                    # 1 dedo que não é polegar = COMANDO VÁLIDO, não mão fechada
                    return False
            
            # Mais de 1 dedo = definitivamente não é mão fechada
            is_fechada = False
            
            # Debug: log apenas quando detecta mão fechada (para não poluir o console)
            if is_fechada:
                print(f"🔍 [DEBUG] Mão fechada detectada: {num_dedos} dedo(s) estendido(s) = {dedos_estendidos}")
            
            return is_fechada
        except Exception as e:
            # Em caso de erro, retorna False (não considera fechada)
            print(f"⚠️ Erro ao detectar mão fechada: {e}")
            return False
    
    def detectar_gesto(self, landmarks) -> Tuple[Tuple[int, ...], List[int]]:
        """
        Detecta o gesto baseado nos landmarks da mão.
        
        Args:
            landmarks: Lista de landmarks da mão do MediaPipe.
            
        Returns:
            Tupla contendo:
            - Chave do gesto (tupla ordenada de dedos estendidos)
            - Lista de dedos estendidos (não ordenada)
        """
        dedos_estendidos = self.detectar_dedos_estendidos(landmarks)
        chave = tuple(sorted(dedos_estendidos))
        return chave, dedos_estendidos
    
    def processar_frame(self, imagem_rgb):
        """
        Processa um frame de imagem para detectar mãos.
        
        Args:
            imagem_rgb: Imagem em formato RGB.
            
        Returns:
            Resultado do processamento do MediaPipe.
        """
        return self.hands.process(imagem_rgb)
    
    def liberar(self):
        """Libera recursos do detector."""
        self.hands.close()

