#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 MÓDULO ALERTAS - Integração Sistema BRK + CCB Alerta Bot
📧 FUNÇÃO: Envio automático de alertas via Telegram após processamento faturas
👨‍💼 RESPONSÁVEL: Sidney Gubitoso - Auxiliar Tesouraria Administrativa Mauá
📅 DATA CRIAÇÃO: 04/07/2025
📁 LOCALIZAÇÃO: processor/alertas/__init__.py

🎯 MÓDULOS DISPONÍVEIS:
- alert_processor: Orquestração principal dos alertas
- ccb_database: Acesso à base CCB via OneDrive
- message_formatter: Formatação de mensagens Telegram
- telegram_sender: Envio via API Telegram

📋 EXEMPLO DE USO:
from processor.alertas.alert_processor import processar_alerta_fatura

dados_fatura = {...}  # Dados extraídos pelo EmailProcessor
resultado = processar_alerta_fatura(dados_fatura)
"""

# Versão do módulo
__version__ = "1.0.0"

# Informações do módulo
__author__ = "Sidney Gubitoso"
__email__ = "auxiliar.tesouraria.maua@example.com"
__description__ = "Integração alertas BRK + CCB via Telegram"

# Imports principais para facilitar uso
try:
    from .alert_processor import processar_alerta_fatura
    from .telegram_sender import enviar_telegram, testar_telegram_bot
    from .message_formatter import formatar_mensagem_alerta
    from .ccb_database import obter_responsaveis_por_codigo
    
    # Lista de funções públicas
    __all__ = [
        'processar_alerta_fatura',
        'enviar_telegram', 
        'testar_telegram_bot',
        'formatar_mensagem_alerta',
        'obter_responsaveis_por_codigo'
    ]
    
except ImportError as e:
    # Se houver erro de import, não quebrar o sistema
    print(f"⚠️ Erro importando módulos alertas: {e}")
    __all__ = []
