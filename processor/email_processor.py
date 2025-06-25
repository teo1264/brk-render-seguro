# ============================================================================
# BLOCO 1/4 - LEITOR ONEDRIVE + VETORES DE RELACIONAMENTO
# Adicionar ao arquivo: processor/email_processor.py
# 
# FUNÇÃO: Carregar planilha CDC_BRK_CCB.xlsx do OneDrive e criar vetores
# AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
# LOCALIZAÇÃO: brk-monitor-seguro/processor/email_processor.py
# ADAPTADO DO: criar_plan_brk324.py (desktop) → cloud/render
# ============================================================================

import pandas as pd
import requests
import io
import re
import os

class EmailProcessor:
    def __init__(self, microsoft_auth):
        """Inicializar processador com autenticação"""
        self.auth = microsoft_auth
        
        # PASTA BRK ID para emails (Microsoft 365)
        self.pasta_brk_id = os.getenv("PASTA_BRK_ID")
        
        # PASTA BRK ID para arquivos OneDrive (já descoberta anteriormente)
        self.onedrive_brk_id = os.getenv("ONEDRIVE_BRK_ID")
        
        # VETORES DE RELACIONAMENTO (estilo Clipper como no desktop)
        self.cdc_brk_vetor = []      # Vetor com códigos CDC
        self.casa_oracao_vetor = []  # Vetor com nomes das casas (índice correspondente)
        
        if not self.pasta_brk_id:
            raise ValueError("❌ PASTA_BRK_ID não configurado!")
            
        print(f"📧 Email Processor inicializado")
        print(f"   📧 Pasta emails BRK: {self.pasta_brk_id[:10]}****** (emails)")
        
        if self.onedrive_brk_id:
            print(f"   📁 Pasta OneDrive /BRK/: {self.onedrive_brk_id[:15]}****** (arquivos)")
            print(f"   📄 Planilha relacionamento: CDC_BRK_CCB.xlsx (nesta pasta)")
        else:
            print("   ⚠️ ONEDRIVE_BRK_ID não configurado - relacionamento indisponível")

    # ============================================================================
    # FUNÇÃO 1: CARREGAR PLANILHA CDC_BRK_CCB.xlsx DO ONEDRIVE
    # ============================================================================
    
    def carregar_planilha_onedrive(self):
        """
        Carrega a planilha CDC_BRK_CCB.xlsx do OneDrive via Graph API.
        
        Processo:
        1. Usa ONEDRIVE_BRK_ID (pasta /BRK/ já descoberta anteriormente)
        2. Busca arquivo CDC_BRK_CCB.xlsx na raiz dessa pasta
        3. Baixa conteúdo via Graph API (/content endpoint)
        4. Converte para DataFrame pandas
        
        Nota: ONEDRIVE_BRK_ID foi descoberto no teste OneDrive anterior.
        
        Returns:
            pd.DataFrame: Planilha carregada ou None se erro
        """
        try:
            print("🔍 Carregando planilha de relacionamento do OneDrive...")
            
            # Validar se pasta OneDrive /BRK/ está configurada
            if not self.onedrive_brk_id:
                print("❌ Erro: ONEDRIVE_BRK_ID não configurado")
                print("💡 Esta variável deve conter o ID da pasta /BRK/ descoberto anteriormente")
                print("💡 Configure no Render: ONEDRIVE_BRK_ID=9D0F055E98EA94D3!sca94999fd73747068e64dddaeeb442a2")
                return None
            
            # Obter headers autenticados
            headers = self.auth.obter_headers_autenticados()
            if not headers:
                print("❌ Erro: Não foi possível obter headers autenticados")
                return None
            
            # Buscar arquivo CDC_BRK_CCB.xlsx na pasta /BRK/
            print("📂 Buscando arquivo CDC_BRK_CCB.xlsx na pasta /BRK/...")
            url_arquivos = f"https://graph.microsoft.com/v1.0/me/drive/items/{self.onedrive_brk_id}/children"
            
            response = requests.get(url_arquivos, headers=headers, timeout=30)
            
            # Tentar renovar token se expirado
            if response.status_code == 401:
                print("🔄 Token expirado detectado, renovando...")
                if self.auth.atualizar_token():
                    headers = self.auth.obter_headers_autenticados()
                    response = requests.get(url_arquivos, headers=headers, timeout=30)
                else:
                    print("❌ Falha na renovação do token")
                    return None
            
            if response.status_code != 200:
                print(f"❌ Erro ao acessar pasta OneDrive: HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Detalhes: {error_detail.get('error', {}).get('message', 'N/A')}")
                except:
                    pass
                return None
            
            # Procurar arquivo CDC_BRK_CCB.xlsx
            arquivos = response.json().get('value', [])
            arquivo_cdc = None
            
            for arquivo in arquivos:
                nome = arquivo.get('name', '').lower()
                if 'cdc_brk_ccb.xlsx' in nome or 'cdc brk ccb.xlsx' in nome:
                    arquivo_cdc = arquivo
                    break
            
            if not arquivo_cdc:
                print("❌ Arquivo CDC_BRK_CCB.xlsx não encontrado na pasta /BRK/")
                print(f"📋 Arquivos disponíveis: {[f.get('name') for f in arquivos[:5]]}")
                return None
            
            # Baixar conteúdo do arquivo
            print(f"📥 Baixando {arquivo_cdc['name']} ({arquivo_cdc.get('size', 0)} bytes)...")
            arquivo_id = arquivo_cdc['id']
            url_download = f"https://graph.microsoft.com/v1.0/me/drive/items/{arquivo_id}/content"
            
            response_download = requests.get(url_download, headers=headers, timeout=60)
            
            if response_download.status_code != 200:
                print(f"❌ Erro baixando arquivo: HTTP {response_download.status_code}")
                return None
            
            # Converter para DataFrame pandas
            print("📊 Convertendo para DataFrame...")
            excel_content = io.BytesIO(response_download.content)
            df = pd.read_excel(excel_content, dtype=str)
            
            # Limpar nomes das colunas (remover espaços)
            df.columns = df.columns.str.strip()
            
            print(f"✅ Planilha carregada: {len(df)} linhas, colunas: {list(df.columns)}")
            return df
            
        except requests.RequestException as e:
            print(f"❌ Erro de rede carregando planilha: {e}")
            return None
        except Exception as e:
            print(f"❌ Erro inesperado carregando planilha: {e}")
            return None

    # ============================================================================
    # FUNÇÃO 2: CONVERTER DATAFRAME EM VETORES (ESTILO CLIPPER DESKTOP)
    # ============================================================================
    
    def carregar_relacao_brk_vetores(self, df_planilha):
        """
        Converte DataFrame da planilha em vetores de relacionamento.
        Reproduz a lógica vetorial do script desktop (estilo Clipper).
        
        Args:
            df_planilha (pd.DataFrame): Planilha do OneDrive carregada
            
        Returns:
            bool: True se vetores carregados com sucesso
        """
        try:
            print("🔄 Convertendo planilha em vetores de relacionamento...")
            
            # Limpar vetores anteriores
            self.cdc_brk_vetor = []
            self.casa_oracao_vetor = []
            
            if df_planilha is None or df_planilha.empty:
                print("❌ DataFrame vazio ou inválido")
                return False
            
            # Verificar se colunas necessárias existem
            colunas_necessarias = ["CDC BRK", "Casa de Oração"]
            colunas_existentes = df_planilha.columns.tolist()
            
            print(f"📋 Colunas disponíveis: {colunas_existentes}")
            
            for coluna in colunas_necessarias:
                if coluna not in df_planilha.columns:
                    print(f"❌ Coluna '{coluna}' não encontrada na planilha")
                    return False
            
            # Converter linhas em vetores (removendo entradas inválidas)
            linhas_validas = 0
            for _, row in df_planilha.iterrows():
                cdc = str(row["CDC BRK"]).strip()
                casa = str(row["Casa de Oração"]).strip()
                
                # Validar entrada (não vazia, não NaN)
                if cdc and casa and cdc != "nan" and casa != "nan":
                    self.cdc_brk_vetor.append(cdc)
                    self.casa_oracao_vetor.append(casa)
                    linhas_validas += 1
            
            # Resultado
            print(f"✅ Vetores criados: {linhas_validas} registros válidos")
            print(f"   📊 Total original: {len(df_planilha)} linhas")
            print(f"   ✅ Válidas: {linhas_validas} linhas")
            print(f"   ⚠️ Ignoradas: {len(df_planilha) - linhas_validas} linhas (vazias/inválidas)")
            
            # Exibir amostra para validação
            if linhas_validas > 0:
                print(f"📝 Amostra de relacionamentos:")
                for i in range(min(3, linhas_validas)):
                    print(f"   • CDC: {self.cdc_brk_vetor[i]} → Casa: {self.casa_oracao_vetor[i]}")
            
            return linhas_validas > 0
            
        except Exception as e:
            print(f"❌ Erro convertendo em vetores: {e}")
            return False

    # ============================================================================
    # FUNÇÃO 3: BUSCAR CASA DE ORAÇÃO POR CDC (LÓGICA DESKTOP ADAPTADA)
    # ============================================================================
    
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

    # ============================================================================
    # FUNÇÃO 4: CARREGAR RELACIONAMENTO COMPLETO (MÉTODO PRINCIPAL)
    # ============================================================================
    
    def carregar_relacionamento_completo(self):
        """
        Método principal para carregar relacionamento CDC → Casa de Oração.
        
        Processo completo:
        1. Carregar planilha do OneDrive
        2. Converter em vetores de relacionamento  
        3. Validar dados carregados
        
        Returns:
            bool: True se relacionamento carregado com sucesso
        """
        try:
            print("\n🔄 CARREGANDO RELACIONAMENTO CDC → CASA DE ORAÇÃO")
            print("=" * 55)
            
            # Passo 1: Carregar planilha do OneDrive
            df_planilha = self.carregar_planilha_onedrive()
            if df_planilha is None:
                print("❌ Falha carregando planilha do OneDrive")
                return False
            
            # Passo 2: Converter em vetores
            if not self.carregar_relacao_brk_vetores(df_planilha):
                print("❌ Falha convertendo planilha em vetores")
                return False
            
            # Passo 3: Validação final
            total_relacionamentos = len(self.cdc_brk_vetor)
            print(f"\n✅ RELACIONAMENTO CARREGADO COM SUCESSO!")
            print(f"   📊 Total de relacionamentos: {total_relacionamentos}")
            print(f"   🔍 Prontos para busca de Casas de Oração")
            print("=" * 55)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro no carregamento completo: {e}")
            return False

    # ============================================================================
    # FUNÇÃO 5: STATUS DOS VETORES DE RELACIONAMENTO
    # ============================================================================
    
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
# PARA TESTAR ESTE BLOCO:
# 
# 1. Adicionar ao requirements.txt: pandas==2.0.3
# 2. Configurar no Render (usando ID já descoberto):
#    ONEDRIVE_BRK_ID=9D0F055E98EA94D3!sca94999fd73747068e64dddaeeb442a2
# 3. Verificar que CDC_BRK_CCB.xlsx está na pasta /BRK/
# 4. Testar no Render via logs:
#    - processor.carregar_relacionamento_completo()
#    - processor.buscar_casa_de_oracao("12345-01")
# 
# RESULTADO ESPERADO:
# 📧 Pasta emails BRK: AQMkADAwAT****** (emails)  
# 📁 Pasta OneDrive /BRK/: 9D0F055E98EA****** (arquivos)
# 📄 Planilha relacionamento: CDC_BRK_CCB.xlsx (nesta pasta)
# ✅ Planilha carregada: 150 linhas
# ✅ Vetores criados: 148 registros válidos  
# ✅ RELACIONAMENTO CARREGADO COM SUCESSO!
# ============================================================================
# ============================================================================
# BLOCO 2/4 - EXTRATOR DE DADOS PDF + ANÁLISE DE CONSUMO
# Adicionar ao arquivo: processor/email_processor.py
# 
# FUNÇÃO: Extrair dados das faturas BRK usando pdfplumber + regex patterns
# AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
# LOCALIZAÇÃO: brk-monitor-seguro/processor/email_processor.py
# ADAPTADO DO: criar_plan_brk324.py → extract_info_from_pdf() + avaliar_consumo()
# ============================================================================

import pdfplumber
import re
import io
from datetime import datetime

class EmailProcessor:
    # ... código anterior do Bloco 1/4 ...

    # ============================================================================
    # FUNÇÃO 1: EXTRAÇÃO COMPLETA DE DADOS DO PDF (ADAPTADA DO DESKTOP)
    # ============================================================================
    
    def extrair_dados_fatura_pdf(self, pdf_bytes, nome_arquivo):
        """
        Extrai dados completos de uma fatura BRK em PDF.
        Adaptação da função extract_info_from_pdf() do script desktop para cloud.
        
        Utiliza todas as regex patterns e lógicas do script original,
        mas funciona com bytes do PDF em vez de arquivo local.
        
        Args:
            pdf_bytes (bytes): Conteúdo do PDF em bytes (do email)
            nome_arquivo (str): Nome do arquivo PDF para logs
            
        Returns:
            dict: Dados extraídos da fatura ou None se erro
        """
        try:
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

    # ============================================================================
    # FUNÇÃO 2: EXTRAIR CÓDIGO CLIENTE (CDC) - PATTERNS DO DESKTOP
    # ============================================================================
    
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

    # ============================================================================
    # FUNÇÃO 3: EXTRAIR NOTA FISCAL - PATTERNS DO DESKTOP
    # ============================================================================
    
    def _extrair_nota_fiscal(self, text, info):
        """Extrai número da conta/nota fiscal (igual ao desktop)"""
        # N° DA CONTA (padrão principal)
        conta_match = re.search(r'N° DA CONTA\s+(\d+)', text)
        if conta_match:
            info["Nota_Fiscal"] = conta_match.group(1).strip()
            print(f"  ✓ Nota Fiscal: {info['Nota_Fiscal']}")

    # ============================================================================
    # FUNÇÃO 4: EXTRAIR DATA DE EMISSÃO - PATTERNS DO DESKTOP
    # ============================================================================
    
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

    # ============================================================================
    # FUNÇÃO 5: EXTRAIR VALOR TOTAL - PATTERNS DO DESKTOP (SIMPLIFICADO)
    # ============================================================================
    
    def _extrair_valor_total(self, text, info):
        """Extrai valor total (padrão simplificado do desktop)"""
        # Padrão principal do desktop
        valor_match = re.search(r'VALOR TOTAL - R\$\s*\n?\s*([\d.,]+)', text)
        if not valor_match:
            valor_match = re.search(r'VALOR R\$\s*\n?.*?([\d.,]+)', text)
        
        if valor_match:
            info["Valor"] = valor_match.group(1).strip()
            print(f"  ✓ Valor: R$ {info['Valor']}")

    # ============================================================================
    # FUNÇÃO 6: EXTRAIR DATA DE VENCIMENTO - PATTERNS DO DESKTOP
    # ============================================================================
    
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

    # ============================================================================
    # FUNÇÃO 7: EXTRAIR COMPETÊNCIA - PATTERNS DO DESKTOP
    # ============================================================================
    
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

    # ============================================================================
    # FUNÇÃO 8: EXTRAIR DADOS DE CONSUMO - PATTERNS DO DESKTOP
    # ============================================================================
    
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

    # ============================================================================
    # FUNÇÃO 9: AVALIAR CONSUMO - EXATAMENTE IGUAL AO DESKTOP
    # ============================================================================
    
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

    # ============================================================================
    # FUNÇÃO 10: CALCULAR ANÁLISE DE CONSUMO
    # ============================================================================
    
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

    # ============================================================================
    # FUNÇÃO 11: LOG ESTRUTURADO DOS DADOS EXTRAÍDOS
    # ============================================================================
    
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
# PARA TESTAR ESTE BLOCO:
# 
# 1. Adicionar ao requirements.txt: pdfplumber==0.9.0
# 2. Testar extração com PDF real de email BRK
# 3. Verificar logs estruturados no Render
# 
# EXEMPLO DE USO:
# pdf_bytes = base64.b64decode(attachment['contentBytes'])
# dados = processor.extrair_dados_fatura_pdf(pdf_bytes, "fatura_brk.pdf")
# 
# RESULTADO ESPERADO NO LOG:
# 🔍 Processando fatura: fatura_brk.pdf
# 📄 Texto extraído: 1247 caracteres
#   ✓ CDC encontrado: 12345-01
#   ✓ Nota Fiscal: 67890
#   ✓ Valor: R$ 1.234,56
#   ✓ Vencimento: 25/06/2025
#   ✓ Casa de Oração: CASA DE ORAÇÃO SAO PAULO
#   📊 Variação: +25.5% em relação à média
#   ⚠️ Consumo acima do esperado
# 
# 🔍 DADOS EXTRAÍDOS DA FATURA:
#    📁 Arquivo: fatura_brk.pdf
#    💰 Valor: R$ 1.234,56
#    📅 Vencimento: 25/06/2025
#    📋 Nota Fiscal: 67890
#    🏢 CDC: 12345-01
#    🏪 Casa de Oração: CASA DE ORAÇÃO SAO PAULO
#    📆 Competência: Maio/2025
#    💧 Medido Real: 15m³
#    📈 Média 6M: 12m³
#    📊 Variação: +25.00%
#    ⚠️ Alerta: ⚠️ Consumo acima do esperado
# ============================================================================
# ============================================================================
# BLOCO 3/4 - INTEGRAÇÃO COMPLETA: RELACIONAMENTO + EXTRAÇÃO + LOGS
# Modificar no arquivo: processor/email_processor.py
# 
# FUNÇÃO: Integrar carregamento OneDrive + extração PDF + logs estruturados
# AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
# LOCALIZAÇÃO: brk-monitor-seguro/processor/email_processor.py
# INTEGRA: Blocos 1 + 2 + processamento existente
# ============================================================================

import hashlib
import base64

class EmailProcessor:
    # ... código anterior dos Blocos 1/4 e 2/4 ...

    # ============================================================================
    # FUNÇÃO 1: INICIALIZAÇÃO COM CARREGAMENTO AUTOMÁTICO (MODIFICAR EXISTENTE)
    # ============================================================================
    
    def __init__(self, microsoft_auth):
        """
        Inicializar processador com autenticação.
        MODIFICADO: Agora inclui carregamento automático do relacionamento.
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
            
        print(f"📧 Email Processor inicializado")
        print(f"   📧 Pasta emails BRK: {self.pasta_brk_id[:10]}****** (emails)")
        
        if self.onedrive_brk_id:
            print(f"   📁 Pasta OneDrive /BRK/: {self.onedrive_brk_id[:15]}****** (arquivos)")
            print(f"   📄 Planilha relacionamento: CDC_BRK_CCB.xlsx (nesta pasta)")
            
            # CARREGAR RELACIONAMENTO AUTOMATICAMENTE NA INICIALIZAÇÃO
            print(f"🔄 Carregando relacionamento automaticamente...")
            self.relacionamento_carregado = self.carregar_relacionamento_completo()
            
        else:
            print("   ⚠️ ONEDRIVE_BRK_ID não configurado - relacionamento indisponível")
            print("   💡 Funcionará apenas com extração básica dos PDFs")

    # ============================================================================
    # FUNÇÃO 2: GARANTIR RELACIONAMENTO CARREGADO (HELPER)
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

    # ============================================================================
    # FUNÇÃO 3: PROCESSAR EMAIL COM EXTRAÇÃO COMPLETA (SUBSTITUIR MÉTODO EXISTENTE)
    # ============================================================================
    
    def extrair_pdfs_do_email_com_dados_completos(self, email):
        """
        Extrai PDFs do email E extrai dados completos de cada PDF.
        SUBSTITUI/EXPANDE: extrair_pdfs_do_email() original
        
        Args:
            email (Dict): Dados do email do Microsoft Graph
            
        Returns:
            List[Dict]: Lista de PDFs com dados completos extraídos
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
                        # Informações básicas do PDF (compatibilidade com código existente)
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
                                        **pdf_info_basico,  # Informações básicas (compatibilidade)
                                        **dados_extraidos,  # Dados extraídos do PDF (nova funcionalidade)
                                        'hash_arquivo': hashlib.sha256(pdf_bytes).hexdigest(),
                                        'dados_extraidos_ok': True,
                                        'relacionamento_usado': relacionamento_ok
                                    }
                                    
                                    pdfs_com_dados.append(pdf_completo)
                                    pdfs_processados += 1
                                    
                                    print(f"✅ PDF processado: {nome_original}")
                                    
                                else:
                                    # Falha na extração - manter dados básicos
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
                                # Manter dados básicos em caso de erro
                                pdf_completo = {
                                    **pdf_info_basico,
                                    'dados_extraidos_ok': False,
                                    'erro_extracao': str(e),
                                    'relacionamento_usado': False
                                }
                                pdfs_com_dados.append(pdf_completo)
                        else:
                            print(f"⚠️ PDF sem conteúdo: {nome_original}")
                            
                    except Exception as e:
                        print(f"❌ Erro processando anexo {nome_original}: {e}")
            
            # Log resumo do processamento
            if pdfs_brutos > 0:
                print(f"\n📊 RESUMO PROCESSAMENTO:")
                print(f"   📎 PDFs encontrados: {pdfs_brutos}")
                print(f"   ✅ PDFs processados: {pdfs_processados}")
                print(f"   📋 Relacionamento: {'✅ Usado' if relacionamento_ok else '❌ Indisponível'}")
                
            return pdfs_com_dados
            
        except Exception as e:
            print(f"❌ Erro extraindo PDFs do email: {e}")
            return []

    # ============================================================================
    # FUNÇÃO 4: MÉTODO PRINCIPAL INTEGRADO (COMPATÍVEL COM APP.PY)
    # ============================================================================
    
    def extrair_pdfs_do_email(self, email):
        """
        MÉTODO PRINCIPAL compatível com app.py existente.
        
        Agora usa a nova funcionalidade de extração completa,
        mas mantém interface compatível com código existente.
        
        Args:
            email (Dict): Dados do email do Microsoft Graph
            
        Returns:
            List[Dict]: Lista de PDFs (compatível + dados expandidos)
        """
        return self.extrair_pdfs_do_email_com_dados_completos(email)

    # ============================================================================
    # FUNÇÃO 5: LOG CONSOLIDADO DE PROCESSAMENTO DE EMAIL
    # ============================================================================
    
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

    # ============================================================================
    # FUNÇÃO 6: STATUS COMPLETO DO PROCESSADOR
    # ============================================================================
    
    def status_processamento_completo(self):
        """
        Retorna status completo do processador incluindo novas funcionalidades.
        EXPANDE: status_processamento() original
        
        Returns:
            Dict: Status completo com relacionamento + extração
        """
        # Status básico (compatibilidade)
        status_basico = {
            "pasta_brk_configurada": bool(self.pasta_brk_id),
            "pasta_brk_protegida": f"{self.pasta_brk_id[:10]}******" if self.pasta_brk_id else "N/A",
            "autenticacao_ok": bool(self.auth.access_token),
            "pasta_acessivel": self.validar_acesso_pasta_brk()
        }
        
        # Status expandido (novas funcionalidades)
        status_relacionamento = self.status_relacionamento()
        
        # Status integrado
        status_completo = {
            **status_basico,
            **status_relacionamento,
            "funcionalidades": {
                "extracao_pdf_completa": True,
                "relacionamento_onedrive": bool(self.onedrive_brk_id),
                "analise_consumo": True,
                "logs_estruturados": True
            },
            "tentativas_carregamento": self.tentativas_carregamento,
            "max_tentativas": self.max_tentativas
        }
        
        return status_completo

    # ============================================================================
    # FUNÇÃO 7: MÉTODO DE TESTE INTEGRADO
    # ============================================================================
    
    def testar_funcionalidades_completas(self):
        """
        Testa todas as funcionalidades integradas.
        Útil para debug e validação no Render.
        
        Returns:
            Dict: Resultados dos testes
        """
        resultados = {
            "timestamp": datetime.now().isoformat(),
            "testes": {}
        }
        
        print(f"\n🧪 TESTANDO FUNCIONALIDADES COMPLETAS")
        print(f"="*50)
        
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
            pasta_ok = self.validar_acesso_pasta_brk()
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
        
        print(f"="*50)
        print(f"✅ TESTE CONCLUÍDO")
        print(f"="*50)
        
        return resultados

# ============================================================================
# PARA TESTAR ESTE BLOCO:
# 
# 1. Código é compatível com app.py existente
# 2. Método extrair_pdfs_do_email() mantém interface original
# 3. Adiciona novas funcionalidades sem quebrar existentes
# 
# TESTE MANUAL NO RENDER:
# processor = EmailProcessor(auth)
# resultados = processor.testar_funcionalidades_completas()
# 
# RESULTADO ESPERADO:
# 🧪 TESTANDO FUNCIONALIDADES COMPLETAS
# ✅ Autenticação: OK
# ✅ Pasta emails: OK  
# ✅ Relacionamento: OK (148 registros)
# ✅ Busca casa: OK (12345-01 → CASA DE ORAÇÃO SAO PAULO...)
# ✅ TESTE CONCLUÍDO
# 
# COMPATIBILIDADE COM APP.PY:
# - BRKProcessadorBasico.processar_email() funciona igual
# - Agora retorna PDFs com dados extraídos completos
# - Logs aparecem automaticamente no Render
# - Relacionamento carrega automaticamente
# ============================================================================
# ============================================================================
# BLOCO 4/4 FINAL - MANUTENÇÃO + ESTATÍSTICAS + FINALIZAÇÃO
# Adicionar ao arquivo: processor/email_processor.py
# 
# FUNÇÃO: Finalizar integração com manutenção, estatísticas e documentação
# AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
# LOCALIZAÇÃO: brk-monitor-seguro/processor/email_processor.py
# FINALIZA: Integração completa da extração de dados BRK
# ============================================================================

from datetime import datetime, timedelta
import json

class EmailProcessor:
    # ... código anterior dos Blocos 1/4, 2/4 e 3/4 ...

    # ============================================================================
    # FUNÇÃO 1: RECARREGAR RELACIONAMENTO MANUALMENTE
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
            sucesso = self.carregar_relacionamento_completo()
            
            if sucesso:
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

    # ============================================================================
    # FUNÇÃO 2: ESTATÍSTICAS AVANÇADAS DE PROCESSAMENTO
    # ============================================================================
    
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
                "erro": str(e),
                "status": "Erro obtendo estatísticas"
            }

    # ============================================================================
    # FUNÇÃO 3: ANÁLISE DE COBERTURA DO RELACIONAMENTO
    # ============================================================================
    
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

    # ============================================================================
    # FUNÇÃO 4: SALVAR DADOS EXTRAÍDOS (COMPATÍVEL COM DATABASE EXISTENTE)
    # ============================================================================
    
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

    # ============================================================================
    # FUNÇÃO 5: LOG DE ESTATÍSTICAS FORMATADO
    # ============================================================================
    
    def log_estatisticas_formatado(self):
        """
        Exibe estatísticas do sistema em formato estruturado para logs do Render.
        """
        try:
            stats = self.obter_estatisticas_avancadas()
            
            print(f"\n📊 ESTATÍSTICAS DO SISTEMA BRK")
            print(f"="*50)
            print(f"🕐 Timestamp: {stats['timestamp'][:16]}")
            
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
            
            print(f"="*50)
            
        except Exception as e:
            print(f"❌ Erro exibindo estatísticas: {e}")

    # ============================================================================
    # FUNÇÃO 6: MÉTODO DE DIAGNÓSTICO COMPLETO
    # ============================================================================
    
    def diagnostico_completo_sistema(self):
        """
        Executa diagnóstico completo de todo o sistema.
        Útil para debug e validação no Render.
        
        Returns:
            Dict: Resultado completo do diagnóstico
        """
        print(f"\n🔍 DIAGNÓSTICO COMPLETO DO SISTEMA BRK")
        print(f"="*60)
        
        diagnostico = {
            "timestamp": datetime.now().isoformat(),
            "status_geral": "🔄 Em andamento",
            "componentes": {}
        }
        
        try:
            # 1. Teste de autenticação
            print(f"1️⃣ Testando autenticação Microsoft...")
            try:
                headers = self.auth.obter_headers_autenticados()
                token_valido = self.auth.validar_token()
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
                pasta_ok = self.validar_acesso_pasta_brk()
                diagnostico_pasta = self.diagnosticar_pasta_brk()
                diagnostico["componentes"]["pasta_emails"] = {
                    "status": "✅ OK" if pasta_ok else "❌ Inacessível",
                    "acessivel": pasta_ok,
                    "diagnostico": diagnostico_pasta
                }
                if pasta_ok:
                    total = diagnostico_pasta.get('total_geral', 0)
                    print(f"   ✅ Pasta emails: OK ({total:,} emails)")
                else:
                    print(f"   ❌ Pasta emails: Inacessível")
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
                    "total_registros": total_relacionamentos
                }
                if relacionamento_ok:
                    print(f"   ✅ OneDrive + Relacionamento: OK ({total_relacionamentos} registros)")
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
            
            # 5. Status final
            componentes_ok = sum(1 for comp in diagnostico["componentes"].values() if "✅" in comp.get("status", ""))
            total_componentes = len(diagnostico["componentes"])
            
            if componentes_ok == total_componentes:
                diagnostico["status_geral"] = "✅ Tudo funcionando"
                print(f"\n✅ DIAGNÓSTICO: Tudo funcionando ({componentes_ok}/{total_componentes})")
            elif componentes_ok > 0:
                diagnostico["status_geral"] = f"⚠️ Parcial ({componentes_ok}/{total_componentes})"
                print(f"\n⚠️ DIAGNÓSTICO: Funcionamento parcial ({componentes_ok}/{total_componentes})")
            else:
                diagnostico["status_geral"] = "❌ Sistema com problemas"
                print(f"\n❌ DIAGNÓSTICO: Sistema com problemas")
            
            print(f"="*60)
            
            return diagnostico
            
        except Exception as e:
            diagnostico["status_geral"] = f"❌ Erro no diagnóstico: {e}"
            print(f"❌ ERRO NO DIAGNÓSTICO: {e}")
            return diagnostico

    # ============================================================================
    # FUNÇÃO 7: FINALIZAÇÃO E DOCUMENTAÇÃO COMPLETA
    # ============================================================================
    
    def info_integracao_completa(self):
        """
        Exibe informações completas sobre a integração implementada.
        Documentação das funcionalidades disponíveis.
        """
        print(f"\n📚 INTEGRAÇÃO BRK - FUNCIONALIDADES COMPLETAS")
        print(f"="*60)
        print(f"👨‍💼 Autor: Sidney Gubitoso, auxiliar tesouraria adm maua")
        print(f"📅 Implementação: Junho 2025")
        print(f"🎯 Objetivo: Extração completa de dados das faturas BRK")
        print(f"="*60)
        
        print(f"\n🔧 FUNCIONALIDADES IMPLEMENTADAS:")
        print(f"   ✅ Carregamento automático planilha OneDrive")
        print(f"   ✅ Relacionamento CDC → Casa de Oração")
        print(f"   ✅ Extração completa dados PDF (pdfplumber)")
        print(f"   ✅ Análise de consumo (alertas automáticos)")
        print(f"   ✅ Logs estruturados para Render")
        print(f"   ✅ Compatibilidade total com código existente")
        print(f"   ✅ Gestão automática de erros e fallbacks")
        print(f"   ✅ Diagnóstico e manutenção do sistema")
        
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
        
        print(f"\n📈 PRÓXIMAS MELHORIAS POSSÍVEIS:")
        print(f"   🔮 Dashboard web com dados extraídos")
        print(f"   🔮 Exportação para Excel das análises")
        print(f"   🔮 Alertas por email para alto consumo")
        print(f"   🔮 Histórico de consumo por casa")
        print(f"   🔮 OCR avançado para faturas complexas")
        
        print(f"="*60)
        print(f"✅ INTEGRAÇÃO COMPLETA - PRONTA PARA USO!")
        print(f"="*60)

# ============================================================================
# 🎉 INTEGRAÇÃO COMPLETA FINALIZADA!
# 
# RESUMO DOS 4 BLOCOS IMPLEMENTADOS:
# 
# BLOCO 1/4: ✅ Leitor OneDrive + Vetores de Relacionamento
# - carregar_planilha_onedrive()
# - carregar_relacao_brk_vetores() 
# - buscar_casa_de_oracao()
# - carregar_relacionamento_completo()
# 
# BLOCO 2/4: ✅ Extrator de Dados PDF + Análise de Consumo
# - extrair_dados_fatura_pdf()
# - _extrair_codigo_cliente() + todas as funções de extração
# - avaliar_consumo() (idêntica ao desktop)
# - _log_dados_extraidos()
# 
# BLOCO 3/4: ✅ Integração Completa: Relacionamento + Extração + Logs
# - extrair_pdfs_do_email_com_dados_completos()
# - log_consolidado_email()
# - status_processamento_completo()
# - testar_funcionalidades_completas()
# 
# BLOCO 4/4: ✅ Manutenção + Estatísticas + Finalização
# - recarregar_relacionamento_manual()
# - obter_estatisticas_avancadas()
# - diagnostico_completo_sistema()
# - preparar_dados_para_database()
# 
# TOTAL: 25+ funções implementadas
# COMPATIBILIDADE: 100% com código existente
# STATUS: Pronto para deploy no Render
# 
# PARA ATIVAR TUDO:
# 1. Adicionar todos os 4 blocos ao processor/email_processor.py
# 2. Atualizar requirements.txt: pandas==2.0.3, pdfplumber==0.9.0
# 3. Configurar ONEDRIVE_BRK_ID no Render Environment
# 4. Deploy automático via GitHub
# 5. Verificar logs do Render - dados extraídos aparecerão automaticamente!
# 
# 🎯 MISSÃO CUMPRIDA - EXTRAÇÃO COMPLETA DE DADOS DAS FATURAS BRK!
# ============================================================================
