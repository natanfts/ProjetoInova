"""
Repositório para gerenciamento de gestos usando SQLite.
"""

import json
from typing import Dict, Tuple, Optional
from pathlib import Path
from src.config.config import Config
from src.data.database import Database


class GestoRepository:
    """Gerencia o armazenamento e recuperação de gestos usando SQLite."""
    
    def __init__(self, db: Optional[Database] = None):
        """
        Inicializa o repositório de gestos.
        
        Args:
            db: Instância do banco de dados. Se None, cria uma nova.
        """
        self.db = db or Database()
        self._gestos: Dict[Tuple[int, ...], str] = {}
        self._carregar_gestos()
    
    def _carregar_gestos(self):
        """Carrega gestos do banco de dados."""
        self._gestos.clear()
        
        try:
            gestos_db = self.db.listar_gestos()
            for gesto in gestos_db:
                try:
                    dedos_lista = json.loads(gesto['dedos'])
                    dedos = tuple(sorted(dedos_lista))
                    
                    # CRÍTICO: Ignora mão totalmente aberta (4, 8, 12, 16, 20)
                    if dedos == (4, 8, 12, 16, 20):
                        continue
                    
                    # Valida índices
                    indices_validos = {4, 8, 12, 16, 20}
                    if all(d in indices_validos for d in dedos):
                        self._gestos[dedos] = gesto['mensagem']
                except (json.JSONDecodeError, ValueError):
                    continue
        except Exception as e:
            print(f"Erro ao carregar gestos: {e}")
    
    def _validar_padrao_dedos(self, chave: Tuple[int, ...]) -> bool:
        """
        Valida se a combinação de dedos corresponde aos padrões definidos:
        - 1 dedo: apenas indicador (8)
        - 2 dedos: indicador (8) + médio (12)
        - 3 dedos: indicador (8) + médio (12) + anelar (16)
        - 4 dedos: indicador (8) + médio (12) + anelar (16) + mínimo (20)
        
        Args:
            chave: Tupla de dedos estendidos (deve estar ordenada).
            
        Returns:
            True se o padrão for válido, False caso contrário.
        """
        # Padrões esperados (ordenados)
        padroes_validos = {
            1: (8,),                    # Apenas indicador
            2: (8, 12),                 # Indicador + médio
            3: (8, 12, 16),             # Indicador + médio + anelar
            4: (8, 12, 16, 20)          # Indicador + médio + anelar + mínimo
        }
        
        num_dedos = len(chave)
        if num_dedos not in padroes_validos:
            return False
        
        # Ordena a chave para comparação
        chave_ordenada = tuple(sorted(chave))
        padrao_esperado = padroes_validos[num_dedos]
        
        return chave_ordenada == padrao_esperado
    
    def obter_mensagem(self, chave: Tuple[int, ...]) -> Optional[str]:
        """
        Obtém a mensagem associada a uma chave de gesto.
        
        Args:
            chave: Tupla de dedos estendidos.
            
        Returns:
            Mensagem associada ou None se não encontrada.
        """
        # CRÍTICO: Nunca retorna mensagem para gesto vazio (mão fechada)
        if not chave or len(chave) == 0:
            return None
        
        # CRÍTICO: Nunca retorna mensagem para mão totalmente aberta (todos os 5 dedos)
        if chave == (4, 8, 12, 16, 20):
            return None
        
        # NOVA LÓGICA: Valida que o gesto corresponde ao padrão esperado
        num_dedos = len(chave)
        if num_dedos in [1, 2, 3, 4]:
            # CRÍTICO: Valida que a combinação de dedos está correta
            if not self._validar_padrao_dedos(chave):
                return None  # Gesto não corresponde ao padrão esperado
            
            # Tenta obter da configuração simplificada
            mensagem = self.db.obter_mensagem_por_num_dedos(num_dedos)
            if mensagem:
                return mensagem
            else:
                # Gesto válido mas sem mensagem configurada
                print(f"⚠️ [DEBUG] Gesto válido {chave_ordenada} ({num_dedos} dedo(s)) detectado, mas sem mensagem configurada no banco.")
        
        # Fallback: Valida que todos os índices são válidos (4, 8, 12, 16, 20)
        indices_validos = {4, 8, 12, 16, 20}
        if not all(d in indices_validos for d in chave):
            return None
        
        # Tenta obter do cache primeiro (sistema antigo)
        if chave in self._gestos:
            return self._gestos[chave]
        
        # Se não estiver no cache, busca no banco (sistema antigo)
        mensagem = self.db.obter_mensagem_gesto(chave)
        if mensagem:
            self._gestos[chave] = mensagem
        return mensagem
    
    def obter_mensagem_por_num_dedos(self, num_dedos: int) -> Optional[str]:
        """
        Obtém mensagem por número de dedos (1-4).
        
        Args:
            num_dedos: Número de dedos estendidos (1, 2, 3 ou 4).
            
        Returns:
            Mensagem associada ou None se não encontrada.
        """
        if num_dedos not in [1, 2, 3, 4]:
            return None
        return self.db.obter_mensagem_por_num_dedos(num_dedos)
    
    def salvar_gesto(self, chave: Tuple[int, ...], mensagem: str) -> bool:
        """
        Salva um novo gesto no banco de dados.
        
        Args:
            chave: Tupla de dedos estendidos.
            mensagem: Mensagem associada ao gesto.
            
        Returns:
            True se salvo com sucesso, False caso contrário.
        """
        try:
            # Valida índices
            indices_validos = {4, 8, 12, 16, 20}
            if not all(d in indices_validos for d in chave):
                return False
            
            # CRÍTICO: Não permite salvar mão totalmente aberta
            if chave == (4, 8, 12, 16, 20):
                return False
            
            # Salva no banco
            self.db.criar_gesto(chave, mensagem)
            
            # Atualiza cache
            self._gestos[chave] = mensagem
            return True
        except Exception as e:
            print(f"Erro ao salvar gesto: {e}")
            return False
    
    def obter_todos_gestos(self) -> Dict[Tuple[int, ...], str]:
        """
        Retorna todos os gestos salvos.
        
        Returns:
            Dicionário com todos os gestos.
        """
        return self._gestos.copy()
    
    def exportar_para_txt(self, caminho_arquivo: Optional[Path] = None) -> bool:
        """
        Exporta todos os gestos para um arquivo de texto.
        
        Args:
            caminho_arquivo: Caminho do arquivo de exportação. Se None, usa o padrão.
            
        Returns:
            True se exportado com sucesso, False caso contrário.
        """
        caminho = caminho_arquivo or Config.EXPORT_PATH
        
        try:
            with open(caminho, 'w', encoding='utf-8') as f:
                for dedos, mensagem in self._gestos.items():
                    linha_dedos = '|'.join(map(str, dedos))
                    f.write(f"{linha_dedos}: {mensagem}\n")
            return True
        except Exception as e:
            print(f"Erro ao exportar gestos: {e}")
            return False
    
    def recarregar(self):
        """Recarrega os gestos do banco de dados."""
        self._carregar_gestos()
