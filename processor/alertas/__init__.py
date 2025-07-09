#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 MÓDULO ALERTAS - Integração Sistema BRK + CCB Alerta Bot
📧 FUNÇÃO: Envio automático de alertas via Telegram após processamento faturas
👨‍💼 RESPONSÁVEL: Sidney Gubitoso - Auxiliar Tesouraria Administrativa Mauá
📅 DATA CRIAÇÃO: 04/07/2025
📁 LOCALIZAÇÃO: processor/alertas/__init__.py
🆕 VERSÃO: 2.0 - COM ANEXOS PDF

🎯 MÓDULOS DISPONÍVEIS:
- alert_processor: Orquestração principal dos alertas (COM ANEXOS)
- ccb_database: Acesso à base CCB via OneDrive
- message_formatter: Formatação de mensagens Telegram
- telegram_sender: Envio via API Telegram (COM ANEXOS)

📋 EXEMPLO DE USO:
from processor.alertas.alert_processor import processar_alerta_fatura

dados_fatura = {...}  # Dados extraídos pelo EmailProcessor
resultado = processar_alerta_fatura(dados_fatura)  # Envia mensagem + PDF anexado

🆕 FUNCIONALIDADES v2.0:
- Anexo PDF automático baixado do OneDrive
- Fallback para só mensagem se PDF falhar
- Suporte a múltiplos formatos de arquivo
- Rate limiting para documentos
"""

# Versão do módulo
__version__ = "2.0.0"

# Informações do módulo
__author__ = "Sidney Gubitoso"
__email__ = "auxiliar.tesouraria.maua@example.com"
__description__ = "Integração alertas BRK + CCB via Telegram COM ANEXOS PDF"

# Imports principais para facilitar uso
try:
    from .alert_processor import processar_alerta_fatura
    from .telegram_sender import (
        enviar_telegram, 
        enviar_telegram_com_anexo,  # 🆕 NOVA FUNÇÃO
        testar_telegram_bot,
        testar_telegram_com_anexo   # 🆕 NOVA FUNÇÃO
    )
    from .message_formatter import formatar_mensagem_alerta
    from .ccb_database import obter_responsaveis_por_codigo
    
    # Lista de funções públicas
    __all__ = [
        'processar_alerta_fatura',
        'enviar_telegram', 
        'enviar_telegram_com_anexo',        # 🆕 NOVA FUNÇÃO
        'testar_telegram_bot',
        'testar_telegram_com_anexo',        # 🆕 NOVA FUNÇÃO
        'formatar_mensagem_alerta',
        'obter_responsaveis_por_codigo'
    ]
    
    # Status das funcionalidades
    __features__ = {
        'mensagens_basicas': True,
        'anexos_pdf': True,          # 🆕 NOVA FUNCIONALIDADE
        'fallback_automatico': True,
        'rate_limiting': True,
        'consulta_ccb': True,
        'formatacao_avancada': True
    }
    
except ImportError as e:
    # Se houver erro de import, não quebrar o sistema
    print(f"⚠️ Erro importando módulos alertas: {e}")
    __all__ = []
    __features__ = {
        'mensagens_basicas': False,
        'anexos_pdf': False,
        'fallback_automatico': False,
        'rate_limiting': False,
        'consulta_ccb': False,
        'formatacao_avancada': False
    }

# Função de conveniência para testar tudo
def testar_modulo_completo():
    """
    🆕 FUNÇÃO: Testar todo o módulo alertas
    Testa: configuração, envio mensagem, envio com anexo
    """
    try:
        print(f"\n🧪 TESTE MÓDULO ALERTAS COMPLETO v{__version__}")
        print(f"="*50)
        
        # Teste 1: Configuração
        print(f"1️⃣ Testando configuração...")
        from .telegram_sender import verificar_configuracao_telegram
        config = verificar_configuracao_telegram()
        
        if not config.get('bot_token_valido'):
            print(f"❌ Configuração inválida - abortando testes")
            return False
        
        # Teste 2: Mensagem básica
        print(f"\n2️⃣ Testando mensagem básica...")
        from .telegram_sender import testar_telegram_bot
        teste_basico = testar_telegram_bot()
        
        if not teste_basico:
            print(f"❌ Teste básico falhou - abortando")
            return False
        
        # Teste 3: Anexo PDF
        print(f"\n3️⃣ Testando anexo PDF...")
        from .telegram_sender import testar_telegram_com_anexo
        teste_anexo = testar_telegram_com_anexo()
        
        # Teste 4: Consulta CCB
        print(f"\n4️⃣ Testando consulta CCB...")
        from .ccb_database import testar_conexao_ccb
        teste_ccb = testar_conexao_ccb()
        
        # Resultado final
        testes_ok = sum([teste_basico, teste_anexo, teste_ccb])
        print(f"\n📊 RESULTADO TESTES MÓDULO:")
        print(f"   ✅ Configuração: {'OK' if config.get('bot_token_valido') else 'FALHA'}")
        print(f"   ✅ Mensagem básica: {'OK' if teste_basico else 'FALHA'}")
        print(f"   ✅ Anexo PDF: {'OK' if teste_anexo else 'FALHA'}")
        print(f"   ✅ Consulta CCB: {'OK' if teste_ccb else 'FALHA'}")
        print(f"   📈 Score: {testes_ok}/3 testes principais")
        
        if testes_ok >= 2:
            print(f"🎯 MÓDULO ALERTAS: ✅ FUNCIONANDO")
            return True
        else:
            print(f"🎯 MÓDULO ALERTAS: ❌ PROBLEMAS DETECTADOS")
            return False
        
    except Exception as e:
        print(f"❌ Erro testando módulo completo: {e}")
        return False

# Informações para debug
def info_modulo():
    """
    🆕 FUNÇÃO: Informações do módulo alertas
    """
    print(f"\n📦 MÓDULO ALERTAS v{__version__}")
    print(f"="*40)
    print(f"👨‍💼 Autor: {__author__}")
    print(f"📧 Descrição: {__description__}")
    print(f"📅 Versão: {__version__}")
    
    print(f"\n🎯 FUNCIONALIDADES:")
    for funcionalidade, ativo in __features__.items():
        status = "✅ Ativo" if ativo else "❌ Inativo"
        print(f"   {funcionalidade}: {status}")
    
    print(f"\n📋 FUNÇÕES PÚBLICAS:")
    for funcao in __all__:
        print(f"   📝 {funcao}")
    
    print(f"\n💡 EXEMPLO DE USO:")
    print(f"   from processor.alertas import processar_alerta_fatura")
    print(f"   resultado = processar_alerta_fatura(dados_fatura)")
    print(f"   # Envia mensagem + PDF anexado automaticamente")
