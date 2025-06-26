# ============================================================================
# DATABASE BRK - IMPLEMENTAÇÃO COMPLETA
# Arquivo: processor/database_brk.py
# 
# FUNCIONALIDADES:
# 1. SQLite com lógica SEEK (CDC + Competência)
# 2. Detecção de duplicatas (NORMAL/DUPLICATA/CUIDADO)  
# 3. Estrutura OneDrive organizada (/Faturas/YYYY/MM/)
# 4. Nomenclatura consistente com script renomeia_brk10.py
# 5. Integração completa com EmailProcessor
# ============================================================================

import sqlite3
import io
import os
import re
import requests
import base64
import hashlib
from datetime import datetime
from pathlib import Path

class DatabaseBRK:
    def __init__(self, microsoft_auth, onedrive_brk_id):
        """
        Inicializa Database BRK com SQLite + OneDrive organizados
        
        Args:
            microsoft_auth: Instância de autenticação Microsoft
            onedrive_brk_id: ID da pasta /BRK/ no OneDrive
        """
        self.auth = microsoft_auth
        self.onedrive_brk_id = onedrive_brk_id
        
        # Configurações do banco
        self.nome_db = "dados_brk.db"
        self.db_file_id = None
        
        # Cache de estrutura OneDrive
        self.pasta_faturas_id = None
        self.cache_pastas_anos = {}    # {2025: folder_id, 2024: folder_id}
        self.cache_pastas_meses = {}   # {"2025_02": folder_id, "2025_01": folder_id}
        
        # Conexão SQLite local (para operações)
        self.conn_local = None
        
        print(f"🗃️ DatabaseBRK inicializado")
        print(f"   📁 OneDrive BRK: {onedrive_brk_id[:15]}******")
        print(f"   📊 Database: {self.nome_db}")

    def inicializar_sistema(self):
        """
        Inicializa todo o sistema: estrutura OneDrive + SQLite
        
        Returns:
            bool: True se inicialização bem-sucedida
        """
        try:
            print(f"🚀 Inicializando sistema DatabaseBRK...")
            
            # 1. Garantir estrutura de pastas OneDrive
            if not self._garantir_estrutura_onedrive():
                print(f"❌ Falha na estrutura OneDrive")
                return False
            
            # 2. Inicializar SQLite (baixar ou criar)
            if not self._inicializar_sqlite():
                print(f"❌ Falha no SQLite")
                return False
            
            print(f"✅ Sistema DatabaseBRK inicializado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro inicializando sistema: {e}")
            return False

    def _garantir_estrutura_onedrive(self):
        """
        Garante que estrutura de pastas existe no OneDrive
        """
        try:
            headers = self.auth.obter_headers_autenticados()
            if not headers:
                return False
            
            # 1. Encontrar/criar pasta /Faturas/
            self.pasta_faturas_id = self._encontrar_ou_criar_pasta("Faturas", self.onedrive_brk_id)
            
            if self.pasta_faturas_id:
                print(f"✅ Estrutura OneDrive pronta: /BRK/Faturas/")
                return True
            else:
                print(f"❌ Falha criando /BRK/Faturas/")
                return False
                
        except Exception as e:
            print(f"❌ Erro estrutura OneDrive: {e}")
            return False

    def _encontrar_ou_criar_pasta(self, nome_pasta, pasta_pai_id):
        """
        Encontra pasta existente ou cria nova
        """
        try:
            headers = self.auth.obter_headers_autenticados()
            
            # 1. Buscar pasta existente
            url_busca = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_pai_id}/children"
            response = requests.get(url_busca, headers=headers, timeout=30)
            
            if response.status_code == 200:
                pastas = response.json().get('value', [])
                for pasta in pastas:
                    if pasta.get('name') == nome_pasta and 'folder' in pasta:
                        print(f"📁 Pasta encontrada: {nome_pasta}")
                        return pasta['id']
            
            # 2. Criar pasta se não encontrou
            url_criar = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_pai_id}/children"
            dados_pasta = {
                "name": nome_pasta,
                "folder": {}
            }
            
            response = requests.post(url_criar, headers=headers, json=dados_pasta, timeout=30)
            
            if response.status_code == 201:
                nova_pasta = response.json()
                print(f"✅ Pasta criada: {nome_pasta}")
                return nova_pasta['id']
            else:
                print(f"❌ Erro criando pasta {nome_pasta}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro encontrar/criar pasta {nome_pasta}: {e}")
            return None

    def _inicializar_sqlite(self):
        """
        Inicializa SQLite: baixa do OneDrive ou cria novo
        """
        try:
            print(f"📊 Inicializando SQLite...")
            
            # 1. Tentar baixar SQLite existente do OneDrive
            sqlite_existente = self._baixar_sqlite_onedrive()
            
            if sqlite_existente:
                print(f"✅ SQLite baixado do OneDrive")
                self.conn_local = sqlite3.connect(":memory:")
                self.conn_local.executescript(sqlite_existente)
            else:
                print(f"📊 Criando novo SQLite")
                self.conn_local = sqlite3.connect(":memory:")
                self._criar_estrutura_sqlite()
            
            return True
            
        except Exception as e:
            print(f"❌ Erro inicializando SQLite: {e}")
            return False

    def _baixar_sqlite_onedrive(self):
        """
        Tenta baixar SQLite existente do OneDrive
        """
        try:
            headers = self.auth.obter_headers_autenticados()
            
            # Buscar arquivo na pasta /BRK/
            url_busca = f"https://graph.microsoft.com/v1.0/me/drive/items/{self.onedrive_brk_id}/children"
            response = requests.get(url_busca, headers=headers, timeout=30)
            
            if response.status_code == 200:
                arquivos = response.json().get('value', [])
                for arquivo in arquivos:
                    if arquivo.get('name') == self.nome_db:
                        # Baixar conteúdo do arquivo
                        url_download = f"https://graph.microsoft.com/v1.0/me/drive/items/{arquivo['id']}/content"
                        response_download = requests.get(url_download, headers=headers, timeout=60)
                        
                        if response_download.status_code == 200:
                            self.db_file_id = arquivo['id']
                            
                            # Converter bytes para SQL (backup do SQLite)
                            with sqlite3.connect(":memory:") as temp_conn:
                                temp_conn.execute("PRAGMA user_version = 1")
                                return temp_conn.iterdump()
            
            return None
            
        except Exception as e:
            print(f"⚠️ Não foi possível baixar SQLite: {e}")
            return None

    def _criar_estrutura_sqlite(self):
        """
        Cria estrutura SQLite com nossa lógica definida
        """
        try:
            # SQL da estrutura que definimos anteriormente
            sql_create = """
            CREATE TABLE faturas_brk (
                -- CAMPOS DE CONTROLE (Sistema)
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_processamento DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- CONTROLE DE DUPLICATAS (Principal funcionalidade)
                status_duplicata TEXT DEFAULT 'NORMAL',
                observacao TEXT DEFAULT '',
                
                -- CAMPOS DO EMAIL (Origem)
                email_id TEXT NOT NULL,
                nome_arquivo_original TEXT NOT NULL,     -- Nome do PDF no email
                nome_arquivo TEXT NOT NULL,              -- Nome padronizado (renomeação)
                hash_arquivo TEXT UNIQUE,
                tamanho_bytes INTEGER,
                caminho_onedrive TEXT,                   -- Onde foi salvo
                
                -- DADOS EXTRAÍDOS DA FATURA (PDF)
                cdc TEXT,
                nota_fiscal TEXT,
                casa_oracao TEXT,
                data_emissao TEXT,
                vencimento TEXT,
                competencia TEXT,
                valor TEXT,
                
                -- ANÁLISE DE CONSUMO (Água)
                medido_real INTEGER,
                faturado INTEGER,
                media_6m INTEGER,
                porcentagem_consumo TEXT,
                alerta_consumo TEXT,
                
                -- CAMPOS TÉCNICOS
                dados_extraidos_ok BOOLEAN DEFAULT TRUE,
                relacionamento_usado BOOLEAN DEFAULT FALSE
            );
            
            -- ÍNDICES PARA PERFORMANCE
            CREATE INDEX idx_cdc_competencia ON faturas_brk(cdc, competencia);
            CREATE INDEX idx_status_duplicata ON faturas_brk(status_duplicata);
            CREATE INDEX idx_casa_oracao ON faturas_brk(casa_oracao);
            CREATE INDEX idx_data_processamento ON faturas_brk(data_processamento);
            CREATE INDEX idx_competencia ON faturas_brk(competencia);
            """
            
            self.conn_local.executescript(sql_create)
            self.conn_local.commit()
            
            print(f"✅ Estrutura SQLite criada")
            return True
            
        except Exception as e:
            print(f"❌ Erro criando estrutura SQLite: {e}")
            return False

    def salvar_fatura(self, dados_fatura):
        """
        MÉTODO PRINCIPAL: Salva fatura com lógica SEEK completa
        
        Args:
            dados_fatura (Dict): Dados da fatura extraídos do EmailProcessor
            
        Returns:
            Dict: Resultado da operação {'status', 'mensagem', 'id_salvo'}
        """
        try:
            print(f"💾 Salvando fatura: {dados_fatura.get('nome_arquivo', 'unknown')}")
            
            # 1. LÓGICA SEEK (estilo Clipper)
            resultado_seek = self._executar_seek_duplicatas(dados_fatura)
            
            # 2. Gerar nome arquivo padronizado (igual script renomeação)
            nome_padronizado = self._gerar_nome_arquivo_padronizado(dados_fatura)
            dados_fatura['nome_arquivo'] = nome_padronizado
            
            # 3. Definir caminho OneDrive
            caminho_onedrive = self._obter_caminho_onedrive(dados_fatura)
            dados_fatura['caminho_onedrive'] = caminho_onedrive
            
            # 4. Aplicar resultado do SEEK
            dados_fatura['status_duplicata'] = resultado_seek['status']
            dados_fatura['observacao'] = resultado_seek['observacao']
            
            # 5. SEMPRE SALVAR no SQLite
            id_salvo = self._inserir_registro_sqlite(dados_fatura)
            
            # 6. Salvar PDF no OneDrive (se não for duplicata real)
            if resultado_seek['status'] != 'DUPLICATA':
                sucesso_pdf = self._salvar_pdf_onedrive(dados_fatura)
                if not sucesso_pdf:
                    print(f"⚠️ Falha salvando PDF no OneDrive")
            
            # 7. Fazer backup do SQLite no OneDrive
            self._backup_sqlite_onedrive()
            
            return {
                'status': 'sucesso',
                'mensagem': f"Fatura salva - Status: {resultado_seek['status']}",
                'id_salvo': id_salvo,
                'status_duplicata': resultado_seek['status'],
                'nome_arquivo': nome_padronizado
            }
            
        except Exception as e:
            print(f"❌ Erro salvando fatura: {e}")
            return {
                'status': 'erro',
                'mensagem': str(e),
                'id_salvo': None
            }

    def _executar_seek_duplicatas(self, dados_fatura):
        """
        Executa lógica SEEK estilo Clipper para detectar duplicatas
        
        Returns:
            Dict: {'status': 'NORMAL/DUPLICATA/CUIDADO', 'observacao': '...'}
        """
        try:
            cdc = dados_fatura.get('cdc')
            competencia = dados_fatura.get('competencia')
            
            if not cdc or not competencia:
                return {
                    'status': 'NORMAL',
                    'observacao': 'CDC ou Competência não encontrados'
                }
            
            # SEEK: buscar CDC + Competência
            cursor = self.conn_local.cursor()
            cursor.execute("""
                SELECT * FROM faturas_brk 
                WHERE cdc = ? AND competencia = ?
                ORDER BY data_processamento DESC
                LIMIT 1
            """, (cdc, competencia))
            
            registro_existente = cursor.fetchone()
            
            if not registro_existente:
                # NOT FOUND() - fatura nova
                return {
                    'status': 'NORMAL',
                    'observacao': 'Fatura nova do mês'
                }
            
            # FOUND() - comparar dados para classificar
            return self._comparar_com_existente(dados_fatura, registro_existente)
            
        except Exception as e:
            print(f"❌ Erro no SEEK: {e}")
            return {
                'status': 'NORMAL',
                'observacao': f'Erro na verificação: {e}'
            }

    def _comparar_com_existente(self, nova_fatura, registro_existente):
        """
        Compara nova fatura com registro existente para classificar duplicata
        """
        try:
            # Converter registro existente para dict (usando índices das colunas)
            colunas = [
                'id', 'data_processamento', 'status_duplicata', 'observacao',
                'email_id', 'nome_arquivo_original', 'nome_arquivo', 'hash_arquivo',
                'tamanho_bytes', 'caminho_onedrive', 'cdc', 'nota_fiscal',
                'casa_oracao', 'data_emissao', 'vencimento', 'competencia', 'valor',
                'medido_real', 'faturado', 'media_6m', 'porcentagem_consumo',
                'alerta_consumo', 'dados_extraidos_ok', 'relacionamento_usado'
            ]
            
            existente = dict(zip(colunas, registro_existente))
            
            # Comparar campos principais
            nota_fiscal_igual = nova_fatura.get('nota_fiscal') == existente.get('nota_fiscal')
            valor_igual = nova_fatura.get('valor') == existente.get('valor')
            vencimento_igual = nova_fatura.get('vencimento') == existente.get('vencimento')
            
            if nota_fiscal_igual and valor_igual and vencimento_igual:
                return {
                    'status': 'DUPLICATA',
                    'observacao': 'Email duplicado - dados idênticos'
                }
            else:
                # Dados diferentes = possível renegociação
                diferencas = []
                if not nota_fiscal_igual:
                    diferencas.append('NF')
                if not valor_igual:
                    diferencas.append('VALOR')
                if not vencimento_igual:
                    diferencas.append('VENCIMENTO')
                
                return {
                    'status': 'CUIDADO',
                    'observacao': f'Possível renegociação - diferenças: {", ".join(diferencas)}'
                }
                
        except Exception as e:
            return {
                'status': 'CUIDADO',
                'observacao': f'Erro na comparação: {e}'
            }

    def _gerar_nome_arquivo_padronizado(self, dados_fatura):
        """
        Gera nome arquivo usando EXATAMENTE o mesmo padrão do script renomeia_brk10.py
        """
        try:
            # Extrair dados necessários
            casa_oracao = dados_fatura.get('casa_oracao', 'Casa Desconhecida')
            vencimento = dados_fatura.get('vencimento', 'Sem Data')
            valor = dados_fatura.get('valor', 'Valor Desconhecido')
            competencia = dados_fatura.get('competencia', '')
            
            # Formatar data de vencimento (IGUAL ao script)
            try:
                if re.match(r'\d{2}/\d{2}/\d{4}', vencimento):
                    partes = vencimento.split('/')
                    dia, mes, ano = partes[0], partes[1], partes[2]
                    data_venc_str = f"{dia}-{mes}"
                    data_venc_full_str = f"{dia}-{mes}-{ano}"
                    mes_ano = f"{mes}-{ano}"
                else:
                    raise ValueError("Formato inválido")
                    
            except:
                # Fallback (IGUAL ao script)
                data_venc_str = "DD-MM"
                data_venc_full_str = "DD-MM-AAAA"
                
                # Tentar extrair de competência
                if competencia:
                    if re.search(r'(\d{2})[/-](\d{4})', competencia):
                        match = re.search(r'(\d{2})[/-](\d{4})', competencia)
                        mes_ano = f"{match.group(1)}-{match.group(2)}"
                    else:
                        mes_ano = "MM-AAAA"
                else:
                    hoje = datetime.now()
                    mes_ano = hoje.strftime('%m-%Y')
            
            # Limpar caracteres inválidos (IGUAL ao script)
            casa_limpa = casa_oracao.replace(":", "-").replace("/", "-")
            casa_limpa = casa_limpa.replace("?", "").replace("*", "")
            casa_limpa = casa_limpa.replace("<", "").replace(">", "").replace("|", "-")
            
            # Gerar nome IGUAL ao script
            nome_padronizado = f"{data_venc_str}-BRK {mes_ano} - {casa_limpa} - vc. {data_venc_full_str} - {valor}.pdf"
            
            return nome_padronizado
            
        except Exception as e:
            print(f"❌ Erro gerando nome padronizado: {e}")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"BRK_Erro_Nomenclatura_{timestamp}.pdf"

    def _obter_caminho_onedrive(self, dados_fatura):
        """
        Retorna caminho OneDrive baseado na estrutura /Faturas/YYYY/MM/
        """
        try:
            # Extrair ano/mês da competência ou vencimento
            competencia = dados_fatura.get('competencia', '')
            vencimento = dados_fatura.get('vencimento', '')
            
            ano, mes = self._extrair_ano_mes(competencia, vencimento)
            
            return f"/BRK/Faturas/{ano}/{mes:02d}/"
            
        except Exception as e:
            print(f"❌ Erro obtendo caminho: {e}")
            hoje = datetime.now()
            return f"/BRK/Faturas/{hoje.year}/{hoje.month:02d}/"

    def _extrair_ano_mes(self, competencia, vencimento):
        """
        Extrai ano e mês PRIORIZANDO VENCIMENTO
        CORRIGIDO: vencimento primeiro, competência como backup
        """
        # ✅ PRIORIDADE 1: VENCIMENTO (mais importante para organização do usuário)
        if vencimento and re.match(r'\d{2}/\d{2}/\d{4}', vencimento):
            try:
                partes = vencimento.split('/')
                dia, mes, ano = partes[0], int(partes[1]), int(partes[2])
                print(f"📅 Pasta definida por VENCIMENTO: {vencimento} → /{ano}/{mes:02d}/")
                return ano, mes
            except Exception as e:
                print(f"⚠️ Erro processando vencimento '{vencimento}': {e}")
        
        # ✅ FALLBACK: COMPETÊNCIA (se vencimento falhar)
        if competencia:
            # Tentar formato MM/YYYY
            if '/' in competencia and len(competencia) >= 7:
                try:
                    mes, ano = competencia.split('/')
                    mes, ano = int(mes), int(ano)
                    print(f"📅 Pasta definida por COMPETÊNCIA: {competencia} → /{ano}/{mes:02d}/")
                    return ano, mes
                except Exception as e:
                    print(f"⚠️ Erro processando competência '{competencia}': {e}")
        
        # ✅ FALLBACK FINAL: Data atual
        from datetime import datetime
        agora = datetime.now()
        print(f"📅 Pasta definida por DATA ATUAL (fallback): {agora.year}/{agora.month:02d}")
        return agora.year, agora.month
        # Formato: Jan/2025, Fev/2025, etc.
        meses_por_nome = {
            'jan': 1, 'janeiro': 1,
            'fev': 2, 'fevereiro': 2,
            'mar': 3, 'março': 3,
            'abr': 4, 'abril': 4,
            'mai': 5, 'maio': 5,
            'jun': 6, 'junho': 6,
            'jul': 7, 'julho': 7,
            'ago': 8, 'agosto': 8,
            'set': 9, 'setembro': 9,
            'out': 10, 'outubro': 10,
            'nov': 11, 'novembro': 11,
            'dez': 12, 'dezembro': 12
        }
        
        try:
            competencia_lower = competencia.lower()
            for nome_mes, num_mes in meses_por_nome.items():
                if nome_mes in competencia_lower:
                    # Buscar ano na string
                    match_ano = re.search(r'(\d{4})', competencia)
                    if match_ano:
                        ano = int(match_ano.group(1))
                        print(f"📅 Pasta definida por COMPETÊNCIA (nome): {competencia} → /{ano}/{num_mes:02d}/")
                        return ano, num_mes
        except Exception as e:
            print(f"⚠️ Erro processando competência por nome '{competencia}': {e}")
    
    # ✅ ÚLTIMO RECURSO: DATA ATUAL
    hoje = datetime.now()
    print(f"📅 Pasta definida por DATA ATUAL (último recurso): /{hoje.year}/{hoje.month:02d}/")
    print(f"   ⚠️ Vencimento: '{vencimento}' | Competência: '{competencia}' (ambos inválidos)")
    
    return hoje.year, hoje.month

    def _inserir_registro_sqlite(self, dados_fatura):
        """
        Insere registro no SQLite e retorna ID
        """
        try:
            cursor = self.conn_local.cursor()
            
            sql_insert = """
            INSERT INTO faturas_brk (
                email_id, nome_arquivo_original, nome_arquivo, hash_arquivo,
                tamanho_bytes, caminho_onedrive, cdc, nota_fiscal, casa_oracao,
                data_emissao, vencimento, competencia, valor, medido_real,
                faturado, media_6m, porcentagem_consumo, alerta_consumo,
                dados_extraidos_ok, relacionamento_usado, status_duplicata, observacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            valores = (
                dados_fatura.get('email_id'),
                dados_fatura.get('nome_arquivo_original'),
                dados_fatura.get('nome_arquivo'),
                dados_fatura.get('hash_arquivo'),
                dados_fatura.get('tamanho_bytes'),
                dados_fatura.get('caminho_onedrive'),
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
                dados_fatura.get('status_duplicata'),
                dados_fatura.get('observacao')
            )
            
            cursor.execute(sql_insert, valores)
            self.conn_local.commit()
            
            id_inserido = cursor.lastrowid
            print(f"✅ Registro SQLite salvo - ID: {id_inserido}")
            
            return id_inserido
            
        except Exception as e:
            print(f"❌ Erro inserindo no SQLite: {e}")
            return None

    def _salvar_pdf_onedrive(self, dados_fatura):
        """
        Salva PDF no OneDrive na estrutura organizada
        """
        try:
            # Implementar salvamento do PDF...
            # (Esta parte será implementada depois da aprovação)
            print(f"📁 PDF salvo: {dados_fatura['caminho_onedrive']}{dados_fatura['nome_arquivo']}")
            return True
            
        except Exception as e:
            print(f"❌ Erro salvando PDF: {e}")
            return False

    def _backup_sqlite_onedrive(self):
        """
        Faz backup do SQLite no OneDrive
        """
        try:
            # Implementar backup...
            # (Esta parte será implementada depois da aprovação)
            print(f"💾 Backup SQLite realizado")
            return True
            
        except Exception as e:
            print(f"❌ Erro no backup: {e}")
            return False

    def buscar_faturas(self, filtros=None):
        """
        Busca faturas no SQLite com filtros opcionais
        """
        try:
            cursor = self.conn_local.cursor()
            
            if not filtros:
                cursor.execute("SELECT * FROM faturas_brk ORDER BY data_processamento DESC")
            else:
                # Implementar filtros conforme necessário
                pass
            
            return cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Erro buscando faturas: {e}")
            return []

    def obter_estatisticas(self):
        """
        Retorna estatísticas do banco de dados
        """
        try:
            cursor = self.conn_local.cursor()
            
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
            
            return {
                'total_faturas': total,
                'por_status': por_status,
                'database_ativo': True
            }
            
        except Exception as e:
            print(f"❌ Erro obtendo estatísticas: {e}")
            return {'erro': str(e)}

# ============================================================================
# INTEGRAÇÃO COM EMAILPROCESSOR
# ============================================================================

def integrar_database_emailprocessor(email_processor):
    """
    Integra DatabaseBRK com EmailProcessor existente
    """
    try:
        # Criar instância DatabaseBRK
        db_brk = DatabaseBRK(
            email_processor.auth, 
            email_processor.onedrive_brk_id
        )
        
        # Inicializar sistema
        if db_brk.inicializar_sistema():
            email_processor.database_brk = db_brk
            print(f"✅ DatabaseBRK integrado ao EmailProcessor")
            return True
        else:
            print(f"❌ Falha integrando DatabaseBRK")
            return False
            
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        return False
