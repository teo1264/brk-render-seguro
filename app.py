#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏢 APP.PY ORIGINAL SIMPLES - Sistema BRK funcionando
📦 FUNCIONALIDADE: emails → extração → OneDrive → logs
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
"""

import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, session, render_template_string
import logging

# Imports dos módulos (que já funcionam)
from auth.microsoft_auth import MicrosoftAuth
from processor.email_processor import EmailProcessor

# Configuração do Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Configuração de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Instância global do gerenciador de auth
auth_manager = MicrosoftAuth()

# ✅ VARIÁVEIS ORIGINAIS (que funcionavam)
MICROSOFT_CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID')
PASTA_BRK_ID = os.getenv('PASTA_BRK_ID')
ONEDRIVE_BRK_ID = os.getenv('ONEDRIVE_BRK_ID')

# Configuração para logs no Render
os.environ['PYTHONUNBUFFERED'] = '1'

print("🚀 Sistema BRK simples iniciado")
print(f"   📧 Pasta emails: {PASTA_BRK_ID[:10] if PASTA_BRK_ID else 'N/A'}******")
print(f"   📁 OneDrive BRK: {ONEDRIVE_BRK_ID[:15] if ONEDRIVE_BRK_ID else 'N/A'}******")

# ============================================================================
# ROTAS BÁSICAS (que funcionavam)
# ============================================================================

@app.route('/')
def index():
    """Dashboard simples"""
    try:
        if auth_manager.access_token:
            status_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sistema BRK - Dashboard</title>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial; margin: 40px; background: #f5f5f5; }
                    .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .status { color: #28a745; font-weight: bold; font-size: 18px; }
                    .button { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px 5px; display: inline-block; }
                    .button:hover { background: #0056b3; }
                    .info { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🏢 Sistema BRK - Processamento de Faturas</h1>
                    <div class="status">✅ Sistema autenticado e funcionando!</div>
                    
                    <div class="info">
                        <h3>📊 Sistema Original:</h3>
                        <ul>
                            <li>✅ Leitura automática de emails BRK</li>
                            <li>✅ Extração de dados das faturas PDF</li>
                            <li>✅ Relacionamento CDC → Casa de Oração</li>
                            <li>✅ Salvamento organizado no OneDrive</li>
                            <li>✅ Logs estruturados no Render</li>
                        </ul>
                    </div>
                    
                    <h3>🔧 Ações Disponíveis:</h3>
                    <a href="/diagnostico-pasta" class="button">📊 Diagnóstico Pasta</a>
                    <a href="/processar-emails-form" class="button">⚙️ Processar Emails</a>
                    <a href="/status" class="button">📋 Status JSON</a>
                    <a href="/logout" class="button" style="background: #dc3545;">🚪 Logout</a>
                    
                    <div class="info">
                        <small>📱 Sistema simples e eficiente<br>
                        🔧 Sidney Gubitoso - Tesouraria Administrativa Mauá</small>
                    </div>
                </div>
            </body>
            </html>
            """
            return status_html
        else:
            return redirect('/login')
    except Exception as e:
        logger.error(f"Erro na página inicial: {e}")
        return f"Erro: {e}", 500

@app.route('/login')
def login():
    """Login simples"""
    try:
        login_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sistema BRK - Login</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial; margin: 40px; background: #f5f5f5; text-align: center; }
                .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .info { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔑 Sistema BRK - Login</h1>
                <div class="info">
                    <p>Sistema autenticado via token persistente.</p>
                    <p>Processamento automático ativo.</p>
                </div>
                <a href="/" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🏠 Dashboard</a>
            </div>
        </body>
        </html>
        """
        return login_html
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return f"Erro no login: {e}", 500

@app.route('/logout')
def logout():
    """Logout simples"""
    try:
        session.clear()
        logger.info("Logout realizado")
        
        logout_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sistema BRK - Logout</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial; margin: 40px; background: #f5f5f5; text-align: center; }
                .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .button { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚪 Logout Realizado</h1>
                <p>Sessão encerrada. Sistema continua funcionando.</p>
                <a href="/" class="button">🏠 Voltar ao Dashboard</a>
            </div>
        </body>
        </html>
        """
        return logout_html
    except Exception as e:
        logger.error(f"Erro no logout: {e}")
        return f"Erro no logout: {e}", 500

@app.route('/status')
def status():
    """Status JSON simples"""
    try:
        return jsonify({
            "autenticado": bool(auth_manager.access_token),
            "sistema": "BRK Processamento Simples",
            "timestamp": datetime.now().isoformat(),
            "funcionalidade": "emails → extração → OneDrive"
        })
    except Exception as e:
        logger.error(f"Erro no status: {e}")
        return jsonify({"erro": str(e)}), 500

# ============================================================================
# FUNCIONALIDADES PRINCIPAIS (originais)
# ============================================================================

@app.route('/diagnostico-pasta', methods=['GET'])
def diagnostico_pasta():
    """Diagnóstico da pasta BRK (original)"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        processor = EmailProcessor(auth_manager)
        
        # Usar método que EXISTE e funcionava
        resultado = processor.diagnosticar_pasta_brk()
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro no diagnóstico: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/processar-emails-novos', methods=['POST'])
def processar_emails_novos():
    """Processamento original: emails → extração → OneDrive"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        data = request.get_json() or {}
        dias_atras = data.get('dias_atras', 1)
        
        processor = EmailProcessor(auth_manager)
        
        print(f"🔄 Processando emails dos últimos {dias_atras} dia(s)")
        
        # 1. Buscar emails (método original)
        emails = processor.buscar_emails_novos(dias_atras)
        
        if not emails:
            return jsonify({
                "status": "sucesso",
                "mensagem": f"Nenhum email encontrado nos últimos {dias_atras} dia(s)",
                "emails_processados": 0,
                "pdfs_extraidos": 0
            })
        
        # 2. Processar emails (funcionalidade original)
        emails_processados = 0
        pdfs_extraidos = 0
        
        for email in emails:
            try:
                # Extrair PDFs (método que sempre funcionou)
                pdfs_dados = processor.extrair_pdfs_do_email(email)
                
                if pdfs_dados:
                    pdfs_extraidos += len(pdfs_dados)
                    print(f"📎 {len(pdfs_dados)} PDF(s) extraído(s) e dados salvos")
                    
                    # Log consolidado (método existente)
                    processor.log_consolidado_email(email, pdfs_dados)
                
                emails_processados += 1
                
            except Exception as e:
                print(f"❌ Erro processando email: {e}")
                continue
        
        print(f"✅ Processamento concluído: {emails_processados} emails, {pdfs_extraidos} PDFs")
        
        return jsonify({
            "status": "sucesso",
            "mensagem": f"Processamento concluído: {emails_processados} emails, {pdfs_extraidos} PDFs",
            "emails_processados": emails_processados,
            "pdfs_extraidos": pdfs_extraidos,
            "periodo_dias": dias_atras,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro processando emails: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/processar-emails-form', methods=['GET'])
def processar_emails_form():
    """Formulário original para processar emails"""
    try:
        if not auth_manager.access_token:
            return redirect('/login')
        
        form_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sistema BRK - Processar Emails</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial; margin: 40px; background: #f5f5f5; }
                .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 10px 5px; }
                .button:hover { background: #0056b3; }
                .input { padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin: 5px; }
                .status { padding: 15px; margin: 15px 0; border-radius: 5px; }
                .info { background: #e9ecef; }
                .success { background: #d4edda; color: #155724; }
                .error { background: #f8d7da; color: #721c24; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚙️ Processar Emails BRK</h1>
                
                <div class="status info">
                    <h3>📧 Sistema Original</h3>
                    <p>Processamento simples e eficiente:</p>
                    <ul>
                        <li>✅ Lê emails da pasta BRK</li>
                        <li>✅ Extrai dados das faturas PDF</li>
                        <li>✅ Relaciona CDC → Casa de Oração</li>
                        <li>✅ Salva organizadamente no OneDrive</li>
                        <li>✅ Gera logs estruturados</li>
                    </ul>
                </div>
                
                <form id="processarForm">
                    <h3>📅 Período para Processar:</h3>
                    <select id="diasAtras" class="input">
                        <option value="1">Últimas 24 horas</option>
                        <option value="2">Últimos 2 dias</option>
                        <option value="7">Última semana</option>
                        <option value="30">Último mês</option>
                    </select>
                    
                    <br><br>
                    <button type="submit" class="button">🚀 Processar Emails</button>
                    <a href="/" class="button" style="background: #6c757d; text-decoration: none;">🏠 Voltar</a>
                </form>
                
                <div id="resultado" style="margin-top: 20px;"></div>
            </div>
            
            <script>
                document.getElementById('processarForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const diasAtras = document.getElementById('diasAtras').value;
                    const resultadoDiv = document.getElementById('resultado');
                    
                    resultadoDiv.innerHTML = '<div class="status info">🔄 Processando emails... Aguarde...</div>';
                    
                    try {
                        const response = await fetch('/processar-emails-novos', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ dias_atras: parseInt(diasAtras) })
                        });
                        
                        const data = await response.json();
                        
                        if (data.status === 'sucesso') {
                            let html = '<div class="status success">';
                            html += '<h3>✅ Processamento Concluído!</h3>';
                            html += `<p><strong>📧 Emails processados:</strong> ${data.emails_processados || 0}</p>`;
                            html += `<p><strong>📎 PDFs extraídos:</strong> ${data.pdfs_extraidos || 0}</p>`;
                            html += `<p><strong>💾 OneDrive:</strong> Dados salvos e organizados</p>`;
                            html += '</div>';
                            resultadoDiv.innerHTML = html;
                        } else {
                            resultadoDiv.innerHTML = `<div class="status error">❌ Erro: ${data.erro || 'Erro desconhecido'}</div>`;
                        }
                    } catch (error) {
                        resultadoDiv.innerHTML = `<div class="status error">❌ Erro de conexão: ${error.message}</div>`;
                    }
                });
            </script>
        </body>
        </html>
        """
        return form_html
        
    except Exception as e:
        logger.error(f"Erro no formulário: {e}")
        return f"Erro: {e}", 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check original"""
    try:
        status = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "sistema": "BRK Simples",
            "componentes": {
                "flask": "ok",
                "auth": "ok" if auth_manager else "error",
                "processamento": "ativo"
            }
        }
        
        # Teste rápido de autenticação
        if auth_manager.access_token:
            status["componentes"]["token"] = "disponivel"
        else:
            status["componentes"]["token"] = "nao_disponivel"
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "erro": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# ============================================================================
# TRATAMENTO DE ERROS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Página 404"""
    return jsonify({
        "erro": "Endpoint não encontrado",
        "sistema": "BRK Simples",
        "endpoints_disponiveis": [
            "/", "/login", "/logout", "/status",
            "/diagnostico-pasta", "/processar-emails-novos", 
            "/processar-emails-form", "/health"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Tratamento de erros 500"""
    logger.error(f"Erro interno: {error}")
    return jsonify({
        "erro": "Erro interno do servidor",
        "sistema": "BRK Simples",
        "timestamp": datetime.now().isoformat()
    }), 500

# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

def verificar_configuracao():
    """Verifica configurações básicas"""
    variaveis_obrigatorias = ['MICROSOFT_CLIENT_ID', 'PASTA_BRK_ID']
    
    missing = [var for var in variaveis_obrigatorias if not os.getenv(var)]
    
    if missing:
        print(f"❌ ERRO: Variáveis não configuradas: {', '.join(missing)}")
        return False
    
    print(f"✅ Configuração básica OK")
    return True

def inicializar_aplicacao():
    """Inicialização simples"""
    print(f"\n🚀 INICIANDO SISTEMA BRK SIMPLES")
    print(f"="*50)
    
    if not verificar_configuracao():
        return False
    
    if auth_manager.access_token:
        print(f"✅ Autenticação funcionando")
    else:
        print(f"⚠️ Token não encontrado - sistema aguardando autenticação")
    
    print(f"✅ Sistema BRK simples inicializado!")
    print(f"   📧 Processamento de emails ativo")
    print(f"   📁 Salvamento OneDrive configurado")
    print(f"   🌐 Interface web disponível")
    print(f"="*50)
    
    return True

# ============================================================================
# PONTO DE ENTRADA
# ============================================================================

if __name__ == '__main__':
    if inicializar_aplicacao():
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_ENV') == 'development'
        
        print(f"🌐 Servidor iniciando na porta {port}")
        print(f"📱 Sistema simples funcionando!")
        
        app.run(host='0.0.0.0', port=port, debug=debug)
    else:
        print(f"❌ Falha na inicialização")
        exit(1)
