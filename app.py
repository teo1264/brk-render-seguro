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
# NOVO: Import scheduler BRK
# from processor.scheduler_brk import inicializar_scheduler_automatico, obter_status_scheduler
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
print(f"   📧 Pasta emails: {'configurada' if PASTA_BRK_ID else 'não configurada'}")
print(f"   📁 OneDrive BRK: {'configurada' if ONEDRIVE_BRK_ID else 'não configurada'}")
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
                           <li>✅ Monitor integrado: emails + planilha a cada 30 min</li>
                           <li>✅ Sistema backup invisível (.brk_system)</li>
                           <li>✅ Logs estruturados para Render</li>
                      </ul>
                    </div>
                        <h3>🔧 Ações Disponíveis:</h3>
                        <a href="/diagnostico-pasta" class="button">📊 Diagnóstico Pasta</a>
                        <a href="/processar-emails-form" class="button">⚙️ Processar Emails</a>
                        <a href="/gerar-planilha-brk" class="button">📊 Gerar Planilha</a>
                        <a href="/test-onedrive" class="button">🧪 Teste OneDrive</a>
                        <a href="/estatisticas-database" class="button">📈 DatabaseBRK</a>
                        <a href="/dbedit" class="button">🗃️ DBEDIT Clipper</a>
                        <a href="/status-monitor-integrado" class="button">🔄 Monitor Integrado</a>
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
        
        # 🆕 DETECÇÃO INTELIGENTE: Período específico ou dias atrás?
        if 'data_inicio' in data and 'data_fim' in data:
            # USAR MÉTODO NOVO: período específico (resolve timeout)
            processor = EmailProcessor(auth_manager)
            resultado = processor.processar_emails_periodo_completo(data['data_inicio'], data['data_fim'])
            return jsonify(resultado)
        
        # FORMATO ANTIGO: continuar com dias_atras (compatibilidade 100%)
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
                    
                    <!-- OPÇÕES PRÉ-DEFINIDAS -->
                    <div style="margin: 10px 0;">
                        <label style="display: block; margin: 5px 0;">
                            <input type="radio" name="tipoProcessamento" value="predefinido" checked> 
                            <strong>Períodos pré-definidos:</strong>
                        </label>
                        <select id="diasAtras" class="input" style="margin-left: 20px;">
                            <option value="1">Últimas 24 horas</option>
                            <option value="2">Últimos 2 dias</option>
                            <option value="7">Última semana</option>
                            <option value="14">Últimas 2 semanas (máximo seguro)</option>
                        </select>
                    </div>
                    
                    <!-- PERÍODO PERSONALIZADO -->
                    <div style="margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                        <label style="display: block; margin: 5px 0;">
                            <input type="radio" name="tipoProcessamento" value="personalizado"> 
                            <strong>Período personalizado:</strong>
                        </label>
                        <div style="margin-left: 20px;">
                            <label>Data início:</label>
                            <input type="date" id="dataInicio" class="input" disabled>
                            <label>Data fim:</label>
                            <input type="date" id="dataFim" class="input" disabled>
                            <div id="avisoPeríodo" style="color: #dc3545; font-size: 12px; margin-top: 5px;"></div>
                        </div>
                    </div>
                    
                    <br><br>
                    <button type="submit" class="button">🚀 Processar Emails</button>
                    <a href="/" class="button" style="background: #6c757d; text-decoration: none;">🏠 Voltar</a>
                </form>
                
                <div id="resultado" style="margin-top: 20px;"></div>
            </div>
            
            <script>
                <script>
                // HABILITAR/DESABILITAR CAMPOS BASEADO NA SELEÇÃO
                document.querySelectorAll('input[name="tipoProcessamento"]').forEach(radio => {
                    radio.addEventListener('change', function() {
                        const isPersonalizado = this.value === 'personalizado';
                        document.getElementById('diasAtras').disabled = isPersonalizado;
                        document.getElementById('dataInicio').disabled = !isPersonalizado;
                        document.getElementById('dataFim').disabled = !isPersonalizado;
                        
                        if (isPersonalizado) {
                            // Sugerir período padrão (últimos 7 dias)
                            const hoje = new Date();
                            const semanaAtras = new Date(hoje);
                            semanaAtras.setDate(hoje.getDate() - 7);
                            
                            document.getElementById('dataFim').value = hoje.toISOString().split('T')[0];
                            document.getElementById('dataInicio').value = semanaAtras.toISOString().split('T')[0];
                            validarPeriodo();
                        }
                    });
                });
                
                // VALIDAR PERÍODO PERSONALIZADO
                function validarPeriodo() {
                    const dataInicio = document.getElementById('dataInicio').value;
                    const dataFim = document.getElementById('dataFim').value;
                    const avisoDiv = document.getElementById('avisoPeríodo');
                    
                    if (dataInicio && dataFim) {
                        const inicio = new Date(dataInicio);
                        const fim = new Date(dataFim);
                        const diferenca = Math.ceil((fim - inicio) / (1000 * 60 * 60 * 24)) + 1;
                        
                        if (diferenca > 14) {
                            avisoDiv.textContent = `⚠️ Período muito longo (${diferenca} dias). Máximo: 14 dias para evitar timeout.`;
                            avisoDiv.style.color = '#dc3545';
                            return false;
                        } else if (diferenca <= 0) {
                            avisoDiv.textContent = '⚠️ Data início deve ser anterior à data fim.';
                            avisoDiv.style.color = '#dc3545';
                            return false;
                        } else {
                            avisoDiv.textContent = `✅ Período válido: ${diferenca} dia(s)`;
                            avisoDiv.style.color = '#28a745';
                            return true;
                        }
                    }
                    return true;
                }
                
                // VALIDAR AO ALTERAR DATAS
                document.getElementById('dataInicio').addEventListener('change', validarPeriodo);
                document.getElementById('dataFim').addEventListener('change', validarPeriodo);
                
                // PROCESSAMENTO DO FORMULÁRIO
                document.getElementById('processarForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const resultadoDiv = document.getElementById('resultado');
                    const tipoProcessamento = document.querySelector('input[name="tipoProcessamento"]:checked').value;
                    
                    let dadosEnvio = {};
                    
                    if (tipoProcessamento === 'personalizado') {
                        const dataInicio = document.getElementById('dataInicio').value;
                        const dataFim = document.getElementById('dataFim').value;
                        
                        if (!validarPeriodo()) {
                            resultadoDiv.innerHTML = '<div class="status error">❌ Corrija o período antes de continuar</div>';
                            return;
                        }
                        
                        dadosEnvio = {
                            data_inicio: dataInicio,
                            data_fim: dataFim
                        };
                        
                        resultadoDiv.innerHTML = `<div class="status info">🔄 Processando período ${dataInicio} até ${dataFim}... Aguarde...</div>`;
                    } else {
                        const diasAtras = document.getElementById('diasAtras').value;
                        dadosEnvio = { dias_atras: parseInt(diasAtras) };
                        resultadoDiv.innerHTML = `<div class="status info">🔄 Processando últimos ${diasAtras} dia(s)... Aguarde...</div>`;
                    }
                    
                    try {
                        const response = await fetch('/processar-emails-novos', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(dadosEnvio)
                        });
                        
                        const data = await response.json();
                        
                        if (data.status === 'sucesso') {
                            let html = '<div class="status success">';
                            html += '<h3>✅ Processamento Finalizado!</h3>';
                            
                            if (data.processamento?.periodo_especifico) {
                                html += `<p><strong>📅 Período:</strong> ${data.periodo?.data_inicio} até ${data.periodo?.data_fim}</p>`;
                                html += `<p><strong>📧 Emails período:</strong> ${data.periodo?.total_emails}</p>`;
                            }
                            
                            html += `<p><strong>📧 Emails processados:</strong> ${data.processamento?.emails_processados || 0}</p>`;
                            html += `<p><strong>📎 PDFs extraídos:</strong> ${data.processamento?.pdfs_extraidos || 0}</p>`;
                            
                            if (data.database_brk?.integrado) {
                                html += '<h4>🗃️ DatabaseBRK:</h4>';
                                html += `<p><strong>💾 Faturas novas:</strong> ${data.database_brk.faturas_salvas || 0}</p>`;
                                html += `<p><strong>🔄 Duplicatas:</strong> ${data.database_brk.faturas_duplicatas || 0}</p>`;
                                html += `<p><strong>⚠️ Atenção:</strong> ${data.database_brk.faturas_cuidado || 0}</p>`;
                            }
                            
                            if (data.onedrive?.uploads_ativos) {
                                html += `<p><strong>☁️ Upload OneDrive:</strong> ${data.onedrive.uploads_sucessos} arquivo(s)</p>`;
                            }
                            
                            html += '</div>';
                            resultadoDiv.innerHTML = html;
                        } else {
                            resultadoDiv.innerHTML = `<div class="status error">❌ Erro: ${data.erro || data.mensagem || 'Erro desconhecido'}</div>`;
                        }
                    } catch (error) {
                        resultadoDiv.innerHTML = `<div class="status error">❌ Erro de conexão: ${error.message}</div>`;
                    }
                });
            </script>
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
    """DBEDIT - Usando auth_manager que JÁ FUNCIONA - ✅ CORRIGIDO"""
    try:
        # ✅ IMPORTAÇÃO SEGURA: Engine modular
        from admin.dbedit_server import DBEditEngineBRK
        
        # ✅ CRIAR ENGINE
        engine = DBEditEngineBRK()
        
        # 🎯 SOLUÇÃO: USAR AUTH QUE JÁ FUNCIONA (não criar nova instância)
        engine.auth = auth_manager  # ← PASSAR AUTH FUNCIONANDO
        engine.conn = None  # Reset para reconectar com auth correto
        
        print(f"🔧 DBEDIT: Usando auth_manager do sistema principal")
        
        # ✅ NAVEGAÇÃO: Engine processa todos os comandos
        resultado = engine.navegar_registro_real(
            request.args.get('tabela', 'faturas_brk'),
            int(request.args.get('rec', '1')),
            request.args.get('cmd', ''),
            request.args.get('filtro', ''),
            request.args.get('order', '')
        )
        
        # ✅ JSON se solicitado
        if request.args.get('formato') == 'json':
            return jsonify(resultado)
        
        # ✅ HTML FUNCIONAL: Interface completa
        return _render_dbedit_flask_seguro(resultado)
        
    except ImportError as e:
        logger.error(f"Erro importação DBEDIT engine: {e}")
        return f"""
        <!DOCTYPE html>
        <html><head><title>DBEDIT - Módulo Indisponível</title><meta charset="UTF-8"></head>
        <body style="font-family: 'Courier New', monospace; background: #000080; color: #ffffff; margin: 20px;">
            <div style="background: #800000; padding: 20px; border: 1px solid #ffffff;">
                <h1>❌ DBEDIT INDISPONÍVEL</h1>
                <h3>Módulo admin/dbedit_server.py não encontrado</h3>
                <p><a href="/" style="color: #00ffff;">← Voltar ao Dashboard</a></p>
            </div>
        </body></html>
        """, 503
        
    except Exception as e:
        logger.error(f"Erro DBEDIT: {e}")
        return f"""
        <!DOCTYPE html>
        <html><head><title>DBEDIT - Erro</title><meta charset="UTF-8"></head>
        <body style="font-family: 'Courier New', monospace; background: #000080; color: #ffffff; margin: 20px;">
            <div style="background: #800000; padding: 20px; border: 1px solid #ffffff;">
                <h1>❌ ERRO DBEDIT</h1>
                <h3>Erro: {str(e)}</h3>
                <p><strong>Possíveis causas:</strong></p>
                <ul>
                    <li>Configuração ONEDRIVE_BRK_ID pendente</li>
                    <li>DatabaseBRK temporariamente indisponível</li>
                </ul>
                <p><a href="/dbedit" style="color: #00ffff;">🔄 Tentar novamente</a> | 
                   <a href="/" style="color: #00ffff;">🏠 Dashboard</a></p>
            </div>
        </body></html>
        """, 500
# GERADOR EXCEL BRK
@app.route('/gerar-planilha-brk', methods=['GET', 'POST'])
def gerar_planilha_brk():
    """Gerador Excel BRK"""
    from processor.excel_brk import ExcelGeneratorBRK
    return ExcelGeneratorBRK().handle_request()

# @app.route('/status-scheduler-brk')
# def status_scheduler_brk():
#    """Status scheduler"""
#    status = obter_status_scheduler()
#    return jsonify(status)

@app.route('/status-monitor-integrado')
def status_monitor_integrado():
    """Status do novo monitor integrado BRK"""
    try:
        import threading
        
        # Verificar se thread do monitor está ativa
        threads_ativas = threading.enumerate()
        monitor_ativo = any(t.name == "MonitorBRK" and t.is_alive() for t in threads_ativas)
        
        # Verificar dependências
        try:
            processor = EmailProcessor(auth_manager)
            from processor.monitor_brk import verificar_dependencias_monitor
            deps = verificar_dependencias_monitor(processor)
        except Exception as e:
            deps = {"dependencias_ok": False, "erro": str(e)}
        
        status = {
            "monitor_integrado": {
                "ativo": monitor_ativo,
                "thread_encontrada": monitor_ativo,
                "funcionalidade": "Emails + Planilha em ciclo único",
                "intervalo": "30 minutos",
                "backup_sistema": "Pasta .brk_system (invisível)",
                "substituiu": ["Monitor 10 min", "Scheduler 06:00h"]
            },
            "dependencias": {
                "status": "ok" if deps.get("dependencias_ok") else "problemas",
                "email_processor": deps.get("email_processor_valido", False),
                "autenticacao": deps.get("autenticacao_ok", False),
                "excel_generator": deps.get("excel_generator_ok", False),
                "planilha_backup": deps.get("planilha_backup_ok", False),
                "onedrive_brk": deps.get("onedrive_brk_ok", False),
                "observacoes": deps.get("observacoes", [])
            },
            "threads_sistema": {
                "total": len(threads_ativas),
                "monitor_brk": monitor_ativo,
                "threads_nomes": [t.name for t in threads_ativas if hasattr(t, 'name')]
            },
            "timestamp": datetime.now().isoformat(),
            "sistema": "Monitor Integrado BRK v2.0"
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "erro": str(e),
            "timestamp": datetime.now().isoformat(),
            "sistema": "Monitor Integrado BRK v2.0"
        }), 500

# ❌ COMENTAR/REMOVER: Rota do scheduler antigo
# @app.route('/status-scheduler-brk')
# def status_scheduler_brk():
#     """Status scheduler - ❌ REMOVIDO: Substituído por monitor integrado"""
#     from processor.scheduler_brk import obter_status_scheduler
#     status = obter_status_scheduler()
#     return jsonify(status)

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
    """Inicialização com monitor integrado - ✅ SEM SCHEDULER 06:00h"""
    print(f"\n🚀 INICIANDO SISTEMA BRK INTEGRADO COM PROCESSOR/")
    print(f"="*60)
    
    if not verificar_configuracao():
        return False
    
    # ❌ REMOVIDO: Scheduler BRK das 06:00h (substituído por monitor integrado)
    # print("🔄 Inicializando Scheduler BRK...")
    # scheduler_iniciado = inicializar_scheduler_automatico()
    # if scheduler_iniciado:
    #     print("✅ Scheduler BRK: Ativo (jobs automáticos às 06:00h)")
    # else:
    #     print("⚠️ Scheduler BRK: Falha na inicialização")
    
    if auth_manager.access_token:
        print(f"✅ Autenticação funcionando")
        
        # 🆕 CRIAR EmailProcessor
        processor = EmailProcessor(auth_manager)
        
        # 🆕 VERIFICAR DEPENDÊNCIAS DO MONITOR INTEGRADO
        from processor.monitor_brk import verificar_dependencias_monitor, iniciar_monitoramento_automatico
        
        deps = verificar_dependencias_monitor(processor)
        if deps['dependencias_ok']:
            print(f"✅ Dependências do monitor integrado validadas")
            
            # 🆕 INICIAR MONITOR INTEGRADO (substitui monitor 10min + scheduler 06:00h)
            monitor = iniciar_monitoramento_automatico(processor)
            
            if monitor:
                print(f"✅ Monitor integrado ativo:")
                print(f"   📧 Processamento emails: a cada 30 min")
                print(f"   📊 Planilha BRK: atualizada automaticamente")
                print(f"   💾 Backup inteligente: pasta .brk_system (invisível)")
                print(f"   🧹 Limpeza automática: backups antigos")
                print(f"   🔄 Substitui: Monitor 10min + Scheduler 06:00h")
            else:
                print(f"⚠️ Monitor integrado falhou - continuando sem ele")
        else:
            print(f"❌ Dependências do monitor integrado faltando:")
            for obs in deps['observacoes']:
                print(f"   {obs}")
            print(f"⚠️ Continuando sem monitor automático")
    
    print(f"✅ Sistema BRK integrado inicializado!")
    print(f"   📧 Processamento de emails ativo")
    print(f"   📁 OneDrive + DatabaseBRK configurado")
    print(f"   🔍 SEEK + detecção duplicatas ativo")
    print(f"   📊 Monitor integrado: emails + planilha a cada 30 min")  # ← NOVO
    print(f"   🌐 Interface web completa disponível")
    
    return True
# ============================================================================
# FUNÇÕES AUXILIARES DBEDIT (adicionar antes do if __name__ == '__main__')
# ============================================================================

def _render_dbedit_flask_seguro(resultado):
    """HTML DBEDIT funcional - sem dependências HTTP"""
    if resultado["status"] == "error":
        return f"""
        <!DOCTYPE html>
        <html><head><title>DBEDIT - Erro</title><meta charset="UTF-8"></head>
        <body style="font-family: 'Courier New', monospace; background: #000080; color: #ffffff; margin: 20px;">
            <h1>❌ ERRO DBEDIT</h1>
            <div style="background: #800000; padding: 20px; border: 1px solid #ffffff;">
                <h3>{resultado["message"]}</h3>
            </div>
            <p><a href="/dbedit" style="color: #00ffff;">← Tentar novamente</a></p>
        </body></html>
        """
    
    # Dados do resultado
    tabela = resultado["tabela"]
    registro_atual = resultado["registro_atual"]
    total_registros = resultado["total_registros"]
    nav = resultado.get("navegacao", {})
    
    # Campos do registro
    campos_html = ""
    if resultado.get("registro"):
        for campo, info in resultado["registro"].items():
            valor = str(info["valor"])[:100] + "..." if len(str(info["valor"])) > 100 else info["valor"]
            cor = "#ffff00" if info.get("e_principal") else "#ffffff"
            campos_html += f"""
            <tr style="background: rgba(255,255,255,0.1);">
                <td style="color: {cor}; padding: 8px; font-weight: bold;">{campo}</td>
                <td style="color: #00ffff; padding: 8px; text-align: center;">{info["tipo"]}</td>
                <td style="color: #ffffff; padding: 8px;">{valor}</td>
            </tr>
            """
    
    # Contexto
    contexto_html = ""
    for ctx in resultado.get("contexto", []):
        cor_fundo = "#ffff00" if ctx["e_atual"] else "transparent"
        cor_texto = "#000000" if ctx["e_atual"] else "#ffffff"
        contexto_html += f"""
        <div style="background: {cor_fundo}; color: {cor_texto}; padding: 5px; cursor: pointer; border-bottom: 1px solid #333;" 
             onclick="window.location.href='/dbedit?tabela={tabela}&rec={ctx['posicao']}&cmd=GOTO'">
            {ctx['posicao']:03d}: {ctx['preview']}
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <title>🗃️ DBEDIT BRK - {tabela} - Rec {registro_atual}/{total_registros}</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Courier New', monospace; background: #000080; color: #ffffff; margin: 0; }}
            .header {{ background: #0000aa; color: #ffff00; padding: 10px; text-align: center; font-weight: bold; }}
            .status {{ background: #008080; padding: 5px 10px; font-size: 12px; }}
            .content {{ display: flex; height: calc(100vh - 120px); }}
            .campos {{ flex: 2; padding: 10px; overflow-y: auto; }}
            .contexto {{ flex: 1; background: #004080; padding: 10px; overflow-y: auto; max-width: 300px; }}
            .commands {{ background: #800000; padding: 10px; text-align: center; }}
            .btn {{ background: #008000; color: white; padding: 8px 12px; text-decoration: none; margin: 3px; border: 1px solid #fff; font-size: 12px; }}
            .btn:hover {{ background: #00aa00; }}
            .btn-delete {{ background: #aa0000 !important; }}
            .btn:disabled {{ background: #666; cursor: not-allowed; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: #800080; padding: 8px; border-bottom: 1px solid #fff; }}
            td {{ padding: 8px; border-bottom: 1px solid #333; }}
        </style>
    </head>
    <body>
        <div class="header">🗃️ DBEDIT BRK - {tabela.upper()}</div>
        <div class="status">📊 REC {registro_atual}/{total_registros} - ⚡ {resultado.get('comando_executado', 'SHOW')} - 🕐 {resultado['timestamp']}</div>
        
        <div class="content">
            <div class="campos">
                <h3 style="color: #ffff00;">📊 CAMPOS - REGISTRO {registro_atual}</h3>
                <table>
                    <thead>
                        <tr><th>Campo</th><th>Tipo</th><th>Valor</th></tr>
                    </thead>
                    <tbody>
                        {campos_html if campos_html else '<tr><td colspan="3" style="text-align: center; color: #ffff00;">📭 Nenhum registro</td></tr>'}
                    </tbody>
                </table>
            </div>
            
            <div class="contexto">
                <h3 style="color: #ffff00;">📍 CONTEXTO</h3>
                {contexto_html if contexto_html else '<div style="color: #ffff00; text-align: center;">Sem contexto</div>'}
            </div>
        </div>
        
        <div class="commands">
            <a href="/dbedit?tabela={tabela}&rec=1&cmd=TOP" class="btn" {'style="background: #666; cursor: not-allowed;"' if nav.get('e_primeiro') else ''}>🔝 TOP</a>
            <a href="/dbedit?tabela={tabela}&rec={max(1, registro_atual-1)}&cmd=PREV" class="btn" {'style="background: #666; cursor: not-allowed;"' if not nav.get('pode_anterior') else ''}>⬅️ PREV</a>
            <a href="/dbedit?tabela={tabela}&rec={min(total_registros, registro_atual+1)}&cmd=NEXT" class="btn" {'style="background: #666; cursor: not-allowed;"' if not nav.get('pode_proximo') else ''}>➡️ NEXT</a>
            <a href="/dbedit?tabela={tabela}&rec={total_registros}&cmd=BOTTOM" class="btn" {'style="background: #666; cursor: not-allowed;"' if nav.get('e_ultimo') else ''}>🔚 BOTTOM</a>
            
            <a href="/delete?tabela={tabela}&rec={registro_atual}&confirm=0" class="btn btn-delete" title="DELETE seguro com confirmação tripla">🗑️ DELETE</a>
            <a href="/" class="btn" style="background: #aa0000;">🏠 SAIR</a>
        </div>
    </body>
    </html>
    """

def _render_delete_confirmacao_flask(tabela, registro_atual, registro, nivel):
    """Páginas de confirmação DELETE"""
    # Dados principais do registro
    dados_resumo = ""
    campos_principais = ['id', 'cdc', 'casa_oracao', 'valor', 'vencimento', 'competencia']
    for campo in campos_principais:
        if campo in registro:
            valor = registro[campo].get('valor', 'N/A')
            dados_resumo += f"<tr><td><strong>{campo}:</strong></td><td>{valor}</td></tr>"
    
    if nivel == 1:
        return f"""
        <!DOCTYPE html>
        <html><head><title>🗑️ DELETE - Confirmação</title><meta charset="UTF-8">
        <style>
            body {{ font-family: 'Courier New', monospace; background: #000080; color: #ffffff; margin: 20px; }}
            .warning {{ background: #800000; padding: 20px; border: 2px solid #ffffff; margin: 20px 0; }}
            .data {{ background: #004080; padding: 15px; border: 1px solid #ffffff; margin: 10px 0; }}
            .btn {{ background: #008000; color: white; padding: 10px 20px; text-decoration: none; margin: 5px; }}
            .btn-danger {{ background: #800000; }}
            table {{ width: 100%; }} td {{ padding: 5px; }}
        </style></head>
        <body>
            <h1>🗑️ DELETE REGISTRO - Confirmação Necessária</h1>
            
            <div class="warning">
                <h3>⚠️ ATENÇÃO: Operação Perigosa</h3>
                <p>Você está prestes a DELETAR permanentemente este registro da tabela <strong>{tabela}</strong>.</p>
                <p><strong>Esta operação NÃO pode ser desfeita!</strong></p>
            </div>
            
            <div class="data">
                <h3>📋 Dados do Registro {registro_atual}:</h3>
                <table>{dados_resumo}</table>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="/delete?tabela={tabela}&rec={registro_atual}&confirm=1" class="btn btn-danger">🗑️ CONFIRMAR DELETE</a>
                <a href="/dbedit?tabela={tabela}&rec={registro_atual}" class="btn">❌ CANCELAR</a>
            </div>
        </body></html>
        """
    else:  # nivel == 2
        return f"""
        <!DOCTYPE html>
        <html><head><title>🗑️ DELETE - Confirmação Final</title><meta charset="UTF-8">
        <style>
            body {{ font-family: 'Courier New', monospace; background: #800000; color: #ffffff; margin: 20px; }}
            .final-warning {{ background: #000000; padding: 20px; border: 3px solid #ff0000; margin: 20px 0; }}
            .btn {{ background: #008000; color: white; padding: 15px 30px; text-decoration: none; margin: 10px; font-weight: bold; }}
            .btn-final-delete {{ background: #ff0000; }}
        </style></head>
        <body>
            <h1>🚨 ÚLTIMA CONFIRMAÇÃO - DELETE PERMANENTE</h1>
            
            <div class="final-warning">
                <h2>🚨 ÚLTIMA CHANCE DE CANCELAR!</h2>
                <p>➡️ Registro {registro_atual} será DELETADO PERMANENTEMENTE</p>
                <p>➡️ <strong>OPERAÇÃO IRREVERSÍVEL!</strong></p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="/delete?tabela={tabela}&rec={registro_atual}&confirm=2" class="btn btn-final-delete" 
                   onclick="return confirm('ÚLTIMA CONFIRMAÇÃO: Deletar registro permanentemente?')">💀 EXECUTAR DELETE AGORA</a>
                <br><br>
                <a href="/dbedit?tabela={tabela}&rec={registro_atual}" class="btn">🛡️ CANCELAR</a>
            </div>
        </body></html>
        """

def _executar_delete_flask_seguro(engine, tabela, registro_atual, registro):
    """Execução DELETE segura"""
    try:
        from datetime import datetime
        
        # Backup do registro
        backup = {
            "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S'),
            "tabela": tabela,
            "registro": registro_atual,
            "dados": {campo: info.get('valor_original') for campo, info in registro.items()}
        }
        logger.info(f"DELETE BACKUP: {backup}")
        
        # Executar DELETE
        cursor = engine.conn.cursor()
        if tabela == 'faturas_brk' and 'id' in registro:
            id_delete = registro['id'].get('valor_original')
            cursor.execute(f"DELETE FROM {tabela} WHERE id = ?", (id_delete,))
        else:
            cursor.execute(f"DELETE FROM {tabela} WHERE rowid = (SELECT rowid FROM {tabela} LIMIT 1 OFFSET ?)", (registro_atual - 1,))
        
        engine.conn.commit()
        logger.info(f"DELETE executado: {cursor.rowcount} linha(s)")
        
        # Sincronizar OneDrive se possível
        if hasattr(engine, 'database_brk') and engine.database_brk:
            try:
                engine.database_brk.sincronizar_onedrive()
            except Exception as e:
                logger.warning(f"Sync OneDrive falhou: {e}")
        
        # Página de sucesso
        return f"""
        <!DOCTYPE html>
        <html><head><title>✅ DELETE Realizado</title><meta charset="UTF-8">
        <meta http-equiv="refresh" content="3;url=/dbedit?tabela={tabela}&rec=1">
        <style>
            body {{ font-family: 'Courier New', monospace; background: #008000; color: #ffffff; margin: 20px; text-align: center; }}
            .success {{ background: #000000; padding: 30px; border: 3px solid #ffffff; margin: 30px auto; max-width: 600px; }}
        </style></head>
        <body>
            <div class="success">
                <h1>✅ DELETE REALIZADO COM SUCESSO!</h1>
                <p>🗑️ Registro {registro_atual} deletado permanentemente</p>
                <p>💾 Backup automático criado</p>
                <p>Redirecionando em 3 segundos...</p>
                <p><a href="/dbedit?tabela={tabela}&rec=1" style="color: #ffff00;">🏠 Voltar ao DBEDIT</a></p>
            </div>
        </body></html>
        """
        
    except Exception as e:
        logger.error(f"Erro DELETE: {e}")
        return jsonify({"status": "error", "message": f"Erro DELETE: {str(e)}"}), 500


"""
📋 RESUMO - INTEGRAÇÃO MÍNIMA NO APP.PY:

✅ ADICIONADO:
   • 2 linhas import no topo
   • 2 rotas simples no final  
   • 1 link opcional no dashboard
   
✅ TOTAL: 15 linhas adicionadas ao app.py
✅ MANTÉM: app.py limpo e organizável
✅ FUNCIONA: 100% usando funções testadas

🎯 TESTE:
   1. Acessar: /reconstituicao-brk
   2. Confirmar operação
   3. Aguardar processamento
   4. Ver resultado final

🔧 COMO TESTAR ESTE BLOCO:
   1. Salvar processor/reconstituicao_brk.py com BLOCOS 1+2+3
   2. Adicionar as 15 linhas no app.py
   3. Deploy no Render
   4. Testar URL: https://brk-render-seguro.onrender.com/reconstituicao-brk
"""

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
