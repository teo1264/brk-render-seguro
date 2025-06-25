#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: brk/auth_microsoft.py
💾 ONDE SALVAR: ccb-alerta-bot/brk/auth_microsoft.py
🔐 FUNÇÃO: Módulo de Autenticação Microsoft
📦 EXTRAÍDO DE: app.py funcionando no Render
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar da tesouraria
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional


class MicrosoftAuth:
    """Autenticação Microsoft Graph API - VERSÃO SEGURA"""
    
    def __init__(self):
        # CONFIGURAÇÕES APENAS VIA ENVIRONMENT VARIABLES
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.tenant_id = os.getenv("MICROSOFT_TENANT_ID", "consumers")
        
        # VALIDAÇÃO OBRIGATÓRIA
        if not self.client_id:
            raise ValueError("❌ MICROSOFT_CLIENT_ID não configurado!")
        
        # Token management
        self.token_file_persistent = "/opt/render/project/storage/token.json"
        self.token_file_local = "token.json"
        self.access_token = None
        self.refresh_token = None
        
        # Carregar tokens automaticamente
        self.carregar_token()
        
        print(f"🔐 Auth Microsoft inicializado")
        print(f"   Client ID: {self.client_id[:8]}****** (protegido)")
    
    def carregar_token(self) -> bool:
        """Carregar token do persistent disk ou local"""
        if os.path.exists(self.token_file_persistent):
            return self._carregar_do_arquivo(self.token_file_persistent)
        elif os.path.exists(self.token_file_local):
            return self._carregar_do_arquivo(self.token_file_local)
        else:
            print("💡 Token não encontrado - use interface web para upload")
            return False
    
    def _carregar_do_arquivo(self, filepath: str) -> bool:
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
    
    def salvar_token_persistent(self) -> bool:
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

    def atualizar_token(self) -> bool:
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
    
    def obter_token_valido(self) -> Optional[str]:
        """Obter token válido (renova se necessário)"""
        if not self.access_token:
            if not self.carregar_token():
                print("❌ Não foi possível carregar token")
                return None
        
        # TODO: Verificar se token expirou (implementar depois)
        # Por enquanto, sempre tenta usar o atual
        return self.access_token
    
    def testar_acesso_onedrive(self) -> Dict:
        """Teste básico de acesso OneDrive usando credenciais atuais"""
        print("🧪 TESTE ONEDRIVE - INICIANDO")
        
        try:
            if not self.client_id:
                return {
                    "status": "error",
                    "onedrive_access": False,
                    "message": "CLIENT_ID não configurado",
                    "details": "Environment variable MICROSOFT_CLIENT_ID não encontrada"
                }
            
            print(f"✅ CLIENT_ID encontrado: {self.client_id[:10]}******")
            
            # Carregar token atual
            if not self.refresh_token:
                return {
                    "status": "error", 
                    "onedrive_access": False,
                    "message": "Token não encontrado",
                    "details": "Refresh token não disponível"
                }
            
            print("✅ Token.json carregado com sucesso")
            
            # Testar diferentes scopes OneDrive
            print("🔄 Testando diferentes scopes OneDrive...")
            
            scopes_para_testar = [
                "Files.ReadWrite offline_access",
                "Files.ReadWrite.All offline_access", 
                "https://graph.microsoft.com/Files.ReadWrite offline_access",
                "https://graph.microsoft.com/Files.ReadWrite.All offline_access"
            ]
            
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            access_token = None
            scope_funcionou = None
            
            for scope_teste in scopes_para_testar:
                print(f"🧪 Testando scope: {scope_teste}")
                
                token_data_request = {
                    'client_id': self.client_id,
                    'grant_type': 'refresh_token', 
                    'refresh_token': self.refresh_token,
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
                    'client_id': self.client_id,
                    'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token,
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
            
            # Testar acesso OneDrive
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
    
    def criar_pasta_brk(self) -> Dict:
        """Teste criar pasta /BRK no OneDrive"""
        print("📁 TESTE CRIAÇÃO PASTA /BRK - INICIANDO")
        
        try:
            if not self.client_id or not self.refresh_token:
                return {
                    "status": "error",
                    "message": "Configurações básicas não encontradas",
                    "details": "Execute testar_acesso_onedrive primeiro"
                }
            
            # USAR SCOPE QUE FUNCIONOU
            scope_funcional = "Files.ReadWrite offline_access"
            
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            token_request = {
                'client_id': self.client_id,
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
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
            
            # Verificar se pasta /BRK já existe
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
            
            # Criar pasta /BRK se não existir
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
            
            # Listar conteúdo da pasta /BRK
            print("📂 Listando conteúdo da pasta /BRK...")
            
            if pasta_brk_id:
                conteudo_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_brk_id}/children"
            else:
                # Buscar novamente se não temos ID
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
            
            # Retornar resultado completo
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
