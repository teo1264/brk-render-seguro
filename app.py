# ============================================================================
# APP.PY COMPLETO - NOVO COM DATABASEBRK INTEGRADO
# BLOCO 1/5 - IMPORTS E CONFIGURAÇÕES
# ============================================================================

import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, session, render_template_string
import logging

# Imports do sistema existente
from auth.microsoft_auth import MicrosoftAuth
from processor.email_processor import EmailProcessor

# ✅ NOVO: Import da DatabaseBRK
from processor.database_brk import DatabaseBRK, integrar_database_emailprocessor

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

# Configurações de ambiente
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
PASTA_BRK_ID = os.getenv('PASTA_BRK_ID')
ONEDRIVE_BRK_ID = os.getenv('ONEDRIVE_BRK_ID')  # Para DatabaseBRK

print("🚀 Sistema BRK iniciado com DatabaseBRK integrado")
print(f"   📧 Pasta emails: {PASTA_BRK_ID[:10] if PASTA_BRK_ID else 'N/A'}******")
print(f"   📁 OneDrive BRK: {ONEDRIVE_BRK_ID[:15] if ONEDRIVE_BRK_ID else 'N/A'}******")
print(f"   🗃️ DatabaseBRK: Ativo")
# ============================================================================
# APP.PY COMPLETO - NOVO COM DATABASEBRK INTEGRADO  
# BLOCO 2/5 - ROTAS DE AUTENTICAÇÃO (Mantido igual)
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
# APP.PY COMPLETO - NOVO COM DATABASEBRK INTEGRADO
# BLOCO 3/5 - ROTAS PRINCIPAIS COM DATABASEBRK INTEGRADO
# ============================================================================

@app.route('/diagnostico-pasta', methods=['GET'])
def diagnostico_pasta():
    """Diagnóstico da pasta BRK com DatabaseBRK integrado"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        # Criar EmailProcessor
        processor = EmailProcessor(auth_manager)
        
        # ✅ NOVA INTEGRAÇÃO: DatabaseBRK
        database_integrado = integrar_database_emailprocessor(processor)
        if database_integrado:
            print("✅ DatabaseBRK integrado ao diagnóstico")
        else:
            print("⚠️ DatabaseBRK não integrado - continuando diagnóstico básico")
        
        # Executar diagnóstico
        resultado = processor.diagnosticar_pasta_brk()
        
        # ✅ EXPANDIR resultado com info do banco (se disponível)
        if hasattr(processor, 'database_brk'):
            try:
                stats_banco = processor.database_brk.obter_estatisticas()
                resultado['database_brk'] = {
                    'integrado': True,
                    'estatisticas': stats_banco
                }
            except Exception as e:
                resultado['database_brk'] = {
                    'integrado': False,
                    'erro': str(e)
                }
        else:
            resultado['database_brk'] = {'integrado': False}
        
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
        
        # Obter parâmetros
        data = request.get_json() or {}
        dias_atras = data.get('dias_atras', 1)
        
        # Criar EmailProcessor
        processor = EmailProcessor(auth_manager)
        
        # ✅ INTEGRAÇÃO DatabaseBRK
        database_integrado = integrar_database_emailprocessor(processor)
        
        print(f"🔄 Processando emails dos últimos {dias_atras} dia(s)")
        if database_integrado:
            print("✅ DatabaseBRK ativo - faturas serão salvas automaticamente")
        else:
            print("⚠️ DatabaseBRK não disponível - apenas extração")
        
        # Buscar emails
        emails = processor.buscar_emails_novos(dias_atras)
        
        # Contadores
        pdfs_processados = []
        faturas_salvas = []
        faturas_duplicatas = []
        faturas_cuidado = []
        
        # Processar cada email
        for email in emails:
            print(f"📧 Processando email: {email.get('subject', 'Sem assunto')[:50]}...")
            
            # Extrair PDFs do email
            pdfs_do_email = processor.extrair_pdfs_do_email(email)
            pdfs_processados.extend(pdfs_do_email)
            
            # ✅ SALVAR NO DATABASEBRK (se disponível)
            if hasattr(processor, 'database_brk'):
                for pdf_data in pdfs_do_email:
                    if pdf_data.get('dados_extraidos_ok'):
                        try:
                            # Preparar dados para o banco (método já existe no EmailProcessor)
                            dados_para_banco = processor.preparar_dados_para_database(pdf_data)
                            
                            # Salvar fatura com lógica SEEK
                            resultado_save = processor.database_brk.salvar_fatura(dados_para_banco)
                            
                            if resultado_save['status'] == 'sucesso':
                                fatura_info = {
                                    'nome_arquivo': pdf_data.get('filename'),
                                    'nome_arquivo_padronizado': resultado_save.get('nome_arquivo'),
                                    'status_duplicata': resultado_save['status_duplicata'],
                                    'id_banco': resultado_save['id_salvo'],
                                    'cdc': pdf_data.get('Codigo_Cliente'),
                                    'casa_oracao': pdf_data.get('Casa de Oração'),
                                    'valor': pdf_data.get('Valor'),
                                    'observacao': dados_para_banco.get('observacao', '')
                                }
                                
                                # Classificar por tipo
                                if resultado_save['status_duplicata'] == 'DUPLICATA':
                                    faturas_duplicatas.append(fatura_info)
                                elif resultado_save['status_duplicata'] == 'CUIDADO':
                                    faturas_cuidado.append(fatura_info)
                                else:
                                    faturas_salvas.append(fatura_info)
                                
                                print(f"✅ Fatura salva: {pdf_data.get('filename')} → Status: {resultado_save['status_duplicata']}")
                            else:
                                print(f"❌ Erro salvando fatura {pdf_data.get('filename')}: {resultado_save['mensagem']}")
                                
                        except Exception as e:
                            print(f"❌ Erro processando fatura {pdf_data.get('filename')}: {e}")
                            logger.error(f"Erro salvando fatura: {e}")
            
            # Log consolidado do email processado
            if hasattr(processor, 'log_consolidado_email'):
                processor.log_consolidado_email(email, pdfs_do_email)
        
        # ✅ RESPOSTA EXPANDIDA com dados do DatabaseBRK
        resposta = {
            "status": "sucesso",
            "timestamp": datetime.now().isoformat(),
            "processamento": {
                "emails_processados": len(emails),
                "pdfs_extraidos": len(pdfs_processados),
                "dias_analisados": dias_atras
            },
            "database_brk": {
                "integrado": database_integrado,
                "faturas_salvas": len(faturas_salvas),
                "faturas_duplicatas": len(faturas_duplicatas),
                "faturas_cuidado": len(faturas_cuidado),
                "total_processadas": len(faturas_salvas) + len(faturas_duplicatas) + len(faturas_cuidado)
            },
            "detalhes": {
                "faturas_novas": faturas_salvas,
                "faturas_duplicatas": faturas_duplicatas,
                "faturas_cuidado": faturas_cuidado,
                "pdfs_detalhados": pdfs_processados
            }
        }
        
        # Log resumo
        print(f"\n📊 RESUMO DO PROCESSAMENTO:")
        print(f"   📧 Emails: {len(emails)}")
        print(f"   📎 PDFs: {len(pdfs_processados)}")
        if database_integrado:
            print(f"   💾 Faturas salvas: {len(faturas_salvas)}")
            print(f"   🔄 Duplicatas: {len(faturas_duplicatas)}")
            print(f"   ⚠️ Cuidado: {len(faturas_cuidado)}")
        
        return jsonify(resposta)
        
    except Exception as e:
        logger.error(f"Erro processando emails: {e}")
        return jsonify({
            "status": "erro",
            "erro": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

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
                .warning { background: #fff3cd; color: #856404; }
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
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                dias_atras: parseInt(diasAtras)
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (data.status === 'sucesso') {
                            let html = '<div class="status success">';
                            html += '<h3>✅ Processamento Concluído!</h3>';
                            html += `<p><strong>📧 Emails processados:</strong> ${data.processamento.emails_processados}</p>`;
                            html += `<p><strong>📎 PDFs extraídos:</strong> ${data.processamento.pdfs_extraidos}</p>`;
                            
                            if (data.database_brk.integrado) {
                                html += '<h4>🗃️ DatabaseBRK:</h4>';
                                html += `<p><strong>💾 Faturas novas:</strong> ${data.database_brk.faturas_salvas}</p>`;
                                html += `<p><strong>🔄 Duplicatas:</strong> ${data.database_brk.faturas_duplicatas}</p>`;
                                html += `<p><strong>⚠️ Requer atenção:</strong> ${data.database_brk.faturas_cuidado}</p>`;
                            }
                            
                            html += '</div>';
                            resultadoDiv.innerHTML = html;
                        } else {
                            resultadoDiv.innerHTML = `<div class="status error">❌ Erro: ${data.erro}</div>`;
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

# ============================================================================
# APP.PY COMPLETO - NOVO COM DATABASEBRK INTEGRADO
# BLOCO 4/5 - ROTAS ESPECÍFICAS DA DATABASEBRK
# ============================================================================

@app.route('/estatisticas-banco', methods=['GET'])
def estatisticas_banco():
    """Estatísticas completas do DatabaseBRK"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        # Criar EmailProcessor e integrar DatabaseBRK
        processor = EmailProcessor(auth_manager)
        
        if not integrar_database_emailprocessor(processor):
            return jsonify({"erro": "DatabaseBRK não disponível"}), 500
        
        # Obter estatísticas
        stats = processor.database_brk.obter_estatisticas()
        
        # Expandir com informações adicionais
        stats['sistema'] = {
            'onedrive_brk_configurado': bool(processor.onedrive_brk_id),
            'relacionamento_ativo': processor.relacionamento_carregado,
            'total_relacionamentos': len(processor.cdc_brk_vetor)
        }
        
        stats['timestamp'] = datetime.now().isoformat()
        
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
        
        # Parâmetros de consulta
        status_filter = request.args.get('status')  # NORMAL, DUPLICATA, CUIDADO
        casa_filter = request.args.get('casa')
        mes_filter = request.args.get('mes')
        limite = int(request.args.get('limite', 50))
        
        # Criar EmailProcessor e integrar DatabaseBRK
        processor = EmailProcessor(auth_manager)
        
        if not integrar_database_emailprocessor(processor):
            return jsonify({"erro": "DatabaseBRK não disponível"}), 500
        
        # Buscar faturas (implementar filtros conforme necessário)
        faturas_raw = processor.database_brk.buscar_faturas()
        
        # Converter para formato JSON amigável
        faturas_json = []
        colunas = [
            'id', 'data_processamento', 'status_duplicata', 'observacao',
            'email_id', 'nome_arquivo_original', 'nome_arquivo', 'hash_arquivo',
            'tamanho_bytes', 'caminho_onedrive', 'cdc', 'nota_fiscal',
            'casa_oracao', 'data_emissao', 'vencimento', 'competencia', 'valor',
            'medido_real', 'faturado', 'media_6m', 'porcentagem_consumo',
            'alerta_consumo', 'dados_extraidos_ok', 'relacionamento_usado'
        ]
        
        for fatura in faturas_raw:
            fatura_dict = dict(zip(colunas, fatura))
            
            # Aplicar filtros
            if status_filter and fatura_dict['status_duplicata'] != status_filter:
                continue
            if casa_filter and casa_filter.lower() not in (fatura_dict['casa_oracao'] or '').lower():
                continue
            if mes_filter and mes_filter not in (fatura_dict['competencia'] or ''):
                continue
            
            # Formatar para JSON
            faturas_json.append({
                'id': fatura_dict['id'],
                'data_processamento': fatura_dict['data_processamento'],
                'status_duplicata': fatura_dict['status_duplicata'],
                'observacao': fatura_dict['observacao'],
                'cdc': fatura_dict['cdc'],
                'casa_oracao': fatura_dict['casa_oracao'],
                'valor': fatura_dict['valor'],
                'vencimento': fatura_dict['vencimento'],
                'competencia': fatura_dict['competencia'],
                'nota_fiscal': fatura_dict['nota_fiscal'],
                'nome_arquivo': fatura_dict['nome_arquivo'],
                'nome_arquivo_original': fatura_dict['nome_arquivo_original'],
                'alerta_consumo': fatura_dict['alerta_consumo'],
                'medido_real': fatura_dict['medido_real'],
                'media_6m': fatura_dict['media_6m']
            })
            
            # Aplicar limite
            if len(faturas_json) >= limite:
                break
        
        return jsonify({
            'total_encontradas': len(faturas_json),
            'limite_aplicado': limite,
            'filtros': {
                'status': status_filter,
                'casa': casa_filter,
                'mes': mes_filter
            },
            'faturas': faturas_json
        })
        
    except Exception as e:
        logger.error(f"Erro listando faturas: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/faturas-html', methods=['GET'])
def faturas_html():
    """Interface web para visualizar faturas"""
    try:
        if not auth_manager.access_token:
            return redirect('/login')
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sistema BRK - Faturas Salvas</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial; margin: 20px; background: #f5f5f5; }
                .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .filtros { background: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                .filtros input, .filtros select { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 3px; }
                .button { background: #007bff; color: white; padding: 8px 15px; border: none; border-radius: 3px; cursor: pointer; margin: 5px; }
                .button:hover { background: #0056b3; }
                table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f8f9fa; font-weight: bold; }
                .status-normal { color: #28a745; font-weight: bold; }
                .status-duplicata { color: #6c757d; font-style: italic; }
                .status-cuidado { color: #dc3545; font-weight: bold; }
                .alerta-alto { background: #f8d7da; color: #721c24; }
                .alerta-normal { background: #d4edda; color: #155724; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📋 Faturas BRK - DatabaseBRK</h1>
                
                <div class="filtros">
                    <h3>🔍 Filtros:</h3>
                    <select id="statusFilter">
                        <option value="">Todos os status</option>
                        <option value="NORMAL">✅ NORMAL</option>
                        <option value="DUPLICATA">🔄 DUPLICATA</option>
                        <option value="CUIDADO">⚠️ CUIDADO</option>
                    </select>
                    
                    <input type="text" id="casaFilter" placeholder="Nome da casa..." />
                    <input type="text" id="mesFilter" placeholder="Mês/Ano (ex: Janeiro/2025)" />
                    
                    <button class="button" onclick="carregarFaturas()">🔍 Buscar</button>
                    <button class="button" onclick="limparFiltros()">🗑️ Limpar</button>
                    <a href="/" class="button" style="background: #6c757d; text-decoration: none;">🏠 Voltar</a>
                </div>
                
                <div id="resultado">
                    <p>Clique em "Buscar" para carregar as faturas...</p>
                </div>
            </div>
            
            <script>
                async function carregarFaturas() {
                    const status = document.getElementById('statusFilter').value;
                    const casa = document.getElementById('casaFilter').value;
                    const mes = document.getElementById('mesFilter').value;
                    
                    let url = '/faturas?limite=100';
                    if (status) url += `&status=${encodeURIComponent(status)}`;
                    if (casa) url += `&casa=${encodeURIComponent(casa)}`;
                    if (mes) url += `&mes=${encodeURIComponent(mes)}`;
                    
                    document.getElementById('resultado').innerHTML = '<p>🔄 Carregando faturas...</p>';
                    
                    try {
                        const response = await fetch(url);
                        const data = await response.json();
                        
                        if (data.faturas) {
                            exibirFaturas(data);
                        } else {
                            document.getElementById('resultado').innerHTML = `<p>❌ Erro: ${data.erro}</p>`;
                        }
                    } catch (error) {
                        document.getElementById('resultado').innerHTML = `<p>❌ Erro de conexão: ${error.message}</p>`;
                    }
                }
                
                function exibirFaturas(data) {
                    let html = `<p><strong>📊 Total encontradas:</strong> ${data.total_encontradas}</p>`;
                    
                    if (data.faturas.length === 0) {
                        html += '<p>Nenhuma fatura encontrada com os filtros aplicados.</p>';
                        document.getElementById('resultado').innerHTML = html;
                        return;
                    }
                    
                    html += '<table>';
                    html += '<tr>';
                    html += '<th>ID</th><th>Status</th><th>CDC</th><th>Casa</th><th>Valor</th>';
                    html += '<th>Vencimento</th><th>Competência</th><th>Alerta</th><th>Observação</th>';
                    html += '</tr>';
                    
                    data.faturas.forEach(fatura => {
                        const statusClass = `status-${fatura.status_duplicata.toLowerCase()}`;
                        const alertaClass = fatura.alerta_consumo && fatura.alerta_consumo.includes('ALTO') ? 'alerta-alto' : 'alerta-normal';
                        
                        html += '<tr>';
                        html += `<td>${fatura.id}</td>`;
                        html += `<td class="${statusClass}">${fatura.status_duplicata}</td>`;
                        html += `<td>${fatura.cdc || '-'}</td>`;
                        html += `<td>${(fatura.casa_oracao || 'N/A').substring(0, 30)}${fatura.casa_oracao && fatura.casa_oracao.length > 30 ? '...' : ''}</td>`;
                        html += `<td>R$ ${fatura.valor || '-'}</td>`;
                        html += `<td>${fatura.vencimento || '-'}</td>`;
                        html += `<td>${fatura.competencia || '-'}</td>`;
                        html += `<td class="${alertaClass}">${(fatura.alerta_consumo || '').substring(0, 20)}${fatura.alerta_consumo && fatura.alerta_consumo.length > 20 ? '...' : ''}</td>`;
                        html += `<td>${(fatura.observacao || '').substring(0, 30)}${fatura.observacao && fatura.observacao.length > 30 ? '...' : ''}</td>`;
                        html += '</tr>';
                    });
                    
                    html += '</table>';
                    document.getElementById('resultado').innerHTML = html;
                }
                
                function limparFiltros() {
                    document.getElementById('statusFilter').value = '';
                    document.getElementById('casaFilter').value = '';
                    document.getElementById('mesFilter').value = '';
                }
                
                // Carregar faturas automaticamente
                window.onload = function() {
                    carregarFaturas();
                };
            </script>
        </body>
        </html>
        """
        return html
        
    except Exception as e:
        logger.error(f"Erro na interface de faturas: {e}")
        return f"Erro: {e}", 500

@app.route('/recarregar-relacionamento', methods=['POST'])
def recarregar_relacionamento():
    """Força recarregamento do relacionamento CDC → Casa de Oração"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        # Criar EmailProcessor
        processor = EmailProcessor(auth_manager)
        
        # Forçar recarregamento
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
# APP.PY COMPLETO - NOVO COM DATABASEBRK INTEGRADO
# BLOCO 4/5 - ROTAS ESPECÍFICAS DA DATABASEBRK
# ============================================================================

@app.route('/estatisticas-banco', methods=['GET'])
def estatisticas_banco():
    """Estatísticas completas do DatabaseBRK"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        # Criar EmailProcessor e integrar DatabaseBRK
        processor = EmailProcessor(auth_manager)
        
        if not integrar_database_emailprocessor(processor):
            return jsonify({"erro": "DatabaseBRK não disponível"}), 500
        
        # Obter estatísticas
        stats = processor.database_brk.obter_estatisticas()
        
        # Expandir com informações adicionais
        stats['sistema'] = {
            'onedrive_brk_configurado': bool(processor.onedrive_brk_id),
            'relacionamento_ativo': processor.relacionamento_carregado,
            'total_relacionamentos': len(processor.cdc_brk_vetor)
        }
        
        stats['timestamp'] = datetime.now().isoformat()
        
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
        
        # Parâmetros de consulta
        status_filter = request.args.get('status')  # NORMAL, DUPLICATA, CUIDADO
        casa_filter = request.args.get('casa')
        mes_filter = request.args.get('mes')
        limite = int(request.args.get('limite', 50))
        
        # Criar EmailProcessor e integrar DatabaseBRK
        processor = EmailProcessor(auth_manager)
        
        if not integrar_database_emailprocessor(processor):
            return jsonify({"erro": "DatabaseBRK não disponível"}), 500
        
        # Buscar faturas (implementar filtros conforme necessário)
        faturas_raw = processor.database_brk.buscar_faturas()
        
        # Converter para formato JSON amigável
        faturas_json = []
        colunas = [
            'id', 'data_processamento', 'status_duplicata', 'observacao',
            'email_id', 'nome_arquivo_original', 'nome_arquivo', 'hash_arquivo',
            'tamanho_bytes', 'caminho_onedrive', 'cdc', 'nota_fiscal',
            'casa_oracao', 'data_emissao', 'vencimento', 'competencia', 'valor',
            'medido_real', 'faturado', 'media_6m', 'porcentagem_consumo',
            'alerta_consumo', 'dados_extraidos_ok', 'relacionamento_usado'
        ]
        
        for fatura in faturas_raw:
            fatura_dict = dict(zip(colunas, fatura))
            
            # Aplicar filtros
            if status_filter and fatura_dict['status_duplicata'] != status_filter:
                continue
            if casa_filter and casa_filter.lower() not in (fatura_dict['casa_oracao'] or '').lower():
                continue
            if mes_filter and mes_filter not in (fatura_dict['competencia'] or ''):
                continue
            
            # Formatar para JSON
            faturas_json.append({
                'id': fatura_dict['id'],
                'data_processamento': fatura_dict['data_processamento'],
                'status_duplicata': fatura_dict['status_duplicata'],
                'observacao': fatura_dict['observacao'],
                'cdc': fatura_dict['cdc'],
                'casa_oracao': fatura_dict['casa_oracao'],
                'valor': fatura_dict['valor'],
                'vencimento': fatura_dict['vencimento'],
                'competencia': fatura_dict['competencia'],
                'nota_fiscal': fatura_dict['nota_fiscal'],
                'nome_arquivo': fatura_dict['nome_arquivo'],
                'nome_arquivo_original': fatura_dict['nome_arquivo_original'],
                'alerta_consumo': fatura_dict['alerta_consumo'],
                'medido_real': fatura_dict['medido_real'],
                'media_6m': fatura_dict['media_6m']
            })
            
            # Aplicar limite
            if len(faturas_json) >= limite:
                break
        
        return jsonify({
            'total_encontradas': len(faturas_json),
            'limite_aplicado': limite,
            'filtros': {
                'status': status_filter,
                'casa': casa_filter,
                'mes': mes_filter
            },
            'faturas': faturas_json
        })
        
    except Exception as e:
        logger.error(f"Erro listando faturas: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/faturas-html', methods=['GET'])
def faturas_html():
    """Interface web para visualizar faturas"""
    try:
        if not auth_manager.access_token:
            return redirect('/login')
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sistema BRK - Faturas Salvas</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial; margin: 20px; background: #f5f5f5; }
                .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .filtros { background: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                .filtros input, .filtros select { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 3px; }
                .button { background: #007bff; color: white; padding: 8px 15px; border: none; border-radius: 3px; cursor: pointer; margin: 5px; }
                .button:hover { background: #0056b3; }
                table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f8f9fa; font-weight: bold; }
                .status-normal { color: #28a745; font-weight: bold; }
                .status-duplicata { color: #6c757d; font-style: italic; }
                .status-cuidado { color: #dc3545; font-weight: bold; }
                .alerta-alto { background: #f8d7da; color: #721c24; }
                .alerta-normal { background: #d4edda; color: #155724; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📋 Faturas BRK - DatabaseBRK</h1>
                
                <div class="filtros">
                    <h3>🔍 Filtros:</h3>
                    <select id="statusFilter">
                        <option value="">Todos os status</option>
                        <option value="NORMAL">✅ NORMAL</option>
                        <option value="DUPLICATA">🔄 DUPLICATA</option>
                        <option value="CUIDADO">⚠️ CUIDADO</option>
                    </select>
                    
                    <input type="text" id="casaFilter" placeholder="Nome da casa..." />
                    <input type="text" id="mesFilter" placeholder="Mês/Ano (ex: Janeiro/2025)" />
                    
                    <button class="button" onclick="carregarFaturas()">🔍 Buscar</button>
                    <button class="button" onclick="limparFiltros()">🗑️ Limpar</button>
                    <a href="/" class="button" style="background: #6c757d; text-decoration: none;">🏠 Voltar</a>
                </div>
                
                <div id="resultado">
                    <p>Clique em "Buscar" para carregar as faturas...</p>
                </div>
            </div>
            
            <script>
                async function carregarFaturas() {
                    const status = document.getElementById('statusFilter').value;
                    const casa = document.getElementById('casaFilter').value;
                    const mes = document.getElementById('mesFilter').value;
                    
                    let url = '/faturas?limite=100';
                    if (status) url += `&status=${encodeURIComponent(status)}`;
                    if (casa) url += `&casa=${encodeURIComponent(casa)}`;
                    if (mes) url += `&mes=${encodeURIComponent(mes)}`;
                    
                    document.getElementById('resultado').innerHTML = '<p>🔄 Carregando faturas...</p>';
                    
                    try {
                        const response = await fetch(url);
                        const data = await response.json();
                        
                        if (data.faturas) {
                            exibirFaturas(data);
                        } else {
                            document.getElementById('resultado').innerHTML = `<p>❌ Erro: ${data.erro}</p>`;
                        }
                    } catch (error) {
                        document.getElementById('resultado').innerHTML = `<p>❌ Erro de conexão: ${error.message}</p>`;
                    }
                }
                
                function exibirFaturas(data) {
                    let html = `<p><strong>📊 Total encontradas:</strong> ${data.total_encontradas}</p>`;
                    
                    if (data.faturas.length === 0) {
                        html += '<p>Nenhuma fatura encontrada com os filtros aplicados.</p>';
                        document.getElementById('resultado').innerHTML = html;
                        return;
                    }
                    
                    html += '<table>';
                    html += '<tr>';
                    html += '<th>ID</th><th>Status</th><th>CDC</th><th>Casa</th><th>Valor</th>';
                    html += '<th>Vencimento</th><th>Competência</th><th>Alerta</th><th>Observação</th>';
                    html += '</tr>';
                    
                    data.faturas.forEach(fatura => {
                        const statusClass = `status-${fatura.status_duplicata.toLowerCase()}`;
                        const alertaClass = fatura.alerta_consumo && fatura.alerta_consumo.includes('ALTO') ? 'alerta-alto' : 'alerta-normal';
                        
                        html += '<tr>';
                        html += `<td>${fatura.id}</td>`;
                        html += `<td class="${statusClass}">${fatura.status_duplicata}</td>`;
                        html += `<td>${fatura.cdc || '-'}</td>`;
                        html += `<td>${(fatura.casa_oracao || 'N/A').substring(0, 30)}${fatura.casa_oracao && fatura.casa_oracao.length > 30 ? '...' : ''}</td>`;
                        html += `<td>R$ ${fatura.valor || '-'}</td>`;
                        html += `<td>${fatura.vencimento || '-'}</td>`;
                        html += `<td>${fatura.competencia || '-'}</td>`;
                        html += `<td class="${alertaClass}">${(fatura.alerta_consumo || '').substring(0, 20)}${fatura.alerta_consumo && fatura.alerta_consumo.length > 20 ? '...' : ''}</td>`;
                        html += `<td>${(fatura.observacao || '').substring(0, 30)}${fatura.observacao && fatura.observacao.length > 30 ? '...' : ''}</td>`;
                        html += '</tr>';
                    });
                    
                    html += '</table>';
                    document.getElementById('resultado').innerHTML = html;
                }
                
                function limparFiltros() {
                    document.getElementById('statusFilter').value = '';
                    document.getElementById('casaFilter').value = '';
                    document.getElementById('mesFilter').value = '';
                }
                
                // Carregar faturas automaticamente
                window.onload = function() {
                    carregarFaturas();
                };
            </script>
        </body>
        </html>
        """
        return html
        
    except Exception as e:
        logger.error(f"Erro na interface de faturas: {e}")
        return f"Erro: {e}", 500

@app.route('/recarregar-relacionamento', methods=['POST'])
def recarregar_relacionamento():
    """Força recarregamento do relacionamento CDC → Casa de Oração"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        # Criar EmailProcessor
        processor = EmailProcessor(auth_manager)
        
        # Forçar recarregamento
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
# APP.PY COMPLETO - NOVO COM DATABASEBRK INTEGRADO
# BLOCO 5/5 - UTILITÁRIOS E INICIALIZAÇÃO
# ============================================================================

@app.route('/debug-sistema', methods=['GET'])
def debug_sistema():
    """Debug completo do sistema incluindo DatabaseBRK"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        # Criar EmailProcessor e testar integração
        processor = EmailProcessor(auth_manager)
        database_integrado = integrar_database_emailprocessor(processor)
        
        # Informações do sistema
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "autenticacao": {
                "token_disponivel": bool(auth_manager.access_token),
                "token_valido": auth_manager.verificar_token_valido() if auth_manager.access_token else False
            },
            "configuracao": {
                "client_id_configurado": bool(CLIENT_ID),
                "pasta_brk_configurada": bool(PASTA_BRK_ID),
                "onedrive_brk_configurado": bool(ONEDRIVE_BRK_ID),
                "pasta_brk_id": f"{PASTA_BRK_ID[:10]}******" if PASTA_BRK_ID else "N/A",
                "onedrive_brk_id": f"{ONEDRIVE_BRK_ID[:15]}******" if ONEDRIVE_BRK_ID else "N/A"
            },
            "email_processor": {
                "inicializado": True,
                "relacionamento_carregado": processor.relacionamento_carregado,
                "total_relacionamentos": len(processor.cdc_brk_vetor),
                "tentativas_carregamento": processor.tentativas_carregamento
            },
            "database_brk": {
                "integrado": database_integrado,
                "disponivel": hasattr(processor, 'database_brk')
            }
        }
        
        # Testar DatabaseBRK se disponível
        if database_integrado:
            try:
                stats_banco = processor.database_brk.obter_estatisticas()
                debug_info["database_brk"]["estatisticas"] = stats_banco
                debug_info["database_brk"]["funcional"] = True
            except Exception as e:
                debug_info["database_brk"]["erro"] = str(e)
                debug_info["database_brk"]["funcional"] = False
        
        # Executar diagnóstico completo se disponível
        if hasattr(processor, 'diagnostico_completo_sistema'):
            try:
                diagnostico = processor.diagnostico_completo_sistema()
                debug_info["diagnostico_completo"] = diagnostico
            except Exception as e:
                debug_info["diagnostico_erro"] = str(e)
        
        return jsonify(debug_info)
        
    except Exception as e:
        logger.error(f"Erro no debug: {e}")
        return jsonify({
            "erro": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/teste-completo', methods=['POST'])
def teste_completo():
    """Executa teste completo de todas as funcionalidades"""
    try:
        if not auth_manager.access_token:
            return jsonify({"erro": "Token não disponível"}), 401
        
        # Criar EmailProcessor
        processor = EmailProcessor(auth_manager)
        
        # Testar funcionalidades
        resultados_teste = {}
        
        # 1. Teste básico EmailProcessor
        if hasattr(processor, 'testar_funcionalidades_completas'):
            try:
                resultados_teste["email_processor"] = processor.testar_funcionalidades_completas()
            except Exception as e:
                resultados_teste["email_processor"] = {"erro": str(e)}
        
        # 2. Teste DatabaseBRK
        database_integrado = integrar_database_emailprocessor(processor)
        resultados_teste["database_brk"] = {"integrado": database_integrado}
        
        if database_integrado:
            try:
                # Teste inicialização do sistema
                sistema_ok = processor.database_brk.inicializar_sistema()
                resultados_teste["database_brk"]["sistema_inicializado"] = sistema_ok
                
                # Teste estatísticas
                stats = processor.database_brk.obter_estatisticas()
                resultados_teste["database_brk"]["estatisticas"] = stats
                
            except Exception as e:
                resultados_teste["database_brk"]["erro"] = str(e)
        
        # 3. Teste diagnóstico pasta
        try:
            diagnostico_pasta = processor.diagnosticar_pasta_brk()
            resultados_teste["diagnostico_pasta"] = diagnostico_pasta
        except Exception as e:
            resultados_teste["diagnostico_pasta"] = {"erro": str(e)}
        
        return jsonify({
            "status": "teste_completo_executado",
            "timestamp": datetime.now().isoformat(),
            "resultados": resultados_teste
        })
        
    except Exception as e:
        logger.error(f"Erro no teste completo: {e}")
        return jsonify({"erro": str(e)}), 500

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
    variaveis_obrigatorias = ['CLIENT_ID', 'CLIENT_SECRET', 'REDIRECT_URI', 'PASTA_BRK_ID']
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
    
    return True

def inicializar_aplicacao():
    """Inicialização da aplicação"""
    print(f"\n🚀 INICIANDO SISTEMA BRK COM DATABASEBRK")
    print(f"="*60)
    
    # Verificar configuração
    if not verificar_configuracao():
        print(f"❌ Falha na verificação de configuração")
        return False
    
    # Configurar auth manager
    auth_manager.configurar(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
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
# 🎉 APP.PY COMPLETO COM DATABASEBRK FINALIZADO!
# 
# FUNCIONALIDADES IMPLEMENTADAS:
# ✅ Autenticação Microsoft (mantida igual)
# ✅ EmailProcessor integrado (expandido)
# ✅ DatabaseBRK totalmente integrado
# ✅ Detecção automática de duplicatas
# ✅ SQLite organizado no OneDrive
# ✅ Interface web completa
# ✅ Rotas de estatísticas e listagem
# ✅ Debug e monitoramento
# ✅ Tratamento de erros robusto
# ✅ Health check para Render
# 
# ROTAS DISPONÍVEIS:
# 🏠 / - Página inicial
# 🔑 /login, /logout - Autenticação
# 📊 /diagnostico-pasta - Diagnóstico com DatabaseBRK
# ⚙️ /processar-emails-novos - Processamento com salvamento automático
# 📋 /faturas - API de faturas
# 📈 /estatisticas-banco - Estatísticas do DatabaseBRK
# 🔧 /debug-sistema - Debug completo
# 💊 /health - Health check
# 
# DEPLOY: Substituir app.py pelos 5 blocos e fazer commit!
# ============================================================================
