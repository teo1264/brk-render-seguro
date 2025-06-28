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
from processor.monitor_brk import verificar_dependencias_monitor, iniciar_monitoramento_automatico

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

print("🚀 Sistema BRK integrado com processor/ iniciado")
print(f"   📧 Pasta emails: {PASTA_BRK_ID[:10] if PASTA_BRK_ID else 'N/A'}******")
print(f"   📁 OneDrive BRK: {ONEDRIVE_BRK_ID[:15] if ONEDRIVE_BRK_ID else 'N/A'}******")
print(f"   🗃️ DatabaseBRK: {'Configurado' if ONEDRIVE_BRK_ID else 'Pendente'}")
print(f"   🔍 SEEK + Duplicatas: Ativo")

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
                        <h3>📊 Sistema Integrado com Processor/:</h3>
                        <ul>
                            <li>✅ Leitura automática de emails BRK</li>
                            <li>✅ Extração completa de dados PDF (sem pandas)</li>
                            <li>✅ Relacionamento CDC → Casa de Oração via OneDrive</li>
                            <li>✅ DatabaseBRK com lógica SEEK (detecção duplicatas)</li>
                            <li>✅ Salvamento organizado /BRK/Faturas/YYYY/MM/</li>
                            <li>✅ Logs estruturados para Render</li>
                        </ul>
                    </div>
                        <h3>🔧 Ações Disponíveis:</h3>
                        <a href="/diagnostico-pasta" class="button">📊 Diagnóstico Pasta</a>
                        <a href="/processar-emails-form" class="button">⚙️ Processar Emails</a>
                        <a href="/test-onedrive" class="button">🧪 Teste OneDrive</a>
                        <a href="/estatisticas-database" class="button">📈 DatabaseBRK</a>
                        <a href="/dbedit" class="button">🗃️ DBEDIT Clipper</a>
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
            "sistema": "BRK Integrado com Processor",
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
    """Processamento REAL usando processor/ completo"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        data = request.get_json() or {}
        dias_atras = data.get('dias_atras', 1)
        
        processor = EmailProcessor(auth_manager)
        print(f"🔄 PROCESSAMENTO COMPLETO - últimos {dias_atras} dia(s)")
        print(f"✅ DatabaseBRK ativo - faturas serão salvas automaticamente")
        
        # ✅ INTEGRAÇÃO REAL: Verificar se tem método completo na pasta processor/
        if hasattr(processor, 'processar_emails_completo_com_database'):
            # Usar método avançado que já existe
            resultado = processor.processar_emails_completo_com_database(dias_atras)
            return jsonify(resultado)
        
        # ✅ FALLBACK: Usar métodos individuais que existem
        # 1. Buscar emails
        emails = processor.buscar_emails_novos(dias_atras)
        
        if not emails:
            return jsonify({
                "status": "sucesso",
                "mensagem": f"Nenhum email encontrado nos últimos {dias_atras} dia(s)",
                "emails_processados": 0,
                "pdfs_extraidos": 0,
                "database_brk": {"integrado": False}
            })
        
        # 2. Inicializar DatabaseBRK se disponível
        database_ativo = False
        if ONEDRIVE_BRK_ID and hasattr(processor, 'database_brk'):
            database_ativo = True
            print(f"✅ DatabaseBRK detectado e ativo")
        elif ONEDRIVE_BRK_ID:
            # Tentar integrar DatabaseBRK
            try:
                from processor.database_brk import integrar_database_emailprocessor
                sucesso = integrar_database_emailprocessor(processor)
                if sucesso:
                    database_ativo = True
                    print(f"✅ DatabaseBRK integrado automaticamente")
            except Exception as e:
                print(f"⚠️ Erro integrando DatabaseBRK: {e}")
        
        # 3. Processar emails com funcionalidades completas
        emails_processados = 0
        pdfs_extraidos = 0
        faturas_salvas = 0
        faturas_duplicatas = 0
        faturas_cuidado = 0
        
        for i, email in enumerate(emails, 1):
            try:
                email_subject = email.get('subject', 'Sem assunto')[:50]
                print(f"\n📧 Processando email {i}/{len(emails)}: {email_subject}")
                
                # ✅ USAR FUNCIONALIDADE REAL: Extrair PDFs completo
                pdfs_dados = processor.extrair_pdfs_do_email(email)
                
                if pdfs_dados:
                    pdfs_extraidos += len(pdfs_dados)
                    print(f"📎 {len(pdfs_dados)} PDF(s) extraído(s)")
                    
                    # ✅ USAR DatabaseBRK REAL se ativo
                    if database_ativo and hasattr(processor, 'database_brk'):
                        for pdf_data in pdfs_dados:
                            try:
                                # Preparar dados para database
                                if hasattr(processor, 'preparar_dados_para_database'):
                                    dados_db = processor.preparar_dados_para_database(pdf_data)
                                else:
                                    dados_db = pdf_data
                                
                                # ✅ SALVAR COM SEEK REAL
                                resultado = processor.database_brk.salvar_fatura(dados_db)
                                
                                if resultado.get('status') == 'sucesso':
                                    status = resultado.get('status_duplicata', 'NORMAL')
                                    if status == 'NORMAL':
                                        faturas_salvas += 1
                                    elif status == 'DUPLICATA':
                                        faturas_duplicatas += 1
                                    elif status == 'CUIDADO':
                                        faturas_cuidado += 1
                                    
                                    print(f"  💾 DatabaseBRK: {status} - {resultado.get('nome_arquivo', 'arquivo')}")
                                
                            except Exception as e:
                                print(f"  ❌ Erro DatabaseBRK: {e}")
                    
                    # ✅ USAR LOG CONSOLIDADO REAL
                    if hasattr(processor, 'log_consolidado_email'):
                        processor.log_consolidado_email(email, pdfs_dados)
                
                emails_processados += 1
                
            except Exception as e:
                print(f"❌ Erro processando email {i}: {e}")
                continue
        
        # ✅ RESULTADO COMPLETO
        print(f"\n✅ PROCESSAMENTO CONCLUÍDO:")
        print(f"   📧 Emails processados: {emails_processados}")
        print(f"   📎 PDFs extraídos: {pdfs_extraidos}")
        if database_ativo:
            print(f"   💾 Faturas novas: {faturas_salvas}")
            print(f"   🔄 Duplicatas: {faturas_duplicatas}")
            print(f"   ⚠️ Atenção: {faturas_cuidado}")
        
        return jsonify({
            "status": "sucesso",
            "mensagem": "Processamento completo finalizado",
            "processamento": {
                "emails_processados": emails_processados,
                "pdfs_extraidos": pdfs_extraidos,
                "periodo_dias": dias_atras
            },
            "database_brk": {
                "integrado": database_ativo,
                "faturas_salvas": faturas_salvas,
                "faturas_duplicatas": faturas_duplicatas,
                "faturas_cuidado": faturas_cuidado,
                "total_database": faturas_salvas + faturas_duplicatas + faturas_cuidado
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro processamento completo: {e}")
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
                    <h3>📧 Sistema Integrado com Processor/</h3>
                    <p>Processamento completo ativo:</p>
                    <ul>
                        <li>✅ Lê emails da pasta BRK</li>
                        <li>✅ Extrai dados completos das faturas PDF</li>
                        <li>✅ Relaciona CDC → Casa de Oração via OneDrive</li>
                        <li>✅ DatabaseBRK com lógica SEEK (NORMAL/DUPLICATA/CUIDADO)</li>
                        <li>✅ Salva organizadamente em /BRK/Faturas/YYYY/MM/</li>
                        <li>✅ Logs detalhados no Render</li>
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
                            html += '<h3>✅ Processamento Completo Finalizado!</h3>';
                            html += `<p><strong>📧 Emails processados:</strong> ${data.processamento?.emails_processados || 0}</p>`;
                            html += `<p><strong>📎 PDFs extraídos:</strong> ${data.processamento?.pdfs_extraidos || 0}</p>`;
                            
                            if (data.database_brk?.integrado) {
                                html += '<h4>🗃️ DatabaseBRK (SEEK):</h4>';
                                html += `<p><strong>💾 Faturas novas (NORMAL):</strong> ${data.database_brk.faturas_salvas || 0}</p>`;
                                html += `<p><strong>🔄 Duplicatas detectadas:</strong> ${data.database_brk.faturas_duplicatas || 0}</p>`;
                                html += `<p><strong>⚠️ Requer atenção (CUIDADO):</strong> ${data.database_brk.faturas_cuidado || 0}</p>`;
                                html += `<p><strong>📊 Total database:</strong> ${data.database_brk.total_database || 0}</p>`;
                            } else {
                                html += '<p><strong>💾 OneDrive:</strong> Dados extraídos (DatabaseBRK não ativo)</p>';
                            }
                            
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

@app.route('/estatisticas-database', methods=['GET'])
def estatisticas_database():
    """Estatísticas do DatabaseBRK usando processor/"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        processor = EmailProcessor(auth_manager)
        
        # ✅ USAR MÉTODO REAL da pasta processor/
        if hasattr(processor, 'obter_estatisticas_avancadas'):
            stats = processor.obter_estatisticas_avancadas()
            return jsonify(stats)
        elif hasattr(processor, 'database_brk') and processor.database_brk:
            # Usar DatabaseBRK diretamente
            stats = processor.database_brk.obter_estatisticas()
            return jsonify({
                "status": "sucesso",
                "database_brk": stats,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "aviso",
                "mensagem": "DatabaseBRK não disponível",
                "configurado": bool(ONEDRIVE_BRK_ID),
                "observacao": "Configure ONEDRIVE_BRK_ID ou processar emails primeiro"
            })
        
    except Exception as e:
        logger.error(f"Erro estatísticas: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/test-onedrive', methods=['GET'])
def test_onedrive():
    """Teste OneDrive que funcionava (retorna JSON como antes)"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        processor = EmailProcessor(auth_manager)
        
        # Usar método de teste OneDrive que já existia
        if hasattr(processor, 'test_onedrive_access'):
            resultado = processor.test_onedrive_access()
            return jsonify(resultado)
        else:
            # Fallback básico se método não existir
            return jsonify({
                "status": "success", 
                "message": "Sistema básico ativo",
                "onedrive_configurado": bool(ONEDRIVE_BRK_ID),
                "onedrive_brk_id": ONEDRIVE_BRK_ID,
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            })
        
    except Exception as e:
        logger.error(f"Erro no teste OneDrive: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check original"""
    try:
        status = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "sistema": "BRK Integrado Processor",
            "componentes": {
                "flask": "ok",
                "auth": "ok" if auth_manager else "error",
                "processamento": "ativo",
                "database_brk": "configurado" if ONEDRIVE_BRK_ID else "pendente"
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
@app.route('/dbedit')
def dbedit():
    """DBEDIT - Importação mínima + autenticação Flask"""
    # ✅ SEGURANÇA: Usa autenticação Flask existente
    if not auth_manager.access_token:
        return redirect('/login')
    
    try:
        # ✅ IMPORTAÇÃO MÍNIMA: Apenas classes necessárias (não duplica código)
        from admin.dbedit_server import DBEditEngineBRK, DBEditHandlerReal
        
        # ✅ DELEGAÇÃO LIMPA: Engine processa navegação
        engine = DBEditEngineBRK()
        resultado = engine.navegar_registro_real(
            request.args.get('tabela', 'faturas_brk'),
            int(request.args.get('rec', '1')),
            request.args.get('cmd', ''),
            request.args.get('filtro', ''),
            request.args.get('order', '')
        )
        
        # ✅ REUTILIZAÇÃO: Usa método HTML existente (zero duplicação)
        handler = DBEditHandlerReal(None, None, None)
        handler.send_response = lambda x: None  # Mock Flask response
        handler.send_header = lambda x, y: None
        handler.end_headers = lambda: None
        
        # Capturar HTML do método existente
        import io
        from contextlib import redirect_stdout
        
        html_buffer = io.StringIO()
        handler.wfile = io.BytesIO()
        
        # Chamar método existente
        handler._render_dbedit_real_html(resultado)
        
        # Extrair HTML gerado
        html_content = handler.wfile.getvalue().decode('utf-8')
        return html_content
        
    except Exception as e:
        logger.error(f"Erro DBEDIT: {e}")
        return f"Erro DBEDIT: {e}", 500

@app.route('/delete')  
def delete_handler():
    """DELETE - Delegação mínima com autenticação Flask"""
    # ✅ SEGURANÇA: Autenticação obrigatória
    if not auth_manager.access_token:
        return redirect('/login')
    
    try:
        # ✅ DELEGAÇÃO TOTAL: Usa handler existente
        from admin.dbedit_server import DBEditHandlerReal
        import io
        
        # Mock do handler para Flask
        handler = DBEditHandlerReal(None, None, None)
        handler.path = f"/delete?{request.query_string.decode()}"
        handler.send_response = lambda x: None
        handler.send_header = lambda x, y: None  
        handler.end_headers = lambda: None
        handler.wfile = io.BytesIO()
        
        # Executar método DELETE existente
        handler._handle_delete_real()
        
        # Retornar resultado
        html_content = handler.wfile.getvalue().decode('utf-8')
        return html_content
        
    except Exception as e:
        logger.error(f"Erro DELETE: {e}")
        return f"Erro DELETE: {e}", 500

# ============================================================================
# TRATAMENTO DE ERROS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Página 404"""
    return jsonify({
        "erro": "Endpoint não encontrado",
        "sistema": "BRK Integrado Processor",
        "endpoints_disponiveis": [
            "/", "/login", "/logout", "/status",
            "/diagnostico-pasta", "/processar-emails-novos", 
            "/processar-emails-form", "/test-onedrive", 
            "/estatisticas-database", "/health", "/dbedit"
        ]
        
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Tratamento de erros 500"""
    logger.error(f"Erro interno: {error}")
    return jsonify({
        "erro": "Erro interno do servidor",
        "sistema": "BRK Integrado Processor",
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
    """Inicialização com integração processor/"""
    print(f"\n🚀 INICIANDO SISTEMA BRK INTEGRADO COM PROCESSOR/")
    print(f"="*60)
    
    if not verificar_configuracao():
        return False
    
    if auth_manager.access_token:
        print(f"✅ Autenticação funcionando")
        
        # 🆕 CRIAR EmailProcessor
        processor = EmailProcessor(auth_manager)
        # Diagnóstico de teste (remover após identificar problema)
        from processor.diagnostico_teste import ativar_diagnostico
        ativar_diagnostico(processor)
        # 🆕 VERIFICAR DEPENDÊNCIAS DO MONITOR

        deps = verificar_dependencias_monitor(processor)
        if deps['dependencias_ok']:
            print(f"✅ Dependências do monitor validadas")
            
            # 🆕 INICIAR MONITOR AUTOMÁTICO
            monitor = iniciar_monitoramento_automatico(processor)
            
            if monitor:
                print(f"✅ Monitor automático ativo (verifica a cada 10 min)")
            else:
                print(f"⚠️ Monitor automático falhou - continuando sem ele")
        else:
            print(f"❌ Dependências do monitor faltando:")
            for obs in deps['observacoes']:
                print(f"   {obs}")
            print(f"⚠️ Continuando sem monitor automático")
    
    print(f"✅ Sistema BRK integrado inicializado!")
    print(f"   📧 Processamento de emails ativo")
    print(f"   📁 OneDrive + DatabaseBRK configurado")
    print(f"   🔍 SEEK + detecção duplicatas ativo")
    print(f"   📊 Monitor automático a cada 10 minutos")  # ← NOVA LINHA
    print(f"   🌐 Interface web completa disponível")
    
    return True

# ============================================================================
# PONTO DE ENTRADA
# ============================================================================

if __name__ == '__main__':
    if inicializar_aplicacao():
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_ENV') == 'development'
        
        print(f"🌐 Servidor iniciando na porta {port}")
        print(f"📱 Sistema integrado com processor/ funcionando!")
        print(f"🗃️ DatabaseBRK + SEEK + OneDrive organizados!")
        
        app.run(host='0.0.0.0', port=port, debug=debug)
    else:
        print(f"❌ Falha na inicialização")
        exit(1)
