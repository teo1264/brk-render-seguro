#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 BRK RENDER MONITOR - Sistema Seguro (REFATORADO)

DEPLOY: Render.com com PERSISTENT DISK
FUNÇÃO: Monitor email BRK + SQLite + OneDrive básico
SEGURANÇA: Todas as credenciais via variáveis de ambiente
ESTRUTURA: Autenticação e processamento modularizados
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

# IMPORTS DOS MÓDULOS REFATORADOS
from auth import MicrosoftAuth
from processor import EmailProcessor


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


class StatusHandler(BaseHTTPRequestHandler):
    """Servidor web com interface segura + TESTES ONEDRIVE (REFATORADO)"""
    
    def test_onedrive_access(self):
        """Teste básico de acesso OneDrive usando classes refatoradas"""
        print("🧪 TESTE ONEDRIVE - INICIANDO (REFATORADO)")
        
        try:
            # 1. USAR AUTENTICAÇÃO REFATORADA
            auth = MicrosoftAuth()
            
            if not auth.access_token or not auth.refresh_token:
                return {
                    "status": "error",
                    "onedrive_access": False,
                    "message": "Token não encontrado",
                    "details": "Execute upload de token.json primeiro"
                }
            
            print("✅ Autenticação carregada")
            
            # 2. TESTAR DIFERENTES SCOPES ONEDRIVE
            print("🔄 Testando diferentes scopes OneDrive...")
            
            scopes_para_testar = [
                "Files.ReadWrite offline_access",
                "Files.ReadWrite.All offline_access", 
                "https://graph.microsoft.com/Files.ReadWrite offline_access",
                "https://graph.microsoft.com/Files.ReadWrite.All offline_access"
            ]
            
            token_url = f"https://login.microsoftonline.com/{auth.tenant_id}/oauth2/v2.0/token"
            access_token = None
            scope_funcionou = None
            
            for scope_teste in scopes_para_testar:
                print(f"🧪 Testando scope: {scope_teste}")
                
                token_data_request = {
                    'client_id': auth.client_id,
                    'grant_type': 'refresh_token', 
                    'refresh_token': auth.refresh_token,
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
                
                if auth.atualizar_token():
                    access_token = auth.access_token
                    scope_funcionou = "scope atual (sem OneDrive)"
                    print("✅ Token renovado com scope atual")
                else:
                    return {
                        "status": "error",
                        "onedrive_access": False,
                        "message": "Nenhum scope funcionou",
                        "details": "Não foi possível renovar token"
                    }
            
            # 3. TESTAR ACESSO ONEDRIVE
            print("🔍 Testando acesso OneDrive...")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
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
    
    def test_create_brk_folder(self):
        """Teste criar pasta /BRK no OneDrive (REFATORADO)"""
        print("📁 TESTE CRIAÇÃO PASTA /BRK - INICIANDO (REFATORADO)")
        
        try:
            # 1. USAR AUTENTICAÇÃO REFATORADA
            auth = MicrosoftAuth()
            
            if not auth.access_token or not auth.refresh_token:
                return {
                    "status": "error",
                    "message": "Configurações básicas não encontradas",
                    "details": "Execute upload de token.json primeiro"
                }
            
            # USAR SCOPE QUE FUNCIONOU
            scope_funcional = "Files.ReadWrite offline_access"
            
            token_url = f"https://login.microsoftonline.com/{auth.tenant_id}/oauth2/v2.0/token"
            token_request = {
                'client_id': auth.client_id,
                'grant_type': 'refresh_token',
                'refresh_token': auth.refresh_token,
                'scope': scope_funcional
            }
            
            response = requests.post(token_url, data=token_request)
            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": "Erro renovando token",
                    "details": f"HTTP {response.status_code}"
                }
            
            access_token = response.json().get('access_token')
            print("✅ Token renovado")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # 2. VERIFICAR SE PASTA /BRK JÁ EXISTE
            print("🔍 Verificando se pasta /BRK já existe...")
            
            list_url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
            list_response = requests.get(list_url, headers=headers)
            
            pasta_brk_existe = False
            pasta_brk_id = None
            
            if list_response.status_code == 200:
                items = list_response.json().get('value', [])
                for item in items:
                    if item.get('name') == 'BRK' and 'folder' in item:
                        pasta_brk_existe = True
                        pasta_brk_id = item.get('id')
                        print("✅ Pasta /BRK já existe")
                        break
            
            # 3. CRIAR PASTA /BRK SE NÃO EXISTIR
            if not pasta_brk_existe:
                print("📁 Criando pasta /BRK...")
                
                create_url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
                create_data = {
                    "name": "BRK",
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "fail"
                }
                
                create_response = requests.post(create_url, headers=headers, json=create_data)
                
                if create_response.status_code == 201:
                    pasta_criada = create_response.json()
                    pasta_brk_id = pasta_criada.get('id')
                    print("✅ Pasta /BRK criada com sucesso!")
                elif create_response.status_code == 409:
                    print("⚠️ Pasta /BRK já existia (conflito)")
                    pasta_brk_existe = True
                else:
                    return {
                        "status": "error",
                        "message": f"Erro criando pasta /BRK: {create_response.status_code}",
                        "details": create_response.text[:300]
                    }
            
            # 4. LISTAR CONTEÚDO DA PASTA /BRK
            print("📂 Listando conteúdo da pasta /BRK...")
            
            if pasta_brk_id:
                conteudo_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_brk_id}/children"
            else:
                conteudo_url = "https://graph.microsoft.com/v1.0/me/drive/root:/BRK:/children"
            
            conteudo_response = requests.get(conteudo_url, headers=headers)
            
            conteudo_pasta = []
            if conteudo_response.status_code == 200:
                items = conteudo_response.json().get('value', [])
                for item in items:
                    conteudo_pasta.append({
                        "nome": item.get('name'),
                        "tipo": "pasta" if 'folder' in item else "arquivo",
                        "tamanho": item.get('size', 0),
                        "modificado": item.get('lastModifiedDateTime', 'N/A')[:10]
                    })
                print(f"✅ Conteúdo listado: {len(conteudo_pasta)} items")
            
            # 5. RETORNAR RESULTADO COMPLETO
            return {
                "status": "success",
                "brk_folder_access": True,
                "message": "Pasta /BRK criada e acessível!",
                "details": {
                    "pasta_existia": pasta_brk_existe,
                    "pasta_criada": not pasta_brk_existe,
                    "pasta_id": pasta_brk_id[:20] + "..." if pasta_brk_id else "N/A",
                    "conteudo_atual": conteudo_pasta,
                    "total_items": len(conteudo_pasta),
                    "permissoes": "Leitura + Escrita confirmadas",
                    "teste_timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }
            }
            
        except Exception as e:
            print(f"❌ ERRO: {str(e)}")
            return {
                "status": "error",
                "brk_folder_access": False,
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
                <h1>🚀 BRK MONITOR SEGURO (REFATORADO)</h1>
                <p><strong>Status:</strong> ✅ Ativo</p>
                <p><strong>Estrutura:</strong> ✅ Modularizada (auth + processor)</p>
                <p><strong>Última exec:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                <hr>
                <h3>🔒 Config Segura</h3>
                <p><strong>Client ID:</strong> {client_safe}</p>
                <p><strong>Pasta BRK:</strong> {pasta_safe}</p>
                <hr>
                <p><a href="/upload-token">📁 Upload Token</a> | <a href="/health">🔍 Health</a> | <a href="/test-onedrive">🧪 Teste OneDrive</a> | <a href="/create-brk-folder">📂 Criar /BRK</a></p>
                <small>🔒 Dados protegidos - Versão refatorada</small>
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
        
        elif self.path == '/create-brk-folder':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            try:
                resultado = self.test_create_brk_folder()
                self.wfile.write(json.dumps(resultado, indent=2, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                erro_response = {
                    "status": "error",
                    "brk_folder_access": False,
                    "message": "Erro executando teste criação pasta",
                    "details": str(e)
                }
                self.wfile.write(json.dumps(erro_response, indent=2).encode('utf-8'))
        
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health = {
                "status": "healthy",
                "service": "brk-monitor-seguro-refatorado",
                "timestamp": datetime.now().isoformat(),
                "estrutura": "modularizada",
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
    """Processador principal (REFATORADO)"""
    
    def __init__(self):
        """Inicializar com classes refatoradas"""
        print("🔧 Inicializando BRK Processador (REFATORADO)...")
        
        # AUTENTICAÇÃO MICROSOFT
        self.microsoft_auth = MicrosoftAuth()
        
        # PROCESSAMENTO DE EMAILS  
        self.email_processor = EmailProcessor(self.microsoft_auth)
        
        # COMPONENTES EXISTENTES
        self.database = DatabaseBRKBasico()
        self.onedrive = OneDriveBasico()
        
        print("✅ BRK Processador refatorado inicializado")
        print("   📊 Estrutura: auth + processor + database + onedrive")
    
    def extrair_info_pdf(self, pdf_content: bytes, filename: str) -> Dict:
        """Extrair informações básicas do PDF (mantido)"""
        return {
            'Data_Emissao': 'A extrair', 'Nota_Fiscal': 'A extrair', 'Valor': 'A extrair',
            'Codigo_Cliente': 'A extrair', 'Vencimento': 'A extrair', 'Competencia': 'A extrair',
            'nome_arquivo': filename, 'tamanho_bytes': len(pdf_content),
            'hash_arquivo': hashlib.sha256(pdf_content).hexdigest()
        }
    
    def processar_email(self, email: Dict) -> int:
        """Processar um email (ATUALIZADO)"""
        email_id = email.get('id', 'unknown')
        pdfs_processados = 0
        
        try:
            # USAR EMAIL_PROCESSOR REFATORADO
            pdfs = self.email_processor.extrair_pdfs_do_email(email)
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
        """Executar ciclo completo com diagnóstico (ATUALIZADO)"""
        print("🚀 INICIANDO PROCESSAMENTO BRK (REFATORADO)")
        print("=" * 40)
        
        inicio = datetime.now()
        
        try:
            # DIAGNÓSTICO COM EMAIL_PROCESSOR
            print("📊 DIAGNÓSTICO PASTA BRK:")
            diagnostico = self.email_processor.diagnosticar_pasta_brk()
            
            if diagnostico['status'] == 'sucesso':
                print(f"   📧 Total: {diagnostico['total_geral']:,}")
                print(f"   📅 24h: {diagnostico['ultimas_24h']}")
                print(f"   📆 Mês: {diagnostico['mes_atual']}")
                print()
            else:
                print("   ❌ Falha no diagnóstico")
                print()
            
            # BUSCAR EMAILS COM EMAIL_PROCESSOR
            emails = self.email_processor.buscar_emails_novos(dias_atras=1)
            
            if not emails:
                print("📧 Nenhum email novo")
                return
            
            # PROCESSAR
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
            
            # RESULTADO
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
            print("✅ EXECUÇÃO CONCLUÍDA (REFATORADO)")
            print("=" * 40)


def executar_processamento_background():
    """Background processing (ATUALIZADO)"""
    try:
        processador = BRKProcessadorBasico()
        
        while True:
            try:
                processador.executar_ciclo()
                time.sleep(600)  # 10 minutos
            except Exception as e:
                print(f"❌ Erro background: {e}")
                time.sleep(60)
                
    except Exception as e:
        print(f"❌ Erro fatal inicializando processador: {e}")
        print("⚠️ Background processamento interrompido")


def main():
    """Função principal SEGURA (REFATORADO)"""
    print("🚀 BRK MONITOR SEGURO - INICIANDO (REFATORADO)")
    print("=" * 50)
    print("📊 ESTRUTURA: auth/ + processor/ + app.py")
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
    
    # Testar imports dos módulos refatorados
    try:
        from auth import MicrosoftAuth
        from processor import EmailProcessor
        print("✅ Imports refatorados OK")
        
        # Teste básico de inicialização
        test_auth = MicrosoftAuth()
        print("✅ MicrosoftAuth inicializado")
        
        test_processor = EmailProcessor(test_auth)
        print("✅ EmailProcessor inicializado")
        
    except Exception as e:
        print(f"❌ Erro nos imports refatorados: {e}")
        print("⚠️ Verifique estrutura de pastas auth/ e processor/")
        return
    
    # Iniciar background
    bg_thread = threading.Thread(target=executar_processamento_background, daemon=True)
    bg_thread.start()
    print("🔄 Background iniciado (refatorado)")
    
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
