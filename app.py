#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏢 APP.PY LIMPO - Sistema BRK com DatabaseBRK Integrado
📦 ARQUITETURA MODULAR: auth/ + processor/ + app.py minimalista
🔧 CADA ROTA: 3-5 linhas máximo - lógica nos módulos
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
"""

# ============================================================================
# APP.PY LIMPO - BLOCO 1/5 - IMPORTS E CONFIGURAÇÕES
# ============================================================================

import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, session, render_template_string
import logging

# Imports dos módulos (arquitetura modular)
from auth.microsoft_auth import MicrosoftAuth
from processor.email_processor import EmailProcessor
from processor.database_brk import integrar_database_emailprocessor

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

# ✅ VARIÁVEIS CORRIGIDAS - CONSISTENTES COM AUTH/MICROSOFT_AUTH.PY
# ✅ VARIÁVEIS EXATAS DO RENDER (confirmadas)
MICROSOFT_CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID')
PASTA_BRK_ID = os.getenv('PASTA_BRK_ID')
ONEDRIVE_BRK_ID = os.getenv('ONEDRIVE_BRK_ID')

# Configuração para logs no Render
os.environ['PYTHONUNBUFFERED'] = '1'

print("🚀 Sistema BRK iniciado com DatabaseBRK integrado")
print(f"   📧 Pasta emails: {PASTA_BRK_ID[:10] if PASTA_BRK_ID else 'N/A'}******")
print(f"   📁 OneDrive BRK: {ONEDRIVE_BRK_ID[:15] if ONEDRIVE_BRK_ID else 'N/A'}******")
print(f"   🗃️ DatabaseBRK: Ativo")

# ============================================================================
# APP.PY LIMPO - BLOCO 2/5 - ROTAS DE AUTENTICAÇÃO (CORRETO - MANTIDO)
# ============================================================================

@app.route('/')
def index():
    """Página inicial com status da autenticação"""
    try:
        if auth_manager.access_token:
            status_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sistema BRK - Autenticado</title>
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
                    <h1>🏢 Sistema BRK - Controle de Faturas</h1>
                    <div class="status">✅ Sistema autenticado e pronto para uso!</div>
                    
                    <div class="info">
                        <h3>📊 Funcionalidades Disponíveis:</h3>
                        <ul>
                            <li>✅ Extração completa de dados das faturas PDF</li>
                            <li>✅ Relacionamento CDC → Casa de Oração</li>
                            <li>✅ Análise de consumo com alertas automáticos</li>
                            <li>✅ Detecção inteligente de duplicatas</li>
                            <li>✅ Banco SQLite organizado no OneDrive</li>
                            <li>✅ Estrutura de pastas automatizada</li>
                        </ul>
                    </div>
                    
                    <h3>🔧 Ações Disponíveis:</h3>
                    <a href="/diagnostico-pasta" class="button">📊 Diagnóstico da Pasta</a>
                    <a href="/processar-emails-form" class="button">⚙️ Processar Emails</a>
                    <a href="/estatisticas-banco" class="button">📈 Estatísticas do Banco</a>
                    <a href="/faturas" class="button">📋 Ver Faturas</a>
                    <a href="/logout" class="button" style="background: #dc3545;">🚪 Logout</a>
                    
                    <div class="info">
                        <small>📱 Desenvolvido para Tesouraria Administrativa Mauá<br>
                        🔧 Versão com DatabaseBRK integrado - Sidney Gubitoso</small>
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
    """Inicia o processo de autenticação Microsoft"""
    try:
        auth_url = auth_manager.obter_url_autorizacao()
        logger.info("Redirecionando para autenticação Microsoft")
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return f"Erro no login: {e}", 500

@app.route('/callback')
def callback():
    """Callback da autenticação Microsoft"""
    try:
        code = request.args.get('code')
        if not code:
            return "Código de autorização não recebido", 400
        
        if auth_manager.trocar_codigo_por_token(code):
            logger.info("Autenticação Microsoft bem-sucedida")
            return redirect('/')
        else:
            return "Falha na autenticação", 400
    except Exception as e:
        logger.error(f"Erro no callback: {e}")
        return f"Erro no callback: {e}", 500

@app.route('/logout')
def logout():
    """Logout do sistema"""
    try:
        auth_manager.logout()
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
                <p>Você foi desconectado do sistema BRK com sucesso.</p>
                <a href="/login" class="button">🔑 Fazer Login Novamente</a>
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
    """Status da autenticação em JSON"""
    try:
        return jsonify({
            "autenticado": bool(auth_manager.access_token),
            "token_valido": auth_manager.verificar_token_valido() if auth_manager.access_token else False,
            "sistema": "BRK com DatabaseBRK",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erro no status: {e}")
        return jsonify({"erro": str(e)}), 500

# ============================================================================
# APP.PY LIMPO - BLOCO 3/5 - ROTAS PRINCIPAIS (REFATORADO LIMPO)
# ============================================================================

@app.route('/diagnostico-pasta', methods=['GET'])
def diagnostico_pasta():
    """Diagnóstico da pasta BRK com DatabaseBRK integrado"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        processor = EmailProcessor(auth_manager)
        resultado = processor.diagnosticar_pasta_brk()
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro no diagnóstico: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/processar-emails-novos', methods=['POST'])
def processar_emails_novos():
    """Processa emails novos com salvamento automático no DatabaseBRK"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        data = request.get_json() or {}
        processor = EmailProcessor(auth_manager)
        resultado = processor.processar_emails_completo_com_database(data.get('dias_atras', 1))
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro processando emails: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/processar-emails-form', methods=['GET'])
def processar_emails_form():
    """Formulário para processar emails com DatabaseBRK"""
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
                    <h3>🗃️ Sistema com DatabaseBRK Integrado</h3>
                    <ul>
                        <li>✅ Extração automática de dados das faturas</li>
                        <li>✅ Detecção inteligente de duplicatas</li>
                        <li>✅ Classificação: NORMAL / DUPLICATA / CUIDADO</li>
                        <li>✅ Salvamento organizado no OneDrive</li>
                        <li>✅ Banco SQLite com histórico completo</li>
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
                            html += `<p><strong>📧 Emails processados:</strong> ${data.processamento?.emails_processados || 0}</p>`;
                            html += `<p><strong>📎 PDFs extraídos:</strong> ${data.processamento?.pdfs_extraidos || 0}</p>`;
                            
                            if (data.database_brk?.integrado) {
                                html += '<h4>🗃️ DatabaseBRK:</h4>';
                                html += `<p><strong>💾 Faturas novas:</strong> ${data.database_brk.faturas_salvas || 0}</p>`;
                                html += `<p><strong>🔄 Duplicatas:</strong> ${data.database_brk.faturas_duplicatas || 0}</p>`;
                                html += `<p><strong>⚠️ Requer atenção:</strong> ${data.database_brk.faturas_cuidado || 0}</p>`;
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

@app.route('/recarregar-relacionamento', methods=['POST'])
def recarregar_relacionamento():
    """Força recarregamento do relacionamento CDC → Casa de Oração"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        processor = EmailProcessor(auth_manager)
        sucesso = processor.recarregar_relacionamento_manual(forcar=True)
        
        if sucesso:
            return jsonify({
                "status": "sucesso",
                "mensagem": "Relacionamento recarregado com sucesso",
                "total_registros": len(processor.cdc_brk_vetor),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "erro", 
                "mensagem": "Falha no recarregamento do relacionamento"
            }), 500
            
    except Exception as e:
        logger.error(f"Erro recarregando relacionamento: {e}")
        return jsonify({"erro": str(e)}), 500

# ============================================================================
# APP.PY LIMPO - BLOCO 4/5 - ROTAS DATABASEBRK (REFATORADO LIMPO)
# ============================================================================

@app.route('/estatisticas-banco', methods=['GET'])
def estatisticas_banco():
    """Estatísticas completas do DatabaseBRK"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        processor = EmailProcessor(auth_manager)
        stats = processor.obter_estatisticas_database_completas()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Erro obtendo estatísticas: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/faturas', methods=['GET'])
def listar_faturas():
    """Lista faturas do DatabaseBRK com filtros opcionais"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        processor = EmailProcessor(auth_manager)
        resultado = processor.buscar_faturas_com_filtros(request.args)
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro listando faturas: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/faturas-html', methods=['GET'])
def faturas_html():
    """Interface web para visualizar faturas"""
    try:
        if not auth_manager.access_token:
            return redirect('/login')
        
        processor = EmailProcessor(auth_manager)
        html_interface = processor.gerar_interface_faturas_html()
        return html_interface
        
    except Exception as e:
        logger.error(f"Erro na interface de faturas: {e}")
        return f"Erro: {e}", 500

@app.route('/debug-sistema', methods=['GET'])
def debug_sistema():
    """Debug completo do sistema incluindo DatabaseBRK"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        processor = EmailProcessor(auth_manager)
        debug_info = processor.diagnostico_completo_sistema()
        return jsonify(debug_info)
        
    except Exception as e:
        logger.error(f"Erro no debug: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/teste-completo', methods=['POST'])
def teste_completo():
    """Executa teste completo de todas as funcionalidades"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        processor = EmailProcessor(auth_manager)
        resultados = processor.testar_funcionalidades_completas()
        return jsonify(resultados)
        
    except Exception as e:
        logger.error(f"Erro no teste completo: {e}")
        return jsonify({"erro": str(e)}), 500

# ============================================================================
# APP.PY LIMPO - BLOCO 5/5 - UTILITÁRIOS E INICIALIZAÇÃO (CORRETO - MANTIDO)
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check para monitoramento do Render"""
    try:
        status = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "sistema": "BRK com DatabaseBRK",
            "componentes": {
                "flask": "ok",
                "auth": "ok" if auth_manager else "error",
                "database_brk": "disponivel"
            }
        }
        
        # Teste rápido de autenticação se token disponível
        if auth_manager.access_token:
            status["componentes"]["token"] = "disponivel"
            try:
                if auth_manager.verificar_token_valido():
                    status["componentes"]["token"] = "valido"
                else:
                    status["componentes"]["token"] = "expirado"
            except:
                status["componentes"]["token"] = "erro_verificacao"
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
# TRATAMENTO DE ERROS GLOBAIS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Página 404 customizada"""
    return jsonify({
        "erro": "Endpoint não encontrado",
        "sistema": "BRK com DatabaseBRK",
        "endpoints_disponiveis": [
            "/", "/login", "/logout", "/status",
            "/diagnostico-pasta", "/processar-emails-novos", "/processar-emails-form",
            "/estatisticas-banco", "/faturas", "/faturas-html",
            "/recarregar-relacionamento", "/debug-sistema", "/teste-completo", "/health"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Tratamento de erros 500"""
    logger.error(f"Erro interno: {error}")
    return jsonify({
        "erro": "Erro interno do servidor",
        "sistema": "BRK com DatabaseBRK",
        "timestamp": datetime.now().isoformat()
    }), 500

# ============================================================================
# INICIALIZAÇÃO DO APLICATIVO
# ============================================================================
def verificar_configuracao():
    """Verifica se todas as variáveis de ambiente estão configuradas"""
    variaveis_obrigatorias = ['MICROSOFT_CLIENT_ID', 'PASTA_BRK_ID']
    variaveis_opcionais = ['ONEDRIVE_BRK_ID']
    
    missing = [var for var in variaveis_obrigatorias if not os.getenv(var)]
    
    if missing:
        print(f"❌ ERRO: Variáveis de ambiente não configuradas: {', '.join(missing)}")
        print(f"   Configure estas variáveis no Render para o sistema funcionar")
        return False
    
    print(f"✅ Variáveis obrigatórias configuradas")
    
    # Verificar opcionais
    for var in variaveis_opcionais:
        if os.getenv(var):
            print(f"✅ {var} configurado (DatabaseBRK ativo)")
        else:
            print(f"⚠️ {var} não configurado (DatabaseBRK limitado)")
    
    # Confirmar PYTHONUNBUFFERED para logs
    if os.getenv('PYTHONUNBUFFERED'):
        print(f"✅ PYTHONUNBUFFERED configurado (logs Render otimizados)")
    
    return True

def inicializar_aplicacao():
    """Inicialização da aplicação"""
    print(f"\n🚀 INICIANDO SISTEMA BRK COM DATABASEBRK")
    print(f"="*60)
    
    # Verificar configuração
    if not verificar_configuracao():
        print(f"❌ Falha na verificação de configuração")
        return False
    
    # Configurar auth manager (já inicializado no topo)
    print(f"✅ Microsoft Auth configurado")
    
    print(f"✅ Sistema BRK inicializado com sucesso!")
    print(f"   🗃️ DatabaseBRK: Integrado")
    print(f"   📊 SQLite: Automático")
    print(f"   📁 OneDrive: Organizado")
    print(f"   🔍 Duplicatas: Detecção ativa")
    print(f"="*60)
    
    return True

# ============================================================================
# PONTO DE ENTRADA
# ============================================================================

if __name__ == '__main__':
    # Inicializar aplicação
    if inicializar_aplicacao():
        # Executar aplicação
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_ENV') == 'development'
        
        print(f"🌐 Iniciando servidor na porta {port}")
        print(f"🔧 Debug mode: {debug}")
        print(f"📱 Acesse: https://seu-app.onrender.com")
        
        app.run(host='0.0.0.0', port=port, debug=debug)
    else:
        print(f"❌ Falha na inicialização - servidor não iniciado")
        exit(1)

# ============================================================================
# 🎉 APP.PY LIMPO FINALIZADO!
# 
# ARQUITETURA MODULAR ALCANÇADA:
# ✅ auth/ → Apenas autenticação Microsoft
# ✅ processor/ → Toda inteligência do sistema  
# ✅ app.py → Apenas rotas Flask minimalistas
# 
# CADA ROTA: 3-5 linhas máximo
# LÓGICA: 100% nos módulos processor/
# VARIÁVEIS: Consistentes (MICROSOFT_*)
# 
# STATUS: ✅ PRONTO PARA DEPLOY
# ============================================================================
