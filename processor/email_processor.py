#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/email_processor.py
💾 ONDE SALVAR: brk-monitor-seguro/processor/email_processor.py
📦 FUNÇÃO: Processamento de emails BRK via Microsoft Graph
🔧 DESCRIÇÃO: Busca, diagnóstico e extração de PDFs dos emails
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar da tesouraria
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any
from auth.microsoft_auth import MicrosoftAuth


class EmailProcessor:
    """
    Processador de emails BRK via Microsoft Graph API
    
    Responsabilidades:
    - Buscar emails novos na pasta BRK
    - Diagnosticar pasta (total, 24h, mês atual)
    - Extrair PDFs dos anexos
    - Usar autenticação via MicrosoftAuth
    """
    
    def __init__(self, microsoft_auth: MicrosoftAuth):
        """
        Inicializar processador com autenticação
        
        Args:
            microsoft_auth (MicrosoftAuth): Instância configurada de autenticação
        """
        self.auth = microsoft_auth
        
        # PASTA BRK ID via environment variable
        self.pasta_brk_id = os.getenv("PASTA_BRK_ID")
        
        if not self.pasta_brk_id:
            raise ValueError("❌ PASTA_BRK_ID não configurado!")
        
        print(f"📧 Email Processor inicializado")
        print(f"   Pasta BRK: {self.pasta_brk_id[:10]}****** (protegido)")
    
    def buscar_emails_novos(self, dias_atras: int = 1) -> List[Dict]:
        """
        Buscar emails novos na pasta BRK
        
        Args:
            dias_atras (int): Quantos dias atrás buscar (padrão: 1)
            
        Returns:
            List[Dict]: Lista de emails encontrados
        """
        try:
            # Calcular data limite
            data_limite = datetime.now() - timedelta(days=dias_atras)
            data_limite_str = data_limite.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # URL e parâmetros para Microsoft Graph
            url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_brk_id}/messages"
            params = {
                '$filter': f"receivedDateTime ge {data_limite_str}",
                '$expand': 'attachments',
                '$top': 10,
                '$orderby': 'receivedDateTime desc'
            }
            
            # Primeira tentativa com token atual
            headers = self.auth.obter_headers_autenticados()
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Se token expirou, tentar renovar
            if response.status_code == 401:
                print("🔄 Token expirado detectado, renovando...")
                if self.auth.atualizar_token():
                    headers = self.auth.obter_headers_autenticados()
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                else:
                    print("❌ Falha na renovação do token")
                    return []
            
            # Processar resposta
            if response.status_code == 200:
                data = response.json()
                emails = data.get('value', [])
                print(f"📧 Encontrados {len(emails)} emails")
                return emails
                
            elif response.status_code == 404:
                print(f"❌ Pasta BRK não encontrada: {self.pasta_brk_id}")
                return []
                
            else:
                print(f"❌ Erro buscando emails: HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Detalhes: {error_detail.get('error', {}).get('message', 'N/A')}")
                except:
                    pass
                return []
                
        except requests.RequestException as e:
            print(f"❌ Erro de rede na busca: {e}")
            return []
        except Exception as e:
            print(f"❌ Erro inesperado na busca: {e}")
            return []
    
    def extrair_pdfs_do_email(self, email: Dict) -> List[Dict]:
        """
        Extrair PDFs dos anexos do email
        
        Args:
            email (Dict): Dados do email do Microsoft Graph
            
        Returns:
            List[Dict]: Lista de informações dos PDFs encontrados
        """
        pdfs = []
        
        try:
            attachments = email.get('attachments', [])
            email_id = email.get('id', 'unknown')
            
            for attachment in attachments:
                filename = attachment.get('name', '').lower()
                
                # Verificar se é PDF
                if filename.endswith('.pdf'):
                    pdf_info = {
                        'email_id': email_id,
                        'filename': attachment.get('name', 'unnamed.pdf'),
                        'size': attachment.get('size', 0),
                        'content_bytes': attachment.get('contentBytes', ''),
                        'received_date': email.get('receivedDateTime', ''),
                        'email_subject': email.get('subject', ''),
                        'sender': email.get('from', {}).get('emailAddress', {}).get('address', 'unknown')
                    }
                    pdfs.append(pdf_info)
                    
            if pdfs:
                print(f"📎 Encontrados {len(pdfs)} PDFs no email")
                
            return pdfs
            
        except Exception as e:
            print(f"❌ Erro extraindo PDFs: {e}")
            return []
    
    def diagnosticar_pasta_brk(self) -> Dict:
        """
        Diagnóstico completo da pasta BRK
        
        Conta emails por período:
        - Total geral
        - Últimas 24 horas  
        - Mês atual
        
        Returns:
            Dict: Estatísticas da pasta BRK
        """
        try:
            headers = self.auth.obter_headers_autenticados()
            base_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_brk_id}/messages"
            
            # TOTAL GERAL
            print("📊 Contando emails totais...")
            response_total = requests.get(
                base_url, 
                headers=headers, 
                params={'$top': 1, '$count': 'true'},
                timeout=30
            )
            
            # Se token expirou, renovar e tentar novamente
            if response_total.status_code == 401:
                if self.auth.atualizar_token():
                    headers = self.auth.obter_headers_autenticados()
                    response_total = requests.get(
                        base_url, 
                        headers=headers, 
                        params={'$top': 1, '$count': 'true'},
                        timeout=30
                    )
            
            total_geral = 0
            if response_total.status_code == 200:
                total_geral = response_total.json().get('@odata.count', 0)
            else:
                print(f"⚠️ Erro contando total: HTTP {response_total.status_code}")
            
            # ÚLTIMAS 24 HORAS
            print("📊 Contando emails 24h...")
            data_24h = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
            params_24h = {
                '$filter': f"receivedDateTime ge {data_24h}",
                '$top': 1,
                '$count': 'true'
            }
            
            response_24h = requests.get(base_url, headers=headers, params=params_24h, timeout=30)
            total_24h = 0
            if response_24h.status_code == 200:
                total_24h = response_24h.json().get('@odata.count', 0)
            else:
                print(f"⚠️ Erro contando 24h: HTTP {response_24h.status_code}")
            
            # MÊS ATUAL
            print("📊 Contando emails do mês...")
            primeiro_dia = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            data_mes = primeiro_dia.strftime('%Y-%m-%dT%H:%M:%SZ')
            params_mes = {
                '$filter': f"receivedDateTime ge {data_mes}",
                '$top': 1,
                '$count': 'true'
            }
            
            response_mes = requests.get(base_url, headers=headers, params=params_mes, timeout=30)
            total_mes = 0
            if response_mes.status_code == 200:
                total_mes = response_mes.json().get('@odata.count', 0)
            else:
                print(f"⚠️ Erro contando mês: HTTP {response_mes.status_code}")
            
            # Resultado consolidado
            resultado = {
                'total_geral': total_geral,
                'ultimas_24h': total_24h,
                'mes_atual': total_mes,
                'status': 'sucesso',
                'pasta_id': self.pasta_brk_id[:10] + "******",
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Diagnóstico concluído: {total_geral} total, {total_24h} em 24h, {total_mes} no mês")
            return resultado
            
        except requests.RequestException as e:
            print(f"❌ Erro de rede no diagnóstico: {e}")
            return self._resultado_erro_diagnostico(str(e))
        except Exception as e:
            print(f"❌ Erro inesperado no diagnóstico: {e}")
            return self._resultado_erro_diagnostico(str(e))
    
    def _resultado_erro_diagnostico(self, erro: str) -> Dict:
        """
        Gerar resultado padrão para erro no diagnóstico
        
        Args:
            erro (str): Mensagem de erro
            
        Returns:
            Dict: Resultado com valores zerados
        """
        return {
            'total_geral': 0,
            'ultimas_24h': 0,
            'mes_atual': 0,
            'status': 'erro',
            'erro': erro,
            'timestamp': datetime.now().isoformat()
        }
    
    def buscar_email_por_id(self, email_id: str) -> Dict:
        """
        Buscar email específico por ID
        
        Args:
            email_id (str): ID do email no Microsoft Graph
            
        Returns:
            Dict: Dados do email ou vazio se não encontrado
        """
        try:
            url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}"
            params = {'$expand': 'attachments'}
            
            headers = self.auth.obter_headers_autenticados()
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Tentar renovar token se expirado
            if response.status_code == 401:
                if self.auth.atualizar_token():
                    headers = self.auth.obter_headers_autenticados()
                    response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Email não encontrado: {email_id}")
                return {}
                
        except Exception as e:
            print(f"❌ Erro buscando email {email_id}: {e}")
            return {}
    
    def validar_acesso_pasta_brk(self) -> bool:
        """
        Validar se consegue acessar a pasta BRK
        
        Returns:
            bool: True se pasta acessível
        """
        try:
            url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_brk_id}"
            headers = self.auth.obter_headers_autenticados()
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 401:
                if self.auth.atualizar_token():
                    headers = self.auth.obter_headers_autenticados()
                    response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                pasta_info = response.json()
                print(f"✅ Pasta BRK acessível: {pasta_info.get('displayName', 'N/A')}")
                return True
            else:
                print(f"❌ Pasta BRK inacessível: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro validando pasta BRK: {e}")
            return False
    
    def status_processamento(self) -> Dict:
        """
        Obter status atual do processamento
        
        Returns:
            Dict: Informações sobre estado do processamento
        """
        return {
            "pasta_brk_configurada": bool(self.pasta_brk_id),
            "pasta_brk_protegida": f"{self.pasta_brk_id[:10]}******" if self.pasta_brk_id else "N/A",
            "autenticacao_ok": bool(self.auth.access_token),
            "pasta_acessivel": self.validar_acesso_pasta_brk()
        }
