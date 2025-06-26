#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/database_brk.py
💾 ONDE SALVAR: brk-monitor-seguro/processor/database_brk.py
📦 FUNÇÃO: Database BRK com SQLite + OneDrive organizado
🔧 DESCRIÇÃO: Sistema de controle de faturas com lógica SEEK
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua

🚨 DEPENDÊNCIAS OBRIGATÓRIAS:
   ✅ auth/microsoft_auth.py - Autenticação Microsoft
   ✅ SQLite (built-in Python)
   ✅ requests - HTTP requests para OneDrive
"""

import sqlite3
import os
import re
import requests
import hashlib
from datetime import datetime
from pathlib import Path


class DatabaseBRK:
    """
    Database BRK com SQLite + OneDrive organizado.
    
    MVP: Inicialização básica + salvamento simples
    """
    
    def __init__(self, auth_manager, onedrive_brk_id):
        """
        Inicializar DatabaseBRK básico.
        
        Args:
            auth_manager: Instância de MicrosoftAuth
            onedrive_brk_id: ID da pasta /BRK/ no OneDrive
        """
        self.auth = auth_manager
        self.onedrive_brk_id = onedrive_brk_id
        
        # Database SQLite no OneDrive (conforme sua observação)
        self.db_path = '/opt/render/project/storage/database_brk.db'
        self.conn = None
        
        # Cache básico
        self.relacionamento_cdc = {}
        
        print(f"🗃️ DatabaseBRK inicializado:")
        print(f"   📁 OneDrive: {onedrive_brk_id[:15]}******")
        print(f"   💾 Database: database_brk.db")
        
        # Inicializar estruturas básicas
        self._inicializar_database()
    
    def _inicializar_database(self):
        """
        Inicializa database SQLite com estrutura mínima.
        MVP: Apenas criar tabela se não existir.
        """
        try:
            # Garantir que diretório existe
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Conectar SQLite
            self.conn = sqlite3.connect(self.db_path)
            
            # Criar tabela básica
            self._criar_tabela_faturas()
            
            print(f"✅ Database inicializado: {self.db_path}")
            
        except Exception as e:
            print(f"❌ Erro inicializando database: {e}")
            raise
    
    def _criar_tabela_faturas(self):
        """
        Cria tabela faturas_brk com estrutura mínima funcional.
        """
        sql_create = """
        CREATE TABLE IF NOT EXISTS faturas_brk (
            -- CAMPOS DE CONTROLE
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_processamento DATETIME DEFAULT CURRENT_TIMESTAMP,
            status_duplicata TEXT DEFAULT 'NORMAL',
            observacao TEXT DEFAULT '',
            
            -- DADOS DO EMAIL
            email_id TEXT NOT NULL,
            nome_arquivo_original TEXT NOT NULL,
            nome_arquivo TEXT NOT NULL,
            hash_arquivo TEXT UNIQUE,
            
            -- DADOS EXTRAÍDOS DA FATURA
            cdc TEXT,
            nota_fiscal TEXT,
            casa_oracao TEXT,
            data_emissao TEXT,
            vencimento TEXT,
            competencia TEXT,
            valor TEXT,
            
            -- CONTROLE TÉCNICO
            dados_extraidos_ok BOOLEAN DEFAULT TRUE,
            relacionamento_usado BOOLEAN DEFAULT FALSE
        );
        """
        
        self.conn.execute(sql_create)
        
        # Índice básico para SEEK
        self.conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_cdc_competencia 
        ON faturas_brk(cdc, competencia)
        """)
        
        self.conn.commit()
        print(f"✅ Tabela faturas_brk criada")
    
    def salvar_fatura(self, dados_fatura):
        """
        Salva fatura no database com lógica básica.
        MVP: Salvar sem duplicar, retornar sucesso/erro.
        
        Args:
            dados_fatura (dict): Dados extraídos pelo EmailProcessor
            
        Returns:
            dict: {'status': 'sucesso/erro', 'mensagem': '...', 'id_salvo': int}
        """
        try:
            print(f"💾 Salvando fatura: {dados_fatura.get('nome_arquivo_original', 'unknown')}")
            
            # 1. Verificar se já existe (SEEK básico)
            status_duplicata = self._verificar_duplicata_simples(dados_fatura)
            
            # 2. Gerar nome padronizado
            nome_padronizado = self._gerar_nome_padronizado(dados_fatura)
            
            # 3. Inserir no SQLite
            id_salvo = self._inserir_fatura_sqlite(dados_fatura, status_duplicata, nome_padronizado)
            
            # 4. Retornar resultado
            return {
                'status': 'sucesso',
                'mensagem': f'Fatura salva - Status: {status_duplicata}',
                'id_salvo': id_salvo,
                'status_duplicata': status_duplicata,
                'nome_arquivo': nome_padronizado
            }
            
        except Exception as e:
            print(f"❌ Erro salvando fatura: {e}")
            return {
                'status': 'erro', 
                'mensagem': str(e),
                'id_salvo': None
            }
    
    def _verificar_duplicata_simples(self, dados_fatura):
        """
        Verifica duplicata básica: CDC + Competência.
        MVP: Lógica SEEK simples.
        """
        try:
            cdc = dados_fatura.get('cdc')
            competencia = dados_fatura.get('competencia')
            
            if not cdc or not competencia:
                return 'NORMAL'
            
            # SEEK: buscar registro existente
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM faturas_brk 
                WHERE cdc = ? AND competencia = ?
            """, (cdc, competencia))
            
            count = cursor.fetchone()[0]
            
            if count == 0:
                return 'NORMAL'  # Primeira vez
            else:
                return 'DUPLICATA'  # Já existe
                
        except Exception as e:
            print(f"⚠️ Erro verificando duplicata: {e}")
            return 'NORMAL'  # Default seguro
    
    def _gerar_nome_padronizado(self, dados_fatura):
        """
        Gera nome arquivo padronizado estilo renomeia_brk10.py.
        MVP: Formato básico funcional.
        """
        try:
            # Extrair dados
            casa_oracao = dados_fatura.get('casa_oracao', 'Casa Desconhecida')
            vencimento = dados_fatura.get('vencimento', '')
            valor = dados_fatura.get('valor', 'Valor Desconhecido')
            competencia = dados_fatura.get('competencia', '')
            
            # Processar vencimento
            if re.match(r'\d{2}/\d{2}/\d{4}', vencimento):
                partes = vencimento.split('/')
                dia, mes, ano = partes[0], partes[1], partes[2]
                data_venc = f"{dia}-{mes}"
                data_venc_full = f"{dia}-{mes}-{ano}"
                mes_ano = f"{mes}-{ano}"
            else:
                # Fallback para competência ou data atual
                hoje = datetime.now()
                data_venc = hoje.strftime('%d-%m')
                data_venc_full = hoje.strftime('%d-%m-%Y')
                mes_ano = hoje.strftime('%m-%Y')
            
            # Limpar nome da casa
            casa_limpa = re.sub(r'[<>:"/\\|?*]', '-', casa_oracao)
            
            # Gerar nome padrão
            nome = f"{data_venc}-BRK {mes_ano} - {casa_limpa} - vc. {data_venc_full} - {valor}.pdf"
            
            return nome
            
        except Exception as e:
            print(f"❌ Erro gerando nome: {e}")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"BRK_Erro_{timestamp}.pdf"
    
    def _inserir_fatura_sqlite(self, dados_fatura, status_duplicata, nome_padronizado):
        """
        Insere fatura no SQLite e retorna ID.
        """
        try:
            cursor = self.conn.cursor()
            
            sql_insert = """
            INSERT INTO faturas_brk (
                email_id, nome_arquivo_original, nome_arquivo, hash_arquivo,
                cdc, nota_fiscal, casa_oracao, data_emissao, vencimento, 
                competencia, valor, dados_extraidos_ok, relacionamento_usado,
                status_duplicata, observacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            valores = (
                dados_fatura.get('email_id'),
                dados_fatura.get('nome_arquivo_original'),
                nome_padronizado,
                dados_fatura.get('hash_arquivo'),
                dados_fatura.get('cdc'),
                dados_fatura.get('nota_fiscal'),
                dados_fatura.get('casa_oracao'),
                dados_fatura.get('data_emissao'),
                dados_fatura.get('vencimento'),
                dados_fatura.get('competencia'),
                dados_fatura.get('valor'),
                dados_fatura.get('dados_extraidos_ok', True),
                dados_fatura.get('relacionamento_usado', False),
                status_duplicata,
                f'Processado automaticamente - Status: {status_duplicata}'
            )
            
            cursor.execute(sql_insert, valores)
            self.conn.commit()
            
            id_inserido = cursor.lastrowid
            print(f"✅ Fatura salva - ID: {id_inserido} - Status: {status_duplicata}")
            
            return id_inserido
            
        except Exception as e:
            print(f"❌ Erro inserindo SQLite: {e}")
            return None
    
    def _extrair_ano_mes(self, competencia, vencimento):
        """
        Extrai ano e mês para organização OneDrive.
        MVP: Lógica simples que sempre funciona.
        
        Args:
            competencia (str): Competência da fatura
            vencimento (str): Data de vencimento
            
        Returns:
            tuple: (ano, mes) como inteiros
        """
        try:
            # OPÇÃO 1: Usar vencimento se válido
            if vencimento and re.match(r'\d{2}/\d{2}/\d{4}', vencimento):
                partes = vencimento.split('/')
                dia, mes, ano = partes[0], int(partes[1]), int(partes[2])
                print(f"📅 Pasta por VENCIMENTO: {vencimento} → /{ano}/{mes:02d}/")
                return ano, mes
            
            # OPÇÃO 2: Usar competência se válida  
            if competencia and '/' in competencia:
                try:
                    if re.match(r'\d{2}/\d{4}', competencia):
                        mes, ano = competencia.split('/')
                        mes, ano = int(mes), int(ano)
                        print(f"📅 Pasta por COMPETÊNCIA: {competencia} → /{ano}/{mes:02d}/")
                        return ano, mes
                except:
                    pass
            
            # OPÇÃO 3: Fallback para data atual
            hoje = datetime.now()
            print(f"📅 Pasta por DATA ATUAL: {hoje.year}/{hoje.month:02d} (fallback)")
            return hoje.year, hoje.month
            
        except Exception as e:
            print(f"❌ Erro extraindo ano/mês: {e}")
            # Fallback final garantido
            hoje = datetime.now()
            return hoje.year, hoje.month
    
    def obter_estatisticas(self):
        """
        Retorna estatísticas básicas do database.
        MVP: Contadores simples.
        
        Returns:
            dict: Estatísticas do sistema
        """
        try:
            cursor = self.conn.cursor()
            
            # Total de faturas
            cursor.execute("SELECT COUNT(*) FROM faturas_brk")
            total = cursor.fetchone()[0]
            
            # Por status
            cursor.execute("""
                SELECT status_duplicata, COUNT(*) 
                FROM faturas_brk 
                GROUP BY status_duplicata
            """)
            por_status = dict(cursor.fetchall())
            
            # Últimas 30 dias
            cursor.execute("""
                SELECT COUNT(*) FROM faturas_brk 
                WHERE data_processamento >= datetime('now', '-30 days')
            """)
            ultimos_30_dias = cursor.fetchone()[0]
            
            return {
                'total_faturas': total,
                'por_status': por_status,
                'ultimos_30_dias': ultimos_30_dias,
                'database_ativo': True,
                'db_path': self.db_path
            }
            
        except Exception as e:
            print(f"❌ Erro obtendo estatísticas: {e}")
            return {
                'erro': str(e),
                'database_ativo': False
            }
    
    def buscar_faturas(self, filtros=None):
        """
        Busca faturas com filtros opcionais.
        MVP: Busca simples.
        
        Args:
            filtros (dict): Filtros opcionais
            
        Returns:
            list: Lista de faturas
        """
        try:
            cursor = self.conn.cursor()
            
            if not filtros:
                cursor.execute("""
                    SELECT * FROM faturas_brk 
                    ORDER BY data_processamento DESC 
                    LIMIT 100
                """)
            else:
                # Implementar filtros básicos conforme necessário
                cursor.execute("""
                    SELECT * FROM faturas_brk 
                    ORDER BY data_processamento DESC 
                    LIMIT 100
                """)
            
            return cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Erro buscando faturas: {e}")
            return []
    
    def fechar_conexao(self):
        """
        Fecha conexão SQLite de forma segura.
        """
        try:
            if self.conn:
                self.conn.close()
                print(f"✅ Conexão SQLite fechada")
        except Exception as e:
            print(f"⚠️ Erro fechando conexão: {e}")
    
    def __del__(self):
        """
        Destructor para garantir fechamento da conexão.
        """
        self.fechar_conexao()


# ============================================================================
# FUNÇÕES DE UTILIDADE
# ============================================================================

def criar_database_brk(auth_manager, onedrive_brk_id):
    """
    Factory function para criar DatabaseBRK.
    
    Args:
        auth_manager: Instância de MicrosoftAuth
        onedrive_brk_id: ID da pasta BRK no OneDrive
        
    Returns:
        DatabaseBRK: Instância configurada
    """
    try:
        db = DatabaseBRK(auth_manager, onedrive_brk_id)
        print(f"✅ DatabaseBRK criado com sucesso")
        return db
    except Exception as e:
        print(f"❌ Erro criando DatabaseBRK: {e}")
        return None
