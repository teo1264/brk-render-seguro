#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Microsoft Auth - VERSÃO CORRIGIDA COM ENVIRONMENT VARIABLES

MUDANÇA PRINCIPAL:
- Migração de leitura de arquivos para Environment Variables
- Mantém fallback para arquivos para compatibilidade
- Resolve problema de disk não persistente no Render

CORREÇÃO APLICADA:
- Adicionada função get_microsoft_token()
- Modificado método carregar_token() para usar env vars primeiro
- Mantido fallback para arquivos existente
"""

import os
import json
import requests
import hashlib
import base64
from datetime import datetime
from cryptography.fernet import Fernet


class MicrosoftAuth:
    def __init__(self):
        """Inicializar autenticação Microsoft com prioridade para Environment Variables"""
        
        # Configuração do Cliente
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.tenant_id = os.getenv("MICROSOFT_TENANT_ID", "consumers")
        
        # Tokens (serão carregados)
        self.access_token = None
        self.refresh_token = None
        
        # Caminhos de fallback para arquivos (compatibilidade)
        self.token_file_persistent = "/opt/render/project/storage/token.json"
        self.token_file_local = "token.json"
        
        # Validação obrigatória
        if not self.client_id:
            print("⚠️ MICROSOFT_CLIENT_ID não configurado")
        
        # Tentar carregar token automaticamente
        self.carregar_token()
        
        self._debug_status()

    def get_microsoft_token(self):
        """
        ✅ NOVA FUNÇÃO - Obter token Microsoft com PRIORIDADE para Environment Variables
        
        PRIORIDADE:
        1. Environment Variables (PERSISTENTE após deploy)
        2. Arquivo criptografado 
        3. Arquivo JSON (fallback)
        
        Returns:
            dict: Token data ou None se não encontrado
        """
        
        # ✅ PRIORIDADE 1: Environment Variables (persistente)
        access_token = os.getenv('MICROSOFT_ACCESS_TOKEN')
        refresh_token = os.getenv('MICROSOFT_REFRESH_TOKEN')
        
        if access_token and refresh_token:
            print("✅ Token carregado das ENVIRONMENT VARIABLES (persistente)")
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'fonte': 'environment_variables'
            }
        
        # ⚠️ FALLBACK 1: Arquivo criptografado
        encrypted_file = self.token_file_persistent.replace('.json', '.enc')
        if os.path.exists(encrypted_file):
            try:
                with open(encrypted_file, 'rb') as f:
                    encrypted_data = f.read()
                token_data = self._decrypt_token_data(encrypted_data)
                if token_data:
                    print(f"🔒 Token carregado de arquivo CRIPTOGRAFADO: {encrypted_file}")
                    print("⚠️ RECOMENDAÇÃO: Migre para Environment Variables!")
                    token_data['fonte'] = 'arquivo_criptografado'
                    return token_data
            except Exception as e:
                print(f"❌ Erro lendo arquivo criptografado: {e}")
        
        # ⚠️ FALLBACK 2: Arquivo JSON (persistent disk)
        if os.path.exists(self.token_file_persistent):
            try:
                with open(self.token_file_persistent, 'r') as f:
                    token_data = json.load(f)
                print(f"💾 Token carregado de arquivo JSON: {self.token_file_persistent}")
                print("⚠️ RECOMENDAÇÃO: Migre para Environment Variables!")
                token_data['fonte'] = 'arquivo_persistent'
                return token_data
            except Exception as e:
                print(f"❌ Erro lendo arquivo persistent: {e}")
        
        # ⚠️ FALLBACK 3: Arquivo JSON (local)
        if os.path.exists(self.token_file_local):
            try:
                with open(self.token_file_local, 'r') as f:
                    token_data = json.load(f)
                print(f"💾 Token carregado de arquivo LOCAL: {self.token_file_local}")
                print("⚠️ RECOMENDAÇÃO: Migre para Environment Variables!")
                token_data['fonte'] = 'arquivo_local'
                return token_data
            except Exception as e:
                print(f"❌ Erro lendo arquivo local: {e}")
        
        # ❌ Nenhum token encontrado
        print("❌ Token Microsoft não encontrado!")
        print("📋 CONFIGURAÇÃO NECESSÁRIA:")
        print("   1. Environment Variables no Render:")
        print("      MICROSOFT_ACCESS_TOKEN=seu_access_token")
        print("      MICROSOFT_REFRESH_TOKEN=seu_refresh_token")
        print("   2. Ou upload via interface web")
        
        return None

    def carregar_token(self) -> bool:
        """
        ✅ MÉTODO MODIFICADO - Carregar token usando get_microsoft_token()
        
        MUDANÇA: Agora usa get_microsoft_token() que prioriza env vars
        
        Returns:
            bool: True se tokens carregados com sucesso
        """
        
        token_data = self.get_microsoft_token()
        
        if token_data:
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            if self.access_token and self.refresh_token:
                fonte = token_data.get('fonte', 'desconhecida')
                print(f"✅ Tokens carregados com sucesso (fonte: {fonte})")
                return True
            else:
                print("❌ Tokens incompletos no token_data")
                return False
        else:
            print("❌ Nenhum token disponível")
            return False

    def _carregar_do_arquivo(self, filepath: str) -> bool:
        """
        ⚠️ MÉTODO MANTIDO para compatibilidade
        
        OBSERVAÇÃO: Este método agora é usado apenas pelos fallbacks
        A prioridade é sempre Environment Variables
        """
        try:
            # 🔐 Tentar carregar arquivo criptografado primeiro
            encrypted_file = filepath.replace('.json', '.enc')
            if os.path.exists(encrypted_file):
                with open(encrypted_file, 'rb') as f:
                    encrypted_data = f.read()
                token_data = self._decrypt_token_data(encrypted_data)
                if token_data:
                    self.access_token = token_data.get('access_token')
                    self.refresh_token = token_data.get('refresh_token')
                    if self.access_token and self.refresh_token:
                        print(f"🔒 Token CRIPTOGRAFADO carregado de: {encrypted_file}")
                        return True
            
            # Fallback: carregar arquivo JSON original
            with open(filepath, 'r') as f:
                token_data = json.load(f)
            
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            if self.access_token and self.refresh_token:
                print(f"💾 Token carregado de: {filepath}")
                return True
            else:
                print(f"❌ Token inválido em: {filepath}")
                return False
                
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {filepath}")
            return False
        except Exception as e:
            print(f"❌ Erro carregando {filepath}: {e}")
            return False

    def _get_encryption_key(self):
        """Obter chave de criptografia (mantido para compatibilidade)"""
        try:
            key_file = "/opt/render/project/storage/.encryption_key"
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    return f.read()
        except Exception:
            pass
        
        # Fallback: gerar chave determinística
        unique_data = f"BRK{self.client_id or 'default'}{os.getenv('RENDER_SERVICE_ID', 'fallback')}"
        return base64.urlsafe_b64encode(hashlib.sha256(unique_data.encode()).digest())

    def _encrypt_token_data(self, token_data):
        """Criptografar dados do token (mantido para compatibilidade)"""
        try:
            key = self._get_encryption_key()
            cipher = Fernet(key)
            json_data = json.dumps(token_data).encode('utf-8')
            return cipher.encrypt(json_data)
        except Exception as e:
            print(f"⚠️ Erro criptografando token: {e}")
            return None

    def _decrypt_token_data(self, encrypted_data):
        """Descriptografar dados do token (mantido para compatibilidade)"""
        try:
            key = self._get_encryption_key()
            cipher = Fernet(key)
            decrypted_data = cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            print(f"⚠️ Erro descriptografando token: {e}")
            return None

    def salvar_token_persistent(self) -> bool:
        """
        Salvar token no persistent disk com proteção (mantido para compatibilidade)
        
        OBSERVAÇÃO: Com Environment Variables, este método é menos necessário
        Mas mantido para casos onde se queira salvar backup em arquivo
        """
        try:
            # Proteger diretório
            token_dir = os.path.dirname(self.token_file_persistent)
            os.makedirs(token_dir, exist_ok=True)
            os.chmod(token_dir, 0o700)
            
            token_data = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_in': 3600,
                'token_type': 'Bearer',
                'scope': 'https://graph.microsoft.com/.default offline_access',
                'saved_at': datetime.now().isoformat(),
                'sistema': 'BRK',
                'client_hash': hashlib.sha256((self.client_id or 'default').encode()).hexdigest()[:8]
            }
            
            # Tentar salvar criptografado primeiro
            encrypted_data = self._encrypt_token_data(token_data)
            if encrypted_data:
                encrypted_file = self.token_file_persistent.replace('.json', '.enc')
                with open(encrypted_file, 'wb') as f:
                    f.write(encrypted_data)
                os.chmod(encrypted_file, 0o600)
                # Remover arquivo antigo não criptografado se existir
                if os.path.exists(self.token_file_persistent):
                    os.remove(self.token_file_persistent)
                print(f"🔒 Token BRK salvo CRIPTOGRAFADO: {encrypted_file}")
            else:
                # Fallback: salvar sem criptografia
                with open(self.token_file_persistent, 'w') as f:
                    json.dump(token_data, f, indent=2)
                os.chmod(self.token_file_persistent, 0o600)
                print(f"💾 Token BRK salvo com proteção: {self.token_file_persistent}")
            
            return True
        except Exception as e:
            print(f"❌ Erro salvando token BRK protegido: {e}")
            return False

    def atualizar_token(self) -> bool:
        """
        Renovar access_token usando refresh_token
        
        MUDANÇA: Agora usa get_microsoft_token() para obter tokens atuais
        """
        try:
            # Usar get_microsoft_token para garantir que temos os tokens mais recentes
            token_data = self.get_microsoft_token()
            if not token_data or not token_data.get('refresh_token'):
                print("❌ Refresh token não disponível para renovação")
                return False
            
            self.refresh_token = token_data['refresh_token']
            
            url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            data = {
                'client_id': self.client_id,
                'scope': 'https://graph.microsoft.com/.default offline_access',
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Atualizar tokens em memória
                self.access_token = token_data['access_token']
                
                # Atualizar refresh_token se fornecido
                if 'refresh_token' in token_data:
                    self.refresh_token = token_data['refresh_token']
                
                # Salvar no persistent disk como backup
                self.salvar_token_persistent()
                
                print("✅ Token BRK renovado com sucesso")
                return True
                
            else:
                print(f"❌ Erro renovando token BRK: HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Detalhes: {error_detail.get('error_description', 'N/A')}")
                except:
                    pass
                return False
                
        except requests.RequestException as e:
            print(f"❌ Erro de rede na renovação BRK: {e}")
            return False
        except Exception as e:
            print(f"❌ Erro inesperado na renovação BRK: {e}")
            return False

    def obter_headers_autenticados(self):
        """
        Obter headers HTTP com token de autorização
        
        MUDANÇA: Usa get_microsoft_token para garantir token mais recente
        """
        # Garantir que temos token atual
        token_data = self.get_microsoft_token()
        if token_data:
            self.access_token = token_data.get('access_token')
        
        if not self.access_token:
            print("❌ Access token não disponível")
            return None
            
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def validar_token(self) -> bool:
        """
        Validar se o token atual funciona
        """
        headers = self.obter_headers_autenticados()
        if not headers:
            return False
            
        try:
            response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False

    def _debug_status(self):
        """Status de debug da autenticação"""
        print(f"🔧 Microsoft Auth BRK - Debug Status:")
        print(f"   Client ID: {'configurado' if self.client_id else 'pendente'}")
        print(f"   Tenant: {self.tenant_id}")
        print(f"   Access Token: {'disponível' if self.access_token else 'não disponível'}")
        print(f"   Refresh Token: {'disponível' if self.refresh_token else 'não disponível'}")

    def obter_status_completo(self):
        """Status completo para diagnóstico"""
        return {
            "autenticado": bool(self.access_token and self.refresh_token),
            "client_id_configurado": bool(self.client_id),
            "client_id_protegido": f"{self.client_id[:8]}******" if self.client_id else "N/A",
            "tenant_id": self.tenant_id,
            "token_valido": self.validar_token() if self.access_token else False,
            "fonte_token": self.get_microsoft_token().get('fonte', 'nenhuma') if self.get_microsoft_token() else 'nenhuma'
        }


# ✅ FUNÇÃO DE TESTE PARA VALIDAÇÃO
def test_microsoft_token():
    """
    Testar se token das environment variables funciona
    """
    try:
        auth = MicrosoftAuth()
        token_data = auth.get_microsoft_token()
        
        if not token_data:
            return False, "Token não encontrado"
        
        headers = {'Authorization': f'Bearer {token_data["access_token"]}'}
        response = requests.get('https://graph.microsoft.com/v1.0/me/drive', headers=headers, timeout=10)
        
        if response.status_code == 200:
            return True, f"✅ Token funcionando - OneDrive conectado (fonte: {token_data.get('fonte', 'desconhecida')})"
        else:
            return False, f"❌ Token inválido - HTTP {response.status_code}"
            
    except Exception as e:
        return False, f"❌ Erro testando token: {e}"


if __name__ == "__main__":
    # Teste rápido quando executado diretamente
    success, message = test_microsoft_token()
    print(f"Token Microsoft: {message}")
