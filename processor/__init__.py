#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/__init__.py
💾 ONDE SALVAR: brk-monitor-seguro/processor/__init__.py
📦 FUNÇÃO: Exports do módulo processor completo
🔧 DESCRIÇÃO: Centraliza acesso aos módulos de processamento de emails, database e monitor
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
"""

from .email_processor import EmailProcessor
from .database_brk import DatabaseBRK
from .monitor_brk import MonitorBRK, verificar_dependencias_monitor, iniciar_monitoramento_automatico

__version__ = "1.0.0"
__author__ = "Sidney Gubitoso, auxiliar tesouraria adm maua"
__all__ = [
    "EmailProcessor",
    "DatabaseBRK", 
    "MonitorBRK",
    "verificar_dependencias_monitor",
    "iniciar_monitoramento_automatico"
]
