#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 PLANILHA BACKUP - Sistema backup invisível para planilha BRK
📁 FUNÇÃO: Salvar backups em pasta oculta sem variáveis adicionais
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
"""

import os
import requests
from datetime import datetime
import hashlib

def obter_pasta_sistema_brk(auth_manager):
    """
    Criar/obter pasta sistema usando ONEDRIVE_BRK_ID existente
    ✅ SEM NOVAS VARIÁVEIS DE AMBIENTE
    """
    try:
        # Usar variável existente
        pasta_brk_id = os.getenv('ONEDRIVE_BRK_ID')
        
        if not pasta_brk_id:
            print("❌ ONEDRIVE_BRK_ID não configurado")
            return None
        
        headers = auth_manager.obter_headers_autenticados()
        
        # 1. Verificar se .brk_system já existe
        print("🔍 Verificando pasta sistema...")
        
        list_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_brk_id}/children"
        response = requests.get(list_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            items = response.json().get('value', [])
            
            # Procurar pasta .brk_system
            for item in items:
                if (item.get('name') == '.brk_system' and 'folder' in item):
                    sistema_id = item.get('id')
                    print(f"✅ Pasta sistema encontrada: {sistema_id[:20]}...")
                    return sistema_id
        
        # 2. Criar pasta sistema se não existir
        print("📁 Criando pasta sistema .brk_system...")
        
        create_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_brk_id}/children"
        create_data = {
            "name": ".brk_system",
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail"
        }
        
        create_response = requests.post(create_url, headers=headers, json=create_data, timeout=30)
        
        if create_response.status_code == 201:
            pasta_criada = create_response.json()
            sistema_id = pasta_criada.get('id')
            print(f"✅ Pasta sistema criada: {sistema_id[:20]}...")
            return sistema_id
        else:
            print(f"❌ Erro criando pasta sistema: {create_response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erro obtendo pasta sistema: {e}")
        return None

def salvar_planilha_inteligente(auth_manager, dados_planilha):
    """
    Salvar planilha com backup invisível se principal ocupada
    ✅ ESTRATÉGIA: Principal → Backup invisível → Limpeza automática
    """
    try:
        print("📊 Iniciando salvamento inteligente da planilha...")
        
        ARQUIVO_PRINCIPAL = "BRK_Planilha.xlsx"
        
        # 1. Limpar backups antigos primeiro (se principal livre)
        limpar_backups_antigos(auth_manager)
        
        # 2. Tentar salvar planilha principal
        if tentar_salvar_principal(auth_manager, dados_planilha, ARQUIVO_PRINCIPAL):
            print("✅ Planilha principal atualizada com sucesso")
            return True
        
        # 3. Principal ocupada - salvar backup invisível
        print("⚠️ Planilha principal ocupada, criando backup invisível...")
        
        backup_salvo = salvar_backup_invisivel(auth_manager, dados_planilha)
        
        if backup_salvo:
            print("💾 Backup invisível criado com sucesso")
            
            # 4. Notificar admin via sistema existente
            try:
                from processor.alertas.telegram_sender import enviar_telegram
                admin_ids = os.getenv("ADMIN_IDS", "").split(",")
                
                if admin_ids and admin_ids[0].strip():
                    mensagem = f"""📊 PLANILHA BRK - BACKUP CRIADO

⚠️ Planilha principal está em uso
💾 Dados salvos em backup invisível
🔄 Sistema tentará consolidar em 30 min

📁 Feche BRK_Planilha.xlsx quando possível
✅ Processamento continua normalmente"""
                    
                    enviar_telegram(admin_ids[0].strip(), mensagem)
                    print("📱 Admin notificado via Telegram")
                    
            except Exception as e:
                print(f"⚠️ Aviso: Falha notificação Telegram: {e}")
            
            return True
        else:
            print("❌ Falha salvando backup invisível")
            return False
            
    except Exception as e:
        print(f"❌ Erro salvamento inteligente: {e}")
        return False

def tentar_salvar_principal(auth_manager, dados_planilha, nome_arquivo):
    """Tentar salvar na planilha principal"""
    try:
        pasta_brk_id = os.getenv('ONEDRIVE_BRK_ID')
        headers = auth_manager.obter_headers_autenticados()
        
        upload_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_brk_id}:/{nome_arquivo}:/content"
        headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        upload_response = requests.put(upload_url, headers=headers, data=dados_planilha, timeout=60)
        
        if upload_response.status_code in [200, 201]:
            print(f"✅ Arquivo principal salvo: {nome_arquivo}")
            return True
        else:
            print(f"❌ Erro salvando principal: HTTP {upload_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        if "locked" in str(e).lower() or "busy" in str(e).lower():
            print("⚠️ Arquivo principal está em uso")
        else:
            print(f"❌ Erro rede salvando principal: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro salvando principal: {e}")
        return False

def salvar_backup_invisivel(auth_manager, dados_planilha):
    """Salvar backup na pasta sistema invisível"""
    try:
        # 1. Obter pasta sistema
        pasta_sistema_id = obter_pasta_sistema_brk(auth_manager)
        
        if not pasta_sistema_id:
            print("❌ Pasta sistema não disponível")
            return False
        
        # 2. Gerar nome técnico único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        hash_unique = hashlib.md5(f"brk_backup_{timestamp}".encode()).hexdigest()[:8]
        nome_backup = f".temp_brk_{timestamp}_{hash_unique}.xlsx"
        
        print(f"💾 Salvando backup: {nome_backup}")
        
        # 3. Upload do backup
        headers = auth_manager.obter_headers_autenticados()
        upload_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_sistema_id}:/{nome_backup}:/content"
        headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        upload_response = requests.put(upload_url, headers=headers, data=dados_planilha, timeout=60)
        
        if upload_response.status_code in [200, 201]:
            print(f"✅ Backup invisível salvo: {nome_backup}")
            return nome_backup
        else:
            print(f"❌ Erro upload backup: {upload_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro salvando backup invisível: {e}")
        return False

def limpar_backups_antigos(auth_manager):
    """Limpar backups antigos da pasta sistema"""
    try:
        pasta_sistema_id = obter_pasta_sistema_brk(auth_manager)
        
        if not pasta_sistema_id:
            return
        
        headers = auth_manager.obter_headers_autenticados()
        
        # Listar arquivos na pasta sistema
        list_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_sistema_id}/children"
        response = requests.get(list_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            items = response.json().get('value', [])
            backups_removidos = 0
            
            for item in items:
                nome = item.get('name', '')
                item_id = item.get('id')
                
                # Deletar APENAS backups BRK temporários
                if nome.startswith('.temp_brk_') and nome.endswith('.xlsx'):
                    delete_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}"
                    delete_response = requests.delete(delete_url, headers=headers, timeout=30)
                    
                    if delete_response.status_code == 204:
                        print(f"🗑️ Backup antigo removido: {nome}")
                        backups_removidos += 1
                    else:
                        print(f"⚠️ Erro removendo {nome}: {delete_response.status_code}")
            
            if backups_removidos > 0:
                print(f"🧹 Limpeza concluída: {backups_removidos} backup(s) antigo(s) removido(s)")
        
    except Exception as e:
        print(f"❌ Erro limpando backups antigos: {e}")
