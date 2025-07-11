#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/database_brk.py - VERSÃO COMPLETA COM BACKUP PREVENTIVO
💾 ONDE SALVAR: brk-monitor-seguro/processor/database_brk.py
🔧 FUNCIONALIDADE: Database BRK + SQLite OneDrive + Backup Preventivo Automático
🛡️ BACKUP PREVENTIVO: Proteção contra corrupção + pasta /backup/ visível
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
"""

import sqlite3
import os
import re
import requests
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path


class DatabaseBRK:
    """
    Database BRK com SQLite no OneDrive + cache local + BACKUP PREVENTIVO.
    
    FUNCIONALIDADES:
    - SQLite híbrido: OneDrive + cache local + fallback Render
    - SEEK estilo Clipper: CDC + Competência
    - Backup preventivo automático com validação
    - Proteção contra corrupção de arquivos
    - Pasta /backup/ visível com versionamento
    """
    
    def __init__(self, auth_manager, onedrive_brk_id):
        """Inicializar DatabaseBRK com SQLite no OneDrive."""
        self.auth = auth_manager
        self.onedrive_brk_id = onedrive_brk_id
        
        # Configurações database OneDrive
        self.db_filename = "database_brk.db"
        self.db_onedrive_id = None
        self.db_local_cache = None
        self.db_fallback_render = '/opt/render/project/storage/database_brk.db'
        
        # Conexão SQLite
        self.conn = None
        self.usando_onedrive = False
        self.usando_fallback = False
        
        print(f"🗃️ DatabaseBRK inicializado:")
        print(f"   📁 Pasta OneDrive /BRK/: configurada")
        print(f"   💾 Database: {self.db_filename} (OneDrive + cache)")
        print(f"   🔄 Fallback: Render disk")
        print(f"   🛡️ Backup preventivo: ativo (proteção automática)")
        
        # Inicializar database no OneDrive
        self._inicializar_database_sistema()
    
    def _inicializar_database_sistema(self):
        """Inicializa sistema completo: OneDrive → cache local → fallback."""
        try:
            print(f"📊 Inicializando database no OneDrive...")
            
            # ETAPA 1: Verificar se database existe no OneDrive
            database_existe = self._verificar_database_onedrive()
            
            if database_existe:
                print(f"✅ Database encontrado no OneDrive")
                if self._baixar_database_para_cache():
                    self.usando_onedrive = True
                    print(f"📥 Database sincronizado para cache local")
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
                # Salvar em cache local temporário
                with tempfile.NamedTemporaryFile(delete=False, suffix='.db', prefix='brk_cache_') as tmp_file:
                    tmp_file.write(response.content)
                    self.db_local_cache = tmp_file.name
                
                print(f"📥 Database baixado para cache: {self.db_local_cache}")
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
            
            print(f"✅ Fallback ativo: {self.db_fallback_render}")
            print(f"⚠️ ATENÇÃO: Dados no Render disk - sem backup OneDrive")
            
        except Exception as e:
            print(f"❌ Erro crítico no fallback: {e}")
            raise

def sincronizar_onedrive(self):
        """Sincroniza database local com OneDrive (backup) + BACKUP PREVENTIVO AUTOMÁTICO."""
        try:
            if not self.usando_onedrive:
                print(f"⚠️ Sincronização ignorada - usando fallback Render")
                return False
            
            if not self.db_local_cache or not os.path.exists(self.db_local_cache):
                print(f"⚠️ Cache local não disponível para sincronização")
                return False
            
            # Fechar conexão temporariamente para sync
            if self.conn:
                self.conn.close()
            
            # Upload para OneDrive
            sucesso = self._upload_database_onedrive()
            
            # Reconectar
            self.conn = sqlite3.connect(self.db_local_cache)
            
            if sucesso:
                print(f"🔄 Database sincronizado com OneDrive")
                
                # 🛡️ BACKUP PREVENTIVO AUTOMÁTICO (NOVA FUNCIONALIDADE):
                try:
                    resultado_backup = self.executar_backup_preventivo()
                    status_backup = resultado_backup.get('status', 'erro')
                    print(f"🛡️ Backup preventivo: {status_backup}")
                    
                    if status_backup == 'cancelado':
                        print(f"   ⚠️ Motivo: {resultado_backup.get('motivo', 'N/A')}")
                        print(f"   🛡️ Proteção ativa: versões anteriores preservadas")
                    elif status_backup == 'sucesso':
                        print(f"   ✅ Backup validado salvo: /BRK/backup/database_brk_valido_01.db")
                except Exception as e:
                    print(f"   ⚠️ Backup preventivo falhou (sistema continua): {e}")
                
                return True
            else:
                print(f"⚠️ Falha na sincronização OneDrive")
                return False
                
        except Exception as e:
            print(f"❌ Erro sincronização: {e}")
            try:
                if self.db_local_cache:
                    self.conn = sqlite3.connect(self.db_local_cache)
            except:
                pass
            return False
    
    def salvar_fatura(self, dados_fatura):
        """MÉTODO PRINCIPAL: Salva fatura com lógica SEEK + sincronização OneDrive."""
        try:
            print(f"💾 Salvando fatura: {dados_fatura.get('nome_arquivo_original', 'unknown')}")
            
            # 1. LÓGICA SEEK (estilo Clipper)
            status_duplicata = self._verificar_duplicata_seek(dados_fatura)
            
            # 2. Gerar nome padronizado
            nome_padronizado = self._gerar_nome_padronizado(dados_fatura)
            
            # 3. Inserir no SQLite
            id_salvo = self._inserir_fatura_sqlite(dados_fatura, status_duplicata, nome_padronizado)
            
            # 4. Integração alertas
            try:
                from processor.alertas.alert_processor import processar_alerta_fatura
                processar_alerta_fatura(dados_fatura)
            except ImportError:
                pass  # Alertas opcionais
            
            # 5. Sincronizar com OneDrive (inclui backup preventivo automático)
            self.sincronizar_onedrive()
            
            # 6. Retornar resultado
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
                # Fallback usando competência ou data atual
                ano, mes = self._extrair_ano_mes(competencia, vencimento)
                hoje = datetime.now()
                data_venc = hoje.strftime('%d-%m')
                data_venc_full = hoje.strftime('%d-%m-%Y')
                mes_ano = f"{mes:02d}-{ano}"
            
            # Limpar nome da casa
            casa_limpa = re.sub(r'[<>:"/\\|?*]', '-', casa_oracao)
            
            # Gerar nome padrão renomeia_brk10.py
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
    
    def obter_estatisticas(self):
        """Retorna estatísticas do database com informações OneDrive."""
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
                'usando_onedrive': self.usando_onedrive,
                'usando_fallback': self.usando_fallback,
                'cache_local': self.db_local_cache,
                'onedrive_id': self.db_onedrive_id,
                'backup_preventivo': True
            }
            
        except Exception as e:
            print(f"❌ Erro obtendo estatísticas: {e}")
            return {
                'erro': str(e),
                'database_ativo': False,
                'usando_onedrive': self.usando_onedrive,
                'usando_fallback': self.usando_fallback,
                'backup_preventivo': False
            }
    
    def buscar_faturas(self, filtros=None):
        """Busca faturas com filtros opcionais."""
        try:
            cursor = self.conn.cursor()
            
            if not filtros:
                cursor.execute("""
                    SELECT * FROM faturas_brk 
                    ORDER BY data_processamento DESC 
                    LIMIT 100
                """)
            else:
                cursor.execute("""
                    SELECT * FROM faturas_brk 
                    ORDER BY data_processamento DESC 
                    LIMIT 100
                """)
            
            return cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Erro buscando faturas: {e}")
            return []
    
    def status_sistema(self):
        """Retorna status completo do sistema database."""
        return {
            'usando_onedrive': self.usando_onedrive,
            'usando_fallback': self.usando_fallback,
            'cache_local_existe': bool(self.db_local_cache and os.path.exists(self.db_local_cache)),
            'conexao_ativa': bool(self.conn),
            'onedrive_id': self.db_onedrive_id,
            'filename': self.db_filename,
            'backup_preventivo_ativo': True
        }

def obter_meses_com_faturas(self):
        """
        🆕 NOVA FUNÇÃO: Detecta todos os meses/anos que possuem faturas no database.
        
        Returns:
            List[Tuple[int, int]]: Lista de (mes, ano) únicos encontrados
        """
        try:
            if not self.conn:
                print("❌ Conexão database não disponível")
                return []
            
            print("🔍 Detectando meses com faturas no database...")
            
            cursor = self.conn.cursor()
            
            # Query para buscar TODOS os vencimentos e competências
            query = """
                SELECT DISTINCT vencimento, competencia 
                FROM faturas_brk 
                WHERE status_duplicata = 'NORMAL'
                AND (vencimento IS NOT NULL OR competencia IS NOT NULL)
                ORDER BY vencimento, competencia
            """
            
            cursor.execute(query)
            resultados = cursor.fetchall()
            
            print(f"📊 Encontrados {len(resultados)} registros únicos de datas")
            
            # Set para evitar duplicatas
            meses_encontrados = set()
            
            # Processar cada resultado
            for row in resultados:
                vencimento = row[0] if row[0] else ""
                competencia = row[1] if row[1] else ""
                
                # Extrair mês/ano do vencimento (formato: DD/MM/YYYY)
                if vencimento and "/" in vencimento:
                    try:
                        partes = vencimento.split("/")
                        if len(partes) == 3:
                            mes_venc = int(partes[1])
                            ano_venc = int(partes[2])
                            if 1 <= mes_venc <= 12 and 2020 <= ano_venc <= 2030:
                                meses_encontrados.add((mes_venc, ano_venc))
                                print(f"   📅 Vencimento: {vencimento} → {mes_venc}/{ano_venc}")
                    except (ValueError, IndexError):
                        pass
                
                # Extrair mês/ano da competência (formatos: "Julho/2025", "07/2025")
                if competencia and "/" in competencia:
                    try:
                        # Tentar formato "Julho/2025"
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
                                            print(f"   📆 Competência: {competencia} → {numero}/{ano_comp}")
                                        break
                        
                        # Tentar formato "07/2025"
                        else:
                            partes = competencia.split("/")
                            if len(partes) == 2:
                                mes_comp = int(partes[0])
                                ano_comp = int(partes[1])
                                if 1 <= mes_comp <= 12 and 2020 <= ano_comp <= 2030:
                                    meses_encontrados.add((mes_comp, ano_comp))
                                    print(f"   📆 Competência: {competencia} → {mes_comp}/{ano_comp}")
                                    
                    except (ValueError, IndexError):
                        pass
            
            # Converter para lista ordenada
            meses_lista = sorted(list(meses_encontrados))
            
            print(f"\n✅ MESES DETECTADOS:")
            meses_nomes = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
                5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 
                9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
            }
            
            for mes, ano in meses_lista:
                print(f"   📊 {meses_nomes[mes]}/{ano} → Planilha: BRK-Planilha-{ano}-{mes:02d}.xlsx")
            
            print(f"🎯 TOTAL: {len(meses_lista)} planilha(s) serão geradas")
            
            return meses_lista
            
        except Exception as e:
            print(f"❌ Erro detectando meses com faturas: {e}")
            return []

    def obter_estatisticas_por_mes(self, mes, ano):
        """
        🆕 NOVA FUNÇÃO: Estatísticas específicas de um mês/ano.
        
        Args:
            mes (int): Mês (1-12)
            ano (int): Ano (ex: 2025)
            
        Returns:
            Dict: Estatísticas do mês específico
        """
        try:
            if not self.conn:
                return {"erro": "Conexão indisponível"}
            
            cursor = self.conn.cursor()
            
            # Contar faturas do mês específico
            query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status_duplicata = 'NORMAL' THEN 1 END) as normais,
                    COUNT(CASE WHEN status_duplicata = 'DUPLICATA' THEN 1 END) as duplicatas,
                    COUNT(CASE WHEN status_duplicata = 'FALTANTE' THEN 1 END) as faltantes
                FROM faturas_brk 
                WHERE (
                    vencimento LIKE ? 
                    OR competencia LIKE ?
                    OR competencia LIKE ?
                )
            """
            
            # Parâmetros de busca para o mês/ano
            mes_str = f"__{mes:02d}/{ano}"  # Para vencimento DD/MM/YYYY
            comp_str1 = f"%/{ano}"          # Para competência Mês/YYYY
            comp_str2 = f"{mes:02d}/{ano}"  # Para competência MM/YYYY
            
            cursor.execute(query, (mes_str, comp_str1, comp_str2))
            resultado = cursor.fetchone()
            
            if resultado:
                return {
                    "mes": mes,
                    "ano": ano,
                    "total_faturas": resultado[0],
                    "normais": resultado[1],
                    "duplicatas": resultado[2],
                    "faltantes": resultado[3],
                    "status": "sucesso"
                }
            else:
                return {
                    "mes": mes,
                    "ano": ano,
                    "total_faturas": 0,
                    "status": "sem_dados"
                }
                
        except Exception as e:
            return {
                "mes": mes,
                "ano": ano,
                "erro": str(e),
                "status": "erro"
            }

    # ============================================================================
    # MÉTODOS DE COMPATIBILIDADE COM EMAILPROCESSOR
    # ============================================================================
    
    def inicializar_sistema(self):
        """Método de compatibilidade com EmailProcessor atual."""
        try:
            if self.conn:
                print(f"✅ Sistema DatabaseBRK já inicializado")
                return True
            else:
                self._inicializar_database_sistema()
                return bool(self.conn)
        except Exception as e:
            print(f"❌ Erro reinicializando sistema: {e}")
            return False
    
    def verificar_conexao(self):
        """Método de compatibilidade - verifica se conexão está ativa."""
        try:
            if self.conn:
                cursor = self.conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True
            return False
        except Exception as e:
            print(f"⚠️ Conexão database inativa: {e}")
            return False
    
    def get_connection(self):
        """Método de compatibilidade - retorna conexão SQLite."""
        return self.conn
    
    def salvar_dados_fatura(self, dados_fatura):
        """Alias para salvar_fatura - compatibilidade com nomes diferentes."""
        return self.salvar_fatura(dados_fatura)
    
    def inserir_fatura(self, dados_fatura):
        """Outro alias possível para salvar_fatura."""
        return self.salvar_fatura(dados_fatura)

    # ============================================================================
    # 🛡️ MÉTODOS BACKUP PREVENTIVO - PROTEÇÃO AUTOMÁTICA COMPLETA
    # ============================================================================

    def _backup_preventivo_disponivel(self):
        """Verifica se backup preventivo está habilitado e OneDrive disponível."""
        try:
            return (
                self.usando_onedrive and 
                self.onedrive_brk_id and 
                self.db_local_cache and 
                os.path.exists(self.db_local_cache)
            )
        except Exception:
            return False

    def _validar_database_antes_backup(self, arquivo_path):
        """
        Valida integridade do database ANTES de fazer backup.
        Só salva backup se arquivo estiver íntegro.
        
        Args:
            arquivo_path (str): Caminho para arquivo SQLite
            
        Returns:
            Tuple[bool, str]: (válido, mensagem)
        """
        try:
            # VALIDAÇÃO 1: Arquivo existe e tem tamanho > 0
            if not os.path.exists(arquivo_path):
                return False, "Arquivo não existe"
            
            tamanho = os.path.getsize(arquivo_path)
            if tamanho == 0:
                return False, "Arquivo vazio"
            
            if tamanho < 1024:  # SQLite mínimo ~1KB
                return False, f"Arquivo muito pequeno ({tamanho} bytes)"
            
            # VALIDAÇÃO 2: SQLite válido - testar abertura
            import sqlite3
            conn_test = sqlite3.connect(arquivo_path, timeout=5)
            
            try:
                # VALIDAÇÃO 3: Testar query básica
                cursor = conn_test.cursor()
                cursor.execute("SELECT COUNT(*) FROM faturas_brk")
                count = cursor.fetchone()[0]
                
                # VALIDAÇÃO 4: Verificar se tem dados razoáveis
                if count < 0:  # Impossível ter count negativo
                    return False, "Database corrompido (count inválido)"
                
                # VALIDAÇÃO 5: Testar estrutura da tabela
                cursor.execute("PRAGMA table_info(faturas_brk)")
                colunas = cursor.fetchall()
                
                if len(colunas) < 10:  # Tabela deve ter muitas colunas
                    return False, "Estrutura da tabela incompleta"
                
                conn_test.close()
                
                return True, f"Database válido ({count} registros, {tamanho} bytes)"
                
            except Exception as e:
                conn_test.close()
                return False, f"Erro validando SQLite: {e}"
            
        except Exception as e:
            return False, f"Erro abrindo database: {e}"

    def _garantir_pasta_backup_onedrive(self):
        """
        Garante que pasta /backup/ existe no OneDrive.
        (Pasta VISÍVEL, não oculta)
        
        Returns:
            str: ID da pasta backup ou None se erro
        """
        try:
            headers = self.auth.obter_headers_autenticados()
            if not headers:
                print("❌ Headers autenticação indisponíveis")
                return None
            
            # Buscar pasta backup dentro de /BRK/
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{self.onedrive_brk_id}/children"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                itens = response.json().get('value', [])
                
                # Procurar pasta backup existente
                for item in itens:
                    if item.get('name') == 'backup' and 'folder' in item:
                        print(f"✅ Pasta backup encontrada: {item['id'][:15]}...")
                        return item['id']
                
                # Pasta não existe - criar nova
                print(f"📁 Criando pasta /backup/ (não existia)...")
                return self._criar_pasta_backup_onedrive(headers)
            else:
                print(f"❌ Erro acessando OneDrive: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro verificando pasta backup: {e}")
            return None

    def _criar_pasta_backup_onedrive(self, headers):
        """
        Cria pasta backup no OneDrive.
        
        Args:
            headers: Headers autenticados Microsoft Graph
            
        Returns:
            str: ID da nova pasta ou None se erro
        """
        try:
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{self.onedrive_brk_id}/children"
            
            data = {
                "name": "backup",
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename"
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 201:
                nova_pasta = response.json()
                pasta_id = nova_pasta['id']
                print(f"✅ Pasta backup criada: {pasta_id[:15]}...")
                return pasta_id
            else:
                print(f"❌ Erro criando pasta backup: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro criando pasta backup: {e}")
            return None

    def _rotacionar_versoes_backup(self, pasta_backup_id):
        """
        Rotaciona versões existentes de backup.
        
        ANTES: database_brk_valido_01.db, database_brk_valido_02.db
        DEPOIS: database_brk_valido_02.db, database_brk_valido_03.db
        (Remove a mais antiga, move as outras)
        
        Args:
            pasta_backup_id (str): ID da pasta backup no OneDrive
        """
        try:
            headers = self.auth.obter_headers_autenticados()
            if not headers:
                return
            
            # Buscar arquivos na pasta backup
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_backup_id}/children"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"⚠️ Não foi possível acessar pasta backup para rotação")
                return
            
            arquivos = response.json().get('value', [])
            
            # Encontrar versões existentes
            versoes = {}
            for arquivo in arquivos:
                nome = arquivo.get('name', '')
                if nome.startswith('database_brk_valido_') and nome.endswith('.db'):
                    # Extrair número da versão
                    try:
                        num_versao = nome.replace('database_brk_valido_', '').replace('.db', '')
                        versoes[int(num_versao)] = arquivo
                    except:
                        pass
            
            # Rotacionar versões (3 → deletar, 2 → 3, 1 → 2)
            if 3 in versoes:
                # Deletar versão 03 (mais antiga)
                try:
                    url_delete = f"https://graph.microsoft.com/v1.0/me/drive/items/{versoes[3]['id']}"
                    requests.delete(url_delete, headers=headers, timeout=30)
                    print(f"🗑️ Versão 03 removida (rotação)")
                except Exception as e:
                    print(f"⚠️ Erro removendo versão 03: {e}")
            
            if 2 in versoes:
                # Renomear versão 02 → 03
                try:
                    url_rename = f"https://graph.microsoft.com/v1.0/me/drive/items/{versoes[2]['id']}"
                    data_rename = {"name": "database_brk_valido_03.db"}
                    requests.patch(url_rename, headers=headers, json=data_rename, timeout=30)
                    print(f"📝 Versão 02 → 03 (rotação)")
                except Exception as e:
                    print(f"⚠️ Erro renomeando 02→03: {e}")
            
            if 1 in versoes:
                # Renomear versão 01 → 02
                try:
                    url_rename = f"https://graph.microsoft.com/v1.0/me/drive/items/{versoes[1]['id']}"
                    data_rename = {"name": "database_brk_valido_02.db"}
                    requests.patch(url_rename, headers=headers, json=data_rename, timeout=30)
                    print(f"📝 Versão 01 → 02 (rotação)")
                except Exception as e:
                    print(f"⚠️ Erro renomeando 01→02: {e}")
            
        except Exception as e:
            print(f"⚠️ Erro na rotação de versões: {e}")

    def _salvar_backup_validado(self, pasta_backup_id, database_bytes):
        """
        Salva nova versão validada como database_brk_valido_01.db
        
        Args:
            pasta_backup_id (str): ID da pasta backup
            database_bytes (bytes): Conteúdo do database válido
            
        Returns:
            bool: True se salvamento bem-sucedido
        """
        try:
            headers = self.auth.obter_headers_autenticados()
            headers['Content-Type'] = 'application/octet-stream'
            
            # Salvar como versão 01 (mais recente)
            nome_backup = "database_brk_valido_01.db"
            nome_encodado = requests.utils.quote(nome_backup)
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_backup_id}:/{nome_encodado}:/content"
            
            response = requests.put(url, headers=headers, data=database_bytes, timeout=120)
            
            if response.status_code in [200, 201]:
                arquivo_info = response.json()
                print(f"✅ BACKUP VALIDADO salvo: {nome_backup} ({len(database_bytes)} bytes)")
                return True
            else:
                print(f"❌ Erro salvando backup: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro salvando backup validado: {e}")
            return False

    def _salvar_log_backup(self, pasta_backup_id, validacao_info, sucesso):
        """
        Salva log do backup em backup_log.txt
        
        Args:
            pasta_backup_id (str): ID da pasta backup
            validacao_info (str): Informações da validação
            sucesso (bool): Se backup foi bem-sucedido
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status = "SUCESSO" if sucesso else "FALHA"
            
            log_content = f"[{timestamp}] BACKUP {status}: {validacao_info}\n"
            
            headers = self.auth.obter_headers_autenticados()
            headers['Content-Type'] = 'text/plain'
            
            # Tentar baixar log existente primeiro
            nome_log = "backup_log.txt"
            url_download = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_backup_id}:/{nome_log}:/content"
            
            try:
                response_download = requests.get(url_download, headers=headers, timeout=30)
                if response_download.status_code == 200:
                    log_existente = response_download.text
                    log_content = log_existente + log_content
            except:
                pass  # Se não conseguir baixar, criar novo
            
            # Salvar log atualizado
            url_upload = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_backup_id}:/{nome_log}:/content"
            response = requests.put(url_upload, headers=headers, data=log_content.encode('utf-8'), timeout=60)
            
            if response.status_code in [200, 201]:
                print(f"📝 Log backup atualizado")
            
        except Exception as e:
            print(f"⚠️ Erro salvando log backup: {e}")

    def executar_backup_preventivo(self):
        """
        ✅ MÉTODO PRINCIPAL: Executa backup preventivo com validação.
        
        FLUXO:
        1. Verifica se backup está disponível
        2. Valida database atual ANTES de fazer backup
        3. Se válido: rotaciona versões e salva novo backup
        4. Se inválido: mantém versões anteriores (proteção)
        5. Registra resultado em log
        
        Returns:
            Dict: Resultado do backup preventivo
        """
        try:
            # ETAPA 1: Verificar disponibilidade
            if not self._backup_preventivo_disponivel():
                return {
                    'status': 'pulado',
                    'motivo': 'Backup preventivo não disponível (OneDrive ou cache)',
                    'protecao_ativa': False
                }
            
            print(f"🛡️ Iniciando backup preventivo...")
            
            # ETAPA 2: Validar database ANTES do backup
            valido, validacao_info = self._validar_database_antes_backup(self.db_local_cache)
            
            if not valido:
                print(f"⚠️ BACKUP CANCELADO: {validacao_info}")
                print(f"   🛡️ Versões anteriores preservadas (proteção contra corrupção)")
                
                return {
                    'status': 'cancelado',
                    'motivo': validacao_info,
                    'protecao_ativa': True,
                    'versoes_preservadas': True
                }
            
            # ETAPA 3: Garantir pasta backup existe
            pasta_backup_id = self._garantir_pasta_backup_onedrive()
            if not pasta_backup_id:
                return {
                    'status': 'erro',
                    'motivo': 'Não foi possível criar/acessar pasta backup',
                    'protecao_ativa': False
                }
            
            # ETAPA 4: Ler database validado
            with open(self.db_local_cache, 'rb') as f:
                database_bytes = f.read()
            
            # ETAPA 5: Rotacionar versões existentes
            self._rotacionar_versoes_backup(pasta_backup_id)
            
            # ETAPA 6: Salvar nova versão validada
            sucesso = self._salvar_backup_validado(pasta_backup_id, database_bytes)
            
            # ETAPA 7: Registrar resultado em log
            self._salvar_log_backup(pasta_backup_id, validacao_info, sucesso)
            
            if sucesso:
                print(f"✅ BACKUP PREVENTIVO CONCLUÍDO")
                print(f"   📊 Status: {validacao_info}")
                print(f"   💾 Salvo: /BRK/backup/database_brk_valido_01.db")
                print(f"   🔄 Versões mantidas: 01, 02, 03 (últimas 3 válidas)")
                
                return {
                    'status': 'sucesso',
                    'validacao': validacao_info,
                    'protecao_ativa': True,
                    'versoes_mantidas': 3,
                    'pasta_backup': '/BRK/backup/'
                }
            else:
                return {
                    'status': 'erro',
                    'motivo': 'Falha salvando backup validado',
                    'protecao_ativa': True
                }
            
        except Exception as e:
            print(f"❌ Erro backup preventivo: {e}")
            return {
                'status': 'erro',
                'motivo': str(e),
                'protecao_ativa': False
            }

    def restaurar_backup_manual_instrucoes(self):
        """
        Exibe instruções para restauração manual via OneDrive.
        Útil quando usuário reporta problemas no database.
        """
        print(f"\n🛡️ INSTRUÇÕES RESTAURAÇÃO MANUAL - BACKUP PREVENTIVO")
        print(f"="*60)
        print(f"📍 LOCALIZAÇÃO DOS BACKUPS:")
        print(f"   🌐 OneDrive Web: /BRK/backup/")
        print(f"   📄 Versões disponíveis:")
        print(f"      • database_brk_valido_01.db  (mais recente)")
        print(f"      • database_brk_valido_02.db  (anterior)")
        print(f"      • database_brk_valido_03.db  (mais antiga)")
        print(f"")
        print(f"🔧 COMO RESTAURAR:")
        print(f"   1. Acesse OneDrive web")
        print(f"   2. Navegue para pasta /BRK/backup/")
        print(f"   3. Selecione database_brk_valido_01.db")
        print(f"   4. Clique 'Baixar'")
        print(f"   5. Renomeie para: database_brk.db")
        print(f"   6. Vá para pasta /BRK/")
        print(f"   7. Arraste e solte o arquivo renomeado")
        print(f"   8. Confirme substituição")
        print(f"   9. Sistema voltará a funcionar no próximo ciclo")
        print(f"")
        print(f"📊 STATUS ATUAL:")
        print(f"   📁 OneDrive configurado: {'✅' if self.usando_onedrive else '❌'}")
        print(f"   💾 Cache local: {'✅' if self.db_local_cache else '❌'}")
        print(f"   🔗 Conexão ativa: {'✅' if self.conn else '❌'}")
        print(f"="*60)

    def fechar_conexao(self):
        """Fecha conexão SQLite e limpa cache temporário."""
        try:
            if self.usando_onedrive:
                self.sincronizar_onedrive()
            
            if self.conn:
                self.conn.close()
                print(f"✅ Conexão SQLite fechada")
            
            if self.db_local_cache and os.path.exists(self.db_local_cache):
                try:
                    os.unlink(self.db_local_cache)
                    print(f"🗑️ Cache local limpo: {self.db_local_cache}")
                except:
                    print(f"⚠️ Cache local não pôde ser removido")
                    
        except Exception as e:
            print(f"⚠️ Erro fechando conexão: {e}")
    
    def __del__(self):
        """Destructor para garantir limpeza de recursos."""
        self.fechar_conexao()


# ============================================================================
# FUNÇÕES DE UTILIDADE
# ============================================================================

def criar_database_brk(auth_manager, onedrive_brk_id):
    """Factory function para criar DatabaseBRK com OneDrive."""
    try:
        db = DatabaseBRK(auth_manager, onedrive_brk_id)
        print(f"✅ DatabaseBRK criado - OneDrive: {db.usando_onedrive}")
        return db
    except Exception as e:
        print(f"❌ Erro criando DatabaseBRK: {e}")
        return None


def integrar_database_emailprocessor(email_processor):
    """Função de compatibilidade com EmailProcessor."""
    try:
        if hasattr(email_processor, 'database_brk') and email_processor.database_brk:
            print(f"✅ DatabaseBRK já integrado ao EmailProcessor")
            return True
        
        db_brk = DatabaseBRK(
            email_processor.auth, 
            email_processor.onedrive_brk_id
        )
        
        email_processor.database_brk = db_brk
        print(f"✅ DatabaseBRK integrado ao EmailProcessor")
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        return False
