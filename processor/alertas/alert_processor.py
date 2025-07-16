#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚨 ALERT PROCESSOR - VERSÃO CORRIGIDA (AUTENTICAÇÃO)
📧 FUNÇÃO: Processar alertas automáticos + anexar fatura PDF
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
🔧 CORREÇÃO: Reutilizar autenticação do sistema principal
"""

import os
import requests
import re
from datetime import datetime
from .ccb_database import obter_responsaveis_por_codigo
from .telegram_sender import enviar_telegram, enviar_telegram_com_anexo
from .message_formatter import formatar_mensagem_alerta

def processar_alerta_fatura(dados_fatura):
    """
    FUNÇÃO PRINCIPAL - Processar alerta COM ANEXO PDF
    🔧 CORREÇÃO: Reutilizar autenticação do sistema principal
    """
    try:
        print(f"\n🚨 INICIANDO PROCESSAMENTO ALERTA COM ANEXO")
        
        # 1. Obter código da casa
        codigo_casa = dados_fatura.get('casa_oracao', '')
        
        if not codigo_casa:
            print("⚠️ Código da casa não encontrado em dados_fatura")
            return False
        
        print(f"🏠 Casa detectada: {codigo_casa}")
        
        # 2. Consultar responsáveis na base CCB
        print(f"🔍 Consultando responsáveis para {codigo_casa}...")
        responsaveis = obter_responsaveis_por_codigo(codigo_casa)
        
        if not responsaveis:
            # Fallback para admin se não encontrar responsáveis
            print(f"⚠️ Nenhum responsável encontrado para {codigo_casa}")
            print(f"📱 Enviando para admin como fallback...")
            
            admin_ids = os.getenv("ADMIN_IDS", "").split(",")
            if admin_ids and admin_ids[0].strip():
                responsaveis = [{'user_id': admin_ids[0].strip(), 'nome': 'Admin', 'funcao': 'Administrador'}]
            else:
                print(f"❌ ADMIN_IDS não configurado - cancelando envio")
                return False
        
        print(f"👥 Responsáveis encontrados: {len(responsaveis)}")
        
        # 3. Formatar mensagem completa
        print(f"📝 Formatando mensagem...")
        mensagem = formatar_mensagem_alerta(dados_fatura)
        
        if not mensagem or mensagem == "Erro na formatação da mensagem":
            print(f"❌ Erro na formatação da mensagem")
            return False
        
        print(f"✅ Mensagem formatada: {len(mensagem)} caracteres")
        
        # 4. ✅ VERSÃO DEFENSIVA: Obter PDF dos dados OU OneDrive
        print(f"📎 Obtendo PDF para anexo...")
        pdf_bytes = None
        fonte_pdf = "nenhuma"

        # PRIMEIRO: Tentar usar PDF dos dados (registros novos)
        content_bytes = dados_fatura.get('content_bytes')
        if content_bytes and content_bytes.strip() and len(content_bytes) > 100:
           try:
               import base64
               pdf_bytes = base64.b64decode(content_bytes)
               fonte_pdf = "content_bytes"
               print(f"✅ PDF dos dados (novo): {len(pdf_bytes)} bytes")
           except Exception as e:
               print(f"⚠️ Erro decodificando content_bytes: {e}")
               pdf_bytes = None
        else:
            print(f"📝 content_bytes: {'ausente' if not content_bytes else 'inválido'} - usando fallback")

        # FALLBACK: OneDrive (registros antigos)
        if not pdf_bytes:
            print(f"📥 Usando fallback OneDrive (registro antigo)")
            pdf_bytes = _baixar_pdf_onedrive_corrigido(dados_fatura)
            if pdf_bytes:
                fonte_pdf = "onedrive"
                print(f"✅ PDF do OneDrive: {len(pdf_bytes)} bytes")
            else:
                print(f"⚠️ PDF não encontrado no OneDrive")

        # ÚLTIMO RECURSO: Log detalhado
        if not pdf_bytes:
            fonte_pdf = "nenhuma"
            print(f"⚠️ PDF não disponível em nenhuma fonte")
            print(f"   📝 content_bytes: {'presente' if content_bytes else 'ausente'}")
            print(f"   📁 OneDrive: falhou")
            print(f"   📨 Enviando apenas mensagem")

        nome_arquivo = _gerar_nome_arquivo_pdf(dados_fatura)
        
        # 5. Enviar para cada responsável COM OU SEM ANEXO
        enviados_sucesso = 0
        enviados_erro = 0
        
        for responsavel in responsaveis:
            user_id = responsavel.get('user_id')
            nome = responsavel.get('nome', 'Responsável')
            funcao = responsavel.get('funcao', 'N/A')
            
            if not user_id:
                print(f"⚠️ user_id vazio para {nome}")
                enviados_erro += 1
                continue
            
            print(f"📱 Enviando para: {nome} ({funcao}) - ID: {user_id}")
            
            # 🆕 ENVIAR COM ANEXO SE DISPONÍVEL
            if pdf_bytes:
                sucesso = enviar_telegram_com_anexo(user_id, mensagem, pdf_bytes, nome_arquivo)
                
                if not sucesso:
                    # Fallback: Se anexo falha, enviar só mensagem
                    print(f"⚠️ Falha no envio com anexo - tentando só mensagem")
                    sucesso = enviar_telegram(user_id, mensagem)
            else:
                # Enviar só mensagem (comportamento atual)
                sucesso = enviar_telegram(user_id, mensagem)
            
            if sucesso:
                enviados_sucesso += 1
                print(f"✅ Enviado para {nome}")
            else:
                enviados_erro += 1
                print(f"❌ Falha enviando para {nome}")
        
        # 6. 🧹 LIMPEZA DA MEMÓRIA
        if pdf_bytes:
            pdf_bytes = None
            print(f"🧹 PDF removido da memória")
        
        # 7. Resultado final
        print(f"\n📊 RESULTADO PROCESSAMENTO ALERTA:")
        print(f"   🏠 Casa: {codigo_casa}")
        print(f"   👥 Responsáveis: {len(responsaveis)}")
        print(f"   📎 PDF anexado: {'✅ Sim' if pdf_foi_anexado else '❌ Não'}")
        print(f"   📁 Fonte PDF: {fonte_pdf}")
        print(f"   ✅ Enviados: {enviados_sucesso}")
        print(f"   ❌ Falhas: {enviados_erro}")
        
        return enviados_sucesso > 0
        
    except Exception as e:
        print(f"❌ Erro processando alerta: {e}")
        return False

def _baixar_pdf_onedrive_corrigido(dados_fatura):
    """
    🔧 FUNÇÃO CORRIGIDA: Baixar PDF usando autenticação do sistema principal
    
    CORREÇÃO: Reutilizar auth_manager global ao invés de criar nova instância
    """
    try:
        # 1. Construir caminho do arquivo
        caminho_arquivo = _construir_caminho_onedrive(dados_fatura)
        
        if not caminho_arquivo:
            print(f"❌ Erro construindo caminho do arquivo")
            return None
        
        print(f"📁 Caminho construído: {caminho_arquivo}")
        
        # 2. 🔧 CORREÇÃO: Reutilizar autenticação do sistema principal
        auth_manager = _obter_auth_manager_global()
        
        if not auth_manager or not auth_manager.access_token:
            print(f"❌ Autenticação global não disponível")
            return None
        
        headers = auth_manager.obter_headers_autenticados()
        
        # 3. Baixar via Microsoft Graph API
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:{caminho_arquivo}:/content"
        
        print(f"📥 Baixando PDF via Graph API (auth corrigida)...")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ PDF baixado com sucesso: {len(response.content)} bytes")
            return response.content
        else:
            print(f"❌ Erro baixando PDF: HTTP {response.status_code}")
            
            # 🔧 CORREÇÃO: Tentar renovar token se 401
            if response.status_code == 401:
                print(f"🔄 Tentando renovar token...")
                if auth_manager.atualizar_token():
                    headers = auth_manager.obter_headers_autenticados()
                    response = requests.get(url, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        print(f"✅ PDF baixado após renovação: {len(response.content)} bytes")
                        return response.content
                    else:
                        print(f"❌ Erro mesmo após renovação: HTTP {response.status_code}")
                        return None
                else:
                    print(f"❌ Falha renovando token")
                    return None
            
            return None
            
    except Exception as e:
        print(f"❌ Erro baixando PDF do OneDrive: {e}")
        return None

def _obter_auth_manager_global():
    """
    🔧 FUNÇÃO CORRIGIDA: Obter auth_manager do sistema principal
    
    CORREÇÃO: Reutilizar instância global ao invés de criar nova
    """
    try:
        # Método 1: Importar do app.py global
        import sys
        if 'app' in sys.modules:
            app_module = sys.modules['app']
            if hasattr(app_module, 'auth_manager'):
                print(f"🔐 Usando auth_manager do app.py")
                return app_module.auth_manager
        
        # Método 2: Tentar importar diretamente
        try:
            from app import auth_manager
            print(f"🔐 Usando auth_manager importado")
            return auth_manager
        except ImportError:
            pass
        
        # Método 3: Criar nova instância (fallback)
        print(f"🔐 Criando nova instância auth (fallback)")
        from auth.microsoft_auth import MicrosoftAuth
        return MicrosoftAuth()
        
    except Exception as e:
        print(f"❌ Erro obtendo auth_manager: {e}")
        return None

def _construir_caminho_onedrive(dados_fatura):
    """
    🔄 FUNÇÃO MANTIDA: Construir caminho completo do PDF no OneDrive
    """
    try:
        # 1. Extrair ano e mês
        ano, mes = _extrair_ano_mes(
            dados_fatura.get('competencia', ''),
            dados_fatura.get('vencimento', '')
        )
        
        # 2. Gerar nome padronizado
        nome_arquivo = _gerar_nome_padronizado(dados_fatura)
        
        # 3. Construir caminho completo
        caminho = f"/BRK/Faturas/{ano}/{mes:02d}/{nome_arquivo}"
        
        print(f"📁 Caminho construído: {caminho}")
        return caminho
        
    except Exception as e:
        print(f"❌ Erro construindo caminho: {e}")
        return None

def _extrair_ano_mes(competencia, vencimento):
    """
    🔄 FUNÇÃO MANTIDA: Extrair ano e mês
    """
    try:
        # Prioridade 1: Competência
        if competencia:
            meses_nome = {
                'janeiro': 1, 'jan': 1, 'fevereiro': 2, 'fev': 2,
                'março': 3, 'mar': 3, 'abril': 4, 'abr': 4,
                'maio': 5, 'mai': 5, 'junho': 6, 'jun': 6,
                'julho': 7, 'jul': 7, 'agosto': 8, 'ago': 8,
                'setembro': 9, 'set': 9, 'outubro': 10, 'out': 10,
                'novembro': 11, 'nov': 11, 'dezembro': 12, 'dez': 12
            }
            
            if '/' in competencia:
                mes_parte, ano_parte = competencia.split('/')
                mes_parte = mes_parte.strip().lower()
                ano_parte = ano_parte.strip()
                
                if mes_parte in meses_nome:
                    return int(ano_parte), meses_nome[mes_parte]
                
                if mes_parte.isdigit():
                    return int(ano_parte), int(mes_parte)
        
        # Prioridade 2: Vencimento
        if vencimento:
            match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', vencimento)
            if match:
                dia, mes, ano = match.groups()
                return int(ano), int(mes)
        
        # Fallback: Mês atual
        from datetime import datetime
        hoje = datetime.now()
        print(f"⚠️ Usando mês atual como fallback: {hoje.year}/{hoje.month}")
        return hoje.year, hoje.month
        
    except Exception as e:
        print(f"❌ Erro extraindo ano/mês: {e}")
        from datetime import datetime
        hoje = datetime.now()
        return hoje.year, hoje.month

def _gerar_nome_padronizado(dados_fatura):
    """
    🔄 FUNÇÃO MANTIDA: Gerar nome padronizado
    """
    try:
        # Extrair dados
        vencimento = dados_fatura.get('vencimento', '')
        casa = dados_fatura.get('casa_oracao', 'Casa')
        valor = dados_fatura.get('valor', '0')
        competencia = dados_fatura.get('competencia', '')
        
        # Formatar vencimento
        if vencimento:
            match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', vencimento)
            if match:
                dia, mes, ano = match.groups()
                dia_mes = f"{dia.zfill(2)}-{mes.zfill(2)}"
                venc_completo = f"{dia.zfill(2)}-{mes.zfill(2)}-{ano}"
            else:
                dia_mes = "XX-XX"
                venc_completo = "XX-XX-XXXX"
        else:
            dia_mes = "XX-XX"
            venc_completo = "XX-XX-XXXX"
        
        # Formatar competência
        if competencia:
            ano, mes = _extrair_ano_mes(competencia, vencimento)
            comp_formato = f"{mes:02d}-{ano}"
        else:
            comp_formato = "XX-XXXX"
        
        # Limpar casa
        casa_limpa = re.sub(r'[<>:"/\\|?*]', '', casa)
        if len(casa_limpa) > 40:
            casa_limpa = casa_limpa[:40] + "..."
        
        # Formatar valor
        if valor:
            valor_limpo = re.sub(r'[^\d,.]', '', str(valor))
            if not valor_limpo:
                valor_limpo = "0"
        else:
            valor_limpo = "0"
        
        # Construir nome final
        nome = f"{dia_mes}-BRK {comp_formato} - {casa_limpa} - vc. {venc_completo} - {valor_limpo}.pdf"
        
        # Limitar tamanho
        if len(nome) > 200:
            nome = nome[:197] + "....pdf"
        
        return nome
        
    except Exception as e:
        print(f"❌ Erro gerando nome padronizado: {e}")
        return f"fatura-{datetime.now().strftime('%Y%m%d')}.pdf"

def _gerar_nome_arquivo_pdf(dados_fatura):
    """
    🔄 FUNÇÃO MANTIDA: Gerar nome amigável para anexo Telegram
    """
    try:
        casa = dados_fatura.get('casa_oracao', 'Casa')
        vencimento = dados_fatura.get('vencimento', '')
        
        # Extrair partes da casa
        if 'BR' in casa and '-' in casa:
            partes = casa.split('-')
            if len(partes) >= 2:
                codigo_casa = partes[0].strip()
                nome_casa = partes[1].strip()[:20]
            else:
                codigo_casa = casa[:10]
                nome_casa = casa[10:30]
        else:
            codigo_casa = casa[:10]
            nome_casa = casa[10:30]
        
        # Extrair mês/ano do vencimento
        if vencimento:
            match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', vencimento)
            if match:
                dia, mes, ano = match.groups()
                periodo = f"{mes.zfill(2)}-{ano}"
            else:
                periodo = "periodo"
        else:
            periodo = "periodo"
        
        # Nome final
        nome = f"BRK-{codigo_casa}-{periodo}.pdf"
        
        # Limpar caracteres especiais
        nome = re.sub(r'[<>:"/\\|?*]', '', nome)
        
        return nome
        
    except Exception as e:
        print(f"❌ Erro gerando nome arquivo: {e}")
        return "fatura-brk.pdf"
