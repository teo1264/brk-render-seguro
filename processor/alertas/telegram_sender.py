#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📱 TELEGRAM SENDER - Envio Alertas via Telegram
📧 FUNÇÃO: Enviar mensagens via Telegram Bot reutilizando token CCB
👨‍💼 RESPONSÁVEL: Sidney Gubitoso - Auxiliar Tesouraria Administrativa Mauá
📅 DATA CRIAÇÃO: 04/07/2025
📁 SALVAR EM: processor/alertas/telegram_sender.py
"""

import os
import requests
import time

def enviar_telegram(user_id, mensagem):
    """
    Enviar mensagem via Telegram
    Reutiliza TELEGRAM_BOT_TOKEN do CCB Alerta Bot
    
    Args:
        user_id (str/int): ID do usuário Telegram
        mensagem (str): Mensagem formatada para envio
    
    Returns:
        bool: True se envio bem-sucedido, False caso contrário
    """
    try:
        print(f"📱 Enviando Telegram para user_id: {user_id}")
        
        # 1. Verificar token
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not bot_token:
            print(f"❌ TELEGRAM_BOT_TOKEN não configurado")
            return False
        
        print(f"🤖 Bot token: {bot_token[:20]}...")
        
        # 2. Preparar dados para API
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        data = {
            'chat_id': user_id,
            'text': mensagem,
            'parse_mode': 'Markdown'
        }
        
        print(f"📤 Enviando mensagem ({len(mensagem)} caracteres)...")
        
        # 3. Fazer requisição
        response = requests.post(url, data=data, timeout=10)
        
        # 4. Verificar resultado
        if response.status_code == 200:
            response_data = response.json()
            
            if response_data.get('ok'):
                message_id = response_data.get('result', {}).get('message_id')
                print(f"✅ Telegram enviado com sucesso - Message ID: {message_id}")
                return True
            else:
                error_description = response_data.get('description', 'Erro desconhecido')
                print(f"❌ Telegram API erro: {error_description}")
                return False
        else:
            print(f"❌ Telegram HTTP erro: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Detalhes: {error_data}")
            except:
                print(f"   Resposta: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout enviando Telegram para {user_id}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de rede enviando Telegram: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado enviando Telegram: {e}")
        return False

def enviar_telegram_bulk(user_ids, mensagem, delay_segundos=1):
    """
    Enviar mensagem para múltiplos usuários com delay
    Evita rate limiting do Telegram
    
    Args:
        user_ids (list): Lista de IDs dos usuários
        mensagem (str): Mensagem para envio
        delay_segundos (int): Delay entre envios (padrão: 1 segundo)
    
    Returns:
        dict: Resultado detalhado dos envios
    """
    try:
        print(f"📱 Enviando Telegram em lote para {len(user_ids)} usuários")
        
        sucessos = 0
        falhas = 0
        detalhes = []
        
        for i, user_id in enumerate(user_ids, 1):
            print(f"📤 Enviando {i}/{len(user_ids)} para user_id: {user_id}")
            
            sucesso = enviar_telegram(user_id, mensagem)
            
            if sucesso:
                sucessos += 1
                detalhes.append({'user_id': user_id, 'status': 'sucesso'})
                print(f"✅ {i}/{len(user_ids)}: Sucesso")
            else:
                falhas += 1
                detalhes.append({'user_id': user_id, 'status': 'falha'})
                print(f"❌ {i}/{len(user_ids)}: Falha")
            
            # Delay entre envios (exceto no último)
            if i < len(user_ids) and delay_segundos > 0:
                print(f"⏱️ Aguardando {delay_segundos}s...")
                time.sleep(delay_segundos)
        
        resultado = {
            'total_usuarios': len(user_ids),
            'sucessos': sucessos,
            'falhas': falhas,
            'taxa_sucesso': (sucessos / len(user_ids)) * 100 if user_ids else 0,
            'detalhes': detalhes
        }
        
        print(f"📊 RESULTADO BULK TELEGRAM:")
        print(f"   👥 Total usuários: {resultado['total_usuarios']}")
        print(f"   ✅ Sucessos: {resultado['sucessos']}")
        print(f"   ❌ Falhas: {resultado['falhas']}")
        print(f"   📈 Taxa sucesso: {resultado['taxa_sucesso']:.1f}%")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro no envio bulk: {e}")
        return {
            'total_usuarios': len(user_ids) if user_ids else 0,
            'sucessos': 0,
            'falhas': len(user_ids) if user_ids else 0,
            'taxa_sucesso': 0,
            'erro': str(e)
        }

def testar_telegram_bot():
    """
    Testar funcionamento do bot Telegram
    Envia mensagem de teste para admin
    """
    try:
        print(f"\n🧪 TESTE TELEGRAM BOT")
        print(f"="*30)
        
        # Verificar configurações
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        admin_ids = os.getenv("ADMIN_IDS", "").split(",")
        
        print(f"🤖 Bot token: {'✅ Configurado' if bot_token else '❌ Não configurado'}")
        print(f"👨‍💼 Admin IDs: {'✅ Configurado' if admin_ids and admin_ids[0] else '❌ Não configurado'}")
        
        if not bot_token:
            print(f"❌ Configure TELEGRAM_BOT_TOKEN")
            return False
        
        if not admin_ids or not admin_ids[0].strip():
            print(f"❌ Configure ADMIN_IDS")
            return False
        
        # Testar info do bot
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_data = bot_info.get('result', {})
                print(f"🤖 Bot ativo: @{bot_data.get('username', 'N/A')}")
                print(f"🏷️ Nome: {bot_data.get('first_name', 'N/A')}")
            else:
                print(f"❌ Bot token inválido")
                return False
        else:
            print(f"❌ Erro consultando bot: HTTP {response.status_code}")
            return False
        
        # Enviar mensagem de teste para admin
        admin_id = admin_ids[0].strip()
        mensagem_teste = """🧪 *TESTE SISTEMA BRK + CCB ALERTA*

✅ Bot Telegram funcionando  
✅ Integração Sistema BRK ativa  
✅ Base CCB Alerta conectada  

🤖 *Sistema BRK Automático*
🔧 *Teste realizado com sucesso!*"""
        
        print(f"📤 Enviando mensagem teste para admin: {admin_id}")
        sucesso = enviar_telegram(admin_id, mensagem_teste)
        
        if sucesso:
            print(f"✅ Teste Telegram Bot: SUCESSO")
            return True
        else:
            print(f"❌ Teste Telegram Bot: FALHOU")
            return False
        
    except Exception as e:
        print(f"❌ Erro teste Telegram Bot: {e}")
        return False

def verificar_configuracao_telegram():
    """
    Verificar se configurações Telegram estão corretas
    Útil para debug sem enviar mensagens
    """
    try:
        print(f"\n🔍 VERIFICAÇÃO CONFIGURAÇÃO TELEGRAM")
        print(f"="*40)
        
        configuracao = {
            'bot_token_configurado': bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            'admin_ids_configurado': bool(os.getenv("ADMIN_IDS")),
            'bot_token_valido': False,
            'admin_ids_validos': []
        }
        
        # Verificar bot token
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if bot_token:
            try:
                url = f"https://api.telegram.org/bot{bot_token}/getMe"
                response = requests.get(url, timeout=5)
                if response.status_code == 200 and response.json().get('ok'):
                    configuracao['bot_token_valido'] = True
            except:
                pass
        
        # Verificar admin IDs
        admin_ids = os.getenv("ADMIN_IDS", "").split(",")
        for admin_id in admin_ids:
            admin_id = admin_id.strip()
            if admin_id and admin_id.isdigit():
                configuracao['admin_ids_validos'].append(admin_id)
        
        print(f"🤖 Bot token: {'✅ Válido' if configuracao['bot_token_valido'] else '❌ Inválido'}")
        print(f"👨‍💼 Admin IDs: {len(configuracao['admin_ids_validos'])} válido(s)")
        
        for admin_id in configuracao['admin_ids_validos']:
            print(f"   👤 {admin_id}")
        
        tudo_ok = (configuracao['bot_token_valido'] and 
                  len(configuracao['admin_ids_validos']) > 0)
        
        print(f"📊 Configuração geral: {'✅ OK' if tudo_ok else '❌ Problemas detectados'}")
        
        return configuracao
        
    except Exception as e:
        print(f"❌ Erro verificando configuração: {e}")
        return {'erro': str(e)}
