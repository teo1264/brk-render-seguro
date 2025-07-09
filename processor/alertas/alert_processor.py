#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚨 ALERT PROCESSOR - VERSÃO COMPLETA COM ANEXO PDF
📧 FUNÇÃO: Processar alertas automáticos + anexar fatura PDF
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
🆕 FUNCIONALIDADE: Baixa PDF do OneDrive e anexa no Telegram
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
    
    🆕 NOVA FUNCIONALIDADE:
    1. Baixa PDF do OneDrive usando estrutura conhecida
    2. Envia mensagem + PDF anexado via Telegram
    3. Fallback para só mensagem se PDF falhar
    4. Limpeza automática da memória
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
        
        # 4. 🆕 BAIXAR PDF DO ONEDRIVE PARA ANEXAR
        print(f"📎 Tentando baixar PDF do OneDrive...")
        pdf_bytes = _baixar_pdf_onedrive(dados_fatura)
        nome_arquivo = _gerar_nome_arquivo_pdf(dados_fatura)
        
        if pdf_bytes:
            print(f"✅ PDF baixado: {len(pdf_bytes)} bytes - {nome_arquivo}")
        else:
            print(f"⚠️ PDF não encontrado - enviando apenas mensagem")
        
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
        print(f"   📎 PDF anexado: {'✅ Sim' if pdf_bytes else '❌ Não'}")
        print(f"   ✅ Enviados: {enviados_sucesso}")
        print(f"   ❌ Falhas: {enviados_erro}")
        
        return enviados_sucesso > 0
        
    except Exception as e:
        print(f"❌ Erro processando alerta: {e}")
        return False

def _baixar_pdf_onedrive(dados_fatura):
    """
    🆕 FUNÇÃO: Baixar PDF do OneDrive usando estrutura conhecida
    
    ESTRUTURA OneDrive: /BRK/Faturas/YYYY/MM/nome-padronizado.pdf
    
    Args:
        dados_fatura (dict): Dados da fatura processada
        
    Returns:
        bytes: Conteúdo do PDF ou None se erro
    """
    try:
        # 1. Construir caminho do arquivo
        caminho_arquivo = _construir_caminho_onedrive(dados_fatura)
        
        if not caminho_arquivo:
            print(f"❌ Erro construindo caminho do arquivo")
            return None
        
        print(f"📁 Caminho construído: {caminho_arquivo}")
        
        # 2. Obter autenticação (reutilizar do sistema principal)
        from auth.microsoft_auth import MicrosoftAuth
        auth_manager = MicrosoftAuth()
        
        if not auth_manager.access_token:
            print(f"❌ Autenticação não disponível")
            return None
        
        headers = auth_manager.obter_headers_autenticados()
        
        # 3. Baixar via Microsoft Graph API
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:{caminho_arquivo}:/content"
        
        print(f"📥 Baixando PDF via Graph API...")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ PDF baixado com sucesso: {len(response.content)} bytes")
            return response.content
        else:
            print(f"❌ Erro baixando PDF: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erro baixando PDF do OneDrive: {e}")
        return None

def _construir_caminho_onedrive(dados_fatura):
    """
    🆕 FUNÇÃO: Construir caminho completo do PDF no OneDrive
    
    Usa mesma lógica do email_processor.py:
    - Extrai ano/mês de competência ou vencimento
    - Gera nome padronizado igual ao upload
    
    Args:
        dados_fatura (dict): Dados da fatura
        
    Returns:
        str: Caminho completo no OneDrive
    """
    try:
        # 1. Extrair ano e mês (reutilizar lógica do email_processor.py)
        ano, mes = _extrair_ano_mes(
            dados_fatura.get('competencia', ''),
            dados_fatura.get('vencimento', '')
        )
        
        # 2. Gerar nome padronizado (reutilizar lógica do email_processor.py)
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
    🔄 FUNÇÃO REUTILIZADA: Extrair ano e mês (mesma lógica email_processor.py)
    
    Args:
        competencia (str): Competência da fatura (ex: "Julho/2025")
        vencimento (str): Data vencimento (ex: "27/07/2025")
        
    Returns:
        tuple: (ano, mes) como integers
    """
    try:
        # Prioridade 1: Competência
        if competencia:
            # Formatos possíveis: "Julho/2025", "Jul/2025", "07/2025"
            meses_nome = {
                'janeiro': 1, 'jan': 1, 'fevereiro': 2, 'fev': 2,
                'março': 3, 'mar': 3, 'abril': 4, 'abr': 4,
                'maio': 5, 'mai': 5, 'junho': 6, 'jun': 6,
                'julho': 7, 'jul': 7, 'agosto': 8, 'ago': 8,
                'setembro': 9, 'set': 9, 'outubro': 10, 'out': 10,
                'novembro': 11, 'nov': 11, 'dezembro': 12, 'dez': 12
            }
            
            # Tentar formato "Mês/Ano"
            if '/' in competencia:
                mes_parte, ano_parte = competencia.split('/')
                mes_parte = mes_parte.strip().lower()
                ano_parte = ano_parte.strip()
                
                # Mês por nome
                if mes_parte in meses_nome:
                    return int(ano_parte), meses_nome[mes_parte]
                
                # Mês por número
                if mes_parte.isdigit():
                    return int(ano_parte), int(mes_parte)
        
        # Prioridade 2: Vencimento
        if vencimento:
            # Formato: "DD/MM/YYYY"
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
    🔄 FUNÇÃO REUTILIZADA: Gerar nome padronizado (mesma lógica email_processor.py)
    
    Formato: "DD-MM-BRK MM-YYYY - Casa - vc. DD-MM-YYYY - R$ XXX.pdf"
    
    Args:
        dados_fatura (dict): Dados da fatura
        
    Returns:
        str: Nome padronizado do arquivo
    """
    try:
        # Extrair dados
        vencimento = dados_fatura.get('vencimento', '')
        casa = dados_fatura.get('casa_oracao', 'Casa')
        valor = dados_fatura.get('valor', '0')
        competencia = dados_fatura.get('competencia', '')
        
        # Formatar vencimento
        if vencimento:
            # Formato: "DD/MM/YYYY" -> "DD-MM"
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
            # Extrair mês e ano da competência
            ano, mes = _extrair_ano_mes(competencia, vencimento)
            comp_formato = f"{mes:02d}-{ano}"
        else:
            comp_formato = "XX-XXXX"
        
        # Limpar casa (remover caracteres especiais)
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
        
        # Limitar tamanho do nome (limite Windows: 255 caracteres)
        if len(nome) > 200:
            nome = nome[:197] + "....pdf"
        
        return nome
        
    except Exception as e:
        print(f"❌ Erro gerando nome padronizado: {e}")
        return f"fatura-{datetime.now().strftime('%Y%m%d')}.pdf"

def _gerar_nome_arquivo_pdf(dados_fatura):
    """
    🆕 FUNÇÃO: Gerar nome amigável para anexo Telegram
    
    Args:
        dados_fatura (dict): Dados da fatura
        
    Returns:
        str: Nome amigável para anexo
    """
    try:
        casa = dados_fatura.get('casa_oracao', 'Casa')
        vencimento = dados_fatura.get('vencimento', '')
        
        # Extrair partes da casa
        if 'BR' in casa and '-' in casa:
            partes = casa.split('-')
            if len(partes) >= 2:
                codigo_casa = partes[0].strip()
                nome_casa = partes[1].strip()[:20]  # Primeiros 20 caracteres
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
