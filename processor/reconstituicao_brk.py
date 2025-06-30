#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/reconstituicao_brk.py
💾 ONDE SALVAR: brk-monitor-seguro/processor/reconstituicao_brk.py
📦 FUNÇÃO: Reconstituição Total da Base BRK - POR PERÍODO ESPECÍFICO
🔧 DESCRIÇÃO: RESOLVE TIMEOUT - processa 2 emails por vez em período selecionado
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua

🎯 NOVA ESTRATÉGIA: Seleção de período + processamento ultra-leve (2 emails/vez)
♻️ REUTILIZAÇÃO TOTAL - usa funções existentes com controle preciso
"""

import os
import sys
from datetime import datetime, timedelta

# ✅ IMPORTS SIMPLIFICADOS
try:
    from .email_processor import EmailProcessor
    from .database_brk import DatabaseBRK
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from processor.email_processor import EmailProcessor
    from processor.database_brk import DatabaseBRK

# Auth sempre absoluto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.microsoft_auth import MicrosoftAuth


def processar_periodo_brk(auth_manager, data_inicio, data_fim, offset=0, limit_lote=2):
    """
    🆕 NOVA ESTRATÉGIA: Processa emails em período específico, 2 por vez.
    
    Args:
        auth_manager: MicrosoftAuth instance
        data_inicio (str): Data início formato 'YYYY-MM-DD'
        data_fim (str): Data fim formato 'YYYY-MM-DD'
        offset (int): Quantos emails já foram processados
        limit_lote (int): Emails por lote (padrão: 2)
        
    Returns:
        dict: Resultado do lote + progresso do período
    """
    try:
        print(f"\n🔄 RECONSTITUIÇÃO BRK - PERÍODO {data_inicio} a {data_fim}")
        print(f"📊 Lote: emails {offset + 1}-{offset + limit_lote}")
        print(f"="*60)
        
        # ✅ REUTILIZAR: EmailProcessor já testado
        processor = EmailProcessor(auth_manager)
        
        if not processor.database_brk:
            return {
                'status': 'erro',
                'mensagem': 'DatabaseBRK não disponível'
            }
        
        # ETAPA 1: Buscar emails do período específico
        print(f"1️⃣ BUSCANDO EMAILS DO PERÍODO...")
        emails_periodo = _buscar_emails_periodo(processor, data_inicio, data_fim)
        
        if not emails_periodo:
            return {
                'status': 'erro',
                'mensagem': f'Nenhum email encontrado no período {data_inicio} a {data_fim}'
            }
        
        # ETAPA 2: Aplicar offset e limite
        total_emails = len(emails_periodo)
        emails_lote = emails_periodo[offset:offset + limit_lote]
        emails_restantes = max(0, total_emails - (offset + limit_lote))
        
        print(f"📧 Total no período: {total_emails} emails")
        print(f"📋 Lote atual: {len(emails_lote)} emails")
        print(f"⏳ Restantes: {emails_restantes} emails")
        
        if not emails_lote:
            return {
                'status': 'sucesso',
                'mensagem': 'Todos os emails do período foram processados',
                'emails_processados': 0,
                'pdfs_extraidos': 0,
                'faturas_salvas': 0,
                'total_emails': total_emails,
                'offset_atual': offset,
                'emails_restantes': 0,
                'finalizado': True,
                'periodo': f"{data_inicio} a {data_fim}"
            }
        
        # ETAPA 3: Processar lote de 2 emails
        print(f"2️⃣ PROCESSANDO {len(emails_lote)} EMAILS...")
        resultado_lote = _processar_lote_periodo(processor, emails_lote)
        
        # ETAPA 4: Resultado com progresso do período
        resultado_final = {
            'status': 'sucesso',
            'mensagem': f'Lote processado: {len(emails_lote)} emails do período',
            'emails_processados': resultado_lote['emails_processados'],
            'pdfs_extraidos': resultado_lote['pdfs_extraidos'],
            'faturas_salvas': resultado_lote['faturas_salvas'],
            'duplicatas_detectadas': resultado_lote.get('duplicatas_detectadas', 0),
            'erros': resultado_lote.get('erros', 0),
            # 📊 PROGRESSO DO PERÍODO
            'total_emails': total_emails,
            'offset_atual': offset,
            'proximo_offset': offset + limit_lote if emails_restantes > 0 else None,
            'emails_restantes': emails_restantes,
            'finalizado': emails_restantes == 0,
            'progresso_pct': ((offset + len(emails_lote)) / total_emails) * 100,
            'periodo': f"{data_inicio} a {data_fim}",
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n✅ LOTE CONCLUÍDO!")
        print(f"   📧 Emails processados: {resultado_final['emails_processados']}")
        print(f"   📎 PDFs extraídos: {resultado_final['pdfs_extraidos']}")  
        print(f"   💾 Faturas salvas: {resultado_final['faturas_salvas']}")
        print(f"   📊 Progresso período: {resultado_final['progresso_pct']:.1f}%")
        print(f"   ⏳ Restam: {emails_restantes} emails")
        print(f"="*60)
        
        return resultado_final
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return {
            'status': 'erro',
            'mensagem': str(e),
            'offset_atual': offset,
            'periodo': f"{data_inicio} a {data_fim}"
        }


def _buscar_emails_periodo(processor, data_inicio, data_fim):
    """
    🆕 BUSCA EMAILS EM PERÍODO ESPECÍFICO
    
    Args:
        processor: EmailProcessor instance
        data_inicio (str): 'YYYY-MM-DD'
        data_fim (str): 'YYYY-MM-DD'
        
    Returns:
        list: Emails do período ordenados por data
    """
    try:
        # Calcular diferença em dias
        inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        fim = datetime.strptime(data_fim, '%Y-%m-%d')
        dias_total = (fim - inicio).days + 1
        
        print(f"📅 Período: {dias_total} dias")
        
        # ✅ REUTILIZAR: buscar_emails_novos com dias calculados
        # Buscar desde a data mais antiga até hoje
        hoje = datetime.now()
        dias_desde_inicio = (hoje - inicio).days + 1
        
        todos_emails = processor.buscar_emails_novos(dias_desde_inicio)
        
        # Filtrar apenas emails do período
        emails_periodo = []
        for email in todos_emails:
            try:
                # Extrair data do email
                email_date = email.get('receivedDateTime', '')
                if email_date:
                    # Parse data do email (formato ISO)
                    email_dt = datetime.fromisoformat(email_date.replace('Z', '+00:00')).replace(tzinfo=None)
                    email_date_str = email_dt.strftime('%Y-%m-%d')
                    
                    # Verificar se está no período
                    if data_inicio <= email_date_str <= data_fim:
                        emails_periodo.append(email)
            except Exception as e:
                print(f"⚠️ Erro filtrando email: {e}")
                continue
        
        # Ordenar por data (mais antigos primeiro)
        emails_periodo.sort(key=lambda x: x.get('receivedDateTime', ''))
        
        print(f"📧 Emails encontrados no período: {len(emails_periodo)}")
        return emails_periodo
        
    except Exception as e:
        print(f"❌ Erro buscando emails do período: {e}")
        return []


def _processar_lote_periodo(processor, emails_lote):
    """
    ✅ PROCESSAR LOTE ULTRA-PEQUENO (2 emails)
    
    Args:
        processor: EmailProcessor instance
        emails_lote: Lista de 2 emails max
        
    Returns:
        dict: Estatísticas do micro-lote
    """
    try:
        total_lote = len(emails_lote)
        print(f"📧 Processando micro-lote: {total_lote} emails")
        
        # Contadores
        emails_processados = 0
        pdfs_extraidos = 0
        faturas_salvas = 0
        duplicatas_detectadas = 0
        erros = 0
        
        for i, email in enumerate(emails_lote, 1):
            try:
                email_subject = email.get('subject', 'Sem assunto')[:40]
                email_date = email.get('receivedDateTime', '')[:10]
                
                print(f"📨 {i}/{total_lote}: {email_date} - {email_subject}")
                
                # ✅ REUTILIZAR: extrair_pdfs_do_email() completo
                pdfs_dados = processor.extrair_pdfs_do_email(email)
                
                if pdfs_dados:
                    emails_processados += 1
                    pdfs_extraidos += len(pdfs_dados)
                    
                    # Contar salvamentos e duplicatas
                    for pdf in pdfs_dados:
                        if pdf.get('database_salvo', False):
                            faturas_salvas += 1
                            
                            if pdf.get('database_status') == 'DUPLICATA':
                                duplicatas_detectadas += 1
                    
                    print(f"   ✅ {len(pdfs_dados)} PDF(s) extraído(s)")
                else:
                    print(f"   📭 Nenhum PDF encontrado")
                
            except Exception as e:
                erros += 1
                print(f"   ❌ Erro: {e}")
                continue
        
        # Resultado do micro-lote
        resultado = {
            'emails_processados': emails_processados,
            'pdfs_extraidos': pdfs_extraidos, 
            'faturas_salvas': faturas_salvas,
            'duplicatas_detectadas': duplicatas_detectadas,
            'erros': erros
        }
        
        print(f"📊 MICRO-LOTE PROCESSADO:")
        print(f"   ✅ Emails: {emails_processados}")
        print(f"   📎 PDFs: {pdfs_extraidos}")
        print(f"   💾 Faturas: {faturas_salvas}")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro no micro-lote: {e}")
        return {
            'emails_processados': 0,
            'pdfs_extraidos': 0,
            'faturas_salvas': 0,
            'duplicatas_detectadas': 0,
            'erros': 1
        }


def inicializar_reconstituicao_periodo(auth_manager, data_inicio, data_fim):
    """
    🆕 INICIALIZAÇÃO POR PERÍODO
    
    Args:
        auth_manager: MicrosoftAuth instance
        data_inicio (str): 'YYYY-MM-DD'
        data_fim (str): 'YYYY-MM-DD'
        
    Returns:
        dict: Status da inicialização com contagem real do período
    """
    try:
        print(f"\n🔄 INICIALIZANDO RECONSTITUIÇÃO - PERÍODO {data_inicio} a {data_fim}")
        print(f"="*60)
        
        # ✅ REUTILIZAR: EmailProcessor já testado
        processor = EmailProcessor(auth_manager)
        
        if not processor.database_brk:
            return {
                'status': 'erro',
                'mensagem': 'DatabaseBRK não disponível'
            }
        
        # ETAPA 1: Backup opcional
        print(f"1️⃣ BACKUP AUTOMÁTICO...")
        try:
            backup_ok = processor.database_brk.forcar_sincronizacao_completa()
            if backup_ok:
                print(f"✅ Backup OneDrive realizado")
            else:
                print(f"⚠️ Backup falhou - continuando...")
        except:
            backup_ok = False
            print(f"⚠️ Backup não disponível - continuando...")
        
        # ETAPA 2: Contar emails do período (SEM reset da tabela)
        print(f"2️⃣ CONTANDO EMAILS DO PERÍODO...")
        emails_periodo = _buscar_emails_periodo(processor, data_inicio, data_fim)
        total_emails = len(emails_periodo)
        
        if total_emails == 0:
            return {
                'status': 'erro',
                'mensagem': f'Nenhum email encontrado no período {data_inicio} a {data_fim}'
            }
        
        lotes_necessarios = (total_emails + 1) // 2  # 2 emails por lote
        
        print(f"✅ INICIALIZAÇÃO CONCLUÍDA!")
        print(f"   📧 Emails no período: {total_emails}")
        print(f"   📊 Lotes necessários: {lotes_necessarios} (2 emails/lote)")
        print(f"   ⏱️ Tempo estimado: ~{lotes_necessarios * 10}s total")
        print(f"="*60)
        
        return {
            'status': 'sucesso',
            'mensagem': f'Reconstituição inicializada para período {data_inicio} a {data_fim}',
            'total_emails': total_emails,
            'backup_realizado': backup_ok,
            'lotes_necessarios': lotes_necessarios,
            'emails_por_lote': 2,
            'periodo': f"{data_inicio} a {data_fim}",
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ ERRO na inicialização: {e}")
        return {
            'status': 'erro',
            'mensagem': str(e)
        }


# ============================================================================
# FUNÇÕES PARA APP.PY (interface por período)
# ============================================================================

def executar_reconstituicao_lote(auth_manager, offset=0, data_inicio=None, data_fim=None):
    """
    🆕 EXECUTA LOTE DE PERÍODO ESPECÍFICO
    
    Args:
        auth_manager: MicrosoftAuth instance
        offset (int): Posição atual
        data_inicio (str): Data início 'YYYY-MM-DD'
        data_fim (str): Data fim 'YYYY-MM-DD'
        
    Returns:
        dict: Resultado do lote
    """
    if not data_inicio or not data_fim:
        return {
            'status': 'erro',
            'mensagem': 'Datas de início e fim são obrigatórias'
        }
    
    return processar_periodo_brk(auth_manager, data_inicio, data_fim, offset, limit_lote=2)


def inicializar_reconstituicao_primeira_vez(auth_manager, data_inicio=None, data_fim=None):
    """
    🆕 INICIALIZAÇÃO COM PERÍODO
    """
    if not data_inicio or not data_fim:
        return {
            'status': 'erro',
            'mensagem': 'Datas de início e fim são obrigatórias'
        }
    
    return inicializar_reconstituicao_periodo(auth_manager, data_inicio, data_fim)


def obter_estatisticas_pre_reconstituicao(auth_manager):
    """
    ✅ MANTÉM FUNÇÃO ORIGINAL para compatibilidade
    """
    try:
        processor = EmailProcessor(auth_manager)
        
        pasta_stats = processor.diagnosticar_pasta_brk()
        
        db_stats = {}
        if processor.database_brk:
            db_stats = processor.database_brk.obter_estatisticas()
        
        return {
            'status': 'sucesso',
            'pasta_brk': pasta_stats,
            'database_atual': db_stats,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'erro',
            'erro': str(e)
        }


def gerar_interface_web_lotes(estatisticas, progresso=None, inicializacao=None):
    """
    🆕 INTERFACE COM SELEÇÃO DE PERÍODO
    """
    # Se há resultado de inicialização, mostrar tela de sucesso
    if inicializacao and inicializacao.get('status') == 'sucesso':
        return _gerar_interface_inicializacao_sucesso(inicializacao)
    
    # Se há progresso, mostrar interface de continuação
    if progresso and not progresso.get('finalizado', False):
        return _gerar_interface_continuacao_periodo(progresso)
    
    # Interface inicial com seleção de período
    pasta_stats = estatisticas.get('pasta_brk', {})
    db_stats = estatisticas.get('database_atual', {})
    
    # Datas sugeridas
    hoje = datetime.now()
    inicio_mes = hoje.replace(day=1).strftime('%Y-%m-%d')
    fim_mes = hoje.strftime('%Y-%m-%d')
    inicio_ano = hoje.replace(month=1, day=1).strftime('%Y-%m-%d')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <title>🔄 Reconstituição BRK - Por Período</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            .info {{ background: #e3f2fd; border: 1px solid #2196f3; color: #1565c0; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 5px solid #2196f3; }}
            .form-group {{ margin: 15px 0; }}
            .form-group label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            .form-group input, .form-group select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }}
            .quick-dates {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin: 15px 0; }}
            .quick-btn {{ background: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; text-align: center; border-radius: 5px; cursor: pointer; }}
            .quick-btn:hover {{ background: #e9ecef; }}
            .button {{ background: #2196f3; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; margin: 10px 5px; }}
            .button:hover {{ background: #1976d2; }}
            .button-secondary {{ background: #6c757d; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
            .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔄 Reconstituição BRK - Seleção de Período</h1>
            <p>Processa emails em período específico - Ultra seguro: 2 emails por vez</p>
            
            <div class="info">
                <h3>💡 NOVA ESTRATÉGIA:</h3>
                <ul>
                    <li>📅 <strong>Selecione período exato</strong> (data início/fim)</li>
                    <li>⚡ <strong>2 emails por vez</strong> (ultra-seguro contra timeout)</li>
                    <li>📊 <strong>Progresso real</strong> baseado no período</li>
                    <li>⏱️ <strong>~10 segundos por lote</strong> (sem timeout)</li>
                    <li>🎯 <strong>Controle total</strong> sobre o que processar</li>
                </ul>
            </div>
            
            <form id="periodoForm">
                <div class="form-group">
                    <label for="dataInicio">📅 Data Início:</label>
                    <input type="date" id="dataInicio" name="data_inicio" value="{inicio_mes}" required>
                </div>
                
                <div class="form-group">
                    <label for="dataFim">📅 Data Fim:</label>
                    <input type="date" id="dataFim" name="data_fim" value="{fim_mes}" required>
                </div>
                
                <div class="quick-dates">
                    <div class="quick-btn" onclick="setQuickDate('mes')">📅 Mês Atual</div>
                    <div class="quick-btn" onclick="setQuickDate('trimestre')">📅 Último Trimestre</div>
                    <div class="quick-btn" onclick="setQuickDate('ano')">📅 Ano Atual</div>
                    <div class="quick-btn" onclick="setQuickDate('custom')">📅 Personalizado</div>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <button type="submit" class="button" id="btnInicializar">
                        🔍 ANALISAR PERÍODO
                    </button>
                    <a href="/" class="button button-secondary" style="text-decoration: none;">🏠 Voltar ao Dashboard</a>
                </div>
            </form>
            
            <h3>📊 Status Atual do Sistema</h3>
            <div class="stats">
                <div class="stat-card">
                    <h4>📧 Emails BRK</h4>
                    <p><strong>{pasta_stats.get('total_geral', 'N/A')}</strong> total</p>
                    <p>{pasta_stats.get('mes_atual', 'N/A')} mês atual</p>
                </div>
                <div class="stat-card">
                    <h4>💾 Database Atual</h4>
                    <p><strong>{db_stats.get('total_faturas', 'N/A')}</strong> faturas</p>
                    <p>{'OneDrive' if db_stats.get('usando_onedrive') else 'Local'}</p>
                </div>
            </div>
        </div>
        
        <script>
            function setQuickDate(tipo) {{
                const hoje = new Date();
                const inicioInput = document.getElementById('dataInicio');
                const fimInput = document.getElementById('dataFim');
                
                if (tipo === 'mes') {{
                    const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
                    inicioInput.value = inicioMes.toISOString().split('T')[0];
                    fimInput.value = hoje.toISOString().split('T')[0];
                }} else if (tipo === 'trimestre') {{
                    const inicioTrimestre = new Date(hoje.getFullYear(), hoje.getMonth() - 3, 1);
                    inicioInput.value = inicioTrimestre.toISOString().split('T')[0];
                    fimInput.value = hoje.toISOString().split('T')[0];
                }} else if (tipo === 'ano') {{
                    const inicioAno = new Date(hoje.getFullYear(), 0, 1);
                    inicioInput.value = inicioAno.toISOString().split('T')[0];
                    fimInput.value = hoje.toISOString().split('T')[0];
                }}
            }}
            
            document.getElementById('periodoForm').addEventListener('submit', async function(e) {{
                e.preventDefault();
                
                const dataInicio = document.getElementById('dataInicio').value;
                const dataFim = document.getElementById('dataFim').value;
                const btn = document.getElementById('btnInicializar');
                
                if (dataInicio > dataFim) {{
                    alert('Data início deve ser menor que data fim');
                    return;
                }}
                
                btn.disabled = true;
                btn.innerHTML = '⏳ ANALISANDO PERÍODO...';
                
                try {{
                    const formData = new FormData();
                    formData.append('acao', 'inicializar');
                    formData.append('data_inicio', dataInicio);
                    formData.append('data_fim', dataFim);
                    
                    const response = await fetch('/executar-reconstituicao', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    if (response.ok) {{
                        const html = await response.text();
                        document.body.innerHTML = html;
                    }} else {{
                        alert('Erro ao analisar período');
                        btn.disabled = false;
                        btn.innerHTML = '🔍 ANALISAR PERÍODO';
                    }}
                }} catch (error) {{
                    alert('Erro de conexão: ' + error.message);
                    btn.disabled = false;
                    btn.innerHTML = '🔍 ANALISAR PERÍODO';
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return html


def _gerar_interface_inicializacao_sucesso(resultado):
    """Interface de sucesso da inicialização com período"""
    total_emails = resultado.get('total_emails', 0)
    lotes_necessarios = resultado.get('lotes_necessarios', 0)
    periodo = resultado.get('periodo', '')
    data_inicio = resultado.get('data_inicio', '')
    data_fim = resultado.get('data_fim', '')
    
    return f"""<!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <title>✅ Período Analisado</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .button {{ background: #28a745; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; margin: 10px 5px; text-decoration: none; display: inline-block; }}
            .button:hover {{ background: #218838; }}
            .button-secondary {{ background: #6c757d; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin: 20px 0; }}
            .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Período Analisado com Sucesso!</h1>
            
            <div class="success">
                <h3>📊 Análise do Período:</h3>
                <p><strong>📅 Período:</strong> {periodo}</p>
                <p><strong>📧 Emails encontrados:</strong> {total_emails:,}</p>
                <p><strong>📋 Lotes necessários:</strong> {lotes_necessarios} (2 emails/lote)</p>
                <p><strong>⏱️ Tempo estimado:</strong> ~{lotes_necessarios * 10} segundos total</p>
            </div>
            
            <h3>📋 Plano de Processamento:</h3>
            <div class="stats">
                <div class="stat-card">
                    <h4>📧 Por Lote</h4>
                    <p><strong>2</strong> emails</p>
                </div>
                <div class="stat-card">
                    <h4>⏱️ Por Lote</h4>
                    <p><strong>~10s</strong></p>
                </div>
                <div class="stat-card">
                    <h4>🛡️ Segurança</h4>
                    <p><strong>Ultra</strong></p>
                </div>
                <div class="stat-card">
                    <h4>📊 Progresso</h4>
                    <p><strong>Real</strong></p>
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <form method="post" action="/executar-reconstituicao">
                    <input type="hidden" name="acao" value="continuar">
                    <input type="hidden" name="offset" value="0">
                    <input type="hidden" name="data_inicio" value="{data_inicio}">
                    <input type="hidden" name="data_fim" value="{data_fim}">
                    <button type="submit" class="button">
                        🚀 PROCESSAR PRIMEIROS 2 EMAILS
                    </button>
                </form>
                <a href="/reconstituicao-brk" class="button button-secondary">🔙 Cancelar</a>
            </div>
            
            <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin-top: 20px; text-align: center;">
                <small><strong>💡 Estratégia:</strong> Processamento ultra-seguro para evitar timeout do Render</small>
            </div>
        </div>
    </body>
    </html>"""


def _gerar_interface_continuacao_periodo(progresso):
    """Interface de continuação com progresso do período"""
    
    progresso_pct = progresso.get('progresso_pct', 0)
    emails_restantes = progresso.get('emails_restantes', 0)
    proximo_offset = progresso.get('proximo_offset', 0)
    periodo = progresso.get('periodo', '')
    data_inicio = progresso.get('data_inicio', '')
    data_fim = progresso.get('data_fim', '')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <title>🔄 Processando Período - {periodo}</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 700px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .progress {{ background: #e9ecef; height: 30px; border-radius: 15px; overflow: hidden; margin: 20px 0; position: relative; }}
            .progress-bar {{ background: linear-gradient(90deg, #28a745, #20c997); height: 100%; width: {progresso_pct}%; transition: width 0.5s; }}
            .progress-text {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-weight: bold; }}
            .button {{ background: #28a745; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; margin: 10px 5px; text-decoration: none; display: inline-block; }}
            .button:hover {{ background: #218838; }}
            .button-secondary {{ background: #6c757d; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
            .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Lote Processado!</h1>
            <h2>📅 Período: {periodo}</h2>
            
            <div class="success">
                <h3>📊 Resultado do Lote:</h3>
                <p><strong>Emails processados:</strong> {progresso.get('emails_processados', 0)}</p>
                <p><strong>PDFs extraídos:</strong> {progresso.get('pdfs_extraidos', 0)}</p>
                <p><strong>Faturas salvas:</strong> {progresso.get('faturas_salvas', 0)}</p>
            </div>
            
            <h3>📈 Progresso do Período:</h3>
            <div class="progress">
                <div class="progress-bar"></div>
                <div class="progress-text">{progresso_pct:.1f}% concluído</div>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h4>📧 Restantes</h4>
                    <p><strong>{emails_restantes}</strong> emails</p>
                </div>
                <div class="stat-card">
                    <h4>📋 Lotes</h4>
                    <p><strong>~{(emails_restantes + 1) // 2}</strong> restantes</p>
                </div>
                <div class="stat-card">
                    <h4>⏱️ Tempo</h4>
                    <p><strong>~{((emails_restantes + 1) // 2) * 10}s</strong> restantes</p>
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <form method="post" action="/executar-reconstituicao">
                    <input type="hidden" name="acao" value="continuar">
                    <input type="hidden" name="offset" value="{proximo_offset}">
                    <input type="hidden" name="data_inicio" value="{data_inicio}">
                    <input type="hidden" name="data_fim" value="{data_fim}">
                    <button type="submit" class="button">
                        🚀 PROCESSAR PRÓXIMOS 2 EMAILS
                    </button>
                </form>
                <a href="/" class="button button-secondary">🏠 Pausar e Voltar</a>
            </div>
            
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <small><strong>💡 Dica:</strong> Continue clicando para processar todo o período selecionado. Cada lote demora ~10 segundos.</small>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def gerar_resultado_final_lotes(resultado):
    """Resultado final do período"""
    
    if resultado.get('finalizado', False):
        cor = '#28a745'
        emoji = '✅'
        titulo = 'PERÍODO PROCESSADO!'
    else:
        cor = '#dc3545'
        emoji = '❌' 
        titulo = 'PROCESSAMENTO INTERROMPIDO'
    
    periodo = resultado.get('periodo', 'N/A')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{emoji} Reconstituição - {periodo}</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial; margin: 40px; text-align: center; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            .header {{ background: {cor}; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .stats {{ text-align: left; margin: 20px 0; }}
            .button {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{emoji} {titulo}</h1>
                <h2>📅 {periodo}</h2>
            </div>
            
            <div class="stats">
                <h3>📊 Resultado Final:</h3>
                <p><strong>Status:</strong> {resultado.get('status', 'desconhecido').title()}</p>
                <p><strong>Período:</strong> {periodo}</p>
                <p><strong>Progresso:</strong> {resultado.get('progresso_pct', 0):.1f}%</p>
                <p><strong>Emails processados:</strong> {resultado.get('emails_processados', 0):,}</p>
                <p><strong>PDFs extraídos:</strong> {resultado.get('pdfs_extraidos', 0):,}</p>
                <p><strong>Faturas salvas:</strong> {resultado.get('faturas_salvas', 0):,}</p>
                <p><strong>Timestamp:</strong> {resultado.get('timestamp', 'N/A')[:19]}</p>
            </div>
            
            <div>
                <a href="/" class="button">🏠 Voltar ao Dashboard</a>
                <a href="/reconstituicao-brk" class="button">🔄 Novo Período</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


# ============================================================================
# FUNÇÕES DE COMPATIBILIDADE (manter originais funcionando)
# ============================================================================

def executar_reconstituicao_simples(auth_manager):
    """✅ COMPATIBILIDADE: Redireciona para versão período"""
    hoje = datetime.now()
    inicio_mes = hoje.replace(day=1).strftime('%Y-%m-%d')
    fim_mes = hoje.strftime('%Y-%m-%d')
    
    return processar_periodo_brk(auth_manager, inicio_mes, fim_mes, offset=0, limit_lote=2)


def gerar_interface_web_simples(estatisticas):
    """✅ COMPATIBILIDADE: Redireciona para versão período"""
    return gerar_interface_web_lotes(estatisticas)
