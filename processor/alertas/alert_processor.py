#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚨 ALERT PROCESSOR - Orquestração Principal Sistema BRK + CCB
📧 FUNÇÃO: Processar alertas automáticos após salvar fatura
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
"""

import os
# ============================================================================
# MODIFICAÇÃO 3: processor/alertas/alert_processor.py
# LOCALIZAR: Função processar_alerta_fatura()
# AÇÃO: SUBSTITUIR toda a função por esta versão
# ============================================================================

# IMPORTS NO TOPO DO ARQUIVO (substituir a linha de import existente):
from .ccb_database import obter_responsaveis_por_codigo
from .telegram_sender import enviar_telegram, enviar_telegram_com_anexo  # ← LINHA MODIFICADA
from .message_formatter import formatar_mensagem_alerta

def processar_alerta_fatura(dados_fatura):
    """
    FUNÇÃO PRINCIPAL - Chamada após salvar fatura no database_brk.py
    🆕 AGORA COM SUPORTE A PDF ANEXO
    
    Integração Sistema BRK + CCB Alerta Bot
    """
    try:
        print(f"\n🚨 INICIANDO PROCESSAMENTO ALERTA COM ANEXO")
        
        # 1. Obter código da casa
        codigo_casa = dados_fatura.get('casa_oracao', '')
        
        if not codigo_casa:
            print("⚠️ Código da casa não encontrado em dados_fatura")
            return False
        
        print(f"🏠 Casa detectada: {codigo_casa}")
        
        # 2. 🆕 VERIFICAR SE TEM PDF DISPONÍVEL PARA ANEXO
        pdf_bytes = dados_fatura.get('pdf_bytes')
        nome_arquivo = dados_fatura.get('nome_arquivo_pdf', 'fatura-brk.pdf')
        
        if pdf_bytes and len(pdf_bytes) > 0:
            print(f"📎 PDF disponível para anexo: {nome_arquivo} ({len(pdf_bytes)} bytes)")
            print(f"✅ Alertas serão enviados COM ANEXO")
            anexo_disponivel = True
        else:
            print(f"⚠️ PDF não disponível - alertas sem anexo (sistema normal)")
            anexo_disponivel = False
        
        # 3. Consultar responsáveis na base CCB (sistema existente)
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
        
        # 4. Formatar mensagem completa (sistema existente)
        print(f"📝 Formatando mensagem...")
        mensagem = formatar_mensagem_alerta(dados_fatura)
        
        if not mensagem or mensagem == "Erro na formatação da mensagem":
            print(f"❌ Erro na formatação da mensagem")
            return False
        
        print(f"✅ Mensagem formatada: {len(mensagem)} caracteres")
        
        # 5. 🆕 ENVIAR PARA CADA RESPONSÁVEL (COM OU SEM ANEXO)
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
            
            # 🎯 DECISÃO INTELIGENTE: Com ou sem anexo
            if anexo_disponivel:
                # Tentar enviar com anexo
                print(f"📎 Tentativa COM ANEXO para {nome}")
                sucesso = enviar_telegram_com_anexo(user_id, mensagem, pdf_bytes, nome_arquivo)
            else:
                # Enviar apenas mensagem (sistema existente)
                print(f"📄 Tentativa SEM ANEXO para {nome}")
                sucesso = enviar_telegram(user_id, mensagem)
            
            if sucesso:
                enviados_sucesso += 1
                print(f"✅ Enviado para {nome}")
            else:
                enviados_erro += 1
                print(f"❌ Falha enviando para {nome}")
        
        # 6. Resultado final
        print(f"\n📊 RESULTADO PROCESSAMENTO ALERTA:")
        print(f"   🏠 Casa: {codigo_casa}")
        print(f"   👥 Responsáveis: {len(responsaveis)}")
        print(f"   📎 Anexo PDF: {'✅ Disponível' if anexo_disponivel else '❌ Indisponível'}")
        print(f"   ✅ Enviados: {enviados_sucesso}")
        print(f"   ❌ Falhas: {enviados_erro}")
        
        if anexo_disponivel and enviados_sucesso > 0:
            print(f"🎉 SUCESSO: Alertas enviados COM FATURA ANEXA!")
        elif enviados_sucesso > 0:
            print(f"✅ SUCESSO: Alertas enviados (sem anexo)")
        
        return enviados_sucesso > 0
        
    except Exception as e:
        print(f"❌ Erro processando alerta: {e}")
        return False

# ============================================================================
# 🎯 INSTRUÇÕES PARA APLICAR:
# 
# 1. Abrir: processor/alertas/alert_processor.py no GitHub
# 2. Localizar: IMPORTS no topo (linha ~7)
# 3. Substituir: from .telegram_sender import enviar_telegram
#    Por: from .telegram_sender import enviar_telegram, enviar_telegram_com_anexo
# 
# 4. Localizar: def processar_alerta_fatura(dados_fatura):
# 5. Selecionar: Toda a função (até o último return False)
# 6. Substituir: Por esta versão completa
# 7. Salvar: Commit com mensagem "AlertProcessor: Adicionar suporte anexo PDF"
# 
# ✅ RESULTADO: Sistema detecta PDF e envia anexo automaticamente
# ✅ FALLBACK: Se PDF não disponível, usa sistema existente
# ============================================================================
