#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/reconstituicao_brk.py
💾 ONDE SALVAR: brk-monitor-seguro/processor/reconstituicao_brk.py
📦 FUNÇÃO: Reconstituição Total da Base BRK - PROCESSAMENTO EM LOTES
🔧 DESCRIÇÃO: RESOLVE TIMEOUT - processa 10 emails por vez
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua

🎯 MODIFICAÇÃO: Processa em lotes pequenos para evitar timeout Render
♻️ REUTILIZAÇÃO TOTAL - usa funções existentes com limite
"""

import os
import sys
from datetime import datetime

# ✅ IMPORTS SIMPLIFICADOS (corrigido)
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


def reconstituir_base_brk_lotes(auth_manager, offset=0, limit_lote=10):
    """
    🔄 NOVO: Reconstituição em lotes pequenos para evitar timeout.
    
    ESTRATÉGIA: Processar apenas 10 emails por vez, reutilizando funções existentes
    
    Args:
        auth_manager: MicrosoftAuth instance
        offset (int): A partir de qual email começar (default: 0)
        limit_lote (int): Quantos emails processar (default: 10)
        
    Returns:
        dict: Resultado do lote + progresso total
    """
    try:
        print(f"\n🔄 RECONSTITUIÇÃO BRK - LOTE {(offset//limit_lote) + 1}")
        print(f"="*50)
        print(f"📊 Processando emails {offset + 1} a {offset + limit_lote}")
        
        # ✅ REUTILIZAR: EmailProcessor já testado
        processor = EmailProcessor(auth_manager)
        
        if not processor.database_brk:
            return {
                'status': 'erro',
                'mensagem': 'DatabaseBRK não disponível'
            }
        
        # ETAPA 1: Buscar APENAS alguns emails usando função existente
        print(f"\n1️⃣ BUSCANDO EMAILS DO LOTE...")
        # ✅ REUTILIZAR: buscar_emails_novos() mas com período limitado
        todos_emails = processor.buscar_emails_novos(9999)  # Buscar todos primeiro
        
        if not todos_emails:
            return {
                'status': 'erro',
                'mensagem': 'Nenhum email encontrado'
            }
        
        # 🆕 APLICAR LIMITE DE LOTE
        total_emails = len(todos_emails)
        emails_lote = todos_emails[offset:offset + limit_lote]
        emails_restantes = max(0, total_emails - (offset + limit_lote))
        
        print(f"📧 Total na pasta: {total_emails:,} emails")
        print(f"📋 Lote atual: {len(emails_lote)} emails")
        print(f"⏳ Restantes: {emails_restantes:,} emails")
        
        if not emails_lote:
            return {
                'status': 'sucesso',
                'mensagem': 'Todos os emails já foram processados',
                'emails_processados': 0,
                'pdfs_extraidos': 0,
                'faturas_salvas': 0,
                'total_emails': total_emails,
                'offset_atual': offset,
                'emails_restantes': 0,
                'finalizado': True
            }
        
        # ETAPA 2: Processar lote usando função existente
        print(f"\n2️⃣ PROCESSANDO LOTE DE {len(emails_lote)} EMAILS...")
        resultado_lote = _processar_lote_emails(processor, emails_lote)
        
        # ETAPA 3: Resultado do lote
        resultado_final = {
            'status': 'sucesso',
            'mensagem': f'Lote processado: {len(emails_lote)} emails',
            'emails_processados': resultado_lote['emails_processados'],
            'pdfs_extraidos': resultado_lote['pdfs_extraidos'],
            'faturas_salvas': resultado_lote['faturas_salvas'],
            'duplicatas_detectadas': resultado_lote.get('duplicatas_detectadas', 0),
            'erros': resultado_lote.get('erros', 0),
            # 📊 PROGRESSO TOTAL
            'total_emails': total_emails,
            'offset_atual': offset,
            'proximo_offset': offset + limit_lote if emails_restantes > 0 else None,
            'emails_restantes': emails_restantes,
            'finalizado': emails_restantes == 0,
            'progresso_pct': ((offset + len(emails_lote)) / total_emails) * 100,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n✅ LOTE CONCLUÍDO!")
        print(f"   📧 Emails processados: {resultado_final['emails_processados']}")
        print(f"   📎 PDFs extraídos: {resultado_final['pdfs_extraidos']}")  
        print(f"   💾 Faturas salvas: {resultado_final['faturas_salvas']}")
        print(f"   📊 Progresso total: {resultado_final['progresso_pct']:.1f}%")
        print(f"   ⏳ Restam: {emails_restantes:,} emails")
        print(f"="*50)
        
        return resultado_final
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return {
            'status': 'erro',
            'mensagem': str(e),
            'offset_atual': offset
        }


def _processar_lote_emails(processor, emails_lote):
    """
    ✅ REUTILIZAR: Processar lote usando extrair_pdfs_do_email() existente.
    
    MODIFICAÇÃO: Apenas processa lista menor de emails (10 max)
    
    Args:
        processor: EmailProcessor instance (já testado)
        emails_lote: Lista pequena de emails (máximo 10)
        
    Returns:
        dict: Estatísticas do lote
    """
    try:
        total_lote = len(emails_lote)
        print(f"📧 Processando lote de {total_lote} emails...")
        
        # Contadores
        emails_processados = 0
        pdfs_extraidos = 0
        faturas_salvas = 0
        duplicatas_detectadas = 0
        erros = 0
        
        for i, email in enumerate(emails_lote, 1):
            try:
                email_subject = email.get('subject', 'Sem assunto')[:30]
                
                # ✅ REUTILIZAR: extrair_pdfs_do_email() completo
                # Esta função JÁ faz tudo: extrai, processa, salva database, upload OneDrive
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
                
                # Log de progresso detalhado (lote pequeno)
                print(f"📊 {i}/{total_lote} - {email_subject}")
                
            except Exception as e:
                erros += 1
                print(f"❌ Erro email {i}: {e}")
                continue
        
        # Resultado do lote
        resultado = {
            'emails_processados': emails_processados,
            'pdfs_extraidos': pdfs_extraidos, 
            'faturas_salvas': faturas_salvas,
            'duplicatas_detectadas': duplicatas_detectadas,
            'erros': erros
        }
        
        print(f"\n📊 LOTE PROCESSADO:")
        print(f"   ✅ Emails processados: {emails_processados}")
        print(f"   📎 PDFs extraídos: {pdfs_extraidos}")
        print(f"   💾 Faturas salvas: {faturas_salvas}")
        print(f"   🔄 Duplicatas: {duplicatas_detectadas}")
        print(f"   ❌ Erros: {erros}")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro no processamento do lote: {e}")
        return {
            'emails_processados': 0,
            'pdfs_extraidos': 0,
            'faturas_salvas': 0,
            'duplicatas_detectadas': 0,
            'erros': 1
        }


def _resetar_tabela_existente(database_brk):
    """
    ✅ REUTILIZAR: Conexão do DatabaseBRK para reset.
    MANTÉM FUNÇÃO ORIGINAL sem modificações.
    """
    try:
        if not database_brk.conn:
            print(f"❌ Conexão database não disponível")
            return False
        
        cursor = database_brk.conn.cursor()
        
        # Contar antes
        cursor.execute("SELECT COUNT(*) FROM faturas_brk")
        antes = cursor.fetchone()[0]
        
        print(f"🗑️ Removendo {antes:,} registros existentes...")
        
        # ✅ REUTILIZAR: Reset simples
        cursor.execute("DELETE FROM faturas_brk")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='faturas_brk'")
        database_brk.conn.commit()
        
        # Verificar
        cursor.execute("SELECT COUNT(*) FROM faturas_brk")
        depois = cursor.fetchone()[0]
        
        if depois == 0:
            print(f"✅ Tabela resetada: {antes:,} → 0 registros")
            return True
        else:
            print(f"❌ Reset falhou: ainda há {depois} registros")
            return False
            
    except Exception as e:
        print(f"❌ Erro no reset: {e}")
        return False


def inicializar_reconstituicao_primeira_vez(auth_manager):
    """
    🆕 FUNÇÃO NOVA: Inicializa reconstituição (apenas primeira vez).
    
    - Reset da tabela
    - Backup OneDrive  
    - Retorna estatísticas iniciais
    
    Args:
        auth_manager: MicrosoftAuth instance
        
    Returns:
        dict: Status da inicialização
    """
    try:
        print(f"\n🔄 INICIALIZANDO RECONSTITUIÇÃO TOTAL")
        print(f"="*50)
        
        # ✅ REUTILIZAR: EmailProcessor já testado
        processor = EmailProcessor(auth_manager)
        
        if not processor.database_brk:
            return {
                'status': 'erro',
                'mensagem': 'DatabaseBRK não disponível'
            }
        
        # ETAPA 1: Backup usando função existente
        print(f"1️⃣ BACKUP AUTOMÁTICO...")
        backup_ok = processor.database_brk.forcar_sincronizacao_completa()
        if backup_ok:
            print(f"✅ Backup OneDrive realizado")
        else:
            print(f"⚠️ Backup falhou - continuando...")
        
        # ETAPA 2: Reset da tabela usando conexão existente
        print(f"2️⃣ RESETANDO TABELA...")
        if not _resetar_tabela_existente(processor.database_brk):
            return {
                'status': 'erro',
                'mensagem': 'Falha no reset da tabela'
            }
        
        # ETAPA 3: Contar emails totais
        print(f"3️⃣ CONTANDO EMAILS TOTAIS...")
        todos_emails = processor.buscar_emails_novos(9999)
        total_emails = len(todos_emails)
        
        print(f"✅ INICIALIZAÇÃO CONCLUÍDA!")
        print(f"   📧 Total de emails encontrados: {total_emails:,}")
        print(f"   📊 Lotes necessários: {(total_emails + 9) // 10}")  # Arredondar para cima
        print(f"="*50)
        
        return {
            'status': 'sucesso',
            'mensagem': 'Reconstituição inicializada',
            'total_emails': total_emails,
            'backup_realizado': backup_ok,
            'lotes_necessarios': (total_emails + 9) // 10,
            'emails_por_lote': 10,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ ERRO na inicialização: {e}")
        return {
            'status': 'erro',
            'mensagem': str(e)
        }


# ============================================================================
# FUNÇÕES PARA APP.PY (interface em lotes)
# ============================================================================

def executar_reconstituicao_lote(auth_manager, offset=0, limit_lote=10):
    """
    🆕 FUNÇÃO NOVA: Executa um lote da reconstituição.
    
    Args:
        auth_manager: MicrosoftAuth instance
        offset (int): Posição inicial
        limit_lote (int): Quantidade por lote
        
    Returns:
        dict: Resultado do lote + progresso
    """
    return reconstituir_base_brk_lotes(auth_manager, offset, limit_lote)


def obter_estatisticas_pre_reconstituicao(auth_manager):
    """
    ✅ MANTÉM FUNÇÃO ORIGINAL sem modificações.
    
    Args:
        auth_manager: MicrosoftAuth instance
        
    Returns:
        dict: Estatísticas atuais
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
    🆕 INTERFACE NOVA: Interface web para processamento em lotes.
    
    Args:
        estatisticas (dict): Estatísticas do sistema
        progresso (dict): Progresso atual (se existir)
        inicializacao (dict): Resultado da inicialização (se existir)
        
    Returns:
        str: HTML da interface em lotes
    """
    # Se há resultado de inicialização, mostrar tela de sucesso
    if inicializacao and inicializacao.get('status') == 'sucesso':
        return _gerar_interface_inicializacao_sucesso(inicializacao)
    
    pasta_stats = estatisticas.get('pasta_brk', {})
    db_stats = estatisticas.get('database_atual', {})
    
    # Se há progresso, mostrar interface de continuação
    if progresso and not progresso.get('finalizado', False):
        return _gerar_interface_continuacao(progresso)
    
    # Interface inicial
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <title>🔄 Reconstituição BRK - Em Lotes</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 40px; 
                background: #f5f5f5; 
            }}
            .container {{ 
                max-width: 800px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px; 
                border-radius: 10px; 
                box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
            }}
            .info {{ 
                background: #e3f2fd; 
                border: 1px solid #2196f3; 
                color: #1565c0; 
                padding: 20px; 
                border-radius: 8px; 
                margin: 20px 0; 
                border-left: 5px solid #2196f3; 
            }}
            .stats {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 15px; 
                margin: 20px 0; 
            }}
            .stat-card {{ 
                background: #f8f9fa; 
                padding: 15px; 
                border-radius: 8px; 
                text-align: center; 
            }}
            .button {{ 
                background: #2196f3; 
                color: white; 
                padding: 15px 30px; 
                border: none; 
                border-radius: 8px; 
                font-size: 16px; 
                cursor: pointer; 
                margin: 10px 5px; 
                text-decoration: none; 
                display: inline-block; 
            }}
            .button:hover {{ background: #1976d2; }}
            .button-secondary {{ background: #6c757d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔄 Reconstituição BRK - Processamento em Lotes</h1>
            <p>Sistema otimizado para evitar timeout do Render</p>
            
            <div class="info">
                <h3>💡 COMO FUNCIONA:</h3>
                <ul>
                    <li>📋 Processa <strong>10 emails por vez</strong> (evita timeout)</li>
                    <li>⏱️ Cada lote demora ~10-15 segundos</li>
                    <li>🔄 Clique "Processar Próximo Lote" para continuar</li>
                    <li>📊 Progresso salvo automaticamente</li>
                    <li>✅ Para de ~250 emails = ~25 cliques</li>
                </ul>
            </div>
            
            <h3>📊 Status Atual do Sistema</h3>
            <div class="stats">
                <div class="stat-card">
                    <h4>📧 Emails BRK</h4>
                    <p><strong>{pasta_stats.get('total_geral', 'N/A'):,}</strong> total</p>
                    <p>{pasta_stats.get('mes_atual', 'N/A')} mês atual</p>
                </div>
                <div class="stat-card">
                    <h4>💾 Database Atual</h4>
                    <p><strong>{db_stats.get('total_faturas', 'N/A'):,}</strong> faturas</p>
                    <p>{'OneDrive' if db_stats.get('usando_onedrive') else 'Local'}</p>
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <form method="post" action="/executar-reconstituicao" onsubmit="return confirmarInicializacao()">
                    <input type="hidden" name="acao" value="inicializar">
                    <button type="submit" class="button" id="btnInicializar">
                        🚀 INICIALIZAR RECONSTITUIÇÃO
                    </button>
                </form>
                <a href="/" class="button button-secondary">🏠 Voltar ao Dashboard</a>
            </div>
        </div>
        
        <script>
            function confirmarInicializacao() {{
                const confirmacao = confirm('ATENÇÃO: Esta operação irá ZERAR a base atual e reprocessar todos os emails.\\n\\nIniciar processamento em lotes?');
                if (!confirmacao) return false;
                
                // Mostrar progresso
                const btn = document.getElementById('btnInicializar');
                btn.disabled = true;
                btn.innerHTML = '⏳ INICIALIZANDO... (backup + reset)';
                
                return true;
            }}
        </script>
    </body>
    </html>
    """
    
    return html


def _gerar_interface_continuacao(progresso):
    """
    🆕 INTERFACE DE CONTINUAÇÃO: Mostra progresso e botão continuar.
    
    Args:
        progresso (dict): Dados do progresso atual
        
    Returns:
        str: HTML da interface de continuação
    """
    
    progresso_pct = progresso.get('progresso_pct', 0)
    emails_restantes = progresso.get('emails_restantes', 0)
    proximo_offset = progresso.get('proximo_offset', 0)
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <title>🔄 Reconstituição BRK - Lote Concluído</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 700px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .progress {{ background: #e9ecef; height: 30px; border-radius: 15px; overflow: hidden; margin: 20px 0; }}
            .progress-bar {{ background: #28a745; height: 100%; width: {progresso_pct}%; transition: width 0.5s; }}
            .button {{ background: #28a745; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; margin: 10px 5px; text-decoration: none; display: inline-block; }}
            .button:hover {{ background: #218838; }}
            .button-secondary {{ background: #6c757d; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
            .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Lote Processado com Sucesso!</h1>
            
            <div class="success">
                <h3>📊 Resultado do Lote:</h3>
                <p><strong>Emails processados:</strong> {progresso.get('emails_processados', 0)}</p>
                <p><strong>PDFs extraídos:</strong> {progresso.get('pdfs_extraidos', 0)}</p>
                <p><strong>Faturas salvas:</strong> {progresso.get('faturas_salvas', 0)}</p>
            </div>
            
            <h3>📈 Progresso Total:</h3>
            <div class="progress">
                <div class="progress-bar"></div>
            </div>
            <p style="text-align: center;"><strong>{progresso_pct:.1f}% concluído</strong></p>
            
            <div class="stats">
                <div class="stat-card">
                    <h4>📧 Restantes</h4>
                    <p><strong>{emails_restantes:,}</strong> emails</p>
                </div>
                <div class="stat-card">
                    <h4>📋 Lotes</h4>
                    <p><strong>~{(emails_restantes + 9) // 10}</strong> restantes</p>
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <form method="post" action="/executar-reconstituicao">
                    <input type="hidden" name="acao" value="continuar">
                    <input type="hidden" name="offset" value="{proximo_offset}">
                    <button type="submit" class="button">
                        🚀 PROCESSAR PRÓXIMOS 10 EMAILS
                    </button>
                </form>
                <a href="/" class="button button-secondary">🏠 Pausar e Voltar</a>
            </div>
            
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <small><strong>💡 Dica:</strong> Deixe esta página aberta e continue clicando "Processar Próximos 10" até finalizar.</small>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def gerar_resultado_final_lotes(resultado):
    """
    🆕 RESULTADO FINAL: Página quando termina todos os lotes.
    
    Args:
        resultado (dict): Resultado final da reconstituição
        
    Returns:
        str: HTML do resultado final
    """
    
    if resultado.get('finalizado', False):
        cor = '#28a745'
        emoji = '✅'
        titulo = 'RECONSTITUIÇÃO CONCLUÍDA!'
    else:
        cor = '#dc3545'
        emoji = '❌' 
        titulo = 'RECONSTITUIÇÃO INTERROMPIDA'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{emoji} Reconstituição BRK - Finalizada</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial; margin: 40px; text-align: center; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            .header {{ background: {cor}; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .stats {{ text-align: left; margin: 20px 0; }}
            .button {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{emoji} {titulo}</h1>
            </div>
            
            <div class="stats">
                <h3>📊 Resultado Final:</h3>
                <p><strong>Status:</strong> {resultado.get('status', 'desconhecido').title()}</p>
                <p><strong>Progresso:</strong> {resultado.get('progresso_pct', 0):.1f}%</p>
                <p><strong>Emails processados:</strong> {resultado.get('emails_processados', 0):,}</p>
                <p><strong>PDFs extraídos:</strong> {resultado.get('pdfs_extraidos', 0):,}</p>
                <p><strong>Faturas salvas:</strong> {resultado.get('faturas_salvas', 0):,}</p>
                <p><strong>Timestamp:</strong> {resultado.get('timestamp', 'N/A')[:19]}</p>
            </div>
            
            <div>
                <a href="/" class="button">🏠 Voltar ao Dashboard</a>
                <a href="/reconstituicao-brk" class="button">🔄 Nova Reconstituição</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def _gerar_interface_inicializacao_sucesso(resultado):
    """Interface de sucesso da inicialização"""
    total_emails = resultado.get('total_emails', 0)
    lotes_necessarios = resultado.get('lotes_necessarios', 0)
    
    return f"""<!DOCTYPE html>
    <html><head><title>✅ Inicialização Concluída</title><meta charset="UTF-8">
    <style>body{{font-family:Arial;margin:40px;background:#f5f5f5;}}.container{{max-width:600px;margin:0 auto;background:white;padding:30px;border-radius:10px;}}</style>
    </head><body><div class="container">
    <h1>✅ Reconstituição Inicializada!</h1>
    <p>📊 {total_emails:,} emails encontrados</p>
    <p>📋 {lotes_necessarios} lotes necessários</p>
    <form method="post" action="/executar-reconstituicao">
        <input type="hidden" name="acao" value="continuar">
        <input type="hidden" name="offset" value="0">
        <button type="submit">🚀 PROCESSAR PRIMEIROS 10 EMAILS</button>
    </form>
    </div></body></html>"""


# ============================================================================
# FUNÇÕES DE COMPATIBILIDADE (manter originais funcionando)
# ============================================================================

def executar_reconstituicao_simples(auth_manager):
    """
    ✅ COMPATIBILIDADE: Mantém função original para não quebrar código existente.
    Agora redireciona para versão em lotes.
    """
    return reconstituir_base_brk_lotes(auth_manager, offset=0, limit_lote=10)


def gerar_interface_web_simples(estatisticas):
    """
    ✅ COMPATIBILIDADE: Mantém função original.
    Agora redireciona para versão em lotes.
    """
    return gerar_interface_web_lotes(estatisticas)
