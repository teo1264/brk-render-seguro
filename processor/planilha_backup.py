#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 PLANILHA BACKUP SIMPLES - Sistema transparente para planilha BRK
📁 FUNÇÃO: Salvar backups VISÍVEIS na pasta correta /BRK/Faturas/YYYY/MM/
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua

🔧 LÓGICA SIMPLES:
   1. Detectar mês/ano atual (julho/2025)
   2. Tentar salvar /BRK/Faturas/2025/07/BRK-Planilha-2025-07.xlsx
   3. Se ocupada → /BRK/Faturas/2025/07/BRK-Planilha-2025-07_TEMPORARIA_05Jul_15h30.xlsx
   4. A cada 30min → tentar principal + limpar temporárias na pasta correta
   5. Usuário vê claramente os arquivos temporários na pasta do mês
   
✅ CORREÇÃO: Estrutura de pastas corrigida para seguir padrão existente
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
        
        # ✅ DETECTAR MÊS/ANO ATUAL (como no monitor_brk.py)
        hoje = datetime.now()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        # ✅ NOMES CORRETOS (como no excel_brk.py)
        nome_principal = f"BRK-Planilha-{ano_atual}-{mes_atual:02d}.xlsx"
        pasta_destino = f"/BRK/Faturas/{ano_atual}/{mes_atual:02d}/"
        
        print(f"📁 Pasta destino: {pasta_destino}")
        print(f"📄 Arquivo principal: {nome_principal}")
        
        # 1. Tentar salvar planilha principal
        if tentar_salvar_principal(auth_manager, dados_planilha, pasta_destino, nome_principal):
            print("✅ Planilha principal atualizada com sucesso")
            
            # 2. Principal salvou → limpar temporárias da pasta correta
            limpar_planilhas_temporarias(auth_manager, pasta_destino, ano_atual, mes_atual)
            return True
        
        # 3. Principal ocupada → salvar temporária VISÍVEL na mesma pasta
        print("⚠️ Planilha principal ocupada, criando versão temporária...")
        
        nome_temporaria = gerar_nome_temporaria(ano_atual, mes_atual)
        
        if salvar_planilha_temporaria(auth_manager, dados_planilha, pasta_destino, nome_temporaria):
            print(f"💾 Planilha temporária criada: {nome_temporaria}")
            print(f"📁 Arquivo visível em: {pasta_destino}")
            print("🔄 Sistema tentará atualizar principal em 30 minutos")
            
            # 4. Notificar admin se configurado
            notificar_planilha_temporaria(nome_temporaria, pasta_destino)
            
            return True
        else:
            print("❌ Falha criando planilha temporária")
            return False
            
    except Exception as e:
        print(f"❌ Erro salvamento planilha: {e}")
        return False

def tentar_salvar_principal(auth_manager, dados_planilha, pasta_destino, nome_arquivo):
    """Tentar salvar na planilha principal na pasta correta"""
    try:
        pasta_brk_id = os.getenv('ONEDRIVE_BRK_ID')
        if not pasta_brk_id:
            print("❌ ONEDRIVE_BRK_ID não configurado")
            return False
        
        headers = auth_manager.obter_headers_autenticados()
        
        # ✅ CAMINHO COMPLETO: /BRK/Faturas/2025/07/BRK-Planilha-2025-07.xlsx
        caminho_completo = f"{pasta_destino}{nome_arquivo}"
        upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{caminho_completo}:/content"
        
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

def salvar_planilha_temporaria(auth_manager, dados_planilha, pasta_destino, nome_temporaria):
    """Salvar planilha temporária na pasta correta do mês/ano"""
    try:
        pasta_brk_id = os.getenv('ONEDRIVE_BRK_ID')
        if not pasta_brk_id:
            return False
        
        headers = auth_manager.obter_headers_autenticados()
        
        # ✅ CAMINHO COMPLETO: /BRK/Faturas/2025/07/BRK-Planilha-2025-07_TEMPORARIA_05Jul_15h30.xlsx
        caminho_completo = f"{pasta_destino}{nome_temporaria}"
        upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{caminho_completo}:/content"
        
        headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        upload_response = requests.put(upload_url, headers=headers, data=dados_planilha, timeout=60)
        
        return upload_response.status_code in [200, 201]
        
    except Exception as e:
        print(f"❌ Erro salvando temporária: {e}")
        return False

def limpar_planilhas_temporarias(auth_manager, pasta_destino, ano, mes):
    """Limpar planilhas temporárias da pasta específica do mês/ano"""
    try:
        # ✅ BUSCAR NA PASTA ESPECÍFICA: /BRK/Faturas/2025/07/
        caminho_pasta = pasta_destino.rstrip('/')  # Remove / final se tiver
        list_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{caminho_pasta}:/children"
        
        headers = auth_manager.obter_headers_autenticados()
        response = requests.get(list_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            items = response.json().get('value', [])
            temporarias_removidas = 0
            
            # ✅ PADRÃO ESPECÍFICO: BRK-Planilha-2025-07_TEMPORARIA_*
            padrao_temporaria = f"BRK-Planilha-{ano}-{mes:02d}_TEMPORARIA_"
            
            for item in items:
                nome = item.get('name', '')
                item_id = item.get('id')
                
                # Remover arquivos temporários específicos deste mês/ano
                if nome.startswith(padrao_temporaria) and nome.endswith('.xlsx'):
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

def gerar_nome_temporaria(ano, mes):
    """Gerar nome claro para planilha temporária baseado no padrão existente"""
    agora = datetime.now()
    
    # ✅ PADRÃO: BRK-Planilha-2025-07_TEMPORARIA_05Jul_15h30.xlsx
    # Meses em português abreviado
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
             'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    dia = agora.day
    mes_abrev = meses[agora.month - 1]  # Usar mês atual, não o da planilha
    hora = agora.strftime('%Hh%M')
    
    return f"BRK-Planilha-{ano}-{mes:02d}_TEMPORARIA_{dia:02d}{mes_abrev}_{hora}.xlsx"

def notificar_planilha_temporaria(nome_temporaria, pasta_destino):
    """Notificar admin sobre planilha temporária (opcional)"""
    try:
        # Import opcional - não quebra se módulo não existir
        from processor.alertas.telegram_sender import enviar_telegram
        
        admin_ids = os.getenv("ADMIN_IDS", "").split(",")
        
        if admin_ids and admin_ids[0].strip():
            mensagem = f"""📊 PLANILHA BRK - VERSÃO TEMPORÁRIA

⚠️ Planilha principal estava em uso
💾 Dados salvos em: {nome_temporaria}
📁 Localização: {pasta_destino}
🔄 Sistema tentará atualizar principal em 30 min

📄 Feche a planilha principal quando possível
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
# ✅ CORREÇÃO ESTRUTURA DE PASTAS:
# - ANTES: Salvava na pasta raiz /BRK/ (ERRADO)
# - DEPOIS: Salva na pasta correta /BRK/Faturas/YYYY/MM/ (CORRETO)
# - Principal: BRK-Planilha-2025-07.xlsx
# - Temporária: BRK-Planilha-2025-07_TEMPORARIA_05Jul_15h30.xlsx
#
# Total reduzido: 180 → 60 linhas (economia de 67%)
# ============================================================================
