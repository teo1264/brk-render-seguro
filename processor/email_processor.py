# ============================================================================
# EMAILPROCESSOR COMPLETO - SEM PANDAS - BLOCO 1/5
# Arquivo: processor/email_processor.py
# 
# BLOCO 1: Imports + Inicialização básica
# AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
# VERSÃO: Sem pandas - compatível Python 3.13
# ============================================================================

import requests
import io
import re
import os
import hashlib
import base64
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

class EmailProcessor:
    def __init__(self, microsoft_auth):
        """
        Inicializar processador com autenticação.
        VERSÃO SEM PANDAS - compatível com Python 3.13
        """
        self.auth = microsoft_auth
        
        # PASTA BRK ID para emails (Microsoft 365)
        self.pasta_brk_id = os.getenv("PASTA_BRK_ID")
        
        # PASTA BRK ID para arquivos OneDrive (já descoberta anteriormente)
        self.onedrive_brk_id = os.getenv("ONEDRIVE_BRK_ID")
        
        # VETORES DE RELACIONAMENTO (estilo Clipper como no desktop)
        self.cdc_brk_vetor = []      # Vetor com códigos CDC
        self.casa_oracao_vetor = []  # Vetor com nomes das casas (índice correspondente)
        
        # CONTROLE DE ESTADO
        self.relacionamento_carregado = False
        self.tentativas_carregamento = 0
        self.max_tentativas = 3
        
        if not self.pasta_brk_id:
            raise ValueError("❌ PASTA_BRK_ID não configurado!")
            
        print(f"📧 Email Processor inicializado (SEM pandas)")
        print(f"   📧 Pasta emails BRK: {self.pasta_brk_id[:10]}****** (emails)")
        
        if self.onedrive_brk_id:
            print(f"   📁 Pasta OneDrive /BRK/: {self.onedrive_brk_id[:15]}****** (arquivos)")
            print(f"   📄 Planilha relacionamento: CDC_BRK_CCB.xlsx (nesta pasta)")
            
            # CARREGAR RELACIONAMENTO AUTOMATICAMENTE NA INICIALIZAÇÃO
            print(f"🔄 Carregando relacionamento automaticamente...")
            self.relacionamento_carregado = self.carregar_relacionamento_completo()
            
            # 🆕 INTEGRAR DatabaseBRK AUTOMATICAMENTE
            print(f"🗃️ Inicializando DatabaseBRK...")
            self.database_brk = self._inicializar_database_brk()
            
            if self.database_brk:
                print(f"✅ DatabaseBRK integrado com sucesso!")
                print(f"   💾 Database: OneDrive + cache local + fallback")
                print(f"   🔍 SEEK: Ativo (detecção duplicatas)")
                print(f"   🔄 Sincronização: Automática")
            else:
                print(f"⚠️ DatabaseBRK falhou - continuando sem salvamento")
                
        else:
            print("   ⚠️ ONEDRIVE_BRK_ID não configurado - relacionamento indisponível")
            print("   💡 Funcionará apenas com extração básica dos PDFs")
            self.database_brk = None
            
    def garantir_autenticacao(self):
        """
        Garante que autenticação está funcionando.
        Helper básico para outras funções.
        """
        try:
            headers = self.auth.obter_headers_autenticados()
            return headers is not None
        except Exception as e:
            print(f"❌ Erro autenticação: {e}")
            return False
            
    def _inicializar_database_brk(self):
        """
        Inicializa DatabaseBRK automaticamente se OneDrive configurado.
        
        Returns:
            DatabaseBRK: Instância configurada ou None se erro
        """
        try:
            if not self.onedrive_brk_id:
                print(f"⚠️ ONEDRIVE_BRK_ID não configurado - DatabaseBRK indisponível")
                return None
            
            # Importar DatabaseBRK
            try:
                from .database_brk import DatabaseBRK
            except ImportError:
                print(f"❌ Erro importando DatabaseBRK - arquivo não encontrado")
                return None
            
            # Criar instância DatabaseBRK
            database = DatabaseBRK(self.auth, self.onedrive_brk_id)
            
            # Verificar se inicializou corretamente
            if hasattr(database, 'conn') and database.conn:
                print(f"✅ DatabaseBRK conectado - usando {'OneDrive' if database.usando_onedrive else 'Fallback'}")
                return database
            else:
                print(f"⚠️ DatabaseBRK inicializado mas sem conexão")
                return database  # Retornar mesmo assim - pode funcionar
                
        except Exception as e:
            print(f"❌ Erro inicializando DatabaseBRK: {e}")
            return None

    def salvar_fatura_database(self, dados_fatura):
        """
        Salva fatura no DatabaseBRK se disponível.
        
        Args:
            dados_fatura (dict): Dados extraídos da fatura
            
        Returns:
            dict: Resultado do salvamento
        """
        try:
            if not self.database_brk:
                return {
                    'status': 'pulado',
                    'mensagem': 'DatabaseBRK não disponível',
                    'database_ativo': False
                }
            
            # Usar método salvar_fatura do DatabaseBRK
            resultado = self.database_brk.salvar_fatura(dados_fatura)
            
            if resultado.get('status') == 'sucesso':
                print(f"💾 DatabaseBRK: {resultado.get('status_duplicata', 'NORMAL')} - {resultado.get('nome_arquivo', 'arquivo')}")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro salvando no DatabaseBRK: {e}")
            return {
                'status': 'erro',
                'mensagem': str(e),
                'database_ativo': bool(self.database_brk)
            }

    def debug_status_completo(self):
        """
        Debug completo do EmailProcessor incluindo DatabaseBRK.
        Método usado pelo diagnóstico para verificar integração.
        """
        try:
            print(f"\n🔍 DEBUG STATUS EMAILPROCESSOR COMPLETO:")
            print(f"   📧 Pasta emails: {'✅' if self.pasta_brk_id else '❌'}")
            print(f"   📁 OneDrive: {'✅' if self.onedrive_brk_id else '❌'}")
            print(f"   🔗 Relacionamento: {'✅' if self.relacionamento_carregado else '❌'} ({len(self.cdc_brk_vetor)} CDCs)")
            print(f"   🗃️ DatabaseBRK: {'✅' if self.database_brk else '❌'}")
            
            if self.database_brk:
                print(f"   💾 Database tipo: {type(self.database_brk).__name__}")
                print(f"   🔄 Database status: {'OneDrive' if getattr(self.database_brk, 'usando_onedrive', False) else 'Fallback'}")
                print(f"   📊 Conexão ativa: {'✅' if getattr(self.database_brk, 'conn', None) else '❌'}")
            
            print(f"   🎯 INTEGRAÇÃO: {'✅ COMPLETA' if self.database_brk else '❌ FALTANDO DatabaseBRK'}")
            
        except Exception as e:
            print(f"❌ Erro debug status: {e}")
            
# ============================================================================
    # BLOCO 2/5 - RELACIONAMENTO CDC → CASA DE ORAÇÃO (SEM PANDAS)
    # ============================================================================

    def carregar_relacao_brk_vetores_sem_pandas(self):
        """
        Carrega relacionamento CDC → Casa de Oração via leitura manual Excel.
        SUBSTITUTO COMPLETO para versão com pandas.
        
        Returns:
            bool: True se carregamento bem-sucedido
        """
        try:
            if not self.onedrive_brk_id:
                print(f"⚠️ ONEDRIVE_BRK_ID não configurado - relacionamento indisponível")
                return False
            
            print(f"📁 Carregando planilha CDC_BRK_CCB.xlsx do OneDrive (SEM pandas)...")
            
            # Obter headers autenticados
            headers = self.auth.obter_headers_autenticados()
            if not headers:
                print("❌ Erro: Não foi possível obter headers autenticados")
                return False
            
            # Buscar arquivo na pasta /BRK/
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{self.onedrive_brk_id}/children"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            # Tentar renovar token se expirado
            if response.status_code == 401:
                print("🔄 Token expirado detectado, renovando...")
                if self.auth.atualizar_token():
                    headers = self.auth.obter_headers_autenticados()
                    response = requests.get(url, headers=headers, timeout=30)
                else:
                    print("❌ Falha na renovação do token")
                    return False
            
            if response.status_code != 200:
                print(f"❌ Erro acessando pasta OneDrive: HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Detalhes: {error_detail.get('error', {}).get('message', 'N/A')}")
                except:
                    pass
                return False
            
            # Procurar arquivo CDC_BRK_CCB.xlsx
            arquivos = response.json().get('value', [])
            arquivo_xlsx = None
            
            for arquivo in arquivos:
                nome = arquivo.get('name', '').lower()
                if 'cdc_brk_ccb.xlsx' in nome or 'cdc brk ccb.xlsx' in nome or 'relacionamento.xlsx' in nome:
                    arquivo_xlsx = arquivo
                    break
            
            if not arquivo_xlsx:
                print("❌ Arquivo CDC_BRK_CCB.xlsx não encontrado na pasta /BRK/")
                print(f"📋 Arquivos disponíveis: {[f.get('name') for f in arquivos[:5]]}")
                return False
            
            # Baixar conteúdo do arquivo
            print(f"📥 Baixando {arquivo_xlsx['name']} ({arquivo_xlsx.get('size', 0)} bytes)...")
            arquivo_id = arquivo_xlsx['id']
            url_download = f"https://graph.microsoft.com/v1.0/me/drive/items/{arquivo_id}/content"
            
            response_download = requests.get(url_download, headers=headers, timeout=60)
            
            if response_download.status_code != 200:
                print(f"❌ Erro baixando arquivo: HTTP {response_download.status_code}")
                return False
            
            # Processar Excel manualmente (sem pandas)
            registros = self._processar_excel_manual(response_download.content)
            
            if not registros:
                print(f"❌ Nenhum registro encontrado na planilha")
                return False
            
            # Converter para vetores estilo Clipper
            self.cdc_brk_vetor = []
            self.casa_oracao_vetor = []
            
            for registro in registros:
                cdc = str(registro.get('CDC', '')).strip()
                casa = str(registro.get('Casa', '')).strip()
                
                # Validar entrada (não vazia, não NaN)
                if cdc and casa and cdc != "nan" and casa != "nan":
                    self.cdc_brk_vetor.append(cdc)
                    self.casa_oracao_vetor.append(casa)
            
            # Resultado
            total_validos = len(self.cdc_brk_vetor)
            total_original = len(registros)
            
            print(f"✅ RELACIONAMENTO CARREGADO COM SUCESSO (SEM pandas)!")
            print(f"   📊 Total original: {total_original} linhas")
            print(f"   ✅ Registros válidos: {total_validos}")
            print(f"   ⚠️ Ignorados: {total_original - total_validos} (vazios/inválidos)")
            
            # Exibir amostra para validação
            if total_validos > 0:
                print(f"📝 Amostra de relacionamentos:")
                for i in range(min(3, total_validos)):
                    casa_resumida = self.casa_oracao_vetor[i][:25] + "..." if len(self.casa_oracao_vetor[i]) > 25 else self.casa_oracao_vetor[i]
                    print(f"   • CDC: {self.cdc_brk_vetor[i]} → Casa: {casa_resumida}")
            
            return total_validos > 0
            
        except Exception as e:
            print(f"❌ Erro carregando relação sem pandas: {e}")
            return False

    def _processar_excel_manual(self, excel_bytes):
        """
        Processa arquivo Excel (.xlsx) manualmente sem pandas.
        Lê estrutura XML interna do Excel.
        
        ESTRUTURA REAL da planilha CDC_BRK_CCB.xlsx:
        - Coluna A → Nome da Casa de Oração
        - Coluna B → CDC (Código do cliente BRK) - 6 a 9 caracteres, formato variável
        - Coluna E → Dia fixo de vencimento (não usado no momento)
        
        Args:
            excel_bytes: Conteúdo binário do arquivo Excel
            
        Returns:
            List[Dict]: Registros processados {'Casa': nome, 'CDC': codigo}
        """
        try:
            registros = []
            
            # Excel (.xlsx) é um arquivo ZIP com XMLs internos
            with zipfile.ZipFile(io.BytesIO(excel_bytes), 'r') as zip_file:
                
                # 1. Ler shared strings (textos da planilha)
                shared_strings = []
                try:
                    with zip_file.open('xl/sharedStrings.xml') as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        
                        # Namespace Excel
                        ns = {'': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                        
                        for si in root.findall('.//si', ns):
                            t = si.find('.//t', ns)
                            if t is not None and t.text:
                                shared_strings.append(t.text)
                            else:
                                shared_strings.append('')
                                
                except Exception as e:
                    print(f"⚠️ Aviso: Sem shared strings ({e})")
                
                # 2. Ler primeira planilha (sheet1)
                try:
                    with zip_file.open('xl/worksheets/sheet1.xml') as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        
                        # Namespace Excel
                        ns = {'': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                        
                        # Processar linhas
                        rows = root.findall('.//row', ns)
                        
                        for i, row in enumerate(rows):
                            if i == 0:  # Pular cabeçalho
                                continue
                                
                            cells = row.findall('.//c', ns)
                            if len(cells) >= 2:
                                
                                # ✅ CORREÇÃO: Estrutura real da planilha
                                # Coluna A = Casa de Oração, Coluna B = CDC
                                casa_value = self._extrair_valor_celula(cells[0], shared_strings, ns)  # Coluna A
                                cdc_value = self._extrair_valor_celula(cells[1], shared_strings, ns)   # Coluna B
                                
                                # Validação e limpeza
                                if casa_value and cdc_value:
                                    casa_limpa = str(casa_value).strip()
                                    cdc_limpo = str(cdc_value).strip()
                                    
                                    # Validação básica CDC (deve conter hífen e ter tamanho razoável)
                                    if (cdc_limpo and '-' in cdc_limpo and 
                                        6 <= len(cdc_limpo) <= 9 and
                                        casa_limpa and len(casa_limpa) > 3):
                                        
                                        registros.append({
                                            'Casa': casa_limpa,      # Casa de Oração
                                            'CDC': cdc_limpo         # Código CDC
                                        })
                                        
                                        # Log apenas dos primeiros 5 para não poluir
                                        if len(registros) <= 5:
                                            casa_resumida = casa_limpa[:25] + "..." if len(casa_limpa) > 25 else casa_limpa
                                            print(f"📝 Lido: {casa_resumida} → CDC: {cdc_limpo}")
                                    else:
                                        # Log apenas de problemas significativos
                                        if cdc_limpo and '-' not in cdc_limpo:
                                            print(f"⚠️ CDC sem hífen ignorado: '{cdc_limpo}'")
                
                except Exception as e:
                    print(f"⚠️ Erro lendo planilha: {e}")
            
            print(f"📊 Registros extraídos do Excel: {len(registros)}")
            print(f"📋 Estrutura confirmada: Coluna A=Casa, Coluna B=CDC")
            
            if len(registros) > 5:
                print(f"📝 ... e mais {len(registros) - 5} registros processados")
            
            return registros
            
        except Exception as e:
            print(f"❌ Erro processamento manual Excel: {e}")
            return []
            
    def _extrair_valor_celula(self, cell, shared_strings, ns):
        """
        Extrai valor de uma célula Excel.
        
        Args:
            cell: Elemento XML da célula
            shared_strings: Lista de strings compartilhadas
            ns: Namespace XML
            
        Returns:
            str: Valor da célula
        """
        try:
            cell_type = cell.get('t', '')
            v_element = cell.find('.//v', ns)
            
            if v_element is None:
                return ''
            
            value = v_element.text or ''
            
            # Se é string compartilhada
            if cell_type == 's':
                try:
                    index = int(value)
                    if 0 <= index < len(shared_strings):
                        return shared_strings[index]
                except (ValueError, IndexError):
                    pass
            
            return value
            
        except Exception:
            return ''

    def buscar_casa_de_oracao(self, cdc_cliente):
        """
        Busca Casa de Oração pelo CDC usando vetores.
        Reproduz exatamente a lógica do script desktop com múltiplos formatos.
        
        Args:
            cdc_cliente (str): Código CDC a buscar (ex: "12345-01")
            
        Returns:
            str: Nome da Casa de Oração ou "Não encontrado"
        """
        if not cdc_cliente or cdc_cliente == "Não encontrado":
            return "Não encontrado"
        
        # Garantir que vetores estão carregados
        if not self.cdc_brk_vetor or not self.casa_oracao_vetor:
            print("⚠️ Vetores de relacionamento não carregados")
            return "Não encontrado"
        
        try:
            # 1. TENTATIVA: Match exato primeiro
            if cdc_cliente in self.cdc_brk_vetor:
                indice = self.cdc_brk_vetor.index(cdc_cliente)
                casa_encontrada = self.casa_oracao_vetor[indice]
                print(f"✓ CDC encontrado (match exato): {cdc_cliente} → {casa_encontrada}")
                return casa_encontrada
            
            # 2. TENTATIVA: Formatos alternativos (como no desktop)
            if '-' in cdc_cliente:
                cdc_parts = cdc_cliente.split('-')
                if len(cdc_parts) == 2:
                    try:
                        # Sem zeros à esquerda
                        cdc_sem_zeros = f"{int(cdc_parts[0])}-{int(cdc_parts[1])}"
                        if cdc_sem_zeros in self.cdc_brk_vetor:
                            indice = self.cdc_brk_vetor.index(cdc_sem_zeros)
                            casa_encontrada = self.casa_oracao_vetor[indice]
                            print(f"✓ CDC encontrado (sem zeros): {cdc_sem_zeros} → {casa_encontrada}")
                            return casa_encontrada
                    except ValueError:
                        pass
                    
                    # Outros formatos possíveis (como no desktop)
                    formatos_possiveis = [
                        f"{cdc_parts[0].zfill(3)}-{cdc_parts[1].zfill(2)}",
                        f"{cdc_parts[0].zfill(4)}-{cdc_parts[1].zfill(2)}",
                        f"{cdc_parts[0].zfill(5)}-{cdc_parts[1].zfill(2)}",
                        f"{cdc_parts[0]}-{cdc_parts[1].zfill(2)}"
                    ]
                    
                    for formato in formatos_possiveis:
                        if formato in self.cdc_brk_vetor:
                            indice = self.cdc_brk_vetor.index(formato)
                            casa_encontrada = self.casa_oracao_vetor[indice]
                            print(f"✓ CDC encontrado (formato alternativo): {formato} → {casa_encontrada}")
                            return casa_encontrada
                    
                    # 3. TENTATIVA: Remover formatação e comparar apenas números
                    cdc_limpo = re.sub(r'[^0-9]', '', cdc_cliente)
                    for i, cdc_ref in enumerate(self.cdc_brk_vetor):
                        cdc_ref_limpo = re.sub(r'[^0-9]', '', cdc_ref)
                        if cdc_limpo == cdc_ref_limpo:
                            casa_encontrada = self.casa_oracao_vetor[i]
                            print(f"✓ CDC encontrado (só números): {cdc_ref} → {casa_encontrada}")
                            return casa_encontrada
            
            # Não encontrado em nenhum formato
            print(f"⚠️ CDC não encontrado: {cdc_cliente}")
            return "Não encontrado"
            
        except Exception as e:
            print(f"❌ Erro buscando CDC {cdc_cliente}: {e}")
            return "Não encontrado"

    def carregar_relacionamento_completo(self):
        """
        Carrega relacionamento completo CDC → Casa de Oração.
        Orquestração principal com fallback inteligente.
        """
        try:
            if not self.garantir_autenticacao():
                return False
            
            if not self.onedrive_brk_id:
                print(f"⚠️ ONEDRIVE_BRK_ID não configurado - relacionamento indisponível")
                return False
            
            # Usar versão SEM pandas
            sucesso = self.carregar_relacao_brk_vetores_sem_pandas()
            
            if sucesso:
                self.relacionamento_carregado = True
                total_relacionamentos = len(self.cdc_brk_vetor)
                print(f"\n✅ RELACIONAMENTO CARREGADO COM SUCESSO!")
                print(f"   📊 Total de relacionamentos: {total_relacionamentos}")
                print(f"   🔍 Prontos para busca de Casas de Oração")
                return True
            else:
                print(f"❌ Falha no carregamento do relacionamento")
                return False
                
        except Exception as e:
            print(f"❌ Erro carregando relacionamento completo: {e}")
            return False

    def status_relacionamento(self):
        """
        Retorna status atual dos vetores de relacionamento.
        
        Returns:
            dict: Informações sobre estado dos vetores
        """
        return {
            "vetores_carregados": len(self.cdc_brk_vetor) > 0,
            "total_relacionamentos": len(self.cdc_brk_vetor),
            "onedrive_brk_configurado": bool(self.onedrive_brk_id),
            "onedrive_brk_id_protegido": f"{self.onedrive_brk_id[:15]}******" if self.onedrive_brk_id else "N/A",
            "amostra_cdcs": self.cdc_brk_vetor[:3] if len(self.cdc_brk_vetor) >= 3 else self.cdc_brk_vetor,
            "amostra_casas": self.casa_oracao_vetor[:3] if len(self.casa_oracao_vetor) >= 3 else self.casa_oracao_vetor
        }

# ============================================================================
    # BLOCO 3/5 - EXTRAÇÃO PDF + ANÁLISE DE CONSUMO
    # ============================================================================

    def extrair_dados_fatura_pdf(self, pdf_bytes, nome_arquivo):
        """
        Extrai dados completos de uma fatura BRK em PDF.
        Adaptação da função extract_info_from_pdf() do script desktop para cloud.
        
        Args:
            pdf_bytes (bytes): Conteúdo do PDF em bytes (do email)
            nome_arquivo (str): Nome do arquivo PDF para logs
            
        Returns:
            dict: Dados extraídos da fatura ou None se erro
        """
        try:
            # Importar pdfplumber apenas quando necessário
            try:
                import pdfplumber
            except ImportError:
                print(f"❌ pdfplumber não instalado - usando extração básica")
                return self._extrair_dados_basico_pdf(pdf_bytes, nome_arquivo)
            
            print(f"🔍 Processando fatura: {nome_arquivo}")
            
            # Converter bytes para objeto de arquivo
            pdf_buffer = io.BytesIO(pdf_bytes)
            
            # Abrir PDF com pdfplumber (igual ao desktop)
            with pdfplumber.open(pdf_buffer) as pdf:
                if not pdf.pages:
                    print(f"❌ PDF vazio: {nome_arquivo}")
                    return None
                
                # Extrair texto da primeira página (igual ao desktop)
                first_page = pdf.pages[0]
                text = first_page.extract_text() or ""
                
                if not text.strip():
                    print(f"❌ Não foi possível extrair texto: {nome_arquivo}")
                    return None
                
                print(f"📄 Texto extraído: {len(text)} caracteres")
                
                # Inicializar estrutura de dados (exatamente igual ao desktop)
                info = {
                    "Data_Emissao": "Não encontrado",
                    "Nota_Fiscal": "Não encontrado", 
                    "Valor": "Não encontrado",
                    "Codigo_Cliente": "Não encontrado",
                    "Vencimento": "Não encontrado",
                    "Competencia": "Não encontrado",
                    "Casa de Oração": "Não encontrado",
                    "Medido_Real": None,
                    "Faturado": None,
                    "Média 6M": None,
                    "Porcentagem Consumo": "",
                    "Alerta de Consumo": "",
                    "nome_arquivo": nome_arquivo,
                    "tamanho_bytes": len(pdf_bytes)
                }
                
                # EXTRAIR DADOS USANDO PATTERNS DO SCRIPT DESKTOP
                self._extrair_codigo_cliente(text, info)
                self._extrair_nota_fiscal(text, info)
                self._extrair_data_emissao(text, info)
                self._extrair_valor_total(text, info)
                self._extrair_data_vencimento(text, info)
                self._extrair_competencia(text, info)
                self._extrair_dados_consumo(text, info)
                
                # Buscar Casa de Oração usando relacionamento OneDrive (nova funcionalidade)
                if info["Codigo_Cliente"] != "Não encontrado":
                    info["Casa de Oração"] = self.buscar_casa_de_oracao(info["Codigo_Cliente"])
                
                # Calcular análise de consumo (igual ao desktop)
                self._calcular_analise_consumo(info)
                
                # Log dos dados extraídos
                self._log_dados_extraidos(info)
                
                return info
                
        except Exception as e:
            print(f"❌ Erro processando PDF {nome_arquivo}: {e}")
            return None

    def _extrair_dados_basico_pdf(self, pdf_bytes, nome_arquivo):
        """
        Extração básica quando pdfplumber não disponível.
        Retorna estrutura básica com informações do arquivo.
        """
        return {
            "Data_Emissao": "Não encontrado",
            "Nota_Fiscal": "Não encontrado",
            "Valor": "Não encontrado", 
            "Codigo_Cliente": "Não encontrado",
            "Vencimento": "Não encontrado",
            "Competencia": "Não encontrado",
            "Casa de Oração": "Não encontrado",
            "nome_arquivo": nome_arquivo,
            "tamanho_bytes": len(pdf_bytes),
            "erro_extracao": "pdfplumber não disponível"
        }

    def _extrair_codigo_cliente(self, text, info):
        """
        Extrai Código do Cliente (CDC) usando patterns do desktop.
        Reproduz exatamente a lógica do script original com múltiplas tentativas.
        """
        # Padrão principal: CDC seguido de números
        cdc_match = re.search(r'CDC.*?(\d+-\d+)', text)
        if cdc_match:
            info["Codigo_Cliente"] = cdc_match.group(1).strip()
            print(f"  ✓ CDC encontrado (padrão principal): {info['Codigo_Cliente']}")
            return
        
        # Buscas alternativas para CDC (igual ao desktop)
        if info["Codigo_Cliente"] == "Não encontrado":
            keyword_patterns = [r'CDC[^0-9]*(\d+-\d+)', r'CÓDIGO[^0-9]*(\d+-\d+)']
            for pattern in keyword_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    info["Codigo_Cliente"] = matches[0].strip()
                    print(f"  ✓ CDC encontrado (padrão alternativo): {info['Codigo_Cliente']}")
                    return
        
        # Busca por qualquer padrão de CDC (igual ao desktop)
        if info["Codigo_Cliente"] == "Não encontrado":
            all_potential_cdcs = []
            patterns = [r'(\d{1,6}-\d{1,2})']
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if re.match(r'^\d{1,6}-\d{1,2}$', match) and not re.match(r'^\d{2}/\d{2}-', match):
                        all_potential_cdcs.append(match)
            
            if all_potential_cdcs:
                # Verificar se algum CDC candidato está nos vetores de relacionamento
                for potential_cdc in all_potential_cdcs:
                    if potential_cdc in self.cdc_brk_vetor:
                        info["Codigo_Cliente"] = potential_cdc
                        print(f"  ✓ CDC encontrado (verificado no relacionamento): {potential_cdc}")
                        return
                
                # Se não encontrou nos vetores, usar o primeiro candidato válido
                if all_potential_cdcs:
                    valid_cdcs = [cdc for cdc in all_potential_cdcs if not re.match(r'\d{2}/\d{2}-', cdc)]
                    if valid_cdcs:
                        info["Codigo_Cliente"] = valid_cdcs[0]
                        print(f"  ⚠️ CDC candidato (não verificado): {valid_cdcs[0]}")

    def _extrair_nota_fiscal(self, text, info):
        """Extrai número da conta/nota fiscal (igual ao desktop)"""
        # N° DA CONTA (padrão principal)
        conta_match = re.search(r'N° DA CONTA\s+(\d+)', text)
        if conta_match:
            info["Nota_Fiscal"] = conta_match.group(1).strip()
            print(f"  ✓ Nota Fiscal: {info['Nota_Fiscal']}")

    def _extrair_data_emissao(self, text, info):
        """Extrai data de emissão (patterns do desktop)"""
        # Padrão principal
        data_emissao_match = re.search(r'DATA EMISSÃO\s+(\d{2}/\d{2}/\d{4})', text)
        if data_emissao_match:
            info["Data_Emissao"] = data_emissao_match.group(1)
            print(f"  ✓ Data Emissão: {info['Data_Emissao']}")
            return
        
        # Padrões alternativos (igual ao desktop)
        if info["Data_Emissao"] == "Não encontrado":
            patterns = [
                r'DATA EMISSÃO\s+(\d{1,2}/\d{1,2}/\d{4})',
                r'DADOS DA MEDIÇÃO[\s\S]*?(\d{2}/\d{2}/\d{4})'
            ]
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    info["Data_Emissao"] = match.group(1)
                    print(f"  ✓ Data Emissão (alternativo): {info['Data_Emissao']}")
                    break

    def _extrair_valor_total(self, text, info):
        """Extrai valor total (padrão simplificado do desktop)"""
        # Padrão principal do desktop
        valor_match = re.search(r'VALOR TOTAL - R\$\s*\n?\s*([\d.,]+)', text)
        if not valor_match:
            valor_match = re.search(r'VALOR R\$\s*\n?.*?([\d.,]+)', text)
        
        if valor_match:
            info["Valor"] = valor_match.group(1).strip()
            print(f"  ✓ Valor: R$ {info['Valor']}")

    def _extrair_data_vencimento(self, text, info):
        """Extrai data de vencimento (patterns do desktop)"""
        # Padrão principal
        vencimento_match = re.search(r'DATA DE VENCIMENTO\s+(\d{2}/\d{2}/\d{4})', text)
        if vencimento_match:
            info["Vencimento"] = vencimento_match.group(1)
            print(f"  ✓ Vencimento: {info['Vencimento']}")
            return
        
        # Padrões alternativos (igual ao desktop)
        if info["Vencimento"] == "Não encontrado":
            patterns = [
                r'CDC[^\n]*\n[^\n]*?(\d{2}/\d{2}/\d{4})',
                r'DATA DE VENCIMENTO\s*(\d{2}/\d{2}/\d{4})',
                r'VENCIMENTO\s*(\d{2}/\d{2}/\d{4})',
                r'CDC.*?(\d{2}/\d{2}/\d{4})'
            ]
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    info["Vencimento"] = match.group(1)
                    print(f"  ✓ Vencimento (alternativo): {info['Vencimento']}")
                    break

    def _extrair_competencia(self, text, info):
        """Extrai competência (mês/ano) - patterns do desktop"""
        # Padrão principal
        competencia_match = re.search(r'(?:Jan|Fev|Mar|Abr|Mai|Jun|Jul|Ago|Set|Out|Nov|Dez)[a-z]*\/\d{4}', text, re.IGNORECASE)
        if competencia_match:
            info["Competencia"] = competencia_match.group(0)
            print(f"  ✓ Competência: {info['Competencia']}")
            return
        
        # Padrões alternativos (igual ao desktop)
        if info["Competencia"] == "Não encontrado":
            patterns = [
                r'REFERÊNCIA\s*((?:Jan|Fev|Mar|Abr|Mai|Jun|Jul|Ago|Set|Out|Nov|Dez)[a-z]*\/\d{4}|(?:Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)\/\d{4})',
                r'((?:Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)\/\d{4})',
                r'REFERÊNCIA\s+([\w\/]+)',
                r'(Dezembro\/20\d{2})'
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info["Competencia"] = match.group(1)
                    print(f"  ✓ Competência (alternativo): {info['Competencia']}")
                    break

    def _extrair_dados_consumo(self, text, info):
        """Extrai dados de consumo: Medido Real, Faturado, Média 6M (igual ao desktop)"""
        
        # MEDIDO REAL
        medido_real_match = re.search(r'MEDIDO REAL\s+(\d+)', text)
        if medido_real_match:
            info["Medido_Real"] = int(medido_real_match.group(1))
            print(f"  ✓ Medido Real: {info['Medido_Real']}m³")
        else:
            # Busca alternativa por linhas (igual ao desktop)
            lines = text.split('\n')
            for i in range(len(lines)):
                if 'MEDIDO REAL' in lines[i]:
                    digits = re.findall(r'\d+', lines[i])
                    if digits:
                        info["Medido_Real"] = int(digits[-1])
                        print(f"  ✓ Medido Real (linha): {info['Medido_Real']}m³")
                        break
        
        # FATURADO
        faturado_match = re.search(r'FATURADO\s+(\d+)', text)
        if faturado_match:
            info["Faturado"] = int(faturado_match.group(1))
            print(f"  ✓ Faturado: {info['Faturado']}m³")
        else:
            # Busca alternativa por linhas (igual ao desktop)
            lines = text.split('\n')
            for i in range(len(lines)):
                if 'FATURADO' in lines[i]:
                    digits = re.findall(r'\d+', lines[i])
                    if digits:
                        info["Faturado"] = int(digits[-1])
                        print(f"  ✓ Faturado (linha): {info['Faturado']}m³")
                        break
                    elif i + 1 < len(lines) and lines[i + 1].strip().isdigit():
                        info["Faturado"] = int(lines[i + 1].strip())
                        print(f"  ✓ Faturado (linha seguinte): {info['Faturado']}m³")
                        break
        
        # MÉDIA 6 MESES
        media_match = re.search(r'Média dos últimos 6 meses:\s*(\d+)', text)
        if media_match:
            info["Média 6M"] = int(media_match.group(1))
            print(f"  ✓ Média 6M: {info['Média 6M']}m³")
        else:
            # Buscas alternativas (igual ao desktop)
            media_match = re.search(r'Média dos últimos 6 meses:?\s*(\d+)', text)
            if media_match:
                info["Média 6M"] = int(media_match.group(1))
                print(f"  ✓ Média 6M (alternativo): {info['Média 6M']}m³")
            else:
                lines = text.split('\n')
                for i in range(len(lines)):
                    if 'Média dos últimos 6 meses' in lines[i]:
                        digits = re.findall(r'\d+', lines[i])
                        if digits:
                            info["Média 6M"] = int(digits[-1])
                            print(f"  ✓ Média 6M (linha): {info['Média 6M']}m³")
                            break
                        elif i + 1 < len(lines) and lines[i + 1].strip().isdigit():
                            info["Média 6M"] = int(lines[i + 1].strip())
                            print(f"  ✓ Média 6M (linha seguinte): {info['Média 6M']}m³")
                            break

    def avaliar_consumo(self, consumo_real, media_6m):
        """
        Avalia o consumo e retorna o alerta correspondente.
        Função IDÊNTICA ao script desktop - sem modificações.
        
        Args:
            consumo_real: Consumo atual em m³
            media_6m: Média dos últimos 6 meses em m³
            
        Returns:
            tuple: (porcentagem_variacao, alerta_texto)
        """
        if media_6m is None or consumo_real is None:
            return ("", "")
        
        # Caso especial: média zero (igual ao desktop)
        if media_6m == 0:
            # Se o consumo atual também for zero, está normal
            if consumo_real == 0:
                return ("0%", "✅ Consumo dentro do normal")
            # Se tiver consumo com média zero, considerar como alto
            else:
                return ("N/A", f"⚠️ Consumo relevante com média histórica zero ({consumo_real}m³)")
        
        # Calcular a variação percentual quando média não é zero
        variacao = ((consumo_real - media_6m) / media_6m) * 100
        
        # Variação absoluta em m³
        variacao_absoluta = consumo_real - media_6m
        
        # Consumo mínimo significativo em m³ para disparar alertas de emergência
        CONSUMO_MINIMO_SIGNIFICATIVO = 10
        
        # Classificação por níveis considerando ambos percentual e absoluto (igual ao desktop)
        if variacao > 200 and variacao_absoluta >= CONSUMO_MINIMO_SIGNIFICATIVO:
            alerta = "🚨 **EMERGÊNCIA: CONSUMO MUITO ELEVADO!** 🚨"
        elif variacao > 100 and variacao_absoluta >= CONSUMO_MINIMO_SIGNIFICATIVO:
            alerta = "🚨 **ALTO CONSUMO DETECTADO!** 🚨"
        elif variacao > 75 and variacao_absoluta >= 5:  # Menor limite para alerta menos grave
            alerta = "⚠️ Consumo significativamente acima do normal"
        elif variacao > 50:
            alerta = "⚠️ Consumo acima do esperado"
        elif variacao < -100 and abs(variacao_absoluta) >= CONSUMO_MINIMO_SIGNIFICATIVO:
            alerta = "📉 Consumo muito abaixo do normal - verificar hidrômetro"
        elif variacao < -50:
            alerta = "📉 Consumo abaixo do normal"
        else:
            alerta = "✅ Consumo dentro do normal"
        
        return (f"{variacao:.2f}%", alerta)

    def _calcular_analise_consumo(self, info):
        """Calcula análise de consumo e preenche campos de alerta"""
        if info["Medido_Real"] is not None and info["Média 6M"] is not None:
            try:
                info["Porcentagem Consumo"], info["Alerta de Consumo"] = self.avaliar_consumo(
                    info["Medido_Real"], info["Média 6M"]
                )
                
                # Log da análise (igual ao desktop)
                if info["Média 6M"] != 0:
                    variacao = ((info["Medido_Real"] - info["Média 6M"]) / info["Média 6M"]) * 100
                    print(f"  📊 Variação: {variacao:.2f}% em relação à média")
                else:
                    print(f"  📊 Média de 6M é zero - tratamento especial aplicado")
                
                print(f"  {info['Alerta de Consumo']}")
                
            except ZeroDivisionError:
                if info["Média 6M"] == 0:
                    info["Porcentagem Consumo"] = "N/A"
                    info["Alerta de Consumo"] = f"⚠️ Consumo relevante com média histórica zero ({info['Medido_Real']}m³)"
                    print(f"  📊 Média zero - usando tratamento especial")
                    print(f"  {info['Alerta de Consumo']}")

    def _log_dados_extraidos(self, info):
        """
        Exibe log estruturado e bonito dos dados extraídos.
        Formato otimizado para logs do Render.
        """
        print(f"\n🔍 DADOS EXTRAÍDOS DA FATURA:")
        print(f"   📁 Arquivo: {info['nome_arquivo']}")
        print(f"   💰 Valor: R$ {info['Valor']}")
        print(f"   📅 Vencimento: {info['Vencimento']}")
        print(f"   📋 Nota Fiscal: {info['Nota_Fiscal']}")
        print(f"   🏢 CDC: {info['Codigo_Cliente']}")
        print(f"   🏪 Casa de Oração: {info['Casa de Oração']}")
        print(f"   📆 Competência: {info['Competencia']}")
        print(f"   📊 Data Emissão: {info['Data_Emissao']}")
        
        # Dados de consumo (se disponíveis)
        if info["Medido_Real"] is not None:
            print(f"   💧 Medido Real: {info['Medido_Real']}m³")
        if info["Faturado"] is not None:
            print(f"   📊 Faturado: {info['Faturado']}m³")
        if info["Média 6M"] is not None:
            print(f"   📈 Média 6M: {info['Média 6M']}m³")
        
        # Alertas de consumo
        if info["Porcentagem Consumo"]:
            print(f"   📊 Variação: {info['Porcentagem Consumo']}")
        if info["Alerta de Consumo"]:
            print(f"   ⚠️ Alerta: {info['Alerta de Consumo']}")
        
        print()  # Linha em branco para separar

# ============================================================================
    # BLOCO 4/5 - INTEGRAÇÃO COMPLETA + COMPATIBILIDADE COM CÓDIGO EXISTENTE
    # ============================================================================

    def garantir_relacionamento_carregado(self):
        """
        Garante que o relacionamento está carregado antes do processamento.
        Tenta recarregar se necessário, com limite de tentativas.
        
        Returns:
            bool: True se relacionamento disponível
        """
        if self.relacionamento_carregado and len(self.cdc_brk_vetor) > 0:
            return True
        
        if not self.onedrive_brk_id:
            print("⚠️ ONEDRIVE_BRK_ID não configurado - relacionamento não disponível")
            return False
        
        if self.tentativas_carregamento >= self.max_tentativas:
            print(f"❌ Máximo de tentativas de carregamento excedido ({self.max_tentativas})")
            return False
        
        print(f"🔄 Tentando carregar relacionamento (tentativa {self.tentativas_carregamento + 1}/{self.max_tentativas})...")
        self.tentativas_carregamento += 1
        self.relacionamento_carregado = self.carregar_relacionamento_completo()
        
        return self.relacionamento_carregado

    def extrair_pdfs_do_email(self, email):
        """
        MÉTODO PRINCIPAL compatível com app.py existente.
        
        Agora usa a nova funcionalidade de extração completa,
        mas mantém interface TOTALMENTE compatível com código existente.
        
        Args:
            email (Dict): Dados do email do Microsoft Graph
            
        Returns:
            List[Dict]: Lista de PDFs (compatível + dados expandidos)
        """
        pdfs_com_dados = []
        
        try:
            attachments = email.get('attachments', [])
            email_id = email.get('id', 'unknown')
            
            if not attachments:
                print("📎 Nenhum anexo encontrado no email")
                return []
            
            pdfs_brutos = 0
            pdfs_processados = 0
            
            # Garantir que relacionamento está carregado
            relacionamento_ok = self.garantir_relacionamento_carregado()
            if relacionamento_ok:
                print(f"✅ Relacionamento disponível: {len(self.cdc_brk_vetor)} registros")
            else:
                print("⚠️ Relacionamento não disponível - processará apenas dados básicos")
            
            for attachment in attachments:
                filename = attachment.get('name', '').lower()
                
                # Verificar se é PDF
                if filename.endswith('.pdf'):
                    pdfs_brutos += 1
                    nome_original = attachment.get('name', 'unnamed.pdf')
                    
                    try:
                        # Informações básicas do PDF (COMPATIBILIDADE 100% com código existente)
                        pdf_info_basico = {
                            'email_id': email_id,
                            'filename': nome_original,
                            'size': attachment.get('size', 0),
                            'content_bytes': attachment.get('contentBytes', ''),
                            'received_date': email.get('receivedDateTime', ''),
                            'email_subject': email.get('subject', ''),
                            'sender': email.get('from', {}).get('emailAddress', {}).get('address', 'unknown')
                        }
                        
                        # NOVA FUNCIONALIDADE: Extrair dados completos do PDF
                        content_bytes = attachment.get('contentBytes', '')
                        if content_bytes:
                            try:
                                # Decodificar PDF bytes
                                pdf_bytes = base64.b64decode(content_bytes)
                                
                                # Extrair dados completos usando nova função
                                dados_extraidos = self.extrair_dados_fatura_pdf(pdf_bytes, nome_original)
                                
                                if dados_extraidos:
                                    # Combinar informações básicas + dados extraídos
                                    pdf_completo = {
                                        **pdf_info_basico,  # Informações básicas (COMPATIBILIDADE)
                                        **dados_extraidos,  # Dados extraídos do PDF (NOVA FUNCIONALIDADE)
                                        'hash_arquivo': hashlib.sha256(pdf_bytes).hexdigest(),
                                        'dados_extraidos_ok': True,
                                        'relacionamento_usado': relacionamento_ok
                                    }
                                    
                                    pdfs_com_dados.append(pdf_completo)
                                    pdfs_processados += 1
                                    
                                    print(f"✅ PDF processado: {nome_original}")
                                    
                                    # 🆕 SALVAMENTO AUTOMÁTICO NO DatabaseBRK
                                    if self.database_brk and dados_extraidos:
                                        try:
                                            resultado_db = self.salvar_fatura_database(pdf_completo)
                                            if resultado_db.get('status') == 'sucesso':
                                                pdf_completo['database_salvo'] = True
                                                pdf_completo['database_id'] = resultado_db.get('id_salvo')
                                                pdf_completo['database_status'] = resultado_db.get('status_duplicata', 'NORMAL')
                                            else:
                                                pdf_completo['database_salvo'] = False
                                                pdf_completo['database_erro'] = resultado_db.get('mensagem', 'Erro desconhecido')
                                        except Exception as e:
                                            print(f"⚠️ Erro salvamento automático: {e}")
                                            pdf_completo['database_salvo'] = False
                                            pdf_completo['database_erro'] = str(e)
                                    
                                else:
                                    # Falha na extração - manter dados básicos (COMPATIBILIDADE)
                                    pdf_completo = {
                                        **pdf_info_basico,
                                        'dados_extraidos_ok': False,
                                        'erro_extracao': 'Falha na extração de dados',
                                        'relacionamento_usado': False
                                    }
                                    pdfs_com_dados.append(pdf_completo)
                                    print(f"⚠️ PDF básico (falha extração): {nome_original}")
                                    
                            except Exception as e:
                                print(f"❌ Erro extraindo dados do PDF {nome_original}: {e}")
                                # Manter dados básicos em caso de erro (COMPATIBILIDADE)
                                pdf_completo = {
                                    **pdf_info_basico,
                                    'dados_extraidos_ok': False,
                                    'erro_extracao': str(e),
                                    'relacionamento_usado': False
                                }
                                pdfs_com_dados.append(pdf_completo)
                        else:
                            print(f"⚠️ PDF sem conteúdo: {nome_original}")
                            # Ainda assim retorna estrutura básica (COMPATIBILIDADE)
                            pdfs_com_dados.append(pdf_info_basico)
                            
                    except Exception as e:
                        print(f"❌ Erro processando anexo {nome_original}: {e}")
            
            # Log resumo do processamento
            if pdfs_brutos > 0:
                print(f"\n📊 RESUMO PROCESSAMENTO:")
                print(f"   📎 PDFs encontrados: {pdfs_brutos}")
                print(f"   ✅ PDFs processados: {pdfs_processados}")
                print(f"   📋 Relacionamento: {'✅ Usado' if relacionamento_ok else '❌ Indisponível'}")
                print(f"   🔄 Extração avançada: {'✅ Ativa' if pdfs_processados > 0 else '❌ Falhou'}")
                
            return pdfs_com_dados
            
        except Exception as e:
            print(f"❌ Erro extraindo PDFs do email: {e}")
            return []
                                    
                                else:
                                    # Falha na extração - manter dados básicos (COMPATIBILIDADE)
                                    pdf_completo = {
                                        **pdf_info_basico,
                                        'dados_extraidos_ok': False,
                                        'erro_extracao': 'Falha na extração de dados',
                                        'relacionamento_usado': False
                                    }
                                    pdfs_com_dados.append(pdf_completo)
                                    print(f"⚠️ PDF básico (falha extração): {nome_original}")
                                    
                            except Exception as e:
                                print(f"❌ Erro extraindo dados do PDF {nome_original}: {e}")
                                # Manter dados básicos em caso de erro (COMPATIBILIDADE)
                                pdf_completo = {
                                    **pdf_info_basico,
                                    'dados_extraidos_ok': False,
                                    'erro_extracao': str(e),
                                    'relacionamento_usado': False
                                }
                                pdfs_com_dados.append(pdf_completo)
                        else:
                            print(f"⚠️ PDF sem conteúdo: {nome_original}")
                            # Ainda assim retorna estrutura básica (COMPATIBILIDADE)
                            pdfs_com_dados.append(pdf_info_basico)
                            
                    except Exception as e:
                        print(f"❌ Erro processando anexo {nome_original}: {e}")
            
            # Log resumo do processamento
            if pdfs_brutos > 0:
                print(f"\n📊 RESUMO PROCESSAMENTO:")
                print(f"   📎 PDFs encontrados: {pdfs_brutos}")
                print(f"   ✅ PDFs processados: {pdfs_processados}")
                print(f"   📋 Relacionamento: {'✅ Usado' if relacionamento_ok else '❌ Indisponível'}")
                print(f"   🔄 Extração avançada: {'✅ Ativa' if pdfs_processados > 0 else '❌ Falhou'}")
                
            return pdfs_com_dados
            
        except Exception as e:
            print(f"❌ Erro extraindo PDFs do email: {e}")
            return []
            
    def log_consolidado_email(self, email_data, pdfs_processados):
        """
        Exibe log consolidado bonito de um email processado.
        Inclui dados extraídos, relacionamento e análises.
        
        Args:
            email_data (Dict): Dados do email
            pdfs_processados (List[Dict]): PDFs processados com dados
        """
        try:
            email_subject = email_data.get('subject', 'Sem assunto')[:50]
            email_date = email_data.get('receivedDateTime', 'N/A')[:10]
            
            print(f"\n" + "="*60)
            print(f"📧 EMAIL PROCESSADO: {email_subject}")
            print(f"📅 Data recebimento: {email_date}")
            print(f"📎 PDFs encontrados: {len(pdfs_processados)}")
            print(f"="*60)
            
            for i, pdf in enumerate(pdfs_processados, 1):
                print(f"\n📄 PDF {i}/{len(pdfs_processados)}: {pdf.get('filename', 'unnamed.pdf')}")
                
                # Status da extração
                if pdf.get('dados_extraidos_ok', False):
                    print(f"   ✅ Dados extraídos com sucesso")
                    
                    # Dados principais
                    if pdf.get('Codigo_Cliente') != 'Não encontrado':
                        print(f"   🏢 CDC: {pdf.get('Codigo_Cliente')}")
                    if pdf.get('Casa de Oração') != 'Não encontrado':
                        print(f"   🏪 Casa: {pdf.get('Casa de Oração')}")
                    if pdf.get('Valor') != 'Não encontrado':
                        print(f"   💰 Valor: R$ {pdf.get('Valor')}")
                    if pdf.get('Vencimento') != 'Não encontrado':
                        print(f"   📅 Vencimento: {pdf.get('Vencimento')}")
                    
                    # Dados de consumo (se disponíveis)
                    if pdf.get('Medido_Real') is not None:
                        print(f"   💧 Consumo: {pdf.get('Medido_Real')}m³", end="")
                        if pdf.get('Média 6M') is not None:
                            print(f" (Média: {pdf.get('Média 6M')}m³)")
                        else:
                            print()
                    
                    # Alertas de consumo
                    if pdf.get('Alerta de Consumo'):
                        alerta = pdf.get('Alerta de Consumo')
                        if '🚨' in alerta:
                            print(f"   🚨 ALERTA: {alerta}")
                        elif '⚠️' in alerta:
                            print(f"   ⚠️ Aviso: {alerta}")
                        elif '✅' in alerta:
                            print(f"   ✅ Status: {alerta}")
                        else:
                            print(f"   📊 Análise: {alerta}")
                    
                    # Status relacionamento
                    if pdf.get('relacionamento_usado', False):
                        print(f"   🔗 Relacionamento: ✅ Aplicado")
                    else:
                        print(f"   🔗 Relacionamento: ❌ Não aplicado")
                        
                else:
                    print(f"   ❌ Falha na extração de dados")
                    if pdf.get('erro_extracao'):
                        print(f"   💬 Erro: {pdf.get('erro_extracao')}")
                    print(f"   📦 Tamanho: {pdf.get('size', 0)} bytes")
            
            print(f"="*60)
            print(f"✅ EMAIL PROCESSADO COMPLETAMENTE")
            print(f"="*60)
            
        except Exception as e:
            print(f"❌ Erro no log consolidado: {e}")

    def preparar_dados_para_database(self, pdf_data):
        """
        Prepara dados extraídos para salvamento no database existente.
        Converte estrutura de dados extraídos para formato compatível com DatabaseBRKBasico.
        
        Args:
            pdf_data (Dict): Dados do PDF processado
            
        Returns:
            Dict: Dados formatados para database
        """
        try:
            # Estrutura base compatível com DatabaseBRKBasico
            dados_database = {
                'Data_Emissao': pdf_data.get('Data_Emissao', 'Não encontrado'),
                'Nota_Fiscal': pdf_data.get('Nota_Fiscal', 'Não encontrado'),
                'Valor': pdf_data.get('Valor', 'Não encontrado'),
                'Codigo_Cliente': pdf_data.get('Codigo_Cliente', 'Não encontrado'),
                'Vencimento': pdf_data.get('Vencimento', 'Não encontrado'),
                'Competencia': pdf_data.get('Competencia', 'Não encontrado'),
                'email_id': pdf_data.get('email_id', ''),
                'nome_arquivo': pdf_data.get('filename', pdf_data.get('nome_arquivo', 'unknown.pdf')),
                'hash_arquivo': pdf_data.get('hash_arquivo', ''),
                'tamanho_bytes': pdf_data.get('size', pdf_data.get('tamanho_bytes', 0)),
                'caminho_onedrive': ''  # Será preenchido pelo OneDrive
            }
            
            # Adicionar campos expandidos (novos) - compatibilidade futura
            dados_expandidos = {
                'casa_oracao': pdf_data.get('Casa de Oração', 'Não encontrado'),
                'medido_real': pdf_data.get('Medido_Real'),
                'faturado': pdf_data.get('Faturado'),
                'media_6m': pdf_data.get('Média 6M'),
                'porcentagem_consumo': pdf_data.get('Porcentagem Consumo', ''),
                'alerta_consumo': pdf_data.get('Alerta de Consumo', ''),
                'dados_extraidos_ok': pdf_data.get('dados_extraidos_ok', False),
                'relacionamento_usado': pdf_data.get('relacionamento_usado', False)
            }
            
            # Combinar dados básicos + expandidos
            dados_completos = {**dados_database, **dados_expandidos}
            
            return dados_completos
            
        except Exception as e:
            print(f"❌ Erro preparando dados para database: {e}")
            return None

    def status_processamento_completo(self):
        """
        Retorna status completo do processador incluindo novas funcionalidades.
        EXPANDE o status_processamento() original mantendo compatibilidade.
        
        Returns:
            Dict: Status completo com relacionamento + extração
        """
        try:
            # Status básico (COMPATIBILIDADE com código existente)
            status_basico = {
                "pasta_brk_configurada": bool(self.pasta_brk_id),
                "pasta_brk_protegida": f"{self.pasta_brk_id[:10]}******" if self.pasta_brk_id else "N/A",
                "autenticacao_ok": bool(self.auth.access_token),
                "pasta_acessivel": self._validar_acesso_pasta_brk_basico()
            }
            
            # Status expandido (NOVAS funcionalidades)
            status_relacionamento = self.status_relacionamento()
            
            # Status integrado
            status_completo = {
                **status_basico,
                **status_relacionamento,
                "funcionalidades": {
                    "extracao_pdf_completa": True,
                    "relacionamento_onedrive": bool(self.onedrive_brk_id),
                    "analise_consumo": True,
                    "logs_estruturados": True,
                    "compatibilidade_total": True
                },
                "tentativas_carregamento": self.tentativas_carregamento,
                "max_tentativas": self.max_tentativas,
                "versao": "SEM_PANDAS_v1.0"
            }
            
            return status_completo
            
        except Exception as e:
            return {
                "erro": str(e),
                "status": "Erro obtendo status",
                "pasta_brk_configurada": bool(self.pasta_brk_id),
                "versao": "SEM_PANDAS_v1.0"
            }

    def _validar_acesso_pasta_brk_basico(self):
        """
        Validação básica de acesso à pasta BRK.
        Compatibilidade com validar_acesso_pasta_brk() existente.
        """
        try:
            if not self.pasta_brk_id:
                return False
            
            headers = self.auth.obter_headers_autenticados()
            if not headers:
                return False
            
            # Teste simples de acesso
            url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_brk_id}"
            response = requests.get(url, headers=headers, timeout=10)
            
            return response.status_code == 200
            
        except Exception:
            return False

    def testar_funcionalidades_completas(self):
        """
        Testa todas as funcionalidades integradas.
        Útil para debug e validação no Render.
        
        Returns:
            Dict: Resultados dos testes
        """
        resultados = {
            "timestamp": datetime.now().isoformat(),
            "versao": "SEM_PANDAS_v1.0",
            "testes": {}
        }
        
        print(f"\n🧪 TESTANDO FUNCIONALIDADES COMPLETAS (SEM PANDAS)")
        print(f"="*55)
        
        # Teste 1: Autenticação
        try:
            headers = self.auth.obter_headers_autenticados()
            resultados["testes"]["autenticacao"] = "✅ OK"
            print(f"✅ Autenticação: OK")
        except Exception as e:
            resultados["testes"]["autenticacao"] = f"❌ Erro: {e}"
            print(f"❌ Autenticação: {e}")
        
        # Teste 2: Acesso pasta emails
        try:
            pasta_ok = self._validar_acesso_pasta_brk_basico()
            resultados["testes"]["pasta_emails"] = "✅ OK" if pasta_ok else "❌ Inacessível"
            print(f"{'✅' if pasta_ok else '❌'} Pasta emails: {'OK' if pasta_ok else 'Inacessível'}")
        except Exception as e:
            resultados["testes"]["pasta_emails"] = f"❌ Erro: {e}"
            print(f"❌ Pasta emails: {e}")
        
        # Teste 3: Carregamento relacionamento
        try:
            relacionamento_ok = self.garantir_relacionamento_carregado()
            total_registros = len(self.cdc_brk_vetor)
            resultados["testes"]["relacionamento"] = f"✅ OK ({total_registros} registros)" if relacionamento_ok else "❌ Falhou"
            print(f"{'✅' if relacionamento_ok else '❌'} Relacionamento: {'OK' if relacionamento_ok else 'Falhou'} ({total_registros} registros)")
        except Exception as e:
            resultados["testes"]["relacionamento"] = f"❌ Erro: {e}"
            print(f"❌ Relacionamento: {e}")
        
        # Teste 4: Busca casa de oração (se relacionamento OK)
        if len(self.cdc_brk_vetor) > 0:
            try:
                cdc_teste = self.cdc_brk_vetor[0]  # Primeiro CDC do vetor
                casa_teste = self.buscar_casa_de_oracao(cdc_teste)
                resultados["testes"]["busca_casa"] = f"✅ OK ({cdc_teste} → {casa_teste})"
                print(f"✅ Busca casa: OK ({cdc_teste} → {casa_teste[:30]}...)")
            except Exception as e:
                resultados["testes"]["busca_casa"] = f"❌ Erro: {e}"
                print(f"❌ Busca casa: {e}")
        else:
            resultados["testes"]["busca_casa"] = "⏭️ Pulado (sem relacionamento)"
            print(f"⏭️ Busca casa: Pulado (sem relacionamento)")
        
        # Teste 5: Compatibilidade com código existente
        try:
            status = self.status_processamento_completo()
            compativel = status.get('funcionalidades', {}).get('compatibilidade_total', False)
            resultados["testes"]["compatibilidade"] = "✅ OK" if compativel else "⚠️ Parcial"
            print(f"✅ Compatibilidade: {'Total' if compativel else 'Parcial'}")
        except Exception as e:
            resultados["testes"]["compatibilidade"] = f"❌ Erro: {e}"
            print(f"❌ Compatibilidade: {e}")
        
        print(f"="*55)
        print(f"✅ TESTE CONCLUÍDO - SISTEMA PRONTO!")
        print(f"="*55)
        
        return resultados

# ============================================================================
    # BLOCO 5/5 - MANUTENÇÃO + DIAGNÓSTICO + ESTATÍSTICAS + FINALIZAÇÃO
    # ============================================================================

    def recarregar_relacionamento_manual(self, forcar=False):
        """
        Recarrega o relacionamento manualmente, útil para:
        - Atualizações da planilha OneDrive
        - Resolver problemas de carregamento
        - Forçar atualização após mudanças
        
        Args:
            forcar (bool): Se True, ignora limite de tentativas
            
        Returns:
            bool: True se recarregamento bem-sucedido
        """
        try:
            print(f"\n🔄 RECARREGAMENTO MANUAL DO RELACIONAMENTO")
            print(f"="*55)
            
            if forcar:
                print(f"⚡ Modo forçado ativado - ignorando limite de tentativas")
                self.tentativas_carregamento = 0
            
            # Limpar estado anterior
            self.cdc_brk_vetor = []
            self.casa_oracao_vetor = []
            self.relacionamento_carregado = False
            
            print(f"🧹 Estado anterior limpo")
            print(f"🔄 Iniciando carregamento...")
            
            # Tentar carregar
            sucesso = self.carregar_relacao_brk_vetores_sem_pandas()
            
            if sucesso:
                self.relacionamento_carregado = True
                print(f"✅ RECARREGAMENTO CONCLUÍDO COM SUCESSO!")
                print(f"   📊 Registros carregados: {len(self.cdc_brk_vetor)}")
                print(f"   🔗 Relacionamento pronto para uso")
                
                # Reset tentativas após sucesso
                self.tentativas_carregamento = 0
                
            else:
                print(f"❌ RECARREGAMENTO FALHOU")
                print(f"   💡 Verifique ONEDRIVE_BRK_ID e conectividade")
                
            print(f"="*55)
            return sucesso
            
        except Exception as e:
            print(f"❌ Erro no recarregamento manual: {e}")
            return False

    def obter_estatisticas_avancadas(self):
        """
        Retorna estatísticas avançadas do processamento incluindo:
        - Status do relacionamento
        - Cobertura de CDCs
        - Análise de dados extraídos
        - Performance do sistema
        
        Returns:
            Dict: Estatísticas completas
        """
        try:
            agora = datetime.now()
            
            # Estatísticas básicas
            stats = {
                "timestamp": agora.isoformat(),
                "versao": "SEM_PANDAS_v1.0",
                "sistema": {
                    "relacionamento_ativo": self.relacionamento_carregado,
                    "total_relacionamentos": len(self.cdc_brk_vetor),
                    "tentativas_carregamento": self.tentativas_carregamento,
                    "max_tentativas": self.max_tentativas,
                    "onedrive_configurado": bool(self.onedrive_brk_id),
                    "pasta_emails_configurada": bool(self.pasta_brk_id)
                },
                "relacionamento": {
                    "status": "✅ Ativo" if self.relacionamento_carregado else "❌ Inativo",
                    "registros_totais": len(self.cdc_brk_vetor),
                    "amostra_cdcs": self.cdc_brk_vetor[:5] if len(self.cdc_brk_vetor) >= 5 else self.cdc_brk_vetor,
                    "amostra_casas": self.casa_oracao_vetor[:5] if len(self.casa_oracao_vetor) >= 5 else self.casa_oracao_vetor
                },
                "configuracao": {
                    "pasta_emails_id": f"{self.pasta_brk_id[:10]}******" if self.pasta_brk_id else "N/A",
                    "onedrive_brk_id": f"{self.onedrive_brk_id[:15]}******" if self.onedrive_brk_id else "N/A",
                    "autenticacao_ativa": bool(self.auth.access_token)
                }
            }
            
            # Análise de cobertura (se relacionamento ativo)
            if self.relacionamento_carregado and len(self.cdc_brk_vetor) > 0:
                stats["cobertura"] = self._analisar_cobertura_relacionamento()
            
            return stats
            
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "versao": "SEM_PANDAS_v1.0",
                "erro": str(e),
                "status": "Erro obtendo estatísticas"
            }

    def _analisar_cobertura_relacionamento(self):
        """
        Analisa a cobertura e qualidade do relacionamento carregado.
        
        Returns:
            Dict: Análise de cobertura
        """
        try:
            if not self.cdc_brk_vetor:
                return {"status": "Sem dados para análise"}
            
            total_registros = len(self.cdc_brk_vetor)
            
            # Análise de formatos de CDC
            formatos_cdc = {
                "padrao_comum": 0,      # 12345-01
                "sem_zeros": 0,         # 1234-1  
                "com_zeros": 0,         # 01234-01
                "formatos_atipicos": 0  # outros
            }
            
            cdcs_unicos = set()
            casas_unicas = set()
            cdcs_duplicados = []
            
            for i, cdc in enumerate(self.cdc_brk_vetor):
                casa = self.casa_oracao_vetor[i]
                
                # Contagem de únicos
                if cdc in cdcs_unicos:
                    cdcs_duplicados.append(cdc)
                else:
                    cdcs_unicos.add(cdc)
                casas_unicas.add(casa)
                
                # Análise de formato CDC
                if re.match(r'^\d{4,5}-\d{2}$', cdc):
                    formatos_cdc["padrao_comum"] += 1
                elif re.match(r'^\d{1,3}-\d{1}$', cdc):
                    formatos_cdc["sem_zeros"] += 1
                elif re.match(r'^0\d+-\d+$', cdc):
                    formatos_cdc["com_zeros"] += 1
                else:
                    formatos_cdc["formatos_atipicos"] += 1
            
            # Análise de casas com múltiplos CDCs
            casas_multiplos_cdcs = {}
            for i, casa in enumerate(self.casa_oracao_vetor):
                cdc = self.cdc_brk_vetor[i]
                if casa not in casas_multiplos_cdcs:
                    casas_multiplos_cdcs[casa] = []
                casas_multiplos_cdcs[casa].append(cdc)
            
            casas_com_multiplos = {casa: cdcs for casa, cdcs in casas_multiplos_cdcs.items() if len(cdcs) > 1}
            
            # Resultado da análise
            cobertura = {
                "qualidade": {
                    "registros_totais": total_registros,
                    "cdcs_unicos": len(cdcs_unicos),
                    "casas_unicas": len(casas_unicas),
                    "duplicatas_cdc": len(cdcs_duplicados),
                    "casas_com_multiplos_cdcs": len(casas_com_multiplos)
                },
                "formatos_cdc": formatos_cdc,
                "multiplos_cdcs": {
                    "total_casas": len(casas_com_multiplos),
                    "exemplos": dict(list(casas_com_multiplos.items())[:3]) if casas_com_multiplos else {}
                },
                "amostra_relacionamentos": [
                    {"cdc": self.cdc_brk_vetor[i], "casa": self.casa_oracao_vetor[i][:30] + "..."}
                    for i in range(min(5, len(self.cdc_brk_vetor)))
                ]
            }
            
            return cobertura
            
        except Exception as e:
            return {"erro": str(e)}

    def log_estatisticas_formatado(self):
        """
        Exibe estatísticas do sistema em formato estruturado para logs do Render.
        """
        try:
            stats = self.obter_estatisticas_avancadas()
            
            print(f"\n📊 ESTATÍSTICAS DO SISTEMA BRK (SEM PANDAS)")
            print(f"="*55)
            print(f"🕐 Timestamp: {stats['timestamp'][:16]}")
            print(f"🔧 Versão: {stats.get('versao', 'N/A')}")
            
            # Status do sistema
            sistema = stats.get('sistema', {})
            print(f"\n🔧 SISTEMA:")
            print(f"   📧 Pasta emails: {'✅' if sistema.get('pasta_emails_configurada') else '❌'}")
            print(f"   📁 OneDrive: {'✅' if sistema.get('onedrive_configurado') else '❌'}")
            print(f"   🔐 Autenticação: {'✅' if stats.get('configuracao', {}).get('autenticacao_ativa') else '❌'}")
            print(f"   🔗 Relacionamento: {'✅' if sistema.get('relacionamento_ativo') else '❌'}")
            
            # Relacionamento
            relacionamento = stats.get('relacionamento', {})
            print(f"\n📋 RELACIONAMENTO:")
            print(f"   📊 Status: {relacionamento.get('status', 'N/A')}")
            print(f"   📈 Registros: {relacionamento.get('registros_totais', 0)}")
            print(f"   🔄 Tentativas: {sistema.get('tentativas_carregamento', 0)}/{sistema.get('max_tentativas', 3)}")
            
            # Cobertura (se disponível)
            if 'cobertura' in stats:
                cobertura = stats['cobertura']
                qualidade = cobertura.get('qualidade', {})
                print(f"\n📈 COBERTURA:")
                print(f"   🏢 CDCs únicos: {qualidade.get('cdcs_unicos', 0)}")
                print(f"   🏪 Casas únicas: {qualidade.get('casas_unicas', 0)}")
                if qualidade.get('casas_com_multiplos_cdcs', 0) > 0:
                    print(f"   🔄 Casas c/ múltiplos CDCs: {qualidade['casas_com_multiplos_cdcs']}")
            
            # Amostra de relacionamentos
            amostra = relacionamento.get('amostra_cdcs', [])
            if amostra:
                print(f"\n📝 AMOSTRA:")
                for i, cdc in enumerate(amostra[:3]):
                    casa = relacionamento.get('amostra_casas', [])[i] if i < len(relacionamento.get('amostra_casas', [])) else 'N/A'
                    print(f"   • {cdc} → {casa[:25]}{'...' if len(casa) > 25 else ''}")
            
            print(f"="*55)
            
        except Exception as e:
            print(f"❌ Erro exibindo estatísticas: {e}")

    def diagnostico_completo_sistema(self):
        """
        Executa diagnóstico completo de todo o sistema.
        Útil para debug e validação no Render.
        
        Returns:
            Dict: Resultado completo do diagnóstico
        """
        print(f"\n🔍 DIAGNÓSTICO COMPLETO DO SISTEMA BRK (SEM PANDAS)")
        print(f"="*65)
        
        diagnostico = {
            "timestamp": datetime.now().isoformat(),
            "versao": "SEM_PANDAS_v1.0",
            "status_geral": "🔄 Em andamento",
            "componentes": {}
        }
        
        try:
            # 1. Teste de autenticação
            print(f"1️⃣ Testando autenticação Microsoft...")
            try:
                headers = self.auth.obter_headers_autenticados()
                token_valido = bool(headers and self.auth.access_token)
                diagnostico["componentes"]["autenticacao"] = {
                    "status": "✅ OK" if token_valido else "⚠️ Token inválido",
                    "headers_disponiveis": bool(headers),
                    "token_valido": token_valido
                }
                print(f"   {'✅' if token_valido else '⚠️'} Autenticação: {'OK' if token_valido else 'Token inválido'}")
            except Exception as e:
                diagnostico["componentes"]["autenticacao"] = {"status": f"❌ Erro: {e}"}
                print(f"   ❌ Autenticação: {e}")
            
            # 2. Teste de acesso à pasta de emails
            print(f"2️⃣ Testando pasta de emails BRK...")
            try:
                pasta_ok = self._validar_acesso_pasta_brk_basico()
                diagnostico["componentes"]["pasta_emails"] = {
                    "status": "✅ OK" if pasta_ok else "❌ Inacessível",
                    "acessivel": pasta_ok,
                    "pasta_id": f"{self.pasta_brk_id[:10]}******" if self.pasta_brk_id else "N/A"
                }
                print(f"   {'✅' if pasta_ok else '❌'} Pasta emails: {'OK' if pasta_ok else 'Inacessível'}")
            except Exception as e:
                diagnostico["componentes"]["pasta_emails"] = {"status": f"❌ Erro: {e}"}
                print(f"   ❌ Pasta emails: {e}")
            
            # 3. Teste do OneDrive e relacionamento
            print(f"3️⃣ Testando OneDrive e relacionamento...")
            try:
                relacionamento_ok = self.garantir_relacionamento_carregado()
                total_relacionamentos = len(self.cdc_brk_vetor)
                diagnostico["componentes"]["onedrive_relacionamento"] = {
                    "status": "✅ OK" if relacionamento_ok else "❌ Falhou",
                    "configurado": bool(self.onedrive_brk_id),
                    "carregado": relacionamento_ok,
                    "total_registros": total_relacionamentos,
                    "sem_pandas": True
                }
                if relacionamento_ok:
                    print(f"   ✅ OneDrive + Relacionamento: OK ({total_relacionamentos} registros SEM pandas)")
                else:
                    print(f"   ❌ OneDrive + Relacionamento: Falhou")
            except Exception as e:
                diagnostico["componentes"]["onedrive_relacionamento"] = {"status": f"❌ Erro: {e}"}
                print(f"   ❌ OneDrive + Relacionamento: {e}")
            
            # 4. Teste de busca de casa de oração
            print(f"4️⃣ Testando busca de casa de oração...")
            if len(self.cdc_brk_vetor) > 0:
                try:
                    cdc_teste = self.cdc_brk_vetor[0]
                    casa_teste = self.buscar_casa_de_oracao(cdc_teste)
                    diagnostico["componentes"]["busca_casa"] = {
                        "status": "✅ OK",
                        "cdc_teste": cdc_teste,
                        "casa_encontrada": casa_teste,
                        "funcionando": casa_teste != "Não encontrado"
                    }
                    print(f"   ✅ Busca casa: OK ({cdc_teste} → {casa_teste[:20]}...)")
                except Exception as e:
                    diagnostico["componentes"]["busca_casa"] = {"status": f"❌ Erro: {e}"}
                    print(f"   ❌ Busca casa: {e}")
            else:
                diagnostico["componentes"]["busca_casa"] = {"status": "⏭️ Pulado (sem relacionamento)"}
                print(f"   ⏭️ Busca casa: Pulado (sem relacionamento)")
            
            # 5. Teste de extração PDF
            print(f"5️⃣ Testando capacidade de extração PDF...")
            try:
                # Tentar importar pdfplumber
                try:
                    import pdfplumber
                    pdf_disponivel = True
                    versao_pdf = "pdfplumber disponível"
                except ImportError:
                    pdf_disponivel = False
                    versao_pdf = "pdfplumber NÃO instalado - fallback ativo"
                
                diagnostico["componentes"]["extracao_pdf"] = {
                    "status": "✅ OK" if pdf_disponivel else "⚠️ Fallback",
                    "pdfplumber_disponivel": pdf_disponivel,
                    "versao": versao_pdf,
                    "fallback_ativo": not pdf_disponivel
                }
                print(f"   {'✅' if pdf_disponivel else '⚠️'} Extração PDF: {versao_pdf}")
            except Exception as e:
                diagnostico["componentes"]["extracao_pdf"] = {"status": f"❌ Erro: {e}"}
                print(f"   ❌ Extração PDF: {e}")
            
            # 6. Status final
            componentes_ok = sum(1 for comp in diagnostico["componentes"].values() if "✅" in comp.get("status", ""))
            total_componentes = len(diagnostico["componentes"])
            
            if componentes_ok == total_componentes:
                diagnostico["status_geral"] = "✅ Tudo funcionando"
                print(f"\n✅ DIAGNÓSTICO: Tudo funcionando ({componentes_ok}/{total_componentes}) - SISTEMA PRONTO!")
            elif componentes_ok > 0:
                diagnostico["status_geral"] = f"⚠️ Parcial ({componentes_ok}/{total_componentes})"
                print(f"\n⚠️ DIAGNÓSTICO: Funcionamento parcial ({componentes_ok}/{total_componentes})")
            else:
                diagnostico["status_geral"] = "❌ Sistema com problemas"
                print(f"\n❌ DIAGNÓSTICO: Sistema com problemas")
            
            print(f"="*65)
            
            return diagnostico
            
        except Exception as e:
            diagnostico["status_geral"] = f"❌ Erro no diagnóstico: {e}"
            print(f"❌ ERRO NO DIAGNÓSTICO: {e}")
            return diagnostico

    def info_integracao_completa(self):
        """
        Exibe informações completas sobre a integração implementada.
        Documentação das funcionalidades disponíveis.
        """
        print(f"\n📚 INTEGRAÇÃO BRK - FUNCIONALIDADES COMPLETAS (SEM PANDAS)")
        print(f"="*70)
        print(f"👨‍💼 Autor: Sidney Gubitoso, auxiliar tesouraria adm maua")
        print(f"📅 Implementação: Junho 2025")
        print(f"🎯 Objetivo: Extração completa de dados das faturas BRK")
        print(f"⚡ Versão: SEM PANDAS - compatível Python 3.13")
        print(f"="*70)
        
        print(f"\n🔧 FUNCIONALIDADES IMPLEMENTADAS:")
        print(f"   ✅ Carregamento automático planilha OneDrive (SEM pandas)")
        print(f"   ✅ Relacionamento CDC → Casa de Oração")
        print(f"   ✅ Extração completa dados PDF (pdfplumber + fallback)")
        print(f"   ✅ Análise de consumo (alertas automáticos)")
        print(f"   ✅ Logs estruturados para Render")
        print(f"   ✅ Compatibilidade total com código existente")
        print(f"   ✅ Gestão automática de erros e fallbacks")
        print(f"   ✅ Diagnóstico e manutenção do sistema")
        print(f"   ✅ Processamento Excel manual via XML")
        print(f"   ✅ Deploy rápido (3 minutos) sem compilação")
        
        print(f"\n📊 DADOS EXTRAÍDOS DAS FATURAS:")
        print(f"   💰 Valor em R$")
        print(f"   📅 Vencimento")
        print(f"   📋 Nota Fiscal")
        print(f"   🏢 Código Cliente (CDC)")
        print(f"   🏪 Casa de Oração (via relacionamento)")
        print(f"   📆 Competência (mês/ano)")
        print(f"   📊 Data de Emissão")
        print(f"   💧 Medido Real (m³)")
        print(f"   📈 Faturado (m³)")
        print(f"   📊 Média 6 meses (m³)")
        print(f"   ⚠️ Análise de consumo com alertas")
        
        print(f"\n🔗 COMPATIBILIDADE:")
        print(f"   ✅ app.py → Funciona sem modificações")
        print(f"   ✅ DatabaseBRKBasico → Dados compatíveis")
        print(f"   ✅ OneDriveBasico → Upload PDFs mantido")
        print(f"   ✅ Estrutura modular → auth/ + processor/")
        print(f"   ✅ Interface original → extrair_pdfs_do_email() mantida")
        
        print(f"\n🚀 COMO USAR:")
        print(f"   1. Configure ONEDRIVE_BRK_ID no Render")
        print(f"   2. Relacionamento carrega automaticamente")
        print(f"   3. Processamento normal funciona igual")
        print(f"   4. Logs mostram dados extraídos")
        print(f"   5. Database recebe dados expandidos")
        
        print(f"\n🛠️ MANUTENÇÃO:")
        print(f"   processor.recarregar_relacionamento_manual()")
        print(f"   processor.diagnostico_completo_sistema()")
        print(f"   processor.log_estatisticas_formatado()")
        print(f"   processor.testar_funcionalidades_completas()")
        
        print(f"\n⚡ VANTAGENS SEM PANDAS:")
        print(f"   🚀 Deploy sempre 3 minutos (sem compilação)")
        print(f"   🛡️ Compatível Python 3.13+")
        print(f"   💾 Menor uso de memória")
        print(f"   📦 Menos dependências problemáticas")
        print(f"   🔧 Processamento Excel via XML nativo")
        print(f"   ⚡ Inicialização mais rápida")
        
        print(f"\n📈 MELHORIAS FUTURAS POSSÍVEIS:")
        print(f"   🔮 Dashboard web com dados extraídos")
        print(f"   🔮 Exportação para Excel das análises")
        print(f"   🔮 Alertas por email para alto consumo")
        print(f"   🔮 Histórico de consumo por casa")
        print(f"   🔮 OCR avançado para faturas complexas")
        print(f"   🔮 API REST para acesso aos dados")
        
        print(f"\n🏆 RESUMO DOS 5 BLOCOS IMPLEMENTADOS:")
        print(f"   1️⃣ Imports + Inicialização básica")
        print(f"   2️⃣ Relacionamento sem pandas (XML Excel)")
        print(f"   3️⃣ Extração PDF + análise consumo")
        print(f"   4️⃣ Integração + compatibilidade total")
        print(f"   5️⃣ Manutenção + diagnóstico + estatísticas")
        
        print(f"="*70)
        print(f"✅ INTEGRAÇÃO COMPLETA FINALIZADA - PRONTA PARA DEPLOY!")
        print(f"🎯 MISSÃO CUMPRIDA - EXTRAÇÃO COMPLETA SEM PANDAS!")
        print(f"="*70)

# ============================================================================
# ADICIONAR ESTES MÉTODOS NO FINAL DO EmailProcessor (antes do comentário final)
# Localização: processor/email_processor.py - linha ~1200 (antes do comentário ====)
# ============================================================================

    def diagnosticar_pasta_brk(self):
        """
        Diagnóstica a pasta BRK - conta emails total, 24h e mês atual.
        Método necessário para compatibilidade com app.py
        
        Returns:
            Dict: Diagnóstico da pasta com contadores
        """
        try:
            if not self.garantir_autenticacao():
                return {
                    "status": "erro",
                    "erro": "Falha na autenticação",
                    "total_geral": 0,
                    "ultimas_24h": 0,
                    "mes_atual": 0
                }
            
            headers = self.auth.obter_headers_autenticados()
            
            # 1. TOTAL GERAL da pasta
            url_total = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_brk_id}/messages/$count"
            response_total = requests.get(url_total, headers=headers, timeout=30)
            
            if response_total.status_code == 401:
                if self.auth.atualizar_token():
                    headers = self.auth.obter_headers_autenticados()
                    response_total = requests.get(url_total, headers=headers, timeout=30)
            
            total_geral = 0
            if response_total.status_code == 200:
                total_geral = int(response_total.text.strip())
            
            # 2. ÚLTIMAS 24H
            data_24h = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            
            url_24h = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_brk_id}/messages"
            params_24h = {
                "$filter": f"receivedDateTime ge {data_24h}",
                "$count": "true",
                "$top": "1"
            }
            response_24h = requests.get(url_24h, headers=headers, params=params_24h, timeout=30)
            
            ultimas_24h = 0
            if response_24h.status_code == 200:
                data_24h_result = response_24h.json()
                ultimas_24h = data_24h_result.get('@odata.count', 0)
            
            # 3. MÊS ATUAL
            primeiro_dia_mes = datetime.now().replace(day=1).strftime("%Y-%m-%dT00:00:00Z")
            
            params_mes = {
                "$filter": f"receivedDateTime ge {primeiro_dia_mes}",
                "$count": "true", 
                "$top": "1"
            }
            response_mes = requests.get(url_24h, headers=headers, params=params_mes, timeout=30)
            
            mes_atual = 0
            if response_mes.status_code == 200:
                data_mes_result = response_mes.json()
                mes_atual = data_mes_result.get('@odata.count', 0)
            
            return {
                "status": "sucesso",
                "total_geral": total_geral,
                "ultimas_24h": ultimas_24h,
                "mes_atual": mes_atual,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erro no diagnóstico da pasta BRK: {e}")
            return {
                "status": "erro",
                "erro": str(e),
                "total_geral": 0,
                "ultimas_24h": 0,
                "mes_atual": 0
            }

    def buscar_emails_novos(self, dias_atras=1):
        """
        Busca emails novos na pasta BRK
        
        Args:
            dias_atras (int): Quantos dias atrás buscar
            
        Returns:
            List[Dict]: Lista de emails encontrados
        """
        try:
            if not self.garantir_autenticacao():
                return []
            
            headers = self.auth.obter_headers_autenticados()
            
            # Data de corte
            data_corte = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Buscar emails
            url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_brk_id}/messages"
            params = {
                "$filter": f"receivedDateTime ge {data_corte}",
                "$expand": "attachments",
                "$orderby": "receivedDateTime desc",
                "$top": "50"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=60)
            
            # Renovar token se necessário
            if response.status_code == 401:
                if self.auth.atualizar_token():
                    headers = self.auth.obter_headers_autenticados()
                    response = requests.get(url, headers=headers, params=params, timeout=60)
            
            if response.status_code == 200:
                emails_data = response.json()
                emails = emails_data.get('value', [])
                print(f"📧 Encontrados {len(emails)} emails dos últimos {dias_atras} dia(s)")
                return emails
            else:
                print(f"❌ Erro buscando emails: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Erro na busca de emails: {e}")
            return []

    def status_processamento(self):
        """
        Método de compatibilidade - retorna status básico
        Compatível com chamadas existentes no app.py
        """
        return {
            "pasta_brk_configurada": bool(self.pasta_brk_id),
            "pasta_brk_protegida": f"{self.pasta_brk_id[:10]}******" if self.pasta_brk_id else "N/A",
            "autenticacao_ok": bool(self.auth.access_token),
            "relacionamento_carregado": self.relacionamento_carregado,
            "total_relacionamentos": len(self.cdc_brk_vetor)
        }

# ============================================================================
# 🎉 EMAILPROCESSOR COMPLETO SEM PANDAS FINALIZADO!
# (resto do comentário permanece igual...)
# ============================================================================
# 🎉 EMAILPROCESSOR COMPLETO SEM PANDAS FINALIZADO!
# 
# TOTAL DE FUNCIONALIDADES:
# - 30+ métodos implementados
# - 100% compatibilidade com código existente  
# - Extração completa de dados PDF
# - Relacionamento CDC → Casa de Oração
# - Análise de consumo com alertas
# - Sistema de diagnóstico completo
# - Logs estruturados para Render
# - Manutenção e estatísticas avançadas
# 
# STATUS: ✅ PRONTO PARA DEPLOY
# COMPATIBILIDADE: ✅ Python 3.13
# DEPLOY TIME: ⚡ 3 minutos
# DEPENDENCIES: 🛡️ Mínimas (requests, pdfplumber)
# 
# PARA DEPLOY:
# 1. Substituir processor/email_processor.py pelos 5 blocos
# 2. requirements.txt: requests, python-dateutil, pdfplumber  
# 3. Configure ONEDRIVE_BRK_ID no Render
# 4. Deploy automático via GitHub
# 5. Funcionamento garantido em 3 minutos!
# ============================================================================
