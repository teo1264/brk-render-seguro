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
