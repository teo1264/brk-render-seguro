#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 BRK RENDER MONITOR - Processamento Automático (LIMPO)

DEPLOY: Render.com com PERSISTENT DISK
FUNÇÃO: Processamento automático de emails BRK + SQLite + OneDrive
ESTRUTURA: Modular (auth + processor + admin separados)
SEGURANÇA: Todas as credenciais via variáveis de ambiente
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
"""

import os
import time
import sqlite3
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import base64
import json

# IMPORTS DOS MÓDULOS REFATORADOS
from auth import MicrosoftAuth
from processor import EmailProcessor


class DatabaseBRKBasico:
    """Database SQLite básico com persistent disk"""
    
    def __init__(self, db_path: str = "/opt/render/project/storage/brk_basico.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.criar_tabelas()
        print(f"💾 Database: {self.db_path}")
    
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
            print("✅ Database tabelas criadas")
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
            
            # Verificar duplicata por hash
            if hash_arquivo:
                cursor = conn.execute("SELECT id FROM faturas_brk_basico WHERE hash_arquivo = ?", (hash_arquivo,))
                if cursor.fetchone():
                    print(f"⚠️ PDF duplicado: {dados.get('nome_arquivo', 'unknown')}")
                    conn.close()
                    return False
            
            # Inserir nova fatura
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
            print(f"❌ Erro salvando fatura: {e}")
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
            
            # Total de faturas
            cursor = conn.execute("SELECT COUNT(*) FROM faturas_brk_basico")
            total_faturas = cursor.fetchone()[0]
            
            # Total de emails processados
            cursor = conn.execute("SELECT COUNT(*) FROM emails_processados")
            total_emails = cursor.fetchone()[0]
            
            # Últimas faturas
            cursor = conn.execute("SELECT nome_arquivo, data_processamento FROM faturas_brk_basico ORDER BY data_processamento DESC LIMIT 5")
            ultimas_faturas = cursor.fetchall()
            
            # Estatísticas por mês
            cursor = conn.execute("""
                SELECT DATE(data_processamento) as data, COUNT(*) as total 
                FROM faturas_brk_basico 
                WHERE data_processamento >= DATE('now', '-30 days')
                GROUP BY DATE(data_processamento)
                ORDER BY data DESC LIMIT 10
            """)
            faturas_por_dia = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_faturas': total_faturas,
                'total_emails_processados': total_emails,
                'ultimas_faturas': ultimas_faturas,
                'faturas_por_dia': faturas_por_dia,
                'ultima_atualizacao': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Erro obtendo estatísticas: {e}")
            return {}


class OneDriveBasico:
    """Cliente OneDrive simulado com persistent disk"""
    
    def __init__(self):
        self.base_path = "/BRK"
        self.local_path = Path("/opt/render/project/storage/onedrive_simulado/BRK")
        self.local_path.mkdir(parents=True, exist_ok=True)
        print(f"📤 OneDrive simulado: {self.local_path}")
    
    def upload_pdf(self, pdf_content: bytes, filename: str) -> str:
        """Upload simulado no persistent disk"""
        try:
            # Sanitizar nome do arquivo
            filename_safe = self._sanitizar_filename(filename)
            filepath = self.local_path / filename_safe
            
            # Evitar sobrescrever arquivo existente
            counter = 1
            original_filepath = filepath
            while filepath.exists():
                name_part = original_filepath.stem
                ext_part = original_filepath.suffix
                filepath = self.local_path / f"{name_part}_{counter}{ext_part}"
                counter += 1
            
            # Salvar arquivo
            with open(filepath, 'wb') as f:
                f.write(pdf_content)
            
            caminho = f"{self.base_path}/{filepath.name}"
            print(f"📤 PDF salvo: {filepath.name} ({len(pdf_content)} bytes)")
            return caminho
            
        except Exception as e:
            print(f"❌ Erro upload PDF: {e}")
            return None
    
    def _sanitizar_filename(self, filename: str) -> str:
        """Sanitizar nome do arquivo para evitar problemas no filesystem"""
        # Remover caracteres problemáticos
        import re
        filename_clean = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limitar tamanho
        if len(filename_clean) > 100:
            name_part = filename_clean[:90]
            ext_part = filename_clean[-10:] if '.' in filename_clean else ''
            filename_clean = name_part + ext_part
        
        return filename_clean
    
    def listar_arquivos(self) -> List[Dict]:
        """Listar arquivos salvos"""
        try:
            arquivos = []
            for arquivo in self.local_path.glob("*.pdf"):
                stat = arquivo.stat()
                arquivos.append({
                    'nome': arquivo.name,
                    'tamanho': stat.st_size,
                    'modificado': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'caminho': f"{self.base_path}/{arquivo.name}"
                })
            return arquivos
        except Exception as e:
            print(f"❌ Erro listando arquivos: {e}")
            return []


class BRKProcessadorBasico:
    """Processador principal BRK (MODULAR)"""
    
    def __init__(self):
        """Inicializar com classes refatoradas"""
        print("🔧 Inicializando BRK Processador (MODULAR)...")
        
        try:
            # AUTENTICAÇÃO MICROSOFT
            self.microsoft_auth = MicrosoftAuth()
            
            # PROCESSAMENTO DE EMAILS  
            self.email_processor = EmailProcessor(self.microsoft_auth)
            
            # COMPONENTES DE ARMAZENAMENTO
            self.database = DatabaseBRKBasico()
            self.onedrive = OneDriveBasico()
            
            print("✅ BRK Processador inicializado com sucesso")
            print("   📊 Estrutura: auth + processor + database + onedrive")
            
        except Exception as e:
            print(f"❌ Erro inicializando processador: {e}")
            raise
    
    def extrair_info_pdf(self, pdf_content: bytes, filename: str) -> Dict:
        """
        Extrair informações básicas do PDF
        
        FUTURO: Implementar OCR para extrair dados reais das faturas
        """
        return {
            'Data_Emissao': 'A extrair',
            'Nota_Fiscal': 'A extrair', 
            'Valor': 'A extrair',
            'Codigo_Cliente': 'A extrair',
            'Vencimento': 'A extrair',
            'Competencia': 'A extrair',
            'nome_arquivo': filename,
            'tamanho_bytes': len(pdf_content),
            'hash_arquivo': hashlib.sha256(pdf_content).hexdigest()
        }
    
    def processar_email(self, email: Dict) -> int:
        """Processar um email específico"""
        email_id = email.get('id', 'unknown')
        pdfs_processados = 0
        
        try:
            # Extrair PDFs usando o email processor
            pdfs = self.email_processor.extrair_pdfs_do_email(email)
            if not pdfs:
                return 0
            
            print(f"📎 Processando {len(pdfs)} PDFs...")
            
            for pdf_info in pdfs:
                try:
                    # Decodificar conteúdo do PDF
                    pdf_content = base64.b64decode(pdf_info['content_bytes'])
                    
                    # Extrair informações (futuro: OCR)
                    dados = self.extrair_info_pdf(pdf_content, pdf_info['filename'])
                    dados['email_id'] = email_id
                    
                    # Upload para OneDrive simulado
                    caminho = self.onedrive.upload_pdf(pdf_content, pdf_info['filename'])
                    if caminho:
                        dados['caminho_onedrive'] = caminho
                    
                    # Salvar no banco
                    if self.database.salvar_fatura(dados):
                        pdfs_processados += 1
                        print(f"✅ {pdf_info['filename']}")
                    
                except Exception as e:
                    print(f"❌ Erro processando PDF {pdf_info.get('filename', 'unknown')}: {e}")
            
            return pdfs_processados
            
        except Exception as e:
            print(f"❌ Erro processando email {email_id}: {e}")
            return 0
    
    def executar_ciclo_completo(self):
        """Executar ciclo completo de processamento"""
        print("🚀 INICIANDO PROCESSAMENTO BRK (MODULAR)")
        print("=" * 50)
        
        inicio = datetime.now()
        
        try:
            # 1. DIAGNÓSTICO DA PASTA BRK
            print("📊 DIAGNÓSTICO PASTA BRK:")
            diagnostico = self.email_processor.diagnosticar_pasta_brk()
            
            if diagnostico['status'] == 'sucesso':
                print(f"   📧 Total: {diagnostico['total_geral']:,}")
                print(f"   📅 24h: {diagnostico['ultimas_24h']}")
                print(f"   📆 Mês: {diagnostico['mes_atual']}")
                print()
            else:
                print("   ❌ Falha no diagnóstico")
                print(f"   Erro: {diagnostico.get('erro', 'N/A')}")
                print()
            
            # 2. BUSCAR EMAILS NOVOS
            emails = self.email_processor.buscar_emails_novos(dias_atras=1)
            
            if not emails:
                print("📧 Nenhum email novo encontrado")
                self._mostrar_estatisticas()
                return
            
            # 3. PROCESSAR EMAILS
            total_pdfs = 0
            emails_processados = 0
            emails_novos = 0
            
            for email in emails:
                email_id = email.get('id', '')
                
                # Verificar se já foi processado
                if self.database.email_ja_processado(email_id):
                    print("⏭️ Email já processado")
                    continue
                
                emails_novos += 1
                
                # Processar email
                pdfs_count = self.processar_email(email)
                
                # Marcar como processado
                self.database.marcar_email_processado(email_id, pdfs_count)
                
                emails_processados += 1
                total_pdfs += pdfs_count
            
            # 4. MOSTRAR RESULTADO
            duracao = (datetime.now() - inicio).total_seconds()
            
            print(f"\n📊 RESULTADO DO CICLO:")
            print(f"   📧 Emails encontrados: {len(emails)}")
            print(f"   🆕 Emails novos: {emails_novos}")
            print(f"   ✅ Emails processados: {emails_processados}")
            print(f"   📎 PDFs extraídos: {total_pdfs}")
            print(f"   ⏱️ Tempo: {duracao:.1f}s")
            
            # 5. ESTATÍSTICAS GERAIS
            self._mostrar_estatisticas()
            
        except Exception as e:
            print(f"❌ Erro no ciclo de processamento: {e}")
        finally:
            print("✅ CICLO CONCLUÍDO")
            print("=" * 50)
    
    def _mostrar_estatisticas(self):
        """Mostrar estatísticas do banco"""
        try:
            stats = self.database.obter_estatisticas()
            print(f"\n📈 ESTATÍSTICAS GERAIS:")
            print(f"   💾 Total faturas no banco: {stats.get('total_faturas', 0)}")
            print(f"   📧 Total emails processados: {stats.get('total_emails_processados', 0)}")
            
            # Últimas faturas
            ultimas = stats.get('ultimas_faturas', [])
            if ultimas:
                print(f"   📄 Últimas faturas:")
                for nome, data in ultimas[:3]:
                    data_fmt = data[:10] if data else 'N/A'
                    print(f"      • {nome} ({data_fmt})")
                    
        except Exception as e:
            print(f"❌ Erro obtendo estatísticas: {e}")


def executar_processamento_background():
    """Processamento em background (loop principal)"""
    print("🔄 Iniciando processamento em background...")
    
    try:
        processador = BRKProcessadorBasico()
        
        while True:
            try:
                processador.executar_ciclo_completo()
                
                # Aguardar 10 minutos antes do próximo ciclo
                print(f"⏰ Próximo ciclo em 10 minutos...")
                time.sleep(600)  # 10 minutos
                
            except KeyboardInterrupt:
                print("\n🛑 Processamento interrompido pelo usuário")
                break
            except Exception as e:
                print(f"❌ Erro no processamento background: {e}")
                print("🔄 Tentando novamente em 1 minuto...")
                time.sleep(60)  # 1 minuto antes de tentar novamente
                
    except Exception as e:
        print(f"❌ Erro fatal inicializando processador: {e}")
        print("⚠️ Processamento background interrompido")


def validar_configuracoes():
    """Validar configurações obrigatórias"""
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
        return False
    
    return True


def testar_imports_modulos():
    """Testar se os módulos refatorados estão funcionando"""
    try:
        # Testar imports
        from auth import MicrosoftAuth
        from processor import EmailProcessor
        print("✅ Imports dos módulos OK")
        
        # Testar inicialização básica
        test_auth = MicrosoftAuth()
        print("✅ MicrosoftAuth inicializado")
        
        test_processor = EmailProcessor(test_auth)
        print("✅ EmailProcessor inicializado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos imports dos módulos: {e}")
        print("⚠️ Verifique estrutura de pastas auth/ e processor/")
        return False


def main():
    """Função principal - PROCESSAMENTO PURO"""
    print("🚀 BRK MONITOR - PROCESSAMENTO AUTOMÁTICO")
    print("=" * 60)
    print("📊 ESTRUTURA: Modular (auth/ + processor/ + admin/)")
    print("🎯 FUNÇÃO: Processamento automático de emails BRK")
    print("=" * 60)
    
    # 1. VALIDAR CONFIGURAÇÕES
    if not validar_configuracoes():
        return
    
    # 2. TESTAR MÓDULOS REFATORADOS
    if not testar_imports_modulos():
        return
    
    print("🔒 Configurações validadas!")
    print("📦 Módulos carregados com sucesso!")
    
    # 3. OPÇÃO: INCLUIR SERVIDOR ADMIN
    executar_admin = os.getenv("EXECUTAR_ADMIN_SERVER", "true").lower() == "true"
    
    if executar_admin:
        print("🌐 Iniciando servidor administrativo...")
        
        try:
            from admin import AdminServer
            
            # Iniciar servidor admin em thread separada
            porta_admin = int(os.getenv('PORT', 8080))
            admin_server = AdminServer(porta=porta_admin)
            
            admin_thread = threading.Thread(target=admin_server.iniciar, daemon=True)
            admin_thread.start()
            
            print(f"✅ Servidor administrativo na porta {porta_admin}")
            
        except Exception as e:
            print(f"⚠️ Erro iniciando servidor admin: {e}")
            print("🔄 Continuando apenas com processamento...")
    
    # 4. INICIAR PROCESSAMENTO PRINCIPAL
    print("🔄 Iniciando processamento BRK...")
    
    try:
        executar_processamento_background()
    except KeyboardInterrupt:
        print("\n🛑 Sistema parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")


if __name__ == "__main__":
    main()
