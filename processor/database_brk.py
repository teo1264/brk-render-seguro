#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗃️ CCB DATABASE - Acesso Base CCB Alerta Bot via OneDrive
📧 FUNÇÃO: Consultar responsáveis por código da casa
👨‍💼 RESPONSÁVEL: Sidney Gubitoso - Auxiliar Tesouraria Administrativa Mauá
📅 DATA CRIAÇÃO: 04/07/2025
📁 SALVAR EM: processor/alertas/ccb_database.py
✅ CORRIGIDO: Sem dependência OneDriveManager, acesso direto Graph API
"""

import os
import sqlite3
import requests
import tempfile
from auth.microsoft_auth import MicrosoftAuth

def obter_responsaveis_por_codigo(codigo_casa):
    """
    Consultar responsáveis na base CCB por código da casa
    ✅ CORRIGIDO: Acesso direto via Microsoft Graph API (sem OneDriveManager)
    
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
        
        # 2. Usar auth Microsoft do Sistema BRK
        auth_manager = MicrosoftAuth()
        if not auth_manager.access_token:
            print(f"❌ Auth Microsoft não disponível")
            return []
        
        print(f"🔐 Auth Microsoft: ✅ Disponível")
        
        # 3. Obter headers autenticados
        headers = auth_manager.obter_headers_autenticados()
        if not headers:
            print(f"❌ Headers de autenticação não disponíveis")
            return []
        
        # 4. Buscar database alertas_bot.db na pasta /Alerta/
        print(f"☁️ Buscando alertas_bot.db na pasta /Alerta/...")
        
        # Listar arquivos na pasta /Alerta/
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{onedrive_alerta_id}/children"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erro acessando pasta /Alerta/: HTTP {response.status_code}")
            return []
        
        arquivos = response.json().get('value', [])
        
        # Procurar alertas_bot.db
        db_file_id = None
        for arquivo in arquivos:
            if arquivo.get('name', '').lower() == 'alertas_bot.db':
                db_file_id = arquivo['id']
                print(f"💾 alertas_bot.db encontrado: {arquivo['name']}")
                break
        
        if not db_file_id:
            print(f"❌ alertas_bot.db não encontrado na pasta /Alerta/")
            return []
        
        # 5. Baixar database para cache temporário
        print(f"📥 Baixando alertas_bot.db...")
        
        download_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{db_file_id}/content"
        download_response = requests.get(download_url, headers=headers, timeout=60)
        
        if download_response.status_code != 200:
            print(f"❌ Erro baixando database: HTTP {download_response.status_code}")
            return []
        
        # Salvar em cache local temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db', prefix='ccb_cache_') as tmp_file:
            tmp_file.write(download_response.content)
            db_path = tmp_file.name
        
        print(f"💾 Database baixado para: {db_path}")
        
        # 6. Conectar SQLite e consultar responsáveis
        conn = sqlite3.connect(db_path)
        
        try:
            responsaveis = conn.execute("""
                SELECT user_id, nome, funcao 
                FROM responsaveis 
                WHERE codigo_casa = ?
            """, (codigo_casa,)).fetchall()
            
            # 7. Formatar resultado
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
            
        finally:
            conn.close()
            # Limpar cache temporário
            try:
                os.unlink(db_path)
            except:
                pass
        
    except Exception as e:
        print(f"❌ Erro consultando base CCB: {e}")
        return []

def testar_conexao_ccb():
    """
    Função de teste para verificar conexão com base CCB
    ✅ CORRIGIDO: Sem dependência OneDriveManager
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
        
        # Testar acesso à pasta /Alerta/
        headers = auth_manager.obter_headers_autenticados()
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{onedrive_alerta_id}/children"
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"☁️ Acesso pasta /Alerta/: {'✅ OK' if response.status_code == 200 else '❌ Falhou'}")
        
        if response.status_code != 200:
            return False
        
        # Verificar se alertas_bot.db existe
        arquivos = response.json().get('value', [])
        db_encontrado = any(arquivo.get('name', '').lower() == 'alertas_bot.db' for arquivo in arquivos)
        
        print(f"💾 alertas_bot.db: {'✅ Encontrado' if db_encontrado else '❌ Não encontrado'}")
        
        # Listar todos os arquivos da pasta
        print(f"📂 Arquivos na pasta /Alerta/: {len(arquivos)}")
        for arquivo in arquivos[:5]:  # Mostrar apenas 5 primeiros
            nome = arquivo.get('name', 'N/A')
            tamanho = arquivo.get('size', 0)
            print(f"   📄 {nome} ({tamanho} bytes)")
        if len(arquivos) > 5:
            print(f"   ... e mais {len(arquivos)-5} arquivo(s)")
        
        if db_encontrado:
            print(f"✅ Teste conexão CCB: SUCESSO")
            return True
        else:
            print(f"❌ Teste conexão CCB: alertas_bot.db não encontrado")
            return False
        
    except Exception as e:
        print(f"❌ Teste conexão CCB: FALHOU - {e}")
        return False

def listar_responsaveis_todas_casas():
    """
    Função auxiliar para listar todos os responsáveis (debug)
    ✅ CORRIGIDO: Acesso direto Graph API
    """
    try:
        print(f"\n📋 LISTANDO TODOS OS RESPONSÁVEIS")
        print(f"="*40)
        
        # Verificações básicas
        onedrive_alerta_id = os.getenv("ONEDRIVE_ALERTA_ID")
        if not onedrive_alerta_id:
            print(f"❌ ONEDRIVE_ALERTA_ID não configurado")
            return []
        
        auth_manager = MicrosoftAuth()
        if not auth_manager.access_token:
            print(f"❌ Auth Microsoft não disponível")
            return []
        
        # Baixar database (reutilizar lógica da função principal)
        headers = auth_manager.obter_headers_autenticados()
        
        # Buscar alertas_bot.db
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{onedrive_alerta_id}/children"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erro acessando pasta /Alerta/")
            return []
        
        arquivos = response.json().get('value', [])
        db_file_id = None
        
        for arquivo in arquivos:
            if arquivo.get('name', '').lower() == 'alertas_bot.db':
                db_file_id = arquivo['id']
                break
        
        if not db_file_id:
            print(f"❌ alertas_bot.db não encontrado")
            return []
        
        # Baixar e consultar
        download_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{db_file_id}/content"
        download_response = requests.get(download_url, headers=headers, timeout=60)
        
        if download_response.status_code != 200:
            print(f"❌ Erro baixando database")
            return []
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            tmp_file.write(download_response.content)
            db_path = tmp_file.name
        
        # Consultar todos os responsáveis
        conn = sqlite3.connect(db_path)
        
        try:
            # Estatísticas gerais
            total_responsaveis = conn.execute("SELECT COUNT(*) FROM responsaveis").fetchone()[0]
            print(f"👥 Total responsáveis: {total_responsaveis}")
            
            # Responsáveis por casa
            casas = conn.execute("""
                SELECT codigo_casa, COUNT(*) as total
                FROM responsaveis 
                GROUP BY codigo_casa 
                ORDER BY codigo_casa
            """).fetchall()
            
            print(f"🏠 Casas cadastradas: {len(casas)}")
            for codigo_casa, total in casas:
                print(f"   🏪 {codigo_casa}: {total} responsável(is)")
            
            # Todos os responsáveis
            todos = conn.execute("""
                SELECT codigo_casa, user_id, nome, funcao
                FROM responsaveis 
                ORDER BY codigo_casa, nome
            """).fetchall()
            
            responsaveis_lista = []
            for codigo_casa, user_id, nome, funcao in todos:
                responsaveis_lista.append({
                    'codigo_casa': codigo_casa,
                    'user_id': user_id,
                    'nome': nome,
                    'funcao': funcao
                })
            
            print(f"✅ Lista completa obtida: {len(responsaveis_lista)} responsáveis")
            return responsaveis_lista
            
        finally:
            conn.close()
            try:
                os.unlink(db_path)
            except:
                pass
        
    except Exception as e:
        print(f"❌ Erro listando responsáveis: {e}")
        return []
