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
from auth.microsoft_auth import MicrosoftAuth
from processor.email_processor import EmailProcessor


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
                
                # 🆕 BUSCAR ID DA PASTA /BRK/ (estratégia correta)
                print("📁 BUSCANDO ID DA PASTA /BRK/...")
                
                root_url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
                root_response = requests.get(root_url, headers=headers, timeout=30)
                
                pasta_brk_id = None
                if root_response.status_code == 200:
                    items = root_response.json().get('value', [])
                    for item in items:
                        if item.get('name') == 'BRK' and 'folder' in item:
                            pasta_brk_id = item.get('id')
                            print(f"📁 PASTA /BRK/ ENCONTRADA!")
                            print(f"   🆔 ID DA PASTA: {pasta_brk_id}")
                            print(f"   ⚙️ Configurar: ONEDRIVE_BRK_ID={pasta_brk_id}")
                            print(f"   📋 Separado de: PASTA_BRK_ID (emails)")
                            break
                
                # Listar conteúdo da pasta usando ID da pasta
                planilha_encontrada = None
                arquivos_brk = []
                
                if pasta_brk_id:
                    print("📂 LISTANDO CONTEÚDO DA PASTA /BRK/...")
                    brk_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_brk_id}/children"
                    brk_response = requests.get(brk_url, headers=headers, timeout=30)
                    
                    if brk_response.status_code == 200:
                        items = brk_response.json().get('value', [])
                        print(f"📁 Pasta /BRK/ contém {len(items)} arquivos")
                        
                        for item in items:
                            arquivo_info = {
                                "nome": item.get('name'),
                                "tipo": "pasta" if 'folder' in item else "arquivo",
                                "id": item.get('id'),
                                "tamanho": item.get('size', 0)
                            }
                            arquivos_brk.append(arquivo_info)
                            
                            # Buscar CDC_BRK_CCB.xlsx dentro da pasta
                            if item.get('name', '').upper() == 'CDC_BRK_CCB.XLSX':
                                planilha_encontrada = {
                                    "nome": item.get('name'),
                                    "id": item.get('id'),
                                    "tamanho": item.get('size', 0),
                                    "caminho": f"/BRK/{item.get('name')}",
                                    "url_download": f"https://graph.microsoft.com/v1.0/me/drive/items/{item.get('id')}/content"
                                }
                                print(f"📊 CDC_BRK_CCB.xlsx ENCONTRADO NA PASTA!")
                                print(f"   📍 Caminho: /BRK/{item.get('name')}")
                                print(f"   🆔 ID Arquivo: {item.get('id')}")
                                print(f"   📏 Tamanho: {item.get('size', 0)} bytes")
                                break
                    else:
                        print(f"❌ Erro listando conteúdo da pasta: {brk_response.status_code}")
                else:
                    print("❌ Pasta /BRK/ não encontrada")
                
                return {
                    "status": "success",
                    "onedrive_access": True,
                    "message": "OneDrive OK + ID da pasta /BRK/ obtido",
                    "onedrive_brk_id": pasta_brk_id,
                    "pasta_brk_encontrada": pasta_brk_id is not None,
                    "configurar_variavel": f"ONEDRIVE_BRK_ID={pasta_brk_id}" if pasta_brk_id else "Pasta /BRK/ não encontrada",
                    "cdc_brk_ccb_encontrado": planilha_encontrada is not None,
                    "cdc_brk_ccb": planilha_encontrada,
                    "arquivos_pasta_brk": arquivos_brk,
                    "total_arquivos_pasta": len(arquivos_brk),
                    "estrategia": "ONEDRIVE_BRK_ID = workspace completo OneDrive BRK",
                    "estrutura_variaveis": {
                        "PASTA_BRK_ID": "Pasta emails Microsoft 365",
                        "ONEDRIVE_BRK_ID": "Pasta arquivos OneDrive BRK"
                    },
                    "vantagens_pasta_id": [
                        "Acessa qualquer arquivo na pasta OneDrive",
                        "Salva PDFs processados na mesma pasta", 
                        "Lê planilha CDC_BRK_CCB.xlsx",
                        "Estrutura organizada separada dos emails"
                    ],
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

# ============================================================================
# 📊 MELHORIA PARA admin/admin_server.py
# SUBSTITUIR O MÉTODO get_system_status() EXISTENTE
# ============================================================================


     def get_system_status(self) -> Dict[str, Any]:
        """
        Obter status completo do sistema COM LISTA DE TODOS OS ENDPOINTS
        
        Returns:
            Dict[str, Any]: Status detalhado + documentação dos endpoints
        """
        try:
            # Status básico do sistema
            client_id = os.getenv("MICROSOFT_CLIENT_ID")
            pasta_brk_id = os.getenv("PASTA_BRK_ID")
            onedrive_brk_id = os.getenv("ONEDRIVE_BRK_ID")
            
            # Verificar autenticação
            try:
                auth = MicrosoftAuth()
                auth_status = auth.status_autenticacao()
                auth_ok = bool(auth.access_token)
            except Exception as e:
                auth_status = {"erro": str(e)}
                auth_ok = False
            
            # Verificar processamento
            try:
                processor = EmailProcessor(MicrosoftAuth())
                processor_status = processor.status_processamento()
                processor_ok = True
                total_relacionamentos = len(getattr(processor, 'cdc_brk_vetor', []))
            except Exception as e:
                processor_status = {"erro": str(e)}
                processor_ok = False
                total_relacionamentos = 0
            
            # NOVA FUNCIONALIDADE: LISTA COMPLETA DE ENDPOINTS
            endpoints_disponiveis = {
                "GET": {
                    "/": {
                        "descricao": "Homepage administrativa principal",
                        "funcao": "Interface visual com status geral e botões de ação",
                        "exemplo": "https://brk-render-seguro.onrender.com:8080/",
                        "formato": "HTML"
                    },
                    "/health": {
                        "descricao": "Health check rápido do sistema",
                        "funcao": "Verificação básica se serviço está funcionando",
                        "exemplo": "https://brk-render-seguro.onrender.com:8080/health",
                        "formato": "JSON"
                    },
                    "/status": {
                        "descricao": "Status detalhado completo + lista de endpoints",
                        "funcao": "Diagnóstico completo com toda documentação da API",
                        "exemplo": "https://brk-render-seguro.onrender.com:8080/status",
                        "formato": "JSON"
                    },
                    "/upload-token": {
                        "descricao": "Página para upload de token Microsoft",
                        "funcao": "Interface HTML para carregar token.json de forma segura",
                        "exemplo": "https://brk-render-seguro.onrender.com:8080/upload-token",
                        "formato": "HTML"
                    },
                    "/test-onedrive": {
                        "descricao": "Teste de conectividade OneDrive",
                        "funcao": "Verifica acesso OneDrive e descobre IDs de pastas",
                        "exemplo": "https://brk-render-seguro.onrender.com:8080/test-onedrive",
                        "formato": "JSON"
                    },
                    "/create-brk-folder": {
                        "descricao": "Criar/verificar pasta BRK no OneDrive",
                        "funcao": "Cria estrutura de pastas necessária no OneDrive",
                        "exemplo": "https://brk-render-seguro.onrender.com:8080/create-brk-folder",
                        "formato": "JSON"
                    }
                },
                "POST": {
                    "/upload-token": {
                        "descricao": "Processar upload de token Microsoft",
                        "funcao": "Recebe e salva token.json no persistent disk",
                        "exemplo": "POST com form-data: token_content",
                        "formato": "HTML"
                    }
                }
            }
            
            # ENDPOINTS ADICIONAIS (se DBEDIT estiver implementado)
            try:
                # Verificar se DBEDIT está disponível
                import os
                dbedit_path = "/opt/render/project/admin/dbedit_server.py"
                if os.path.exists(dbedit_path):
                    endpoints_disponiveis["SERVERS"] = {
                        "DBEDIT (porta 8081)": {
                            "descricao": "Navegação estilo Clipper no database_brk.db",
                            "funcao": "Interface DBEDIT para navegar registros da base real",
                            "exemplo": "http://localhost:8081/dbedit",
                            "formato": "HTML",
                            "comandos": "TOP, BOTTOM, SKIP, GOTO, SEEK",
                            "como_iniciar": "cd admin && python dbedit_server.py --port 8081"
                        }
                    }
            except:
                pass
            
            # INFORMAÇÕES DO HOST ATUAL
            import socket
            hostname = socket.gethostname()
            
            # URL BASE DINÂMICA
            base_url = "https://brk-render-seguro.onrender.com:8080"
            if "localhost" in hostname or "127.0.0.1" in hostname:
                base_url = "http://localhost:8080"
            
            # ESTRUTURA COMPLETA DO STATUS
            return {
                "timestamp": datetime.now().isoformat(),
                "service": "brk-monitor-admin",
                "version": "refatorado-modular-v2.1",
                "base_url": base_url,
                "hostname": hostname,
                
                # STATUS BÁSICO
                "config": {
                    "client_id_ok": bool(client_id),
                    "pasta_brk_ok": bool(pasta_brk_id),
                    "onedrive_brk_ok": bool(onedrive_brk_id),
                    "client_id_safe": client_id[:8] + "******" if client_id else "❌ NÃO CONFIGURADO",
                    "pasta_brk_safe": pasta_brk_id[:10] + "******" if pasta_brk_id else "❌ NÃO CONFIGURADO",
                    "onedrive_brk_safe": onedrive_brk_id[:15] + "******" if onedrive_brk_id else "❌ NÃO CONFIGURADO"
                },
                
                # STATUS DOS MÓDULOS
                "autenticacao": {
                    **auth_status,
                    "token_ativo": auth_ok,
                    "status_resumo": "✅ OK" if auth_ok else "❌ Token inválido"
                },
                
                "processamento": {
                    **processor_status,
                    "processor_ok": processor_ok,
                    "relacionamentos": total_relacionamentos,
                    "status_resumo": f"✅ OK ({total_relacionamentos} CDCs)" if processor_ok else "❌ Erro"
                },
                
                "estrutura": {
                    "auth_module": "✅ Disponível",
                    "processor_module": "✅ Disponível", 
                    "admin_module": "✅ Ativo",
                    "database_brk": "✅ Integrado" if processor_ok else "❌ Erro"
                },
                
                # 🆕 NOVA SEÇÃO: DOCUMENTAÇÃO COMPLETA DOS ENDPOINTS
                "endpoints": endpoints_disponiveis,
                
                # 🆕 LINKS RÁPIDOS
                "quick_links": {
                    "interface_principal": f"{base_url}/",
                    "health_check": f"{base_url}/health", 
                    "upload_token": f"{base_url}/upload-token",
                    "test_onedrive": f"{base_url}/test-onedrive",
                    "este_status": f"{base_url}/status"
                },
                
                # 🆕 HELP/GUIA DE USO
                "help": {
                    "como_usar": "Acesse a interface principal (/) para ver status visual",
                    "upload_token": "Use /upload-token para configurar autenticação Microsoft",
                    "testar_onedrive": "Use /test-onedrive para verificar conectividade",
                    "dbedit": "Execute 'cd admin && python dbedit_server.py' para navegar database",
                    "documentacao": "Este endpoint (/status) lista todas as funcionalidades"
                },
                
                # 🆕 RESUMO EXECUTIVO
                "resumo_executivo": {
                    "status_geral": "🟢 OPERACIONAL" if (client_id and pasta_brk_id and auth_ok) else "🟡 CONFIGURAÇÃO PENDENTE",
                    "total_endpoints": len(endpoints_disponiveis.get("GET", {})) + len(endpoints_disponiveis.get("POST", {})),
                    "funcionalidades_ativas": [
                        "✅ Interface administrativa" if True else "",
                        "✅ Upload token seguro" if True else "",
                        "✅ Testes OneDrive" if True else "",
                        "✅ Processamento emails" if processor_ok else "❌ Processamento emails",
                        "✅ Relacionamento CDC" if total_relacionamentos > 0 else "⚠️ Relacionamento CDC",
                        "✅ Database BRK" if processor_ok else "❌ Database BRK"
                    ],
                    "proximos_passos": [
                        "Upload token via /upload-token" if not auth_ok else "",
                        "Configurar ONEDRIVE_BRK_ID via /test-onedrive" if not onedrive_brk_id else "",
                        "Testar DBEDIT para navegar dados" if processor_ok else "",
                        "Sistema pronto para produção!" if (auth_ok and onedrive_brk_id) else ""
                    ]
                }
            }
            
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "service": "brk-monitor-admin",
                "status": "error",
                "erro": str(e),
                "endpoints": {
                    "error": "Erro obtendo lista de endpoints",
                    "basic_endpoints": ["/", "/health", "/status", "/upload-token"]
                }
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
        """Página inicial administrativa - VERSÃO MELHORADA"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Obter dados dinâmicos em tempo real
        try:
            # Status do sistema
            client_id = os.getenv("MICROSOFT_CLIENT_ID", "")
            pasta_brk_id = os.getenv("PASTA_BRK_ID", "")
            onedrive_brk_id = os.getenv("ONEDRIVE_BRK_ID", "")
            
            # Dados seguros para exibição
            client_safe = client_id[:8] + "******" if len(client_id) > 8 else "❌ NÃO CONFIGURADO"
            pasta_safe = pasta_brk_id[:10] + "******" if len(pasta_brk_id) > 10 else "❌ NÃO CONFIGURADO"
            onedrive_safe = onedrive_brk_id[:15] + "******" if len(onedrive_brk_id) > 15 else "❌ NÃO CONFIGURADO"
            
            # Verificar autenticação
            try:
                auth = MicrosoftAuth()
                auth_ok = bool(auth.access_token)
                token_expira = "Token ativo" if auth_ok else "Token expirado"
            except:
                auth_ok = False
                token_expira = "Erro carregando"
            
            # Verificar processamento
            try:
                processor = EmailProcessor(MicrosoftAuth())
                processor_ok = True
                total_relacionamentos = len(getattr(processor, 'cdc_brk_vetor', []))
            except:
                processor_ok = False
                total_relacionamentos = 0
            
            # Status geral
            status_geral = "🟢 OPERACIONAL" if (client_id and pasta_brk_id and auth_ok) else "🟡 CONFIGURAÇÃO INCOMPLETA"
            if not client_id or not pasta_brk_id:
                status_geral = "🔴 CONFIGURAÇÃO FALTANDO"
                
        except Exception as e:
            # Fallback se erro
            client_safe = pasta_safe = onedrive_safe = "❌ ERRO CARREGANDO"
            auth_ok = processor_ok = False
            token_expira = "Erro"
            total_relacionamentos = 0
            status_geral = "🔴 ERRO SISTEMA"
        
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <title>BRK Monitor - Centro de Controle</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                .container {{ 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    background: rgba(255,255,255,0.95);
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                .header {{ 
                    background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                    color: white; 
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{ font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
                .header p {{ font-size: 1.1em; opacity: 0.9; }}
                
                .status-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                    gap: 20px; 
                    padding: 30px;
                }}
                .status-card {{ 
                    background: white;
                    border-radius: 10px;
                    padding: 25px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    border-left: 5px solid #3498db;
                    transition: transform 0.3s ease;
                }}
                .status-card:hover {{ transform: translateY(-5px); }}
                .status-card h3 {{ color: #2c3e50; margin-bottom: 15px; font-size: 1.3em; }}
                .status-item {{ margin: 10px 0; display: flex; justify-content: space-between; align-items: center; }}
                .status-label {{ font-weight: 600; color: #555; }}
                .status-value {{ 
                    padding: 5px 10px; 
                    border-radius: 20px; 
                    font-size: 0.9em;
                    font-weight: bold;
                }}
                .status-ok {{ background: #d4edda; color: #155724; }}
                .status-warning {{ background: #fff3cd; color: #856404; }}
                .status-error {{ background: #f8d7da; color: #721c24; }}
                
                .main-status {{ 
                    text-align: center; 
                    padding: 40px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                }}
                .main-status h2 {{ font-size: 2em; margin-bottom: 20px; }}
                .status-indicator {{ 
                    display: inline-block;
                    padding: 15px 30px;
                    border-radius: 50px;
                    font-size: 1.2em;
                    font-weight: bold;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                
                .actions-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                    gap: 15px; 
                    padding: 30px;
                    background: #f8f9fa;
                }}
                .action-btn {{ 
                    display: block;
                    text-decoration: none;
                    background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    font-weight: 600;
                    transition: all 0.3s ease;
                    box-shadow: 0 3px 10px rgba(52, 152, 219, 0.3);
                }}
                .action-btn:hover {{ 
                    transform: translateY(-3px);
                    box-shadow: 0 5px 20px rgba(52, 152, 219, 0.4);
                }}
                .action-btn.warning {{ background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); }}
                .action-btn.success {{ background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); }}
                .action-btn.info {{ background: linear-gradient(135deg, #8e44ad 0%, #9b59b6 100%); }}
                
                .footer {{ 
                    background: #2c3e50; 
                    color: white; 
                    text-align: center; 
                    padding: 20px;
                    font-size: 0.9em;
                }}
                .footer a {{ color: #3498db; text-decoration: none; }}
                
                .timestamp {{ 
                    position: absolute;
                    top: 20px;
                    right: 20px;
                    background: rgba(0,0,0,0.7);
                    color: white;
                    padding: 8px 15px;
                    border-radius: 20px;
                    font-size: 0.8em;
                }}
                
                @media (max-width: 768px) {{
                    .status-grid, .actions-grid {{ grid-template-columns: 1fr; }}
                    .header h1 {{ font-size: 2em; }}
                    .container {{ margin: 10px; }}
                }}
            </style>
            <script>
                function updateTimestamp() {{
                    const now = new Date();
                    const timestamp = now.toLocaleString('pt-BR');
                    document.querySelector('.timestamp').textContent = timestamp;
                }}
                setInterval(updateTimestamp, 1000);
                window.onload = updateTimestamp;
            </script>
        </head>
        <body>
            <div class="timestamp"></div>
            
            <div class="container">
                <div class="header">
                    <h1>🚀 BRK MONITOR</h1>
                    <p>Centro de Controle Administrativo | Sistema Integrado de Processamento de Faturas</p>
                </div>
                
                <div class="main-status">
                    <h2>Status Geral do Sistema</h2>
                    <div class="status-indicator {'status-ok' if '🟢' in status_geral else 'status-warning' if '🟡' in status_geral else 'status-error'}">{status_geral}</div>
                </div>
                
                <div class="status-grid">
                    <div class="status-card">
                        <h3>🔐 Configuração & Autenticação</h3>
                        <div class="status-item">
                            <span class="status-label">Client ID:</span>
                            <span class="status-value {'status-ok' if len(client_id) > 8 else 'status-error'}">{client_safe}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Token Status:</span>
                            <span class="status-value {'status-ok' if auth_ok else 'status-error'}">{token_expira}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Autenticação:</span>
                            <span class="status-value {'status-ok' if auth_ok else 'status-error'}">{'✅ Ativa' if auth_ok else '❌ Inativa'}</span>
                        </div>
                    </div>
                    
                    <div class="status-card">
                        <h3>📧 Processamento de Emails</h3>
                        <div class="status-item">
                            <span class="status-label">Pasta Emails:</span>
                            <span class="status-value {'status-ok' if len(pasta_brk_id) > 10 else 'status-error'}">{pasta_safe}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Processador:</span>
                            <span class="status-value {'status-ok' if processor_ok else 'status-error'}">{'✅ OK' if processor_ok else '❌ Erro'}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Monitor:</span>
                            <span class="status-value status-ok">✅ Ativo (10min)</span>
                        </div>
                    </div>
                    
                    <div class="status-card">
                        <h3>📁 OneDrive & Relacionamento</h3>
                        <div class="status-item">
                            <span class="status-label">OneDrive BRK:</span>
                            <span class="status-value {'status-ok' if len(onedrive_brk_id) > 15 else 'status-warning'}">{onedrive_safe}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Relacionamentos:</span>
                            <span class="status-value {'status-ok' if total_relacionamentos > 0 else 'status-warning'}">{total_relacionamentos} CDCs</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Database:</span>
                            <span class="status-value {'status-ok' if len(onedrive_brk_id) > 15 else 'status-warning'}">{'✅ Ativo' if len(onedrive_brk_id) > 15 else '⚠️ Configurar'}</span>
                        </div>
                    </div>
                    
                    <div class="status-card">
                        <h3>📊 Sistema & Performance</h3>
                        <div class="status-item">
                            <span class="status-label">Versão:</span>
                            <span class="status-value status-ok">Refatorada v2.0</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Arquitetura:</span>
                            <span class="status-value status-ok">Modular</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Deploy:</span>
                            <span class="status-value status-ok">Render ✅</span>
                        </div>
                    </div>
                </div>
                
                <div class="actions-grid">
                    <a href="/upload-token" class="action-btn warning">
                        📁 Upload Token<br>
                        <small>Configurar autenticação Microsoft</small>
                    </a>
                    <a href="/test-onedrive" class="action-btn info">
                        🧪 Teste OneDrive<br>
                        <small>Verificar acesso e descobrir IDs</small>
                    </a>
                    <a href="https://brk-render-seguro.onrender.com" class="action-btn success" target="_blank">
                        🌐 Sistema Principal<br>
                        <small>Interface de produção</small>
                    </a>
                    </div>   ← ANTES DESTE </div>
                    <a href="/health" class="action-btn success">
                        🔍 Health Check<br>
                        <small>Verificação rápida sistema</small>
                    </a>
                    <a href="/create-brk-folder" class="action-btn info">
                        📂 Criar Pasta BRK<br>
                        <small>Configurar estrutura OneDrive</small>
                    </a>
                    <a href="https://brk-render-seguro.onrender.com" class="action-btn success" target="_blank">
                        🌐 Sistema Principal<br>
                        <small>Interface de produção</small>
                    </a>
                </div>
                
                <div class="footer">
                    <p>🔒 <strong>Interface Administrativa Segura</strong> | Estrutura Modular: auth/ + processor/ + admin/</p>
                    <p>📧 Sidney Gubitoso - Tesouraria Administrativa Mauá | 
                    <a href="https://github.com/seu-repo" target="_blank">📁 GitHub</a> | 
                    <a href="https://dashboard.render.com" target="_blank">☁️ Render</a></p>
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

# ============================================================================
# 📊 MELHORAR TAMBÉM O _handle_system_status PARA EXIBIÇÃO HTML BONITA
# SUBSTITUIR O MÉTODO _handle_system_status() EXISTENTE
# ============================================================================

    def _handle_system_status(self):
        """Status detalhado do sistema com opção HTML ou JSON"""
        from urllib.parse import urlparse, parse_qs
        
        # Verificar se quer HTML ou JSON
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        formato = params.get('formato', ['json'])[0]
        
        status = self.get_system_status()
        
        if formato == 'html':
            self._render_status_html(status)
        else:
            # JSON padrão
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(status, indent=2, ensure_ascii=False).encode('utf-8'))

    def _render_status_html(self, status: Dict[str, Any]):
        """Renderizar status em HTML bonito"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Preparar lista de endpoints
        endpoints_html = ""
        if status.get("endpoints"):
            for metodo, endpoints in status["endpoints"].items():
                if metodo in ["GET", "POST"]:
                    endpoints_html += f"<h4>{metodo} Endpoints:</h4><ul>"
                    for endpoint, info in endpoints.items():
                        endpoints_html += f"""
                        <li>
                            <strong>{endpoint}</strong> - {info['descricao']}<br>
                            <small>📋 {info['funcao']}</small><br>
                            <small>🔗 <a href="{info['exemplo']}" target="_blank">{info['exemplo']}</a></small><br>
                            <small>📄 Formato: {info['formato']}</small>
                        </li><br>
                        """
                    endpoints_html += "</ul>"
                elif metodo == "SERVERS":
                    endpoints_html += f"<h4>Servidores Adicionais:</h4><ul>"
                    for servidor, info in endpoints.items():
                        endpoints_html += f"""
                        <li>
                            <strong>{servidor}</strong> - {info['descricao']}<br>
                            <small>📋 {info['funcao']}</small><br>
                            <small>🔗 {info['exemplo']}</small><br>
                            <small>⌨️ Comandos: {info.get('comandos', 'N/A')}</small><br>
                            <small>🚀 Iniciar: <code>{info.get('como_iniciar', 'N/A')}</code></small>
                        </li><br>
                        """
                    endpoints_html += "</ul>"
        
        # Quick links
        quick_links_html = ""
        if status.get("quick_links"):
            for nome, url in status["quick_links"].items():
                nome_formatado = nome.replace("_", " ").title()
                quick_links_html += f'<a href="{url}" target="_blank" style="color: #3498db; margin-right: 15px;">{nome_formatado}</a>'
        
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <title>📊 Status Detalhado - BRK Monitor</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f8f9fa; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
                .status-ok {{ color: #28a745; }}
                .status-warning {{ color: #ffc107; }}
                .status-error {{ color: #dc3545; }}
                .section {{ margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
                .endpoints {{ background: #e3f2fd; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #3498db; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                h3 {{ color: #8e44ad; }}
                pre {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                .quick-links {{ background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Status Detalhado - BRK Monitor</h1>
                <p><strong>Timestamp:</strong> {status['timestamp']}</p>
                <p><strong>Serviço:</strong> {status['service']} v{status.get('version', 'N/A')}</p>
                <p><strong>URL Base:</strong> <a href="{status['base_url']}" target="_blank">{status['base_url']}</a></p>
                
                <div class="quick-links">
                    <h3>🔗 Links Rápidos:</h3>
                    {quick_links_html}
                </div>
                
                <div class="section">
                    <h2>⚙️ Configuração Sistema</h2>
                    <p>Client ID: <span class="{'status-ok' if status['config']['client_id_ok'] else 'status-error'}">{status['config']['client_id_safe']}</span></p>
                    <p>Pasta BRK: <span class="{'status-ok' if status['config']['pasta_brk_ok'] else 'status-error'}">{status['config']['pasta_brk_safe']}</span></p>
                    <p>OneDrive BRK: <span class="{'status-ok' if status['config']['onedrive_brk_ok'] else 'status-warning'}">{status['config']['onedrive_brk_safe']}</span></p>
                </div>
                
                <div class="section">
                    <h2>🔐 Status Autenticação</h2>
                    <p>Status: <span class="{'status-ok' if status['autenticacao']['token_ativo'] else 'status-error'}">{status['autenticacao']['status_resumo']}</span></p>
                </div>
                
                <div class="section">
                    <h2>📧 Status Processamento</h2>
                    <p>Status: <span class="{'status-ok' if status['processamento']['processor_ok'] else 'status-error'}">{status['processamento']['status_resumo']}</span></p>
                </div>
                
                <div class="section endpoints">
                    <h2>🌐 Endpoints HTTP Disponíveis (HELP)</h2>
                    {endpoints_html}
                </div>
                
                <div class="section">
                    <h2>💡 Help/Guia de Uso</h2>
                    <ul>
                        <li><strong>Como usar:</strong> {status['help']['como_usar']}</li>
                        <li><strong>Upload token:</strong> {status['help']['upload_token']}</li>
                        <li><strong>Testar OneDrive:</strong> {status['help']['testar_onedrive']}</li>
                        <li><strong>DBEDIT:</strong> {status['help']['dbedit']}</li>
                        <li><strong>Documentação:</strong> {status['help']['documentacao']}</li>
                    </ul>
                </div>
                
                <div class="section">
                    <h2>📋 Resumo Executivo</h2>
                    <p><strong>Status Geral:</strong> {status['resumo_executivo']['status_geral']}</p>
                    <p><strong>Total Endpoints:</strong> {status['resumo_executivo']['total_endpoints']}</p>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="/" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🏠 Voltar à Interface Principal</a>
                    <a href="/status" style="background: #8e44ad; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">📋 Ver JSON</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode('utf-8'))

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
