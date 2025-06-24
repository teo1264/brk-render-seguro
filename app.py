#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 BRK RENDER MONITOR - Sistema Seguro

DEPLOY: Render.com com PERSISTENT DISK
FUNÇÃO: Monitor email BRK + SQLite + OneDrive básico
SEGURANÇA: Todas as credenciais via variáveis de ambiente
"""

import os
import time
import sqlite3
import requests
import json
import base64
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class EmailMonitor:
    """Monitor emails BRK - VERSÃO SEGURA"""
    
    def __init__(self):
        # CONFIGURAÇÕES APENAS VIA ENVIRONMENT VARIABLES
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.tenant_id = os.getenv("MICROSOFT_TENANT_ID", "consumers")
        self.pasta_brk_id = os.getenv("PASTA_BRK_ID")
        
        # VALIDAÇÃO OBRIGATÓRIA
        if not self.client_id:
            raise ValueError("❌ MICROSOFT_CLIENT_ID não configurado!")
        if not self.pasta_brk_id:
            raise ValueError("❌ PASTA_BRK_ID não configurado!")
        
        # Token management
        self.token_file_persistent = "/opt/render/project/storage/token.json"
        self.token_file_local = "token.json"
        self.access_token = None
        self.refresh_token = None
        
        # Carregar tokens
        tokens_ok = self.carregar_token()
        
        print(f"📧 Email Monitor SEGURO inicializado")
        print(f"   Client ID: {self.client_id[:8]}****** (protegido)")
        print(f"   Pasta BRK: {self.pasta_brk_id[:10]}****** (protegido)")
        print(f"   Token: {'✅ OK' if tokens_ok else '❌ Faltando'}")
    
    def carregar_token(self):
        """Carregar token do persistent disk ou local"""
        if os.path.exists(self.token_file_persistent):
            return self._carregar_do_arquivo(self.token_file_persistent)
        elif os.path.exists(self.token_file_local):
            return self._carregar_do_arquivo(self.token_file_local)
        else:
            print("💡 Token não encontrado - use interface web para upload")
            return False
    
    def _carregar_do_arquivo(self, filepath: str):
        """Carregar token de arquivo específico"""
        try:
            with open(filepath, 'r') as f:
                token_data = json.load(f)
            
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            if self.access_token and self.refresh_token:
                print(f"✅ Tokens carregados de: {filepath}")
                return True
            else:
                print(f"❌ Tokens incompletos em: {filepath}")
                return False
        except Exception as e:
            print(f"❌ Erro carregando {filepath}: {e}")
            return False
    
    def salvar_token_persistent(self):
        """Salvar token no persistent disk"""
        try:
            os.makedirs(os.path.dirname(self.token_file_persistent), exist_ok=True)
            
            token_data = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_in": 3600
            }
            
            with open(self.token_file_persistent, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            print(f"💾 Token salvo: {self.token_file_persistent}")
            return True
        except Exception as e:
            print(f"❌ Erro salvando token: {e}")
            return False

    def atualizar_token(self):
        """Renovar access_token usando refresh_token"""
        if not self.refresh_token:
            print("❌ Refresh token não disponível")
            return False
        
        try:
            url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            data = {
                'client_id': self.client_id,
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'scope': 'https://graph.microsoft.com/.default offline_access'
            }
            
            response = requests.post(url, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                
                if 'refresh_token' in token_data:
                    self.refresh_token = token_data['refresh_token']
                
                self.salvar_token_persistent()
                print("✅ Token renovado com sucesso")
                return True
            else:
                print(f"❌ Erro renovando token: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro na renovação: {e}")
            return False
    
    def buscar_emails_novos(self, dias_atras: int = 1) -> List[Dict]:
        """Buscar emails novos na pasta BRK"""
        try:
            data_limite = datetime.now() - timedelta(days=dias_atras)
            data_limite_str = data_limite.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_brk_id}/messages"
            headers = {'Authorization': f'Bearer {self.access_token}'}
            params = {
                '$filter': f"receivedDateTime ge {data_limite_str}",
                '$expand': 'attachments',
                '$top': 10
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 401:
                print("🔄 Token expirado, renovando...")
                if self.atualizar_token():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                emails = data.get('value', [])
                print(f"📧 Encontrados {len(emails)} emails")
                return emails
            else:
                print(f"❌ Erro buscando emails: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return []
    
    def extrair_pdfs_do_email(self, email: Dict) -> List[Dict]:
        """Extrair PDFs dos anexos do email"""
        pdfs = []
        try:
            attachments = email.get('attachments', [])
            email_id = email.get('id', 'unknown')
            
            for attachment in attachments:
                filename = attachment.get('name', '').lower()
                if filename.endswith('.pdf'):
                    pdf_info = {
                        'email_id': email_id,
                        'filename': attachment.get('name', 'unnamed.pdf'),
                        'size': attachment.get('size', 0),
                        'content_bytes': attachment.get('contentBytes', ''),
                        'received_date': email.get('receivedDateTime', '')
                    }
                    pdfs.append(pdf_info)
            return pdfs
        except Exception as e:
            print(f"❌ Erro extraindo PDFs: {e}")
            return []

    def diagnosticar_pasta_brk(self) -> Dict:
        """Diagnóstico completo da pasta BRK"""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            base_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_brk_id}/messages"
            
            # Total geral
            response_total = requests.get(base_url, headers=headers, params={'$top': 1, '$count': 'true'})
            
            if response_total.status_code == 401:
                if self.atualizar_token():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response_total = requests.get(base_url, headers=headers, params={'$top': 1, '$count': 'true'})
            
            total_geral = response_total.json().get('@odata.count', 0) if response_total.status_code == 200 else 0
            
            # Últimas 24h
            data_24h = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
            params_24h = {'$filter': f"receivedDateTime ge {data_24h}", '$top': 1, '$count': 'true'}
            response_24h = requests.get(base_url, headers=headers, params=params_24h)
            total_24h = response_24h.json().get('@odata.count', 0) if response_24h.status_code == 200 else 0
            
            # Mês atual
            primeiro_dia = datetime.now().replace(day=1, hour=0, minute=0, second=0).strftime('%Y-%m-%dT%H:%M:%SZ')
            params_mes = {'$filter': f"receivedDateTime ge {primeiro_dia}", '$top': 1, '$count': 'true'}
            response_mes = requests.get(base_url, headers=headers, params=params_mes)
            total_mes = response_mes.json().get('@odata.count', 0) if response_mes.status_code == 200 else 0
            
            return {
                'total_geral': total_geral,
                'ultimas_24h': total_24h,
                'mes_atual': total_mes,
                'status': 'sucesso'
            }
        except Exception as e:
            print(f"❌ Erro diagnóstico: {e}")
            return {'total_geral': 0, 'ultimas_24h': 0, 'mes_atual': 0, 'status': 'erro'}

class DatabaseBRKBasico:
    """Database SQLite básico com persistent disk"""
    
    def __init__(self, db_path: str = "/opt/render/project/storage/brk_basico.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.criar_tabelas()
    
    def criar_tabelas(self):
        """Criar tabelas necessárias"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            sql_faturas = """
            CREATE TABLE IF NOT EXISTS faturas_brk_basico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_emissao TEXT, nota_fiscal TEXT, valor TEXT,
                codigo_cliente TEXT, vencimento TEXT, competencia TEXT,
                email_id TEXT, nome_arquivo TEXT, hash_arquivo TEXT,
                tamanho_bytes INTEGER, caminho_onedrive TEXT,
                data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'processado',
                UNIQUE(hash_arquivo)
            )"""
            
            sql_emails = """
            CREATE TABLE IF NOT EXISTS emails_processados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT UNIQUE NOT NULL,
                data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pdfs_encontrados INTEGER DEFAULT 0,
                status TEXT DEFAULT 'processado'
            )"""
            
            conn.execute(sql_faturas)
            conn.execute(sql_emails)
            conn.commit()
            conn.close()
            print(f"✅ Database criado: {self.db_path}")
        except Exception as e:
            print(f"❌ Erro criando database: {e}")
    
    def email_ja_processado(self, email_id: str) -> bool:
        """Verificar se email já foi processado"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT id FROM emails_processados WHERE email_id = ?", (email_id,))
            resultado = cursor.fetchone()
            conn.close()
            return resultado is not None
        except Exception:
            return False
    
    def salvar_fatura(self, dados: Dict) -> bool:
        """Salvar fatura no banco"""
        try:
            conn = sqlite3.connect(self.db_path)
            hash_arquivo = dados.get('hash_arquivo', '')
            
            if hash_arquivo:
                cursor = conn.execute("SELECT id FROM faturas_brk_basico WHERE hash_arquivo = ?", (hash_arquivo,))
                if cursor.fetchone():
                    print(f"⚠️ PDF duplicado: {dados.get('nome_arquivo', 'unknown')}")
                    conn.close()
                    return False
            
            conn.execute("""
                INSERT INTO faturas_brk_basico 
                (data_emissao, nota_fiscal, valor, codigo_cliente, vencimento, competencia,
                 email_id, nome_arquivo, hash_arquivo, tamanho_bytes, caminho_onedrive)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dados.get('Data_Emissao', ''), dados.get('Nota_Fiscal', ''), dados.get('Valor', ''),
                dados.get('Codigo_Cliente', ''), dados.get('Vencimento', ''), dados.get('Competencia', ''),
                dados.get('email_id', ''), dados.get('nome_arquivo', ''), dados.get('hash_arquivo', ''),
                dados.get('tamanho_bytes', 0), dados.get('caminho_onedrive', '')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Erro salvando: {e}")
            return False
    
    def marcar_email_processado(self, email_id: str, pdfs_count: int):
        """Marcar email como processado"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT OR REPLACE INTO emails_processados (email_id, pdfs_encontrados) VALUES (?, ?)", 
                        (email_id, pdfs_count))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Erro marcando email: {e}")
    
    def obter_estatisticas(self) -> Dict:
        """Estatísticas do banco"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            cursor = conn.execute("SELECT COUNT(*) FROM faturas_brk_basico")
            total_faturas = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM emails_processados")
            total_emails = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT nome_arquivo, data_processamento FROM faturas_brk_basico ORDER BY data_processamento DESC LIMIT 5")
            ultimas_faturas = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_faturas': total_faturas,
                'total_emails_processados': total_emails,
                'ultimas_faturas': ultimas_faturas,
                'ultima_atualizacao': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Erro stats: {e}")
            return {}

class OneDriveBasico:
    """Cliente OneDrive simulado"""
    
    def __init__(self):
        self.base_path = "/BRK"
        self.local_path = Path("/opt/render/project/storage/onedrive_simulado/BRK")
        self.local_path.mkdir(parents=True, exist_ok=True)
        print(f"📤 OneDrive simulado: {self.local_path}")
    
    def upload_pdf(self, pdf_content: bytes, filename: str) -> str:
        """Upload simulado no persistent disk"""
        try:
            filepath = self.local_path / filename
            with open(filepath, 'wb') as f:
                f.write(pdf_content)
            
            caminho = f"{self.base_path}/{filename}"
            print(f"📤 PDF salvo: {filename} ({len(pdf_content)} bytes)")
            return caminho
        except Exception as e:
            print(f"❌ Erro upload: {e}")
            return None
# BLOCO 1/3 - SUBSTITUIR A CLASSE StatusHandler COMPLETA
# Procurar: class StatusHandler(BaseHTTPRequestHandler):
# SUBSTITUIR TODA A CLASSE por esta versão:

class StatusHandler(BaseHTTPRequestHandler):
    """Servidor web com interface segura + TESTE ONEDRIVE"""
    # BLOCO 2/3 - CORRIGIR MÉTODO test_onedrive_access
# Encontrar na classe StatusHandler o método test_onedrive_access
# SUBSTITUIR APENAS esta parte (linha ~330 aproximadamente):

    def test_onedrive_access(self):
        """Teste básico de acesso OneDrive usando credenciais atuais"""
        print("🧪 TESTE ONEDRIVE - INICIANDO")
        
        try:
            # 1. CARREGAR CONFIGURAÇÕES ATUAIS
            client_id = os.getenv('MICROSOFT_CLIENT_ID')
            token_path = "/opt/render/project/storage/token.json"
            
            if not client_id:
                return {
                    "status": "error",
                    "onedrive_access": False,
                    "message": "CLIENT_ID não configurado",
                    "details": "Environment variable MICROSOFT_CLIENT_ID não encontrada"
                }
            
            print(f"✅ CLIENT_ID encontrado: {client_id[:10]}******")
            
            # 2. CARREGAR TOKEN ATUAL
            if not os.path.exists(token_path):
                return {
                    "status": "error", 
                    "onedrive_access": False,
                    "message": "Token não encontrado",
                    "details": f"Arquivo {token_path} não existe"
                }
            
            with open(token_path, 'r') as f:
                token_data = json.load(f)
            
            if 'refresh_token' not in token_data:
                return {
                    "status": "error",
                    "onedrive_access": False, 
                    "message": "Refresh token não encontrado",
                    "details": "Token.json não contém refresh_token"
                }
            
            print("✅ Token.json carregado com sucesso")
            
            # 3. TESTAR DIFERENTES SCOPES ONEDRIVE
            print("🔄 Testando diferentes scopes OneDrive...")
            
            # OPÇÃO 1: Scope específico OneDrive
            scopes_para_testar = [
                "Files.ReadWrite offline_access",
                "Files.ReadWrite.All offline_access", 
                "https://graph.microsoft.com/Files.ReadWrite offline_access",
                "https://graph.microsoft.com/Files.ReadWrite.All offline_access"
            ]
            
            token_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
            access_token = None
            scope_funcionou = None
            
            for scope_teste in scopes_para_testar:
                print(f"🧪 Testando scope: {scope_teste}")
                
                token_data_request = {
                    'client_id': client_id,
                    'grant_type': 'refresh_token', 
                    'refresh_token': token_data['refresh_token'],
                    'scope': scope_teste
                }
                
                response = requests.post(token_url, data=token_data_request)
                
                if response.status_code == 200:
                    new_token = response.json()
                    access_token = new_token.get('access_token')
                    if access_token:
                        scope_funcionou = scope_teste
                        print(f"✅ Scope funcionou: {scope_teste}")
                        break
                else:
                    print(f"❌ Scope falhou: {scope_teste} -> {response.status_code}")
            
            if not access_token:
                # Se nenhum scope OneDrive funcionou, testar scope atual
                print("🔄 Testando com scope atual do email...")
                
                token_data_request = {
                    'client_id': client_id,
                    'grant_type': 'refresh_token',
                    'refresh_token': token_data['refresh_token'],
                    'scope': 'https://graph.microsoft.com/.default offline_access'
                }
                
                response = requests.post(token_url, data=token_data_request)
                
                if response.status_code == 200:
                    new_token = response.json()
                    access_token = new_token.get('access_token')
                    scope_funcionou = "scope atual (sem OneDrive)"
                    print("✅ Token renovado com scope atual")
                else:
                    return {
                        "status": "error",
                        "onedrive_access": False,
                        "message": "Nenhum scope funcionou",
                        "details": f"Último erro: HTTP {response.status_code}: {response.text[:200]}"
                    }
            
            # 4. TESTAR ACESSO ONEDRIVE
            print("🔍 Testando acesso OneDrive...")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Teste básico: informações da raiz do OneDrive
            onedrive_url = "https://graph.microsoft.com/v1.0/me/drive/root"
            
            onedrive_response = requests.get(onedrive_url, headers=headers)
            
            if onedrive_response.status_code == 200:
                drive_info = onedrive_response.json()
                print("✅ ACESSO ONEDRIVE FUNCIONANDO!")
                
                return {
                    "status": "success",
                    "onedrive_access": True,
                    "message": "Credenciais atuais funcionam para OneDrive!",
                    "details": {
                        "scope_usado": scope_funcionou,
                        "drive_id": drive_info.get('id', 'N/A')[:20] + "...",
                        "drive_type": drive_info.get('driveType', 'N/A'),
                        "owner": drive_info.get('owner', {}).get('user', {}).get('displayName', 'N/A'),
                        "teste_timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }
                }
            
            elif onedrive_response.status_code == 403:
                print("❌ ERRO 403: Sem permissão OneDrive")
                return {
                    "status": "error",
                    "onedrive_access": False,
                    "message": "Sem permissão para acessar OneDrive",
                    "details": f"Scope usado: {scope_funcionou}. Aplicação precisa de permissão Files.ReadWrite.All no Azure",
                    "scope_testado": scope_funcionou
                }
            
            else:
                print(f"❌ Erro OneDrive: {onedrive_response.status_code}")
                return {
                    "status": "error", 
                    "onedrive_access": False,
                    "message": f"Erro ao acessar OneDrive: {onedrive_response.status_code}",
                    "details": onedrive_response.text[:300],
                    "scope_usado": scope_funcionou
                }
        
        except Exception as e:
            print(f"❌ ERRO GERAL: {str(e)}")
            return {
                "status": "error",
                "onedrive_access": False,
                "message": "Erro interno no teste",
                "details": str(e)
            }
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            client_id = os.getenv("MICROSOFT_CLIENT_ID", "NÃO CONFIGURADO")
            client_safe = client_id[:8] + "******" if len(client_id) > 8 else "NÃO CONFIGURADO"
            
            pasta_id = os.getenv("PASTA_BRK_ID", "NÃO CONFIGURADO")
            pasta_safe = pasta_id[:10] + "******" if len(pasta_id) > 10 else "NÃO CONFIGURADO"
            
            html = f"""
            <html><head><title>BRK Monitor Status</title></head>
            <body style="font-family: Arial; margin: 50px;">
                <h1>🚀 BRK MONITOR SEGURO</h1>
                <p><strong>Status:</strong> ✅ Ativo</p>
                <p><strong>Última exec:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                <hr>
                <h3>🔒 Config Segura</h3>
                <p><strong>Client ID:</strong> {client_safe}</p>
                <p><strong>Pasta BRK:</strong> {pasta_safe}</p>
                <hr>
                <p><a href="/upload-token">📁 Upload Token</a> | <a href="/health">🔍 Health</a> | <a href="/test-onedrive">🧪 Teste OneDrive</a></p>
                <small>🔒 Dados protegidos - Versão limpa</small>
            </body></html>
            """
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/upload-token':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html><head><title>Upload Token</title></head>
            <body style="font-family: Arial; margin: 50px;">
                <h1>📁 Upload Token</h1>
                <form method="POST" action="/upload-token">
                    <textarea name="token_content" rows="15" cols="70" placeholder='{"access_token": "...", "refresh_token": "..."}'></textarea><br><br>
                    <button type="submit">💾 Salvar Token</button>
                </form>
                <p><a href="/">← Voltar</a></p>
            </body></html>
            """
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/test-onedrive':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            try:
                # Executar teste OneDrive
                resultado = self.test_onedrive_access()
                self.wfile.write(json.dumps(resultado, indent=2, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                erro_response = {
                    "status": "error",
                    "onedrive_access": False,
                    "message": "Erro criando teste OneDrive",
                    "details": str(e)
                }
                self.wfile.write(json.dumps(erro_response, indent=2).encode('utf-8'))
        
        elif self.path == '/onedrive-info':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            info = {
                "teste": "Acesse /test-onedrive para testar acesso",
                "objetivo": "Verificar se credenciais atuais funcionam com OneDrive",
                "url_teste": "https://brk-render-seguro.onrender.com/test-onedrive"
            }
            self.wfile.write(json.dumps(info, indent=2, ensure_ascii=False).encode('utf-8'))
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health = {
                "status": "healthy",
                "service": "brk-monitor-seguro",
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "client_id": "ok" if os.getenv("MICROSOFT_CLIENT_ID") else "missing",
                    "pasta_brk": "ok" if os.getenv("PASTA_BRK_ID") else "missing"
                }
            }
            self.wfile.write(json.dumps(health, indent=2).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/upload-token':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                import urllib.parse
                parsed = urllib.parse.parse_qs(post_data)
                token_content = parsed.get('token_content', [''])[0]
                
                if token_content.strip():
                    token_data = json.loads(token_content)
                    
                    if 'access_token' in token_data and 'refresh_token' in token_data:
                        token_file = "/opt/render/project/storage/token.json"
                        os.makedirs(os.path.dirname(token_file), exist_ok=True)
                        
                        with open(token_file, 'w') as f:
                            json.dump(token_data, f, indent=2)
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        
                        html = """
                        <html><head><title>Sucesso</title></head>
                        <body style="font-family: Arial; margin: 50px;">
                            <h1>✅ Token Salvo!</h1>
                            <p>Sistema funcionará automaticamente</p>
                            <p><a href="/">← Voltar</a></p>
                        </body></html>
                        """
                        self.wfile.write(html.encode('utf-8'))
                        print("✅ Token salvo via web!")
                        
                    else:
                        raise ValueError("Token inválido")
                else:
                    raise ValueError("Conteúdo vazio")
                    
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html = f"<html><body><h1>❌ Erro: {str(e)}</h1><a href='/upload-token'>← Tentar novamente</a></body></html>"
                self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

class BRKProcessadorBasico:
    """Processador principal"""
    
    def __init__(self):
        self.email_monitor = EmailMonitor()
        self.database = DatabaseBRKBasico()
        self.onedrive = OneDriveBasico()
        print("✅ BRK Processador inicializado")
    
    def extrair_info_pdf(self, pdf_content: bytes, filename: str) -> Dict:
        """Extrair informações básicas do PDF"""
        return {
            'Data_Emissao': 'A extrair', 'Nota_Fiscal': 'A extrair', 'Valor': 'A extrair',
            'Codigo_Cliente': 'A extrair', 'Vencimento': 'A extrair', 'Competencia': 'A extrair',
            'nome_arquivo': filename, 'tamanho_bytes': len(pdf_content),
            'hash_arquivo': hashlib.sha256(pdf_content).hexdigest()
        }
    
    def processar_email(self, email: Dict) -> int:
        """Processar um email"""
        email_id = email.get('id', 'unknown')
        pdfs_processados = 0
        
        try:
            pdfs = self.email_monitor.extrair_pdfs_do_email(email)
            if not pdfs:
                return 0
            
            print(f"📎 Processando {len(pdfs)} PDFs...")
            
            for pdf_info in pdfs:
                try:
                    pdf_content = base64.b64decode(pdf_info['content_bytes'])
                    dados = self.extrair_info_pdf(pdf_content, pdf_info['filename'])
                    dados['email_id'] = email_id
                    
                    caminho = self.onedrive.upload_pdf(pdf_content, pdf_info['filename'])
                    if caminho:
                        dados['caminho_onedrive'] = caminho
                    
                    if self.database.salvar_fatura(dados):
                        pdfs_processados += 1
                        print(f"✅ {pdf_info['filename']}")
                except Exception as e:
                    print(f"❌ Erro PDF {pdf_info['filename']}: {e}")
            
            return pdfs_processados
        except Exception as e:
            print(f"❌ Erro email {email_id}: {e}")
            return 0
    
    def executar_ciclo(self):
        """Executar ciclo completo com diagnóstico"""
        print("🚀 INICIANDO PROCESSAMENTO BRK")
        print("=" * 40)
        
        inicio = datetime.now()
        
        try:
            # Diagnóstico
            print("📊 DIAGNÓSTICO PASTA BRK:")
            diagnostico = self.email_monitor.diagnosticar_pasta_brk()
            
            if diagnostico['status'] == 'sucesso':
                print(f"   📧 Total: {diagnostico['total_geral']:,}")
                print(f"   📅 24h: {diagnostico['ultimas_24h']}")
                print(f"   📆 Mês: {diagnostico['mes_atual']}")
                print()
            else:
                print("   ❌ Falha no diagnóstico")
                print()
            
            # Buscar emails novos
            emails = self.email_monitor.buscar_emails_novos(dias_atras=1)
            
            if not emails:
                print("📧 Nenhum email novo")
                return
            
            # Processar
            total_pdfs = 0
            emails_processados = 0
            
            for email in emails:
                email_id = email.get('id', '')
                
                if self.database.email_ja_processado(email_id):
                    print("⏭️ Email já processado")
                    continue
                
                pdfs_count = self.processar_email(email)
                self.database.marcar_email_processado(email_id, pdfs_count)
                
                emails_processados += 1
                total_pdfs += pdfs_count
            
            # Resultado
            duracao = (datetime.now() - inicio).total_seconds()
            
            print(f"\n📊 RESULTADO:")
            print(f"   Emails: {emails_processados}")
            print(f"   PDFs: {total_pdfs}")
            print(f"   Tempo: {duracao:.1f}s")
            
            stats = self.database.obter_estatisticas()
            print(f"   Total DB: {stats.get('total_faturas', 0)}")
            
        except Exception as e:
            print(f"❌ Erro no ciclo: {e}")
        finally:
            print("✅ EXECUÇÃO CONCLUÍDA")
            print("=" * 40)

def executar_processamento_background():
    """Background processing"""
    processador = BRKProcessadorBasico()
    
    while True:
        try:
            processador.executar_ciclo()
            time.sleep(600)  # 10 minutos
        except Exception as e:
            print(f"❌ Erro background: {e}")
            time.sleep(60)

def main():
    """Função principal SEGURA"""
    print("🚀 BRK MONITOR SEGURO - INICIANDO")
    print("=" * 50)
    
    # Validação rigorosa
    required_vars = {
        "MICROSOFT_CLIENT_ID": "Client ID Microsoft",
        "PASTA_BRK_ID": "ID da pasta BRK"
    }
    
    missing = []
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"{var} ({desc})")
        else:
            print(f"✅ {var}: {value[:8]}****** (ok)")
    
    if missing:
        print(f"\n❌ VARIÁVEIS FALTANDO: {missing}")
        print("Configure no Render → Environment → Add Variable")
        print("⚠️ SISTEMA PARADO POR SEGURANÇA")
        return
    
    print("🔒 Configurações validadas!")
    
    # Iniciar background
    bg_thread = threading.Thread(target=executar_processamento_background, daemon=True)
    bg_thread.start()
    print("🔄 Background iniciado")
    
    # Servidor web
    porta = int(os.getenv('PORT', 8080))
    server = HTTPServer(('0.0.0.0', porta), StatusHandler)
    
    print(f"🌐 Servidor na porta {porta}")
    print("=" * 50)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Parado")

if __name__ == "__main__":
    main()
