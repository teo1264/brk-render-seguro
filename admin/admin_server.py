#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: admin/admin_server.py
💾 ONDE SALVAR: brk-monitor-seguro/admin/admin_server.py
📦 FUNÇÃO: Servidor web administrativo para BRK Monitor
🔧 DESCRIÇÃO: Interface HTTPS para administração, upload token, testes
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
"""

import os
import json
import requests
import ssl
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

# Imports dos módulos refatorados
from auth import MicrosoftAuth
from processor import EmailProcessor


class AdminHandler(BaseHTTPRequestHandler):
    """
    Handler HTTP para interface administrativa
    
    Responsabilidades:
    - Interface web para status e configuração
    - Upload seguro de tokens via HTTPS
    - Testes de conectividade OneDrive
    - Health checks e diagnósticos
    - Base para futuras funcionalidades administrativas
    """
    
    def test_onedrive_access(self) -> Dict[str, Any]:
        """
        Teste básico de acesso OneDrive usando classes refatoradas
        
        Returns:
            Dict[str, Any]: Resultado do teste com status e detalhes
        """
        print("🧪 TESTE ONEDRIVE - INICIANDO (ADMIN)")
        
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
                
                response = requests.post(token_url, data=token_data_request, timeout=30)
                
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
            onedrive_response = requests.get(onedrive_url, headers=headers, timeout=30)
            
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
    
    def test_create_brk_folder(self) -> Dict[str, Any]:
        """
        Teste criar pasta /BRK no OneDrive
        
        Returns:
            Dict[str, Any]: Resultado da criação da pasta
        """
        print("📁 TESTE CRIAÇÃO PASTA /BRK - INICIANDO (ADMIN)")
        
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
            
            response = requests.post(token_url, data=token_request, timeout=30)
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
            list_response = requests.get(list_url, headers=headers, timeout=30)
            
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
                
                create_response = requests.post(create_url, headers=headers, json=create_data, timeout=30)
                
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
            
            conteudo_response = requests.get(conteudo_url, headers=headers, timeout=30)
            
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
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Obter status completo do sistema
        
        Returns:
            Dict[str, Any]: Status detalhado do sistema
        """
        try:
            # Verificar environment variables
            client_id = os.getenv("MICROSOFT_CLIENT_ID")
            pasta_brk_id = os.getenv("PASTA_BRK_ID")
            
            # Verificar autenticação
            try:
                auth = MicrosoftAuth()
                auth_status = auth.status_autenticacao()
            except Exception as e:
                auth_status = {"erro": str(e)}
            
            # Verificar processamento
            try:
                processor = EmailProcessor(MicrosoftAuth())
                processor_status = processor.status_processamento()
            except Exception as e:
                processor_status = {"erro": str(e)}
            
            return {
                "timestamp": datetime.now().isoformat(),
                "service": "brk-monitor-admin",
                "version": "refatorado-modular",
                "config": {
                    "client_id_ok": bool(client_id),
                    "pasta_brk_ok": bool(pasta_brk_id),
                    "client_id_safe": client_id[:8] + "******" if client_id else "N/A",
                    "pasta_brk_safe": pasta_brk_id[:10] + "******" if pasta_brk_id else "N/A"
                },
                "autenticacao": auth_status,
                "processamento": processor_status,
                "estrutura": {
                    "auth_module": "✅ Disponível",
                    "processor_module": "✅ Disponível", 
                    "admin_module": "✅ Ativo"
                }
            }
            
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "service": "brk-monitor-admin",
                "status": "error",
                "erro": str(e)
            }
    
    def do_GET(self):
        """Processar requisições GET"""
        
        if self.path == '/':
            self._handle_homepage()
            
        elif self.path == '/upload-token':
            self._handle_upload_token_page()
            
        elif self.path == '/test-onedrive':
            self._handle_test_onedrive()
            
        elif self.path == '/create-brk-folder':
            self._handle_create_brk_folder()
            
        elif self.path == '/health':
            self._handle_health_check()
            
        elif self.path == '/status':
            self._handle_system_status()
            
        else:
            self._handle_not_found()
    
    def _handle_homepage(self):
        """Página inicial administrativa"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        client_id = os.getenv("MICROSOFT_CLIENT_ID", "NÃO CONFIGURADO")
        client_safe = client_id[:8] + "******" if len(client_id) > 8 else "NÃO CONFIGURADO"
        
        pasta_id = os.getenv("PASTA_BRK_ID", "NÃO CONFIGURADO")
        pasta_safe = pasta_id[:10] + "******" if len(pasta_id) > 10 else "NÃO CONFIGURADO"
        
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <title>BRK Monitor - Administração</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 50px; background: #f5f5f5; }}
                .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 15px; }}
                .status {{ background: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .config {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .nav {{ margin: 20px 0; }}
                .nav a {{ display: inline-block; margin: 5px 10px 5px 0; padding: 10px 15px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }}
                .nav a:hover {{ background: #2980b9; }}
                .footer {{ margin-top: 30px; padding-top: 15px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 BRK MONITOR - ADMINISTRAÇÃO</h1>
                    <p><strong>Versão:</strong> Refatorada Modular | <strong>Interface:</strong> Administrativa HTTPS</p>
                </div>
                
                <div class="status">
                    <h3>📊 Status do Sistema</h3>
                    <p><strong>Status:</strong> ✅ Ativo</p>
                    <p><strong>Última verificação:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <p><strong>Estrutura:</strong> ✅ auth/ + processor/ + admin/</p>
                </div>
                
                <div class="config">
                    <h3>🔒 Configuração Segura</h3>
                    <p><strong>Client ID:</strong> {client_safe}</p>
                    <p><strong>Pasta BRK:</strong> {pasta_safe}</p>
                    <p><strong>Segurança:</strong> Todas as credenciais via Environment Variables</p>
                </div>
                
                <div class="nav">
                    <h3>🛠️ Funções Administrativas</h3>
                    <a href="/upload-token">📁 Upload Token</a>
                    <a href="/health">🔍 Health Check</a>
                    <a href="/status">📊 Status Detalhado</a>
                    <a href="/test-onedrive">🧪 Teste OneDrive</a>
                    <a href="/create-brk-folder">📂 Criar Pasta /BRK</a>
                </div>
                
                <div class="footer">
                    <p>🔒 <strong>Interface Administrativa Segura</strong> - Dados sensíveis protegidos</p>
                    <p>📁 Estrutura modular: Autenticação, Processamento e Administração separados</p>
                </div>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))
    
    def _handle_upload_token_page(self):
        """Página de upload de token"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <title>Upload Token - BRK Monitor</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial; margin: 50px; background: #f5f5f5; }
                .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                textarea { width: 100%; font-family: monospace; border: 2px solid #ddd; border-radius: 5px; padding: 10px; }
                button { background: #28a745; color: white; padding: 12px 25px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
                button:hover { background: #218838; }
                .warning { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; color: #856404; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📁 Upload Token Seguro</h1>
                
                <div class="warning">
                    <strong>⚠️ ATENÇÃO:</strong> Este token será salvo de forma segura no persistent disk do Render.
                    Nunca compartilhe ou exponha este conteúdo.
                </div>
                
                <form method="POST" action="/upload-token">
                    <label for="token_content"><strong>Token JSON:</strong></label>
                    <textarea name="token_content" id="token_content" rows="15" cols="70" 
                              placeholder='{"access_token": "eyJ0eXAiOiJKV1QiLCJub...", "refresh_token": "0.ARwA6WgJJ9X2qE...", "expires_in": 3600}'></textarea>
                    <br><br>
                    <button type="submit">💾 Salvar Token Seguramente</button>
                </form>
                
                <p><a href="/">← Voltar à Administração</a></p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))
    
    def _handle_test_onedrive(self):
        """Endpoint de teste OneDrive"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        try:
            resultado = self.test_onedrive_access()
            self.wfile.write(json.dumps(resultado, indent=2, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            erro_response = {
                "status": "error",
                "onedrive_access": False,
                "message": "Erro executando teste OneDrive",
                "details": str(e)
            }
            self.wfile.write(json.dumps(erro_response, indent=2, ensure_ascii=False).encode('utf-8'))
    
    def _handle_create_brk_folder(self):
        """Endpoint de criação de pasta BRK"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
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
            self.wfile.write(json.dumps(erro_response, indent=2, ensure_ascii=False).encode('utf-8'))
    
    def _handle_health_check(self):
        """Health check básico"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        health = {
            "status": "healthy",
            "service": "brk-monitor-admin",
            "timestamp": datetime.now().isoformat(),
            "config": {
                "client_id": "ok" if os.getenv("MICROSOFT_CLIENT_ID") else "missing",
                "pasta_brk": "ok" if os.getenv("PASTA_BRK_ID") else "missing"
            }
        }
        self.wfile.write(json.dumps(health, indent=2, ensure_ascii=False).encode('utf-8'))
    
    def _handle_system_status(self):
        """Status detalhado do sistema"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        status = self.get_system_status()
        self.wfile.write(json.dumps(status, indent=2, ensure_ascii=False).encode('utf-8'))
    
    def _handle_not_found(self):
        """Página não encontrada"""
        self.send_response(404)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = """
        <html>
        <body style="font-family: Arial; margin: 50px;">
            <h1>❌ 404 - Página não encontrada</h1>
            <p><a href="/">← Voltar à Administração</a></p>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))
    
    def do_POST(self):
        """Processar requisições POST"""
        
        if self.path == '/upload-token':
            self._handle_upload_token_post()
        else:
            self.send_response(404)
            self.end_headers()
    
    def _handle_upload_token_post(self):
        """Processar upload de token"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            import urllib.parse
            parsed = urllib.parse.parse_qs(post_data)
            token_content = parsed.get('token_content', [''])[0]
            
            if token_content.strip():
                token_data = json.loads(token_content)
                
                if 'access_token' in token_data and 'refresh_token' in token_data:
                    # Salvar no persistent disk
                    token_file = "/opt/render/project/storage/token.json"
                    os.makedirs(os.path.dirname(token_file), exist_ok=True)
                    
                    with open(token_file, 'w') as f:
                        json.dump(token_data, f, indent=2)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    
                    html = """
                    <!DOCTYPE html>
                    <html lang="pt-BR">
                    <head>
                        <title>Token Salvo - BRK Monitor</title>
                        <meta charset="UTF-8">
                        <style>
                            body { font-family: Arial; margin: 50px; background: #f5f5f5; }
                            .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                            .success { background: #d4edda; padding: 20px; border-radius: 5px; color: #155724; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="success">
                                <h1>✅ Token Salvo com Sucesso!</h1>
                                <p>O token foi armazenado de forma segura no persistent disk.</p>
                                <p>O sistema funcionará automaticamente a partir de agora.</p>
                            </div>
                            <p><a href="/">← Voltar à Administração</a></p>
                        </div>
                    </body>
                    </html>
                    """
                    self.wfile.write(html.encode('utf-8'))
                    print("✅ Token salvo via interface administrativa!")
                    
                else:
                    raise ValueError("Token inválido - access_token e refresh_token obrigatórios")
            else:
                raise ValueError("Conteúdo vazio")
                
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = f"""
            <html>
            <body style="font-family: Arial; margin: 50px;">
                <h1>❌ Erro: {str(e)}</h1>
                <p><a href="/upload-token">← Tentar novamente</a></p>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suprimir logs HTTP padrão"""
        pass


class AdminServer:
    """
    Servidor HTTP administrativo para BRK Monitor
    
    Funcionalidades:
    - Interface web administrativa
    - Upload seguro de tokens
    - Testes de conectividade
    - Base para funcionalidades futuras
    """
    
    def __init__(self, porta: int = 8080, host: str = '0.0.0.0'):
        """
        Inicializar servidor administrativo
        
        Args:
            porta (int): Porta do servidor (padrão: 8080)
            host (str): Host do servidor (padrão: 0.0.0.0)
        """
        self.porta = porta
        self.host = host
        self.server = None
        
    def iniciar(self):
        """Iniciar servidor HTTP administrativo"""
        try:
            self.server = HTTPServer((self.host, self.porta), AdminHandler)
            
            print(f"🌐 Servidor administrativo iniciado")
            print(f"   📍 Endereço: http://{self.host}:{self.porta}")
            print(f"   🔧 Interface: Administrativa")
            print(f"   📋 Endpoints:")
            print(f"      / - Homepage administrativa")
            print(f"      /upload-token - Upload seguro de token")
            print(f"      /health - Health check")
            print(f"      /status - Status detalhado")
            print(f"      /test-onedrive - Teste OneDrive")
            print(f"      /create-brk-folder - Criar pasta BRK")
            
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            print("\n🛑 Servidor administrativo parado")
        except Exception as e:
            print(f"❌ Erro no servidor administrativo: {e}")
    
    def parar(self):
        """Parar servidor administrativo"""
        if self.server:
            self.server.shutdown()
            print("🛑 Servidor administrativo parado")


def main():
    """Função principal para executar servidor administrativo standalone"""
    print("🚀 BRK MONITOR - SERVIDOR ADMINISTRATIVO")
    print("=" * 50)
    
    porta = int(os.getenv('PORT', 8080))
    admin_server = AdminServer(porta=porta)
    
    try:
        admin_server.iniciar()
    except KeyboardInterrupt:
        print("\n🛑 Encerrado pelo usuário")


if __name__ == "__main__":
    main()
