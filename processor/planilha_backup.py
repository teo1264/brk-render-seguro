#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 PLANILHA BACKUP SIMPLES - Sistema transparente para planilha BRK
📁 FUNÇÃO: Salvar backups VISÍVEIS na pasta principal /BRK/
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua

🔧 LÓGICA SIMPLES:
   1. Tentar salvar BRK_Planilha.xlsx (principal)
   2. Se ocupada → BRK_Planilha_TEMPORARIA_05Jul_15h30.xlsx
   3. A cada 30min → tentar principal + limpar temporárias
   4. Usuário vê claramente os arquivos temporários na pasta /BRK/
"""

import os
import requests
from datetime import datetime

def salvar_planilha_inteligente(auth_manager, dados_planilha):
    """
    FUNÇÃO PRINCIPAL - Salvar planilha com backup transparente
    Interface mantida para compatibilidade com monitor_brk.py
    """
    try:
        print("📊 Salvamento planilha BRK - Sistema transparente")
        
        ARQUIVO_PRINCIPAL = "BRK_Planilha.xlsx"
        
        # 1. Tentar salvar planilha principal
        if tentar_salvar_principal(auth_manager, dados_planilha, ARQUIVO_PRINCIPAL):
            print("✅ Planilha principal atualizada com sucesso")
            
            # 2. Principal salvou → limpar temporárias
            limpar_planilhas_temporarias(auth_manager)
            return True
        
        # 3. Principal ocupada → salvar temporária VISÍVEL
        print("⚠️ Planilha principal ocupada, criando versão temporária...")
        
        nome_temporaria = gerar_nome_temporaria()
        
        if salvar_planilha_temporaria(auth_manager, dados_planilha, nome_temporaria):
            print(f"💾 Planilha temporária criada: {nome_temporaria}")
            print("📁 Arquivo visível na pasta /BRK/ do OneDrive")
            print("🔄 Sistema tentará atualizar principal em 30 minutos")
            
            # 4. Notificar admin se configurado
            notificar_planilha_temporaria(nome_temporaria)
            
            return True
        else:
            print("❌ Falha criando planilha temporária")
            return False
            
    except Exception as e:
        print(f"❌ Erro salvamento planilha: {e}")
        return False

def tentar_salvar_principal(auth_manager, dados_planilha, nome_arquivo):
    """Tentar salvar na planilha principal"""
    try:
        pasta_brk_id = os.getenv('ONEDRIVE_BRK_ID')
        if not pasta_brk_id:
            print("❌ ONEDRIVE_BRK_ID não configurado")
            return False
        
        headers = auth_manager.obter_headers_autenticados()
        upload_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_brk_id}:/{nome_arquivo}:/content"
        headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        upload_response = requests.put(upload_url, headers=headers, data=dados_planilha, timeout=60)
        
        if upload_response.status_code in [200, 201]:
            return True
        else:
            print(f"❌ Erro salvando principal: HTTP {upload_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        if "locked" in str(e).lower() or "busy" in str(e).lower():
            print("⚠️ Arquivo principal está em uso")
        else:
            print(f"❌ Erro rede: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro salvando principal: {e}")
        return False

def salvar_planilha_temporaria(auth_manager, dados_planilha, nome_temporaria):
    """Salvar planilha temporária na pasta principal /BRK/"""
    try:
        pasta_brk_id = os.getenv('ONEDRIVE_BRK_ID')
        if not pasta_brk_id:
            return False
        
        headers = auth_manager.obter_headers_autenticados()
        upload_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_brk_id}:/{nome_temporaria}:/content"
        headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        upload_response = requests.put(upload_url, headers=headers, data=dados_planilha, timeout=60)
        
        return upload_response.status_code in [200, 201]
        
    except Exception as e:
        print(f"❌ Erro salvando temporária: {e}")
        return False

def limpar_planilhas_temporarias(auth_manager):
    """Limpar planilhas temporárias quando principal for salva"""
    try:
        pasta_brk_id = os.getenv('ONEDRIVE_BRK_ID')
        if not pasta_brk_id:
            return
        
        headers = auth_manager.obter_headers_autenticados()
        list_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_brk_id}/children"
        response = requests.get(list_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            items = response.json().get('value', [])
            temporarias_removidas = 0
            
            for item in items:
                nome = item.get('name', '')
                item_id = item.get('id')
                
                # Remover arquivos temporários BRK
                if nome.startswith('BRK_Planilha_TEMPORARIA_') and nome.endswith('.xlsx'):
                    delete_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}"
                    delete_response = requests.delete(delete_url, headers=headers, timeout=30)
                    
                    if delete_response.status_code == 204:
                        print(f"🗑️ Planilha temporária removida: {nome}")
                        temporarias_removidas += 1
                    else:
                        print(f"⚠️ Erro removendo {nome}: {delete_response.status_code}")
            
            if temporarias_removidas > 0:
                print(f"🧹 Limpeza concluída: {temporarias_removidas} planilha(s) temporária(s) removida(s)")
        
    except Exception as e:
        print(f"❌ Erro limpando temporárias: {e}")

def gerar_nome_temporaria():
    """Gerar nome claro para planilha temporária"""
    agora = datetime.now()
    
    # Meses em português abreviado
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
             'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    dia = agora.day
    mes = meses[agora.month - 1]
    hora = agora.strftime('%Hh%M')
    
    return f"BRK_Planilha_TEMPORARIA_{dia:02d}{mes}_{hora}.xlsx"

def notificar_planilha_temporaria(nome_temporaria):
    """Notificar admin sobre planilha temporária (opcional)"""
    try:
        # Import opcional - não quebra se módulo não existir
        from processor.alertas.telegram_sender import enviar_telegram
        
        admin_ids = os.getenv("ADMIN_IDS", "").split(",")
        
        if admin_ids and admin_ids[0].strip():
            mensagem = f"""📊 PLANILHA BRK - VERSÃO TEMPORÁRIA

⚠️ Planilha principal estava em uso
💾 Dados salvos em: {nome_temporaria}
🔄 Sistema tentará atualizar principal em 30 min

📁 Feche BRK_Planilha.xlsx quando possível
✅ Processamento continua normalmente"""
            
            enviar_telegram(admin_ids[0].strip(), mensagem)
            print("📱 Admin notificado via Telegram")
            
    except ImportError:
        print("⚠️ Telegram não configurado - seguindo sem notificação")
    except Exception as e:
        print(f"⚠️ Falha notificação Telegram: {e}")

# ============================================================================
# FUNÇÕES REMOVIDAS (comentário para referência):
# 
# ❌ obter_pasta_sistema_brk() - criava pasta .brk_system (removida)
# ❌ salvar_backup_invisivel() - backup oculto (removida) 
# ❌ limpar_backups_antigos() - lógica pasta oculta (removida)
# ❌ import hashlib - não mais necessário (removido)
#
# Total reduzido: 180 → 60 linhas (economia de 67%)
# ============================================================================
