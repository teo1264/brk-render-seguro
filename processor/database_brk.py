#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗃️ DATABASE BRK - CORREÇÃO SYNTAX ERROR
📁 ARQUIVO: processor/database_brk.py - BLOCO 1/5
🎯 CORREÇÃO URGENTE: Sintaxe corrigida + singleton otimizado
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
"""

import sqlite3
import os
import re
import requests
import hashlib
import tempfile
import gc
from datetime import datetime
from pathlib import Path

# ✅ CORREÇÃO: Threading seguro
try:
    import threading
    THREADING_AVAILABLE = True
except ImportError:
    THREADING_AVAILABLE = False
    print("⚠️ Threading não disponível - singleton sem lock")


class DatabaseBRK:
    """
    DatabaseBRK com correção definitiva memory overflow.
    """
    
    # ✅ SINGLETON REAL
    _instance = None
    _lock = threading.Lock() if THREADING_AVAILABLE else None
    
    def __new__(cls, auth_manager, onedrive_brk_id):
        """Singleton REAL para evitar múltiplas instâncias."""
        if cls._lock:
            with cls._lock:
                if cls._instance is None:
                    print(f"🗃️ Criando DatabaseBRK SINGLETON (memory optimized)")
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
                else:
                    print(f"♻️ Reutilizando DatabaseBRK singleton (memory save)")
                return cls._instance
        else:
            if cls._instance is None:
                print(f"🗃️ Criando DatabaseBRK singleton (no threading)")
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            else:
                print(f"♻️ Reutilizando DatabaseBRK singleton")
            return cls._instance
    
    def __init__(self, auth_manager, onedrive_brk_id):
        """Inicialização singleton-safe."""
        if hasattr(self, '_initialized') and self._initialized:
            print(f"⚠️ DatabaseBRK já inicializado - reutilizando configuração existente")
            return
            
        self.auth = auth_manager
        self.onedrive_brk_id = onedrive_brk_id
        
        # Configurações database
        self.db_filename = "database_brk.db"
        self.db_onedrive_id = None
        self.db_local_cache = None
        self.db_fallback_render = '/opt/render/project/storage/database_brk.db'
        
        # Conexão SQLite
        self.conn = None
        self.usando_onedrive = False
        self.usando_fallback = False
        
        # ✅ CORREÇÃO: Controle de sync otimizado
        self._last_sync_time = 0
        self._sync_interval = 3600  # 1 hora entre syncs
        
        print(f"🗃️ DatabaseBRK SINGLETON inicializado (Render optimized)")
        
        # Inicializar database no OneDrive
        self._inicializar_database_sistema()
        
        # ✅ MARCAR COMO INICIALIZADO
        self._initialized = True

def _inicializar_database_sistema(self):
        """Inicializa sistema: OneDrive → cache local → fallback."""
        try:
            print(f"📊 Inicializando database sistema (Render optimized)...")
            
            # ETAPA 1: Verificar se database existe no OneDrive
            database_existe = self._verificar_database_onedrive()
            
            if database_existe:
                print(f"✅ Database encontrado no OneDrive")
                if self._baixar_database_para_cache():
                    self.usando_onedrive = True
                    print(f"📥 Database sincronizado para cache otimizado")
                else:
                    raise Exception("Falha baixando database do OneDrive")
            else:
                print(f"🆕 Database não existe - criando novo no OneDrive")
                if self._criar_database_novo():
                    self.usando_onedrive = True
                    print(f"📤 Database criado e enviado para OneDrive")
                else:
                    raise Exception("Falha criando database no OneDrive")
            
            # ETAPA 2: Conectar SQLite no cache local
            self._conectar_sqlite_cache()
            
        except Exception as e:
            print(f"⚠️ Erro OneDrive: {e}")
            print(f"🔄 Usando fallback Render disk...")
            self._usar_fallback_render()
    
    def _verificar_database_onedrive(self):
        """Verifica se database_brk.db existe na pasta /BRK/ do OneDrive."""
        try:
            headers = self.auth.obter_headers_autenticados()
            if not headers:
                return False
            
            # Buscar arquivos na pasta /BRK/
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{self.onedrive_brk_id}/children"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                arquivos = response.json().get('value', [])
                
                # Procurar database_brk.db
                for arquivo in arquivos:
                    if arquivo.get('name') == self.db_filename:
                        self.db_onedrive_id = arquivo['id']
                        print(f"📊 Database OneDrive encontrado: {arquivo['name']}")
                        return True
                
                print(f"📊 Database não encontrado no OneDrive /BRK/")
                return False
            else:
                print(f"❌ Erro acessando OneDrive: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro verificando OneDrive: {e}")
            return False
    
    def _baixar_database_para_cache(self):
        """Baixa database do OneDrive para cache local temporário."""
        try:
            if not self.db_onedrive_id:
                raise ValueError("ID do database OneDrive não encontrado")
            
            headers = self.auth.obter_headers_autenticados()
            if not headers:
                raise ValueError("Headers de autenticação não disponíveis")
            
            # Download do arquivo
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{self.db_onedrive_id}/content"
            response = requests.get(url, headers=headers, timeout=60)
            
            if response.status_code == 200:
                # ✅ OTIMIZAÇÃO: Cache mais eficiente
                with tempfile.NamedTemporaryFile(delete=False, suffix='.db', prefix='brk_cache_') as tmp_file:
                    tmp_file.write(response.content)
                    self.db_local_cache = tmp_file.name
                
                print(f"📥 Database baixado para cache: {os.path.basename(self.db_local_cache)}")
                return True
            else:
                raise Exception(f"Erro download: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro baixando database: {e}")
            return False

def _criar_database_novo(self):
        """Cria database SQLite novo e faz upload para OneDrive."""
        try:
            print(f"🆕 Criando database SQLite novo...")
            
            # ETAPA 1: Criar cache local temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db', prefix='brk_new_') as tmp_file:
                self.db_local_cache = tmp_file.name
            
            # ETAPA 2: Criar estrutura SQLite
            conn_temp = sqlite3.connect(self.db_local_cache, check_same_thread=False)
            conn_temp.execute("PRAGMA journal_mode=WAL")
            self._criar_estrutura_sqlite(conn_temp)
            conn_temp.close()
            
            # ETAPA 3: Upload para OneDrive
            if self._upload_database_onedrive():
                print(f"✅ Database novo criado e enviado para OneDrive")
                return True
            else:
                raise Exception("Falha no upload para OneDrive")
                
        except Exception as e:
            print(f"❌ Erro criando database novo: {e}")
            return False
    
    def _criar_estrutura_sqlite(self, conn):
        """Cria estrutura SQLite com tabelas e índices."""
        sql_create = """
        CREATE TABLE IF NOT EXISTS faturas_brk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_processamento DATETIME DEFAULT CURRENT_TIMESTAMP,
            status_duplicata TEXT DEFAULT 'NORMAL',
            observacao TEXT DEFAULT '',
            
            email_id TEXT NOT NULL,
            nome_arquivo_original TEXT NOT NULL,
            nome_arquivo TEXT NOT NULL,
            hash_arquivo TEXT UNIQUE,
            
            cdc TEXT,
            nota_fiscal TEXT,
            casa_oracao TEXT,
            data_emissao TEXT,
            vencimento TEXT,
            competencia TEXT,
            valor TEXT,
            
            medido_real INTEGER,
            faturado INTEGER,
            media_6m INTEGER,
            porcentagem_consumo TEXT,
            alerta_consumo TEXT,
            
            dados_extraidos_ok BOOLEAN DEFAULT TRUE,
            relacionamento_usado BOOLEAN DEFAULT FALSE
        );
        
        CREATE INDEX IF NOT EXISTS idx_cdc_competencia ON faturas_brk(cdc, competencia);
        CREATE INDEX IF NOT EXISTS idx_status_duplicata ON faturas_brk(status_duplicata);
        CREATE INDEX IF NOT EXISTS idx_casa_oracao ON faturas_brk(casa_oracao);
        CREATE INDEX IF NOT EXISTS idx_data_processamento ON faturas_brk(data_processamento);
        CREATE INDEX IF NOT EXISTS idx_competencia ON faturas_brk(competencia);
        """
        
        conn.executescript(sql_create)
        conn.commit()
        print(f"✅ Estrutura SQLite criada (tabelas + índices)")
    
    def _conectar_sqlite_cache(self):
        """Conecta SQLite usando cache local."""
        try:
            if not self.db_local_cache or not os.path.exists(self.db_local_cache):
                raise ValueError("Cache local não disponível")
            
            self.conn = sqlite3.connect(self.db_local_cache, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL")
            print(f"✅ SQLite conectado via cache local")
            
        except Exception as e:
            print(f"❌ Erro conectando cache: {e}")
            raise
    
    def _usar_fallback_render(self):
        """Fallback: usar database no Render disk se OneDrive falhar."""
        try:
            print(f"🔄 Iniciando fallback Render disk...")
            
            # Garantir que diretório existe
            os.makedirs(os.path.dirname(self.db_fallback_render), exist_ok=True)
            
            # Conectar SQLite no Render
            self.conn = sqlite3.connect(self.db_fallback_render, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL")
            
            # Criar estrutura se não existir
            self._criar_estrutura_sqlite(self.conn)
            
            self.usando_fallback = True
            self.usando_onedrive = False
            self.db_local_cache = self.db_fallback_render
            
            print(f"✅ Fallback ativo: {self.db_fallback_render}")
            print(f"⚠️ ATENÇÃO: Dados no Render disk - sem backup OneDrive")
            
        except Exception as e:
            print(f"❌ Erro crítico no fallback: {e}")
            raise

def sincronizar_onedrive(self):
        """🔧 CORREÇÃO PRINCIPAL: Sincronização SIMPLES - sem backup reativo."""
        try:
            if not self.usando_onedrive:
                print(f"⚠️ Sincronização ignorada - usando fallback Render")
                return False
            
            if not self.db_local_cache or not os.path.exists(self.db_local_cache):
                print(f"⚠️ Cache local não disponível para sincronização")
                return False
            
            # ✅ CORREÇÃO: Sync controlado por tempo (não reativo)
            import time
            agora = time.time()
            if agora - self._last_sync_time < self._sync_interval:
                print(f"⏸️ Sync em cooldown - última sync há {int((agora - self._last_sync_time)/60)}min")
                return True  # Considera sucesso para não bloquear operações
            
            # Fechar conexão temporariamente para sync
            if self.conn:
                self.conn.close()
            
            # ✅ UPLOAD SIMPLES (removido backup preventivo reativo)
            sucesso = self._upload_database_onedrive()
            
            # Reconectar
            self.conn = sqlite3.connect(self.db_local_cache, check_same_thread=False)
            
            if sucesso:
                self._last_sync_time = agora
                print(f"🔄 Database sincronizado com OneDrive")
                return True
            else:
                print(f"⚠️ Falha na sincronização OneDrive")
                return False
                
        except Exception as e:
            print(f"❌ Erro sincronização: {e}")
            try:
                if self.db_local_cache:
                    self.conn = sqlite3.connect(self.db_local_cache, check_same_thread=False)
            except:
                pass
            return False
    
    def _upload_database_onedrive(self):
        """Faz upload do database local para OneDrive /BRK/."""
        try:
            if not self.db_local_cache or not os.path.exists(self.db_local_cache):
                raise ValueError("Cache local não encontrado para upload")
            
            headers = self.auth.obter_headers_autenticados()
            if not headers:
                raise ValueError("Headers de autenticação não disponíveis")
            
            # Ler database local
            with open(self.db_local_cache, 'rb') as f:
                db_content = f.read()
            
            # Upload para OneDrive
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{self.onedrive_brk_id}:/{self.db_filename}:/content"
            headers['Content-Type'] = 'application/octet-stream'
            
            response = requests.put(url, headers=headers, data=db_content, timeout=120)
            
            if response.status_code in [200, 201]:
                file_info = response.json()
                self.db_onedrive_id = file_info['id']
                print(f"📤 Database uploaded: {file_info['name']} ({len(db_content)} bytes)")
                return True
            else:
                raise Exception(f"Erro upload: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro upload OneDrive: {e}")
            return False

    def salvar_fatura(self, dados_fatura):
        """MÉTODO PRINCIPAL: Salva fatura com lógica SEEK + sincronização otimizada."""
        try:
            print(f"💾 Salvando fatura: {dados_fatura.get('nome_arquivo_original', 'unknown')}")
            
            # 1. LÓGICA SEEK (estilo Clipper)
            status_duplicata = self._verificar_duplicata_seek(dados_fatura)
            
            # 2. Gerar nome padronizado
            nome_padronizado = self._gerar_nome_padronizado(dados_fatura)
            
            # 3. Inserir no SQLite
            id_salvo = self._inserir_fatura_sqlite(dados_fatura, status_duplicata, nome_padronizado)
            
            # 4. Integração alertas (opcional)
            try:
                from processor.alertas.alert_processor import processar_alerta_fatura
                processar_alerta_fatura(dados_fatura)
            except ImportError:
                pass  # Alertas opcionais
            
            # 5. ✅ CORREÇÃO: Sincronizar com OneDrive (versão otimizada)
            self.sincronizar_onedrive()
            
            # 6. ✅ CORREÇÃO: Memory cleanup
            self._cleanup_memory_light()
            
            # 7. Retornar resultado
            return {
                'status': 'sucesso',
                'mensagem': f'Fatura salva - Status: {status_duplicata}',
                'id_salvo': id_salvo,
                'status_duplicata': status_duplicata,
                'nome_arquivo': nome_padronizado,
                'usando_onedrive': self.usando_onedrive
            }
            
        except Exception as e:
            print(f"❌ Erro salvando fatura: {e}")
            return {
                'status': 'erro', 
                'mensagem': str(e),
                'id_salvo': None
            }
    
    def _verificar_duplicata_seek(self, dados_fatura):
        """Lógica SEEK estilo Clipper: CDC + Competência."""
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
                print(f"🔍 SEEK: CDC {cdc} + {competencia} → NOT FOUND() → STATUS: NORMAL")
                return 'NORMAL'
            else:
                print(f"🔍 SEEK: CDC {cdc} + {competencia} → FOUND() → STATUS: DUPLICATA")
                return 'DUPLICATA'
                
        except Exception as e:
            print(f"⚠️ Erro SEEK: {e}")
            return 'NORMAL'

def _gerar_nome_padronizado(self, dados_fatura):
        """Gera nome arquivo padronizado estilo renomeia_brk10.py."""
        try:
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
                ano, mes = self._extrair_ano_mes(competencia, vencimento)
                hoje = datetime.now()
                data_venc = hoje.strftime('%d-%m')
                data_venc_full = hoje.strftime('%d-%m-%Y')
                mes_ano = f"{mes:02d}-{ano}"
            
            casa_limpa = re.sub(r'[<>:"/\\|?*]', '-', casa_oracao)
            nome = f"{data_venc}-BRK {mes_ano} - {casa_limpa} - vc. {data_venc_full} - {valor}.pdf"
            
            print(f"📁 Nome padronizado: {nome}")
            return nome
            
        except Exception as e:
            print(f"❌ Erro gerando nome: {e}")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"BRK_Erro_{timestamp}.pdf"
    
    def _extrair_ano_mes(self, competencia, vencimento):
        """Extrai ano e mês para organização OneDrive."""
        try:
            if vencimento and re.match(r'\d{2}/\d{2}/\d{4}', vencimento):
                partes = vencimento.split('/')
                dia, mes, ano = partes[0], int(partes[1]), int(partes[2])
                return ano, mes
            
            if competencia and '/' in competencia:
                try:
                    if re.match(r'\d{2}/\d{4}', competencia):
                        mes, ano = competencia.split('/')
                        mes, ano = int(mes), int(ano)
                        return ano, mes
                except:
                    pass
            
            hoje = datetime.now()
            return hoje.year, hoje.month
            
        except Exception as e:
            print(f"❌ Erro extraindo ano/mês: {e}")
            hoje = datetime.now()
            return hoje.year, hoje.month

    def _inserir_fatura_sqlite(self, dados_fatura, status_duplicata, nome_padronizado):
        """Insere fatura no SQLite e retorna ID."""
        try:
            cursor = self.conn.cursor()
            
            sql_insert = """
            INSERT INTO faturas_brk (
                email_id, nome_arquivo_original, nome_arquivo, hash_arquivo,
                cdc, nota_fiscal, casa_oracao, data_emissao, vencimento, 
                competencia, valor, medido_real, faturado, media_6m,
                porcentagem_consumo, alerta_consumo, dados_extraidos_ok, 
                relacionamento_usado, status_duplicata, observacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                dados_fatura.get('medido_real'),
                dados_fatura.get('faturado'),
                dados_fatura.get('media_6m'),
                dados_fatura.get('porcentagem_consumo'),
                dados_fatura.get('alerta_consumo'),
                dados_fatura.get('dados_extraidos_ok', True),
                dados_fatura.get('relacionamento_usado', False),
                status_duplicata,
                f'Processado via {"OneDrive" if self.usando_onedrive else "Fallback"} - Status: {status_duplicata}'
            )
            
            cursor.execute(sql_insert, valores)
            self.conn.commit()
            
            id_inserido = cursor.lastrowid
            print(f"✅ Fatura salva - ID: {id_inserido} - Status: {status_duplicata}")
            
            return id_inserido
            
        except Exception as e:
            print(f"❌ Erro inserindo SQLite: {e}")
            return None

    def obter_meses_com_faturas(self):
        """Detecta todos os meses/anos que possuem faturas no database."""
        try:
            if not self.conn:
                return []
            
            cursor = self.conn.cursor()
            query = """
                SELECT DISTINCT vencimento, competencia 
                FROM faturas_brk 
                WHERE status_duplicata = 'NORMAL'
                AND (vencimento IS NOT NULL OR competencia IS NOT NULL)
                ORDER BY vencimento, competencia
            """
            
            cursor.execute(query)
            resultados = cursor.fetchall()
            
            meses_encontrados = set()
            
            for row in resultados:
                vencimento = row[0] if row[0] else ""
                competencia = row[1] if row[1] else ""
                
                if vencimento and "/" in vencimento:
                    try:
                        partes = vencimento.split("/")
                        if len(partes) == 3:
                            mes_venc = int(partes[1])
                            ano_venc = int(partes[2])
                            if 1 <= mes_venc <= 12 and 2020 <= ano_venc <= 2030:
                                meses_encontrados.add((mes_venc, ano_venc))
                    except (ValueError, IndexError):
                        pass
                
                if competencia and "/" in competencia:
                    try:
                        if any(mes_nome in competencia for mes_nome in ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']):
                            meses_nomes = {
                                'Janeiro': 1, 'Jan': 1, 'Fevereiro': 2, 'Fev': 2,
                                'Março': 3, 'Mar': 3, 'Abril': 4, 'Abr': 4,
                                'Maio': 5, 'Mai': 5, 'Junho': 6, 'Jun': 6,
                                'Julho': 7, 'Jul': 7, 'Agosto': 8, 'Ago': 8,
                                'Setembro': 9, 'Set': 9, 'Outubro': 10, 'Out': 10,
                                'Novembro': 11, 'Nov': 11, 'Dezembro': 12, 'Dez': 12
                            }
                            
                            partes = competencia.split("/")
                            if len(partes) == 2:
                                mes_nome = partes[0].strip()
                                ano_comp = int(partes[1].strip())
                                
                                for nome, numero in meses_nomes.items():
                                    if nome.lower() in mes_nome.lower():
                                        if 2020 <= ano_comp <= 2030:
                                            meses_encontrados.add((numero, ano_comp))
                                        break
                        else:
                            partes = competencia.split("/")
                            if len(partes) == 2:
                                mes_comp = int(partes[0])
                                ano_comp = int(partes[1])
                                if 1 <= mes_comp <= 12 and 2020 <= ano_comp <= 2030:
                                    meses_encontrados.add((mes_comp, ano_comp))
                                    
                    except (ValueError, IndexError):
                        pass
            
            meses_lista = sorted(list(meses_encontrados))
            print(f"✅ {len(meses_lista)} mês(es) detectado(s) para planilhas")
            return meses_lista
            
        except Exception as e:
            print(f"❌ Erro detectando meses com faturas: {e}")
            return []

    def obter_estatisticas(self):
        """Retorna estatísticas do database."""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM faturas_brk")
            total = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT status_duplicata, COUNT(*) 
                FROM faturas_brk 
                GROUP BY status_duplicata
            """)
            por_status = dict(cursor.fetchall())
            
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
                'usando_onedrive': self.usando_onedrive,
                'usando_fallback': self.usando_fallback,
                'render_optimized': True,
                'singleton_active': True
            }
            
        except Exception as e:
            print(f"❌ Erro obtendo estatísticas: {e}")
            return {'erro': str(e), 'database_ativo': False}
    
    def get_connection(self):
        """Retorna conexão SQLite."""
        return self.conn
    
    def _cleanup_memory_light(self):
        """Memory cleanup leve após operações."""
        try:
            collected = gc.collect()
            if collected > 0:
                print(f"🧹 Memory cleanup: {collected} objetos coletados")
        except Exception:
            pass

    def fechar_conexao(self):
        """Fecha conexão e limpa cache com memory cleanup."""
        try:
            print(f"🔄 Fechando DatabaseBRK singleton...")
            
            if self.usando_onedrive and self.conn:
                try:
                    self.sincronizar_onedrive()
                except Exception as e:
                    print(f"⚠️ Sync final falhou: {e}")
            
            if self.conn:
                self.conn.close()
                self.conn = None
                print(f"✅ Conexão SQLite fechada")
            
            if (self.db_local_cache and 
                self.db_local_cache != self.db_fallback_render and
                os.path.exists(self.db_local_cache)):
                try:
                    os.unlink(self.db_local_cache)
                    print(f"🗑️ Cache temporário removido")
                except Exception as e:
                    print(f"⚠️ Cache não pôde ser removido: {e}")
            
            collected = gc.collect()
            print(f"🧹 Memory cleanup final: {collected} objetos")
            print(f"✅ DatabaseBRK singleton fechado")
                    
        except Exception as e:
            print(f"⚠️ Erro fechando conexão: {e}")


# ============================================================================
# FUNÇÕES DE UTILIDADE
# ============================================================================

def criar_database_brk(auth_manager, onedrive_brk_id):
    """Factory function para criar DatabaseBRK otimizado."""
    try:
        db = DatabaseBRK(auth_manager, onedrive_brk_id)
        print(f"✅ DatabaseBRK singleton obtido - OneDrive: {db.usando_onedrive}")
        return db
    except Exception as e:
        print(f"❌ Erro criando DatabaseBRK singleton: {e}")
        return None

def integrar_database_emailprocessor(email_processor):
    """Função de compatibilidade com EmailProcessor."""
    try:
        if hasattr(email_processor, 'database_brk') and email_processor.database_brk:
            print(f"✅ DatabaseBRK já integrado ao EmailProcessor (singleton)")
            return True
        
        db_brk = DatabaseBRK(
            email_processor.auth, 
            email_processor.onedrive_brk_id
        )
        
        email_processor.database_brk = db_brk
        print(f"✅ DatabaseBRK singleton integrado ao EmailProcessor")
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        return False
