#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚨 ALERT PROCESSOR - Orquestração Principal Sistema BRK + CCB
📧 FUNÇÃO: Processar alertas automáticos após salvar fatura
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
"""

import os
from .ccb_database import obter_responsaveis_por_codigo
from .telegram_sender import enviar_telegram
from .message_formatter import formatar_mensagem_alerta

def processar_alerta_fatura(dados_fatura):
    """
    FUNÇÃO PRINCIPAL - Chamada após salvar fatura no database_brk.py
    Integração Sistema BRK + CCB Alerta Bot
    """
    try:
        print(f"\n🚨 INICIANDO PROCESSAMENTO ALERTA")
        
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
        
        # 4. Enviar para cada responsável
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
            
            sucesso = enviar_telegram(user_id, mensagem)
            
            if sucesso:
                enviados_sucesso += 1
                print(f"✅ Enviado para {nome}")
            else:
                enviados_erro += 1
                print(f"❌ Falha enviando para {nome}")
        
        # 5. Resultado final
        print(f"\n📊 RESULTADO PROCESSAMENTO ALERTA:")
        print(f"   🏠 Casa: {codigo_casa}")
        print(f"   👥 Responsáveis: {len(responsaveis)}")
        print(f"   ✅ Enviados: {enviados_sucesso}")
        print(f"   ❌ Falhas: {enviados_erro}")
        
        return enviados_sucesso > 0
        
    except Exception as e:
        print(f"❌ Erro processando alerta: {e}")
        return False
