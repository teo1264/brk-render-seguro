"""
Microsoft Authentication Manager - BRK ESPECÍFICO
Token exclusivo: /Alerta/token_brk.json
"""

import os
import json
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

class MicrosoftAuthUnified:
    def __init__(self, client_id: str = None, client_secret: str = None, tenant_id: str = None):
        self.client_id = client_id or os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("MICROSOFT_CLIENT_SECRET") 
        self.tenant_id = tenant_id or os.getenv("MICROSOFT_TENANT_ID", "common")
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        self.alerta_folder_id = os.getenv("ONEDRIVE_ALERTA_ID")
        
        # TOKEN ESPECÍFICO BRK
        self.shared_token_filename = "token_brk.json"
        self.local_fallback_path = "token_backup_brk.json"
        
        if not self.client_id:
            raise ValueError("❌ MICROSOFT_CLIENT_ID não encontrado")
        if not self.encryption_key:
            raise ValueError("❌ ENCRYPTION_KEY não encontrada") 
        if not self.alerta_folder_id:
            raise ValueError("❌ ONEDRIVE_ALERTA_ID não encontrado")
            
        try:
            self.fernet = Fernet(self.encryption_key.encode())
        except Exception as e:
            raise ValueError(f"❌ ENCRYPTION_KEY inválida: {e}")
            
        self._tokens = None
        self._token_expiry = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info("🔐 Microsoft Auth BRK iniciado")
    
    def mask_token(self, token: str) -> str:
        if not token or len(token) < 10:
            return "***VAZIO***"
        return f"{token[:6]}...{token[-4:]}"
    
    def _encrypt_data(self, data: str) -> str:
        try:
            encrypted = self.fernet.encrypt(data.encode()).decode()
            return encrypted
        except Exception as e:
            self.logger.error(f"❌ Erro na criptografia: {e}")
            raise
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        try:
            decrypted = self.fernet.decrypt(encrypted_data.encode()).decode()
            return decrypted
        except Exception as e:
            self.logger.error(f"❌ Erro na descriptografia: {e}")
            raise
    
    def _get_shared_token_url(self) -> str:
        return f"https://graph.microsoft.com/v1.0/me/drive/items/{self.alerta_folder_id}:/{self.shared_token_filename}:/content"
    
    def _load_from_onedrive_shared(self) -> Optional[Dict[str, Any]]:
        try:
            access_token = os.getenv("MICROSOFT_ACCESS_TOKEN") or (self._tokens and self._tokens.get("access_token"))
            
            if not access_token:
                self.logger.warning("⚠️  Sem access_token para acessar OneDrive")
                return None
                
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            url = self._get_shared_token_url()
            self.logger.info(f"📥 Carregando token BRK da pasta Alerta...")
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.logger.info(f"✅ Token BRK carregado: {self.mask_token(token_data.get('refresh_token', ''))}")
                return token_data
            elif response.status_code == 404:
                self.logger.info("📄 Arquivo token_brk.json não existe ainda")
                return None
            else:
                self.logger.warning(f"⚠️  Erro carregar token BRK: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Erro acessar OneDrive Alerta: {e}")
            return None
    
    def _save_to_onedrive_shared(self, token_data: Dict[str, Any]) -> bool:
        try:
            access_token = os.getenv("MICROSOFT_ACCESS_TOKEN") or (self._tokens and self._tokens.get("access_token"))
            
            if not access_token:
                self.logger.error("❌ Sem access_token para salvar")
                return False
                
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            encrypted_data = {
                "access_token": self._encrypt_data(token_data["access_token"]),
                "refresh_token": self._encrypt_data(token_data["refresh_token"]),
                "expires_on": token_data.get("expires_on"),
                "encrypted": True,
                "updated_at": datetime.now().isoformat(),
                "sistema": "BRK"
            }
            
            url = self._get_shared_token_url()
            self.logger.info(f"💾 Salvando token BRK na pasta Alerta...")
            
            response = requests.put(
                url, 
                headers=headers, 
                data=json.dumps(encrypted_data),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                self.logger.info(f"✅ Token BRK salvo: {self.mask_token(token_data['refresh_token'])}")
                return True
            else:
                self.logger.error(f"❌ Erro salvar token BRK: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro salvar token BRK: {e}")
            return False
    
    def load_tokens(self) -> bool:
        self.logger.info("🔍 Iniciando carregamento tokens BRK...")
        
        # 1. Environment variables criptografadas
        access_token_env = os.getenv("MICROSOFT_ACCESS_TOKEN_SECURE")
        refresh_token_env = os.getenv("MICROSOFT_REFRESH_TOKEN_SECURE")
        
        if access_token_env and refresh_token_env:
            try:
                self._tokens = {
                    "access_token": self._decrypt_data(access_token_env),
                    "refresh_token": self._decrypt_data(refresh_token_env),
                    "expires_on": int(os.getenv("MICROSOFT_TOKEN_EXPIRES", "0"))
                }
                self.logger.info(f"✅ Tokens BRK das ENV criptografadas: {self.mask_token(self._tokens['access_token'])}")
                return True
            except Exception as e:
                self.logger.error(f"❌ Erro descriptografar ENV: {e}")
        
        # 2. Environment variables texto plano (bootstrap)
        access_token_plain = os.getenv("MICROSOFT_ACCESS_TOKEN")
        refresh_token_plain = os.getenv("MICROSOFT_REFRESH_TOKEN")
        
        if access_token_plain and refresh_token_plain:
            self._tokens = {
                "access_token": access_token_plain,
                "refresh_token": refresh_token_plain,
                "expires_on": int(os.getenv("MICROSOFT_TOKEN_EXPIRES", str(int(datetime.now().timestamp()) + 3600)))
            }
            self.logger.info("✅ Tokens BRK bootstrap das ENV texto plano")
            
            # Carregar/migrar do OneDrive
            onedrive_tokens = self._load_from_onedrive_shared()
            if onedrive_tokens:
                if onedrive_tokens.get("encrypted"):
                    try:
                        onedrive_tokens["access_token"] = self._decrypt_data(onedrive_tokens["access_token"])
                        onedrive_tokens["refresh_token"] = self._decrypt_data(onedrive_tokens["refresh_token"])
                        self._tokens = onedrive_tokens
                        self.logger.info("✅ Migrado para token BRK OneDrive criptografado")
                    except Exception as e:
                        self.logger.error(f"❌ Erro descriptografar OneDrive: {e}")
                else:
                    self._tokens = onedrive_tokens
                    self.logger.warning("⚠️  Token BRK OneDrive texto puro - migrando...")
                    self.save_tokens(onedrive_tokens["access_token"], onedrive_tokens["refresh_token"])
            
            return True
        
        # 3. OneDrive direto
        onedrive_tokens = self._load_from_onedrive_shared()
        if onedrive_tokens:
            if onedrive_tokens.get("encrypted"):
                try:
                    onedrive_tokens["access_token"] = self._decrypt_data(onedrive_tokens["access_token"])
                    onedrive_tokens["refresh_token"] = self._decrypt_data(onedrive_tokens["refresh_token"])
                except Exception as e:
                    self.logger.error(f"❌ Erro descriptografar OneDrive: {e}")
                    onedrive_tokens = None
                    
            if onedrive_tokens:
                self._tokens = onedrive_tokens
                return True
        
        self.logger.warning("⚠️  Nenhum token BRK encontrado")
        return False
    
    def save_tokens(self, access_token: str, refresh_token: str, expires_in: int = 3600):
        expires_on = int(datetime.now().timestamp()) + expires_in
        
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_on": expires_on
        }
        
        self._tokens = token_data.copy()
        self._token_expiry = datetime.fromtimestamp(expires_on)
        
        self.logger.info(f"💾 Salvando tokens BRK: {self.mask_token(refresh_token)}")
        
        onedrive_saved = self._save_to_onedrive_shared(token_data)
        
        if onedrive_saved:
            self.logger.info("✅ Tokens BRK salvos com sucesso")
        else:
            self.logger.warning("⚠️  OneDrive BRK falhou")
    
    def is_token_valid(self) -> bool:
        if not self._tokens:
            return False
            
        if not self._token_expiry:
            expires_on = self._tokens.get("expires_on")
            if expires_on:
                self._token_expiry = datetime.fromtimestamp(expires_on)
            else:
                return False
        
        return datetime.now() < (self._token_expiry - timedelta(minutes=5))
    
    def refresh_access_token(self) -> bool:
        if not self._tokens or not self._tokens.get("refresh_token"):
            self.logger.error("❌ Refresh token BRK não disponível")
            return False
        
        self.logger.info(f"🔄 Renovando token BRK: {self.mask_token(self._tokens['refresh_token'])}")
        
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': self._tokens["refresh_token"]
            }
            
            response = requests.post(
                f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token',
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_response = response.json()
                
                self.save_tokens(
                    token_response['access_token'],
                    token_response.get('refresh_token', self._tokens["refresh_token"]),
                    token_response.get('expires_in', 3600)
                )
                
                self.logger.info(f"✅ Token BRK renovado: {self.mask_token(token_response['access_token'])}")
                return True
            else:
                self.logger.error(f"❌ Erro renovação BRK: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro renovação BRK: {e}")
            return False
    
    @property
    def access_token(self) -> Optional[str]:
        if not self._tokens:
            if not self.load_tokens():
                return None
        
        if not self.is_token_valid():
            if not self.refresh_access_token():
                return None
        
        return self._tokens.get("access_token")
    
    @property  
    def refresh_token(self) -> Optional[str]:
        if not self._tokens:
            if not self.load_tokens():
                return None
        return self._tokens.get("refresh_token")
    
    # Métodos de compatibilidade BRK
    def obter_headers_autenticados(self) -> dict:
        token = self.access_token
        if not token:
            raise Exception("Token de acesso não disponível")
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def get_microsoft_token(self) -> dict:
        if not self._tokens:
            if not self.load_tokens():
                return {}
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_on': self._tokens.get('expires_on', 0) if self._tokens else 0
        }

# Compatibilidade
class MicrosoftAuth(MicrosoftAuthUnified):
    pass
