#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: admin/__init__.py
💾 ONDE SALVAR: brk-monitor-seguro/admin/__init__.py
📦 FUNÇÃO: Inicializador do módulo administrativo
🔧 DESCRIÇÃO: Centraliza acesso aos módulos de administração
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
"""

from .admin_server import AdminServer, AdminHandler

__version__ = "1.0.0"
__author__ = "Sidney Gubitoso, auxiliar tesouraria adm maua"
__all__ = ["AdminServer", "AdminHandler"]
