"""
Módulo de banco de dados SQLite para o sistema.
"""

import sqlite3
import json
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
from src.config.config import Config


class Database:
    """Gerencia o banco de dados SQLite da aplicação."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Inicializa o banco de dados.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados. Se None, usa o padrão da Config.
        """
        self.db_path = db_path or Config.DB_PATH
        print(f"📦 Inicializando banco de dados SQLite: {self.db_path}")
        self._criar_tabelas()
        self._migrar_csv_para_sqlite()
        print(f"✅ Banco de dados SQLite pronto: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Cria e retorna uma conexão com o banco de dados."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
        return conn
    
    def _criar_tabelas(self):
        """Cria as tabelas necessárias no banco de dados."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Tabela de pacientes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pacientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    quarto TEXT,
                    cpf TEXT UNIQUE,
                    telefone TEXT,
                    observacoes TEXT,
                    ativo INTEGER DEFAULT 1,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de gestos (legado - mantida para compatibilidade)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gestos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dedos TEXT NOT NULL UNIQUE,
                    mensagem TEXT NOT NULL,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de configuração de gestos simplificados (por contagem de dedos)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config_gestos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    num_dedos INTEGER NOT NULL UNIQUE CHECK(num_dedos IN (1, 2, 3, 4)),
                    mensagem TEXT NOT NULL,
                    prioridade TEXT DEFAULT 'normal' CHECK(prioridade IN ('baixa', 'normal', 'alta', 'urgente')),
                    ativo INTEGER DEFAULT 1,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de histórico de solicitações
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_solicitacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id INTEGER NOT NULL,
                    gesto_id INTEGER,
                    dedos TEXT NOT NULL,
                    mensagem TEXT NOT NULL,
                    prioridade TEXT DEFAULT 'normal',
                    status TEXT DEFAULT 'pendente',
                    data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_resolucao TIMESTAMP,
                    observacoes TEXT,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
                    FOREIGN KEY (gesto_id) REFERENCES gestos(id)
                )
            """)
            
            # Índices para melhor performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_paciente_id ON historico_solicitacoes(paciente_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON historico_solicitacoes(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_data_solicitacao ON historico_solicitacoes(data_solicitacao)")
            
            # Migração: Adiciona coluna de prioridade se não existir
            try:
                cursor.execute("PRAGMA table_info(config_gestos)")
                colunas = [col[1] for col in cursor.fetchall()]
                if 'prioridade' not in colunas:
                    # SQLite não suporta CHECK em ALTER TABLE, então apenas adiciona a coluna
                    cursor.execute("ALTER TABLE config_gestos ADD COLUMN prioridade TEXT DEFAULT 'normal'")
                    print("✅ Coluna 'prioridade' adicionada à tabela config_gestos")
            except Exception as e:
                print(f"⚠️ Erro ao verificar/adicionar coluna prioridade: {e}")
            
            conn.commit()
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _migrar_csv_para_sqlite(self):
        """Migra dados do CSV para SQLite se o CSV existir e o banco estiver vazio."""
        # Verifica se há gestos no banco (tabela antiga)
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM gestos")
        count_gestos_antigos = cursor.fetchone()[0]
        
        # Verifica se há configurações simplificadas no banco
        cursor.execute("SELECT COUNT(*) FROM config_gestos")
        count_config_gestos = cursor.fetchone()[0]
        conn.close()
        
        # Se já houver configurações simplificadas, não migra
        if count_config_gestos > 0:
            if count_gestos_antigos > 0:
                print(f"ℹ️ Banco SQLite já possui {count_config_gestos} configuração(ões) de gestos e {count_gestos_antigos} gesto(s) antigo(s).")
            return
        
        # Tenta migrar do CSV
        csv_path = Config.CSV_PATH
        if not csv_path.exists():
            print("ℹ️ Arquivo CSV não encontrado. Banco SQLite será criado vazio.")
            return
        
        print("🔄 Iniciando migração do CSV para SQLite...")
        gestos_migrados = 0
        configs_criadas = 0
        
        try:
            import csv
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Mapeia gestos do CSV para configurações simplificadas (por contagem de dedos)
            gestos_por_contagem = {}  # {num_dedos: mensagem}
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                leitor = csv.DictReader(f)
                for linha in leitor:
                    dedos_str = linha.get('dedos', '').strip().strip('"')
                    mensagem = linha.get('mensagem', '').strip().strip('"')
                    
                    if not dedos_str or not mensagem:
                        continue
                    
                    # Valida dedos
                    try:
                        dedos_lista = [int(d.strip()) for d in dedos_str.split('|') if d.strip()]
                        # Ignora mão totalmente aberta (4, 8, 12, 16, 20)
                        if tuple(sorted(dedos_lista)) == (4, 8, 12, 16, 20):
                            continue
                        # Valida índices
                        indices_validos = {4, 8, 12, 16, 20}
                        if not all(d in indices_validos for d in dedos_lista):
                            continue
                        
                        num_dedos = len(dedos_lista)
                        
                        # Se tiver 1-4 dedos, cria configuração simplificada
                        if num_dedos in [1, 2, 3, 4]:
                            # Usa a primeira mensagem encontrada para cada contagem
                            if num_dedos not in gestos_por_contagem:
                                gestos_por_contagem[num_dedos] = mensagem
                                configs_criadas += 1
                        
                        # Também salva na tabela antiga de gestos (compatibilidade)
                        dedos_json = json.dumps(sorted(dedos_lista))
                        cursor.execute("""
                            INSERT OR IGNORE INTO gestos (dedos, mensagem)
                            VALUES (?, ?)
                        """, (dedos_json, mensagem))
                        gestos_migrados += 1
                    except (ValueError, json.JSONDecodeError):
                        continue
            
            # Cria configurações simplificadas a partir dos gestos migrados
            for num_dedos, mensagem in gestos_por_contagem.items():
                cursor.execute("""
                    INSERT OR IGNORE INTO config_gestos (num_dedos, mensagem, prioridade)
                    VALUES (?, ?, 'normal')
                """, (num_dedos, mensagem))
            
            conn.commit()
            
            if gestos_migrados > 0 or configs_criadas > 0:
                print(f"✅ Migração do CSV para SQLite concluída:")
                print(f"   - {gestos_migrados} gesto(s) migrado(s) para tabela 'gestos' (compatibilidade)")
                print(f"   - {configs_criadas} configuração(ões) criada(s) na tabela 'config_gestos'")
                print(f"   - Banco SQLite: {self.db_path}")
            else:
                print("ℹ️ Nenhum gesto válido encontrado no CSV para migrar.")
        except Exception as e:
            print(f"⚠️ Erro ao migrar CSV para SQLite: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
        finally:
            conn.close()
    
    # ========== MÉTODOS PARA PACIENTES ==========
    
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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO pacientes (nome, quarto, cpf, telefone, observacoes)
                VALUES (?, ?, ?, ?, ?)
            """, (nome, quarto, cpf, telefone, observacoes))
            paciente_id = cursor.lastrowid
            conn.commit()
            return paciente_id
        except sqlite3.IntegrityError as e:
            print(f"Erro ao criar paciente: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def obter_paciente(self, paciente_id: int) -> Optional[Dict[str, Any]]:
        """Obtém um paciente por ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM pacientes WHERE id = ?", (paciente_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def obter_paciente_por_cpf(self, cpf: str) -> Optional[Dict[str, Any]]:
        """Obtém um paciente por CPF."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM pacientes WHERE cpf = ?", (cpf,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def listar_pacientes(self, apenas_ativos: bool = True) -> List[Dict[str, Any]]:
        """Lista todos os pacientes."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if apenas_ativos:
                cursor.execute("SELECT * FROM pacientes WHERE ativo = 1 ORDER BY nome")
            else:
                cursor.execute("SELECT * FROM pacientes ORDER BY nome")
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def atualizar_paciente(self, paciente_id: int, **kwargs) -> bool:
        """Atualiza dados de um paciente."""
        campos_permitidos = ['nome', 'quarto', 'cpf', 'telefone', 'observacoes', 'ativo']
        campos = {k: v for k, v in kwargs.items() if k in campos_permitidos}
        
        if not campos:
            return False
        
        campos['data_atualizacao'] = datetime.now().isoformat()
        sets = ', '.join([f"{k} = ?" for k in campos.keys()])
        valores = list(campos.values()) + [paciente_id]
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"UPDATE pacientes SET {sets} WHERE id = ?", valores)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao atualizar paciente: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def desativar_paciente(self, paciente_id: int) -> bool:
        """Desativa um paciente (não remove do banco)."""
        return self.atualizar_paciente(paciente_id, ativo=0)
    
    # ========== MÉTODOS PARA GESTOS ==========
    
    def criar_gesto(self, dedos: Tuple[int, ...], mensagem: str) -> int:
        """
        Cria um novo gesto.
        
        Args:
            dedos: Tupla de dedos estendidos.
            mensagem: Mensagem associada ao gesto.
            
        Returns:
            ID do gesto criado.
        """
        dedos_json = json.dumps(sorted(dedos))
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO gestos (dedos, mensagem)
                VALUES (?, ?)
            """, (dedos_json, mensagem))
            gesto_id = cursor.lastrowid
            conn.commit()
            return gesto_id
        except Exception as e:
            print(f"Erro ao criar gesto: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def obter_gesto_por_dedos(self, dedos: Tuple[int, ...]) -> Optional[Dict[str, Any]]:
        """Obtém um gesto pelos dedos."""
        dedos_json = json.dumps(sorted(dedos))
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM gestos WHERE dedos = ?", (dedos_json,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def obter_mensagem_gesto(self, dedos: Tuple[int, ...]) -> Optional[str]:
        """Obtém a mensagem de um gesto pelos dedos."""
        gesto = self.obter_gesto_por_dedos(dedos)
        if gesto:
            return gesto['mensagem']
        return None
    
    def listar_gestos(self) -> List[Dict[str, Any]]:
        """Lista todos os gestos."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM gestos ORDER BY mensagem")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def remover_gesto(self, dedos: Tuple[int, ...]) -> bool:
        """Remove um gesto."""
        dedos_json = json.dumps(sorted(dedos))
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM gestos WHERE dedos = ?", (dedos_json,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao remover gesto: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # ========== MÉTODOS PARA HISTÓRICO ==========
    
    def criar_solicitacao(self, paciente_id: int, dedos: Tuple[int, ...], 
                         mensagem: str, prioridade: str = 'normal') -> int:
        """
        Cria uma nova solicitação no histórico.
        
        Args:
            paciente_id: ID do paciente.
            dedos: Tupla de dedos estendidos.
            mensagem: Mensagem da solicitação.
            prioridade: Prioridade da solicitação ('normal' ou 'alta').
            
        Returns:
            ID da solicitação criada.
        """
        dedos_json = json.dumps(sorted(dedos))
        
        # Tenta encontrar o gesto correspondente
        gesto = self.obter_gesto_por_dedos(dedos)
        gesto_id = gesto['id'] if gesto else None
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO historico_solicitacoes 
                (paciente_id, gesto_id, dedos, mensagem, prioridade)
                VALUES (?, ?, ?, ?, ?)
            """, (paciente_id, gesto_id, dedos_json, mensagem, prioridade))
            solicitacao_id = cursor.lastrowid
            conn.commit()
            return solicitacao_id
        except Exception as e:
            print(f"Erro ao criar solicitação: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def listar_solicitacoes(self, paciente_id: Optional[int] = None,
                           status: Optional[str] = None,
                           limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Lista solicitações do histórico.
        
        Args:
            paciente_id: Filtrar por paciente (opcional).
            status: Filtrar por status ('pendente', 'resolvido') (opcional).
            limit: Limitar número de resultados (opcional).
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT h.*, p.nome as paciente_nome, p.quarto as paciente_quarto
                FROM historico_solicitacoes h
                LEFT JOIN pacientes p ON h.paciente_id = p.id
                WHERE 1=1
            """
            params = []
            
            if paciente_id:
                query += " AND h.paciente_id = ?"
                params.append(paciente_id)
            
            if status:
                query += " AND h.status = ?"
                params.append(status)
            
            query += " ORDER BY h.data_solicitacao DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def atualizar_status_solicitacao(self, solicitacao_id: int, 
                                     status: str, observacoes: Optional[str] = None) -> bool:
        """Atualiza o status de uma solicitação."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            data_resolucao = datetime.now().isoformat() if status == 'resolvido' else None
            
            cursor.execute("""
                UPDATE historico_solicitacoes
                SET status = ?, data_resolucao = ?, observacoes = ?
                WHERE id = ?
            """, (status, data_resolucao, observacoes, solicitacao_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao atualizar status: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def obter_estatisticas_paciente(self, paciente_id: int) -> Dict[str, Any]:
        """Obtém estatísticas de solicitações de um paciente."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Total de solicitações
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM historico_solicitacoes
                WHERE paciente_id = ?
            """, (paciente_id,))
            total = cursor.fetchone()['total']
            
            # Pendentes
            cursor.execute("""
                SELECT COUNT(*) as pendentes
                FROM historico_solicitacoes
                WHERE paciente_id = ? AND status = 'pendente'
            """, (paciente_id,))
            pendentes = cursor.fetchone()['pendentes']
            
            # Resolvidas
            cursor.execute("""
                SELECT COUNT(*) as resolvidas
                FROM historico_solicitacoes
                WHERE paciente_id = ? AND status = 'resolvido'
            """, (paciente_id,))
            resolvidas = cursor.fetchone()['resolvidas']
            
            return {
                'total': total,
                'pendentes': pendentes,
                'resolvidas': resolvidas
            }
        finally:
            conn.close()
    
    # ========== MÉTODOS PARA CONFIGURAÇÃO DE GESTOS SIMPLIFICADOS ==========
    
    def obter_config_gesto(self, num_dedos: int) -> Optional[Dict[str, Any]]:
        """Obtém configuração de gesto por número de dedos (1-4)."""
        if num_dedos not in [1, 2, 3, 4]:
            return None
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM config_gestos WHERE num_dedos = ? AND ativo = 1", (num_dedos,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def listar_config_gestos(self) -> List[Dict[str, Any]]:
        """Lista todas as configurações de gestos."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM config_gestos ORDER BY num_dedos")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def salvar_config_gesto(self, num_dedos: int, mensagem: str, prioridade: str = 'normal') -> bool:
        """
        Salva ou atualiza configuração de gesto.
        
        Args:
            num_dedos: Número de dedos (1-4).
            mensagem: Mensagem associada ao gesto.
            prioridade: Prioridade da mensagem ('baixa', 'normal', 'alta', 'urgente').
        """
        if num_dedos not in [1, 2, 3, 4]:
            return False
        
        if prioridade not in ['baixa', 'normal', 'alta', 'urgente']:
            prioridade = 'normal'
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO config_gestos (num_dedos, mensagem, prioridade, ativo)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(num_dedos) DO UPDATE SET
                    mensagem = excluded.mensagem,
                    prioridade = excluded.prioridade,
                    data_atualizacao = CURRENT_TIMESTAMP,
                    ativo = 1
            """, (num_dedos, mensagem, prioridade))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao salvar configuração de gesto: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def obter_mensagem_por_num_dedos(self, num_dedos: int) -> Optional[str]:
        """Obtém mensagem associada a um número de dedos."""
        config = self.obter_config_gesto(num_dedos)
        if config:
            return config['mensagem']
        return None

