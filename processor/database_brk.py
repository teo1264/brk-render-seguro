#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/database_brk.py - VERSÃO CORRIGIDA
💾 ONDE SALVAR: brk-monitor-seguro/processor/database_brk.py
🔧 CORREÇÃO: Fechamento correto das funções + novas funções nas posições certas
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
    Database BRK com SQLite no OneDrive + cache local.
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
        relacionamento_usado BOOLEAN DEFAULT FALSE,
        content_bytes TEXT
    );
    
    CREATE INDEX IF NOT EXISTS idx_cdc_competencia ON faturas_brk(cdc, competencia);
    CREATE INDEX IF NOT EXISTS idx_status_duplicata ON faturas_brk(status_duplicata);
    CREATE INDEX IF NOT EXISTS idx_casa_oracao ON faturas_brk(casa_oracao);
    CREATE INDEX IF NOT EXISTS idx_data_processamento ON faturas_brk(data_processamento);
    CREATE INDEX IF NOT EXISTS idx_competencia ON faturas_brk(competencia);
    """
    
    conn.executescript(sql_create)
    conn.commit()
    print(f"✅ Estrutura SQLite criada (tabelas + índices + content_bytes)")
    
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
        """Sincroniza database local com OneDrive (backup)."""
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
            
            # 5. Sincronizar com OneDrive
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
            relacionamento_usado, status_duplicata, observacao, content_bytes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            f'Processado via {"OneDrive" if self.usando_onedrive else "Fallback"} - Status: {status_duplicata}',
            dados_fatura.get('content_bytes')
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
                'onedrive_id': self.db_onedrive_id
            }
            
        except Exception as e:
            print(f"❌ Erro obtendo estatísticas: {e}")
            return {
                'erro': str(e),
                'database_ativo': False,
                'usando_onedrive': self.usando_onedrive,
                'usando_fallback': self.usando_fallback
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
            'filename': self.db_filename
        }

    # ✅ NOVAS FUNÇÕES ADICIONADAS CORRETAMENTE APÓS status_sistema()
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
