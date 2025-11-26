"""
Repositório para gerenciamento de pacientes.
"""

from typing import List, Dict, Optional, Any
from src.data.database import Database


class PacienteRepository:
    """Gerencia o cadastro e consulta de pacientes."""
    
    def __init__(self, db: Optional[Database] = None):
        """
        Inicializa o repositório de pacientes.
        
        Args:
            db: Instância do banco de dados. Se None, cria uma nova.
        """
        self.db = db or Database()
    
    def criar_paciente(self, nome: str, quarto: Optional[str] = None,
                      cpf: Optional[str] = None, telefone: Optional[str] = None,
                      observacoes: Optional[str] = None) -> int:
        """
        Cria um novo paciente.
        
        Args:
            nome: Nome do paciente.
            quarto: Número do quarto.
            cpf: CPF do paciente (opcional).
            telefone: Telefone do paciente (opcional).
            observacoes: Observações sobre o paciente (opcional).
            
        Returns:
            ID do paciente criado.
        """
        return self.db.criar_paciente(nome, quarto, cpf, telefone, observacoes)
    
    def obter_paciente(self, paciente_id: int) -> Optional[Dict[str, Any]]:
        """Obtém um paciente por ID."""
        return self.db.obter_paciente(paciente_id)
    
    def obter_paciente_por_cpf(self, cpf: str) -> Optional[Dict[str, Any]]:
        """Obtém um paciente por CPF."""
        return self.db.obter_paciente_por_cpf(cpf)
    
    def listar_pacientes(self, apenas_ativos: bool = True) -> List[Dict[str, Any]]:
        """Lista todos os pacientes."""
        return self.db.listar_pacientes(apenas_ativos)
    
    def atualizar_paciente(self, paciente_id: int, **kwargs) -> bool:
        """Atualiza dados de um paciente."""
        return self.db.atualizar_paciente(paciente_id, **kwargs)
    
    def desativar_paciente(self, paciente_id: int) -> bool:
        """Desativa um paciente."""
        return self.db.desativar_paciente(paciente_id)
    
    def obter_estatisticas(self, paciente_id: int) -> Dict[str, Any]:
        """Obtém estatísticas de solicitações de um paciente."""
        return self.db.obter_estatisticas_paciente(paciente_id)

