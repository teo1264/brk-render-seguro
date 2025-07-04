#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗃️ CCB DATABASE - Acesso Base CCB Alerta Bot via OneDrive
📧 FUNÇÃO: Consultar responsáveis por código da casa
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
"""

import os
import sqlite3
from utils.onedrive_manager import OneDriveManager
from auth.microsoft_auth import MicrosoftAuth

def obter_responsaveis_por_codigo(codigo_casa):
    """
    Consultar responsáveis na base CCB por código da casa
    Reutiliza MESMO auth do Sistema BRK, apenas pasta diferente
    
    Args:
        codigo_casa (str): Código da casa (ex: "BR21-0774")
    
    Returns:
        list: Lista de responsáveis [{'user_id': int, 'nome': str, 'funcao': str}]
    """
    try:
        print(f"🔍 Consultando base CCB para: {codigo_casa}")
        
        # 1. Verificar variável ambiente
        onedrive_alerta_id = os.getenv("ONEDRIVE_ALERTA_ID")
        if not onedrive_alerta_id:
            print(f"❌ ONEDRIVE_ALERTA_ID não configurado")
            return []
        
        print(f"📁 OneDrive Alerta ID: {onedrive_alerta_id[:20]}...")
        
        # 2. Reutilizar auth Microsoft do Sistema BRK
        auth_manager = MicrosoftAuth()
        if not auth_manager.access_token:
            print(f"❌ Auth Microsoft não disponível")
            return []
        
        print(f"🔐 Auth Microsoft: ✅ Disponível")
        
        # 3. Acessar OneDrive pasta /Alerta/ (mesmo auth, pasta diferente)
        onedrive_ccb = OneDriveManager(auth_manager)
        onedrive_ccb.alerta_folder_id = onedrive_alerta_id
        
        print(f"☁️ Acessando OneDrive pasta /Alerta/...")
        
        # 4. Obter caminho database CCB
        db_path = onedrive_ccb.obter_caminho_database_hibrido()
        
        if not db_path:
            print(f"❌ Não foi possível obter caminho database CCB")
            return []
        
        print(f"💾 Database CCB: {os.path.basename(db_path)}")
        
        # 5. Conectar e consultar responsáveis
        conn = sqlite3.connect(db_path)
        
        responsaveis = conn.execute("""
            SELECT user_id, nome, funcao 
            FROM responsaveis 
            WHERE codigo_casa = ?
        """, (codigo_casa,)).fetchall()
        
        conn.close()
        
        # 6. Formatar resultado
        resultado = []
        for user_id, nome, funcao in responsaveis:
            resultado.append({
                'user_id': user_id,
                'nome': nome or 'Nome não informado',
                'funcao': funcao or 'Função não informada'
            })
        
        print(f"✅ Responsáveis encontrados: {len(resultado)}")
        for resp in resultado:
            print(f"   👤 {resp['nome']} ({resp['funcao']}) - ID: {resp['user_id']}")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro consultando base CCB: {e}")
        return []

def testar_conexao_ccb():
    """
    Função de teste para verificar conexão com base CCB
    Útil para debug e validação
    """
    try:
        print(f"\n🧪 TESTE CONEXÃO BASE CCB")
        print(f"="*40)
        
        # Verificações básicas
        onedrive_alerta_id = os.getenv("ONEDRIVE_ALERTA_ID")
        print(f"📁 ONEDRIVE_ALERTA_ID: {'✅ Configurado' if onedrive_alerta_id else '❌ Não configurado'}")
        
        if not onedrive_alerta_id:
            return False
        
        auth_manager = MicrosoftAuth()
        print(f"🔐 Auth Microsoft: {'✅ Disponível' if auth_manager.access_token else '❌ Não disponível'}")
        
        if not auth_manager.access_token:
            return False
        
        # Testar acesso OneDrive
        onedrive_ccb = OneDriveManager(auth_manager)
        onedrive_ccb.alerta_folder_id = onedrive_alerta_id
        
        db_path = onedrive_ccb.obter_caminho_database_hibrido()
        print(f"💾 Database path: {'✅ Obtido' if db_path else '❌ Falhou'}")
        
        if not db_path:
            return False
        
        # Testar query básica
        conn = sqlite3.connect(db_path)
        
        # Contar total de responsáveis
        total_responsaveis = conn.execute("SELECT COUNT(*) FROM responsaveis").fetchone()[0]
        print(f"👥 Total responsáveis: {total_responsaveis}")
        
        # Listar casas distintas
        casas = conn.execute("SELECT DISTINCT codigo_casa FROM responsaveis ORDER BY codigo_casa").fetchall()
        print(f"🏠 Casas cadastradas: {len(casas)}")
        for (casa,) in casas[:5]:  # Mostrar apenas 5 primeiras
            print(f"   🏪 {casa}")
        if len(casas) > 5:
            print(f"   ... e mais {len(casas)-5} casas")
        
        conn.close()
        
        print(f"✅ Teste conexão CCB: SUCESSO")
        return True
        
    except Exception as e:
        print(f"❌ Teste conexão CCB: FALHOU - {e}")
        return False
