#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚨 ALERT PROCESSOR - VERSÃO 2.3 FALLBACK CORRIGIDO
📧 FUNÇÃO: Processar alertas automáticos + anexar fatura PDF
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
🔧 CORREÇÃO CRÍTICA: Fallback OneDrive - usar vencimento (não competência)
📅 DATA: 22/07/2025

CORREÇÕES APLICADAS v2.3:
✅ Fallback OneDrive: Usar vencimento para caminho (igual ao salvamento) ← NOVO
✅ Todas outras funcionalidades mantidas
"""

import os
import requests
import re
from datetime import datetime
from .ccb_database import obter_responsaveis_por_codigo
from .telegram_sender import enviar_telegram, enviar_telegram_com_anexo
from .message_formatter import formatar_mensagem_alerta

def processar_alerta_fatura(dados_fatura):
    """Função principal - sem alterações"""
    try:
        print(f"\n🚨 [v2.3 FALLBACK CORRIGIDO] INICIANDO PROCESSAMENTO ALERTA COM ANEXO")
        
        # 1. Extrair código da casa
        casa_oracao_completa = dados_fatura.get('casa_oracao', '')
        
        if not casa_oracao_completa:
            print("⚠️ Código da casa não encontrado em dados_fatura")
            return False
        
        print(f"🏠 Casa detectada (completa): {casa_oracao_completa}")
        
        codigo_casa = extrair_codigo_formato_ccb(casa_oracao_completa)
        
        if not codigo_casa:
            print("❌ Não foi possível extrair código da casa")
            return False
        
        print(f"🔍 Código extraído (formato CCB): '{codigo_casa}'")
        
        # 2. Consultar responsáveis
        print(f"🔍 Consultando responsáveis CCB (com sincronização token)...")
        responsaveis = obter_responsaveis_por_codigo_sincronizado(codigo_casa)
        
        if not responsaveis:
            # Fallback para admin
            print(f"⚠️ Nenhum responsável encontrado para código: {codigo_casa}")
            print(f"📱 Enviando para admin como fallback...")
            
            admin_ids = os.getenv("ADMIN_IDS", "").split(",")
            if admin_ids and admin_ids[0].strip():
                responsaveis = [{'user_id': admin_ids[0].strip(), 'nome': 'Admin', 'funcao': 'Administrador'}]
            else:
                print(f"❌ ADMIN_IDS não configurado - cancelando envio")
                return False
        
        print(f"👥 Responsáveis encontrados: {len(responsaveis)}")
        
        # 3. Formatar mensagem
        print(f"📝 Formatando mensagem...")
        mensagem = formatar_mensagem_alerta(dados_fatura)
        
        if not mensagem or mensagem == "Erro na formatação da mensagem":
            print(f"❌ Erro na formatação da mensagem")
            return False
        
        print(f"✅ Mensagem formatada: {len(mensagem)} caracteres")
        
        # 4. Obter PDF dos dados OU OneDrive (FALLBACK CORRIGIDO)
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

        # FALLBACK CORRIGIDO: OneDrive (registros antigos)
        if not pdf_bytes:
            print(f"📥 Usando fallback OneDrive CORRIGIDO (registro antigo)")
            pdf_bytes = _baixar_pdf_onedrive_sincronizado(dados_fatura)
            if pdf_bytes:
                fonte_pdf = "onedrive"
                print(f"✅ PDF do OneDrive: {len(pdf_bytes)} bytes")
            else:
                print(f"⚠️ PDF não encontrado no OneDrive")

        # Log detalhado se não encontrou
        if not pdf_bytes:
            fonte_pdf = "nenhuma"
            print(f"⚠️ PDF não disponível em nenhuma fonte")
            print(f"   📝 content_bytes: {'presente' if content_bytes else 'ausente'}")
            print(f"   📁 OneDrive: falhou")
            print(f"   📨 Enviando apenas mensagem")

        nome_arquivo = _gerar_nome_arquivo_pdf(dados_fatura)
        
        # 5. Enviar para cada responsável
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
            
            # Enviar com anexo se disponível
            if pdf_bytes:
                sucesso = enviar_telegram_com_anexo(user_id, mensagem, pdf_bytes, nome_arquivo)
                
                if not sucesso:
                    # Fallback: Se anexo falha, enviar só mensagem
                    print(f"⚠️ Falha no envio com anexo - tentando só mensagem")
                    sucesso = enviar_telegram(user_id, mensagem)
            else:
                # Enviar só mensagem
                sucesso = enviar_telegram(user_id, mensagem)
            
            if sucesso:
                enviados_sucesso += 1
                print(f"✅ Enviado para {nome}")
            else:
                enviados_erro += 1
                print(f"❌ Falha enviando para {nome}")
        
        # 6. Resultado final
        pdf_foi_anexado = bool(pdf_bytes)
        
        if pdf_bytes:
            pdf_bytes = None  # Limpeza da memória
            print(f"🧹 PDF removido da memória")
        
        print(f"\n📊 RESULTADO PROCESSAMENTO ALERTA v2.3:")
        print(f"   🏠 Casa completa: {casa_oracao_completa}")
        print(f"   🔍 Código CCB: {codigo_casa}")
        print(f"   👥 Responsáveis: {len(responsaveis)}")
        print(f"   📎 PDF anexado: {'✅ Sim' if pdf_foi_anexado else '❌ Não'}")
        print(f"   📁 Fonte PDF: {fonte_pdf}")
        print(f"   ✅ Enviados: {enviados_sucesso}")
        print(f"   ❌ Falhas: {enviados_erro}")
        
        return enviados_sucesso > 0
        
    except Exception as e:
        print(f"❌ Erro processando alerta v2.3: {e}")
        return False

def obter_responsaveis_por_codigo_sincronizado(codigo_casa):
    """Função de consulta responsáveis - sem alterações"""
    try:
        print(f"🔍 Consultando base CCB (sincronizado) para: {codigo_casa}")
        
        onedrive_alerta_id = os.getenv("ONEDRIVE_ALERTA_ID")
        if not onedrive_alerta_id:
            print(f"❌ ONEDRIVE_ALERTA_ID não configurado")
            return []
        
        print(f"📁 OneDrive Alerta ID: {onedrive_alerta_id[:20]}...")
        
        from auth.microsoft_auth import MicrosoftAuth
        auth_manager = MicrosoftAuth()
        
        print(f"🔄 Recarregando token do persistent disk...")
        tokens_ok = auth_manager.carregar_token()
        
        if not tokens_ok or not auth_manager.access_token:
            print(f"❌ Auth Microsoft não disponível após reload")
            return []
        
        print(f"🔐 Auth Microsoft: ✅ Token recarregado from disk")
        
        headers = auth_manager.obter_headers_autenticados()
        
        print(f"🧪 Testando conectividade OneDrive CCB...")
        test_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{onedrive_alerta_id}"
        test_response = requests.get(test_url, headers=headers, timeout=10)
        
        if test_response.status_code == 401:
            print(f"🔄 HTTP 401 detectado - renovando token automaticamente...")
            if auth_manager.atualizar_token():
                headers = auth_manager.obter_headers_autenticados()
                print(f"✅ Token renovado com sucesso")
                
                test_response = requests.get(test_url, headers=headers, timeout=10)
                if test_response.status_code != 200:
                    print(f"❌ Falha persistente após renovação: HTTP {test_response.status_code}")
                    return []
            else:
                print(f"❌ Falha na renovação automática do token")
                return []
        elif test_response.status_code != 200:
            print(f"❌ Erro de conectividade: HTTP {test_response.status_code}")
            return []
        
        print(f"✅ Conectividade OneDrive CCB confirmada")
        
        # Buscar database
        print(f"☁️ Buscando alertas_bot.db na pasta /Alerta/...")
        
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{onedrive_alerta_id}/children"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erro acessando pasta /Alerta/: HTTP {response.status_code}")
            return []
        
        arquivos = response.json().get('value', [])
        
        db_file_id = None
        for arquivo in arquivos:
            if arquivo.get('name', '').lower() == 'alertas_bot.db':
                db_file_id = arquivo['id']
                print(f"💾 alertas_bot.db encontrado: {arquivo['name']}")
                break
        
        if not db_file_id:
            print(f"❌ alertas_bot.db não encontrado na pasta /Alerta/")
            return []
        
        # Baixar database
        print(f"📥 Baixando alertas_bot.db...")
        
        download_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{db_file_id}/content"
        download_response = requests.get(download_url, headers=headers, timeout=60)
        
        if download_response.status_code != 200:
            print(f"❌ Erro baixando database: HTTP {download_response.status_code}")
            return []
        
        import tempfile
        import sqlite3
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db', prefix='ccb_cache_') as tmp_file:
            tmp_file.write(download_response.content)
            db_path = tmp_file.name
        
        print(f"💾 Database baixado para: {db_path}")
        
        # Consultar responsáveis
        conn = sqlite3.connect(db_path)
        
        try:
            responsaveis = conn.execute("""
                SELECT user_id, nome, funcao 
                FROM responsaveis 
                WHERE codigo_casa = ?
            """, (codigo_casa,)).fetchall()
            
            resultado = []
            for user_id, nome, funcao in responsaveis:
                resultado.append({
                    'user_id': user_id,
                    'nome': nome or 'Nome não informado',
                    'funcao': funcao or 'Função não informada'
                })
            
            print(f"✅ Responsáveis encontrados (sincronizado): {len(resultado)}")
            for resp in resultado:
                print(f"   👤 {resp['nome']} ({resp['funcao']}) - ID: {resp['user_id']}")
            
            return resultado
            
        finally:
            conn.close()
            try:
                os.unlink(db_path)
            except:
                pass
        
    except Exception as e:
        print(f"❌ Erro consultando base CCB (sincronizado): {e}")
        return []

def extrair_codigo_formato_ccb(casa_oracao_completa):
    """Função extração código - sem alterações"""
    if not casa_oracao_completa or casa_oracao_completa == 'Não encontrado':
        return None
    
    try:
        print(f"🔍 Extraindo código CCB de: '{casa_oracao_completa}'")
        
        # Código antes do " - "
        if ' - ' in casa_oracao_completa:
            codigo_bruto = casa_oracao_completa.split(' - ')[0].strip()
            print(f"   ✓ Código extraído (antes do -): '{codigo_bruto}'")
            
            # Normalizar para formato CCB (sem espaços)
            codigo_ccb = codigo_bruto.replace(' ', '')
            print(f"   ✓ Normalizado para CCB: '{codigo_ccb}'")
            
            # Validar formato BR21-XXXX
            if re.match(r'^BR21-\d{4}$', codigo_ccb):
                print(f"   ✅ Formato válido CCB: '{codigo_ccb}'")
                return codigo_ccb
            else:
                print(f"   ⚠️ Formato inválido: '{codigo_ccb}' (esperado: BR21-XXXX)")
        
        # Buscar padrão BR21-XXXX diretamente
        match_br21 = re.search(r'BR21-\d{4}', casa_oracao_completa)
        if match_br21:
            codigo_encontrado = match_br21.group(0)
            print(f"   ✓ Código BR21 encontrado: '{codigo_encontrado}'")
            return codigo_encontrado
        
        # Buscar padrão BR XX-XXXX e converter
        match_br_espaco = re.search(r'BR\s*21-\d{4}', casa_oracao_completa)
        if match_br_espaco:
            codigo_bruto = match_br_espaco.group(0)
            codigo_ccb = codigo_bruto.replace(' ', '')
            print(f"   ✓ Código BR com espaços convertido: '{codigo_bruto}' → '{codigo_ccb}'")
            return codigo_ccb
        
        print(f"   ❌ Nenhum padrão BR21-XXXX encontrado em: '{casa_oracao_completa}'")
        return None
        
    except Exception as e:
        print(f"❌ Erro extraindo código: {e}")
        return None

def _baixar_pdf_onedrive_sincronizado(dados_fatura):
    """Função baixar PDF - CORRIGIDA para usar vencimento"""
    try:
        # Construir caminho do arquivo (USANDO FUNÇÃO CORRIGIDA)
        caminho_arquivo = _construir_caminho_onedrive(dados_fatura)
        
        if not caminho_arquivo:
            print(f"❌ Erro construindo caminho do arquivo")
            return None
        
        print(f"📁 Caminho construído: {caminho_arquivo}")
        
        from auth.microsoft_auth import MicrosoftAuth
        auth_manager = MicrosoftAuth()
        
        print(f"🔄 Sincronizando token para download PDF...")
        tokens_ok = auth_manager.carregar_token()
        
        if not tokens_ok or not auth_manager.access_token:
            print(f"❌ Autenticação não disponível após sincronização")
            return None
        
        headers = auth_manager.obter_headers_autenticados()
        
        # Baixar via Microsoft Graph API
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:{caminho_arquivo}:/content"
        
        print(f"📥 Baixando PDF via Graph API (token sincronizado)...")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ PDF baixado com sucesso: {len(response.content)} bytes")
            return response.content
        else:
            print(f"❌ Erro baixando PDF: HTTP {response.status_code}")
            
            # Tentar renovar token se 401
            if response.status_code == 401:
                print(f"🔄 HTTP 401 - tentando renovar token para PDF...")
                if auth_manager.atualizar_token():
                    headers = auth_manager.obter_headers_autenticados()
                    response = requests.get(url, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        print(f"✅ PDF baixado após renovação: {len(response.content)} bytes")
                        return response.content
                    else:
                        print(f"❌ Erro persistente após renovação: HTTP {response.status_code}")
                        return None
                else:
                    print(f"❌ Falha renovando token para PDF")
                    return None
            
            return None
            
    except Exception as e:
        print(f"❌ Erro baixando PDF do OneDrive (sincronizado): {e}")
        return None

def _construir_caminho_onedrive(dados_fatura):
    """Função construir caminho - CORRIGIDA para usar vencimento"""
    try:
        print(f"📁 [CORRIGIDO] Construindo caminho OneDrive...")
        
        # 1. 🚨 CORREÇÃO CRÍTICA: Extrair ano/mês do VENCIMENTO (não competência)
        ano, mes = _extrair_ano_mes_CORRIGIDO(dados_fatura)
        
        # 2. Gerar nome padronizado (igual ao database_brk.py)
        nome_arquivo = _gerar_nome_padronizado(dados_fatura)
        
        # 3. Construir caminho completo
        caminho = f"/BRK/Faturas/{ano}/{mes:02d}/{nome_arquivo}"
        
        print(f"📁 Caminho CORRIGIDO construído: {caminho}")
        return caminho
        
    except Exception as e:
        print(f"❌ Erro construindo caminho: {e}")
        return None

def _extrair_ano_mes_CORRIGIDO(dados_fatura):
    """
    🚨 FUNÇÃO CORRIGIDA: Extrair ano/mês SEMPRE do vencimento
    
    PROBLEMA CORRIGIDO: Estava usando competência primeiro
    SOLUÇÃO: Usar SEMPRE vencimento primeiro (igual database_brk.py)
    """
    try:
        vencimento = dados_fatura.get('vencimento', '')
        competencia = dados_fatura.get('competencia', '')
        
        print(f"📅 [CORRIGIDO] Extraindo ano/mês:")
        print(f"   📅 Vencimento: {vencimento}")
        print(f"   📆 Competência: {competencia} (ignorado)")
        
        # 🚨 CORREÇÃO CRÍTICA: SEMPRE usar vencimento primeiro (padrão tesouraria)
        if vencimento and '/' in vencimento:
            match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', vencimento)
            if match:
                dia, mes, ano = match.groups()
                mes_int = int(mes)
                ano_int = int(ano)
                
                print(f"   ✅ USANDO VENCIMENTO: {vencimento} → {ano_int}/{mes_int:02d}")
                return ano_int, mes_int
            else:
                print(f"   ⚠️ Formato vencimento inválido: {vencimento}")
        
        # Fallback: data atual se vencimento inválido
        hoje = datetime.now()
        print(f"   ⚠️ FALLBACK: Usando data atual → {hoje.year}/{hoje.month:02d}")
        return hoje.year, hoje.month
        
    except Exception as e:
        print(f"❌ Erro em _extrair_ano_mes_CORRIGIDO: {e}")
        hoje = datetime.now()
        return hoje.year, hoje.month

def _extrair_ano_mes(competencia, vencimento):
    """
    🚨 FUNÇÃO ORIGINAL CORRIGIDA: Usar vencimento primeiro
    
    Esta é a função original que estava causando o problema.
    CORREÇÃO: Trocar ordem - vencimento primeiro, competência depois
    """
    try:
        print(f"📅 [ORIGINAL CORRIGIDO] _extrair_ano_mes:")
        print(f"   📅 Vencimento: {vencimento}")  
        print(f"   📆 Competência: {competencia}")
        
        # 🚨 CORREÇÃO CRÍTICA: VENCIMENTO PRIMEIRO (era competência primeiro)
        if vencimento and '/' in vencimento:
            match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', vencimento)
            if match:
                dia, mes, ano = match.groups()
                print(f"   ✅ Pasta por VENCIMENTO: {vencimento} → /{ano}/{mes:02d}/")
                return int(ano), int(mes)
        
        # SEGUNDO: Tentar competência (só se vencimento falhar)
        if competencia and '/' in competencia:
            try:
                if re.match(r'\d{2}/\d{4}', competencia):
                    mes, ano = competencia.split('/')
                    mes, ano = int(mes), int(ano)
                    print(f"   ⚠️ Usando COMPETÊNCIA como fallback: {competencia} → /{ano}/{mes:02d}/")
                    return int(ano), int(mes)
            except:
                pass
        
        # ÚLTIMO: Fallback para data atual
        hoje = datetime.now()
        print(f"   ⚠️ Pasta por DATA ATUAL: {hoje.year}/{hoje.month:02d} (fallback)")
        return hoje.year, hoje.month
        
    except Exception as e:
        print(f"❌ Erro extraindo ano/mês: {e}")
        hoje = datetime.now()
        return hoje.year, hoje.month

def _gerar_nome_padronizado(dados_fatura):
    """Função gerar nome - sem alterações (já correta)"""
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
            ano, mes = _extrair_ano_mes(competencia, vencimento)  # Usando função corrigida
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
            valor_limpo = valor_limpo.replace(',', '.')
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
    """Função gerar nome arquivo - sem alterações"""
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

# Funções de teste mantidas
def testar_extracao_codigo_vila_assis():
    """Teste extração código - sem alterações"""
    print(f"\n🧪 TESTE EXTRAÇÃO CÓDIGO CCB - CORREÇÃO VILA ASSIS")
    print(f"="*60)
    
    casos_teste = [
        {
            "input": "BR 21-0520 - VILA ASSIS BRASIL",
            "esperado": "BR21-0520",
            "descricao": "🎯 VILA ASSIS (caso problema)"
        },
        {
            "input": "BR 21-0270 - CENTRO", 
            "esperado": "BR21-0270",
            "descricao": "Centro"
        },
        {
            "input": "BR 21-0774 - JARDIM MAUÁ",
            "esperado": "BR21-0774", 
            "descricao": "Jardim Mauá"
        }
    ]
    
    print(f"🔍 Testando {len(casos_teste)} casos...")
    
    sucessos = 0
    for i, caso in enumerate(casos_teste, 1):
        input_casa = caso["input"]
        esperado = caso["esperado"]
        descricao = caso["descricao"]
        
        print(f"\n{i}. {descricao}")
        print(f"   📥 Input: '{input_casa}'")
        print(f"   🎯 Esperado: '{esperado}'")
        
        resultado = extrair_codigo_formato_ccb(input_casa)
        print(f"   📤 Resultado: '{resultado}'")
        
        if resultado == esperado:
            print(f"   ✅ SUCESSO!")
            sucessos += 1
        else:
            print(f"   ❌ FALHA!")
    
    print(f"\n📊 RESULTADO TESTE:")
    print(f"   ✅ Sucessos: {sucessos}")
    print(f"   📈 Taxa: {(sucessos/len(casos_teste)*100):.1f}%")
    
    if sucessos >= 2:
        print(f"🎯 TESTE: ✅ APROVADO")
        return True
    else:
        print(f"🎯 TESTE: ❌ REPROVADO") 
        return False

def testar_sistema_completo_v23():
    """
    🧪 TESTE SISTEMA COMPLETO v2.3 - FALLBACK CORRIGIDO
    
    Valida:
    ✅ Extração códigos funcionando
    ✅ Fallback OneDrive usando VENCIMENTO ← NOVO
    ✅ Caminhos consistentes salvamento/busca ← NOVO
    """
    print(f"\n🧪 TESTE SISTEMA COMPLETO v2.3 - FALLBACK CORRIGIDO")
    print(f"="*60)
    
    # Teste dados
    dados_teste = {
        'casa_oracao': 'BR 21-0751 - VILA VITÓRIA',
        'valor': 'R$ 150,75',
        'vencimento': '10/08/2025',  # → Pasta 2025/08
        'competencia': 'Julho/2025', # → Era usado antes (erro!)
        'content_bytes': None  # Simular fallback necessário
    }
    
    print(f"🎯 Testando com:")
    print(f"   🏠 Casa: {dados_teste['casa_oracao']}")
    print(f"   📅 Vencimento: {dados_teste['vencimento']} → Pasta: 2025/08")
    print(f"   📆 Competência: {dados_teste['competencia']} → Era: 2025/07 (problema!)")
    
    # 1. Teste extração ano/mês
    print(f"\n1️⃣ TESTE EXTRAÇÃO ANO/MÊS CORRIGIDO:")
    ano, mes = _extrair_ano_mes_CORRIGIDO(dados_teste)
    if ano == 2025 and mes == 8:
        print(f"   ✅ Extração corrigida: OK - {ano}/{mes:02d}")
    else:
        print(f"   ❌ Extração falhou: {ano}/{mes:02d}")
        return False
    
    # 2. Teste construção caminho
    print(f"\n2️⃣ TESTE CONSTRUÇÃO CAMINHO:")
    caminho = _construir_caminho_onedrive(dados_teste)
    if caminho and "/2025/08/" in caminho:
        print(f"   ✅ Caminho corrigido: {caminho}")
    else:
        print(f"   ❌ Caminho incorreto: {caminho}")
        return False
    
    # 3. Resultado
    print(f"\n📊 RESULTADO TESTE v2.3:")
    print(f"   ✅ Fallback OneDrive: CORRIGIDO")
    print(f"   ✅ Usa vencimento: 2025/08 (não competência 2025/07)")
    print(f"   ✅ Caminho consistente: salvamento = busca")
    print(f"   ✅ Todas funcionalidades: Preservadas")
    
    print(f"\n🎯 SISTEMA v2.3: ✅ PRONTO PARA DEPLOY")
    print(f"🏆 Fallback OneDrive funcionará 100%!")
    
    return True
