#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 PLANILHA BACKUP SIMPLES - Sistema transparente para planilha BRK
📁 FUNÇÃO: Salvar backups VISÍVEIS na pasta correta /BRK/Faturas/YYYY/MM/
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua

🔧 LÓGICA SIMPLES:
   1. Detectar mês/ano atual (julho/2025) ou específico
   2. Tentar salvar /BRK/Faturas/2025/07/BRK-Planilha-2025-07.xlsx
   3. Se ocupada → /BRK/Faturas/2025/07/BRK-Planilha-2025-07_TEMPORARIA_05Jul_15h30.xlsx
   4. A cada 30min → tentar principal + limpar temporárias na pasta correta
   5. Usuário vê claramente os arquivos temporários na pasta do mês
"""

import os
import requests
from datetime import datetime


def salvar_planilha_inteligente(auth_manager, dados_planilha, mes=None, ano=None):
    """
    🆕 FUNÇÃO CORRIGIDA: Salvar planilha com backup para MÊS/ANO ESPECÍFICO
    
    ANTES: Sempre usava mês/ano atual
    AGORA: Aceita mês/ano específico para múltiplas planilhas
    
    ✅ MUDANÇAS:
       - Parâmetros mes/ano opcionais
       - Se não informado, usa mês/ano atual (compatibilidade)
       - Nomes de arquivo específicos para cada mês/ano
       - Backup na pasta correta de cada mês
    
    Args:
        auth_manager: Gerenciador de autenticação
        dados_planilha: Bytes da planilha Excel
        mes (int, optional): Mês específico (1-12). Se None, usa atual
        ano (int, optional): Ano específico. Se None, usa atual
        
    Returns:
        bool: True se salvamento bem-sucedido
    """
    try:
        # ✅ DETECTAR MÊS/ANO ESPECÍFICO OU USAR ATUAL
        if mes is None or ano is None:
            # Fallback para compatibilidade (lógica original)
            hoje = datetime.now()
            mes_usado = mes if mes is not None else hoje.month
            ano_usado = ano if ano is not None else hoje.year
            print(f"📊 Salvamento planilha BRK - Usando mês/ano atual: {mes_usado:02d}/{ano_usado}")
        else:
            # Usar mês/ano específico informado
            mes_usado = mes
            ano_usado = ano
            print(f"📊 Salvamento planilha BRK - Mês/ano específico: {mes_usado:02d}/{ano_usado}")
        
        # ✅ NOMES CORRETOS PARA O MÊS/ANO ESPECÍFICO
        nome_principal = f"BRK-Planilha-{ano_usado}-{mes_usado:02d}.xlsx"
        pasta_destino = f"/BRK/Faturas/{ano_usado}/{mes_usado:02d}/"
        
        print(f"📁 Pasta destino: {pasta_destino}")
        print(f"📄 Arquivo principal: {nome_principal}")
        
        # 1. Tentar salvar planilha principal
        if tentar_salvar_principal(auth_manager, dados_planilha, pasta_destino, nome_principal):
            print(f"✅ Planilha principal {mes_usado:02d}/{ano_usado} atualizada com sucesso")
            
            # 2. Principal salvou → limpar temporárias da pasta correta
            limpar_planilhas_temporarias(auth_manager, pasta_destino, ano_usado, mes_usado)
            return True
        
        # 3. Principal ocupada → salvar temporária VISÍVEL na mesma pasta
        print(f"⚠️ Planilha principal {mes_usado:02d}/{ano_usado} ocupada, criando versão temporária...")
        
        nome_temporaria = gerar_nome_temporaria(ano_usado, mes_usado)
        
        if salvar_planilha_temporaria(auth_manager, dados_planilha, pasta_destino, nome_temporaria):
            print(f"💾 Planilha temporária criada: {nome_temporaria}")
            print(f"📁 Arquivo visível em: {pasta_destino}")
            print(f"🔄 Sistema tentará atualizar principal em 30 minutos")
            
            # 4. Notificar admin se configurado
            notificar_planilha_temporaria(nome_temporaria, pasta_destino, mes_usado, ano_usado)
            
            return True
        else:
            print(f"❌ Falha criando planilha temporária {mes_usado:02d}/{ano_usado}")
            return False
            
    except Exception as e:
        print(f"❌ Erro salvamento planilha {mes_usado:02d}/{ano_usado}: {e}")
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
    """
    🔧 FUNÇÃO CORRIGIDA: Gerar nome temporário para mês/ano específico
    
    ANTES: Sempre baseado no mês atual para timestamp
    AGORA: Nome baseado no mês/ano da planilha + timestamp atual
    
    Args:
        ano (int): Ano da planilha (ex: 2025)
        mes (int): Mês da planilha (ex: 7 para julho)
        
    Returns:
        str: Nome do arquivo temporário
    """
    agora = datetime.now()
    
    # ✅ PADRÃO CORRIGIDO: BRK-Planilha-{ANO}-{MES}_TEMPORARIA_{dia_atual}{mes_atual}_{hora}
    # Exemplo: BRK-Planilha-2025-08_TEMPORARIA_05Jul_15h30.xlsx
    
    # Meses em português abreviado
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
             'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    dia_atual = agora.day
    mes_atual_abrev = meses[agora.month - 1]  # Mês atual para timestamp
    hora_atual = agora.strftime('%Hh%M')
    
    # Nome: Planilha do mês/ano específico + timestamp atual
    nome = f"BRK-Planilha-{ano}-{mes:02d}_TEMPORARIA_{dia_atual:02d}{mes_atual_abrev}_{hora_atual}.xlsx"
    
    return nome


def notificar_planilha_temporaria(nome_temporaria, pasta_destino, mes, ano):
    """
    🔧 FUNÇÃO CORRIGIDA: Notificar admin sobre planilha temporária específica
    
    ANTES: Mensagem genérica
    AGORA: Mensagem específica para o mês/ano da planilha
    
    Args:
        nome_temporaria (str): Nome do arquivo temporário
        pasta_destino (str): Pasta onde foi salvo
        mes (int): Mês específico da planilha
        ano (int): Ano específico da planilha
    """
    try:
        # Import opcional - não quebra se módulo não existir
        from processor.alertas.telegram_sender import enviar_telegram
        
        admin_ids = os.getenv("ADMIN_IDS", "").split(",")
        
        if admin_ids and admin_ids[0].strip():
            # ✅ Converter número do mês para nome
            meses_nomes = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
                5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 
                9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
            }
            
            nome_mes = meses_nomes.get(mes, f"Mês{mes}")
            
            mensagem = f"""📊 PLANILHA BRK - VERSÃO TEMPORÁRIA

📅 Planilha: {nome_mes}/{ano}
⚠️ Arquivo principal estava em uso
💾 Dados salvos em: {nome_temporaria}
📁 Localização: {pasta_destino}
🔄 Sistema tentará atualizar principal em 30 min

📄 Feche BRK-Planilha-{ano}-{mes:02d}.xlsx quando possível
✅ Processamento continua normalmente"""
            
            enviar_telegram(admin_ids[0].strip(), mensagem)
            print(f"📱 Admin notificado via Telegram sobre planilha {mes:02d}/{ano}")
            
    except ImportError:
        print("⚠️ Telegram não configurado - seguindo sem notificação")
    except Exception as e:
        print(f"⚠️ Falha notificação Telegram: {e}")


# ============================================================================
# FUNÇÕES DE COMPATIBILIDADE (MANTIDAS PARA NÃO QUEBRAR SISTEMA EXISTENTE)
# ============================================================================

def salvar_planilha_backup(auth_manager, dados_planilha):
    """
    🔄 COMPATIBILIDADE: Função original que usava apenas mês atual
    Agora redireciona para a nova função com mês/ano atual
    """
    print("🔄 Usando função de compatibilidade - redirecionando para nova versão")
    return salvar_planilha_inteligente(auth_manager, dados_planilha)


def criar_backup_planilha(auth_manager, dados_planilha, nome_arquivo=None):
    """
    🔄 COMPATIBILIDADE: Outra possível função que pode existir no sistema
    """
    print("🔄 Usando função de compatibilidade - redirecionando para nova versão")
    return salvar_planilha_inteligente(auth_manager, dados_planilha)


# ============================================================================
# EXEMPLO DE USO E TESTES
# ============================================================================

if __name__ == "__main__":
    print(f"🧪 TESTE DO SISTEMA BACKUP PLANILHA BRK")
    print(f"Este módulo deve ser importado pelo monitor_brk.py")
    print(f"")
    print(f"📋 EXEMPLO DE USO:")
    print(f"")
    print(f"# Para planilha do mês atual:")
    print(f"sucesso = salvar_planilha_inteligente(auth, dados_planilha)")
    print(f"")
    print(f"# Para planilha de mês específico:")
    print(f"sucesso = salvar_planilha_inteligente(auth, dados_planilha, mes=8, ano=2025)")
    print(f"")
    print(f"📊 RESULTADO ESPERADO:")
    print(f"   ✅ Planilha principal: /BRK/Faturas/2025/08/BRK-Planilha-2025-08.xlsx")
    print(f"   💾 Se ocupada: /BRK/Faturas/2025/08/BRK-Planilha-2025-08_TEMPORARIA_05Jul_15h30.xlsx")
    print(f"   🧹 Limpeza automática de temporárias antigas")
    print(f"   📱 Notificação admin via Telegram (opcional)")
