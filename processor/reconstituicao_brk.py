#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/reconstituicao_brk.py
💾 ONDE SALVAR: brk-monitor-seguro/processor/reconstituicao_brk.py
📦 FUNÇÃO: Reconstituição Total da Base BRK - MVP SIMPLES
🔧 DESCRIÇÃO: REUTILIZA 100% funcionalidades existentes
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua

🎯 MVP: Reconstrói base usando funções que JÁ FUNCIONAM
♻️ REUTILIZAÇÃO TOTAL - ZERO código novo
"""

import os
import sys
from datetime import datetime

# ✅ REUTILIZAR: Imports dos módulos que JÁ FUNCIONAM
try:
    from email_processor import EmailProcessor
    from database_brk import DatabaseBRK
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from auth.microsoft_auth import MicrosoftAuth
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from processor.email_processor import EmailProcessor
    from processor.database_brk import DatabaseBRK
    from auth.microsoft_auth import MicrosoftAuth


def reconstituir_base_brk_completa(auth_manager):
    """
    🔄 MVP: Reconstituição Total usando funções existentes.
    
    ESTRATÉGIA: REUTILIZAR tudo que já está testado e funcionando
    
    Args:
        auth_manager: MicrosoftAuth instance
        
    Returns:
        dict: Resultado da operação
    """
    try:
        print(f"\n🔄 RECONSTITUIÇÃO TOTAL DA BASE BRK")
        print(f"="*50)
        print(f"⚡ MVP: Usando funções existentes e testadas")
        
        # ✅ REUTILIZAR: EmailProcessor já testado
        print(f"📧 Inicializando EmailProcessor...")
        processor = EmailProcessor(auth_manager)
        
        if not processor.database_brk:
            return {
                'status': 'erro',
                'mensagem': 'DatabaseBRK não disponível'
            }
        
        print(f"✅ EmailProcessor + DatabaseBRK carregados")
        
        # ETAPA 1: Backup usando função existente
        print(f"\n1️⃣ BACKUP AUTOMÁTICO...")
        backup_ok = processor.database_brk.forcar_sincronizacao_completa()
        if backup_ok:
            print(f"✅ Backup OneDrive realizado")
        else:
            print(f"⚠️ Backup falhou - continuando...")
        
        # ETAPA 2: Reset da tabela usando conexão existente
        print(f"\n2️⃣ RESETANDO TABELA...")
        if not _resetar_tabela_existente(processor.database_brk):
            return {
                'status': 'erro',
                'mensagem': 'Falha no reset da tabela'
            }
        
        # ETAPA 3: Buscar TODOS os emails usando função existente
        print(f"\n3️⃣ BUSCANDO TODOS OS EMAILS...")
        # ✅ REUTILIZAR: buscar_emails_novos() com período grande
        todos_emails = processor.buscar_emails_novos(9999)  # ~27 anos
        
        if not todos_emails:
            return {
                'status': 'erro',
                'mensagem': 'Nenhum email encontrado'
            }
        
        print(f"📧 {len(todos_emails):,} emails encontrados")
        
        # ETAPA 4: Processar usando função existente
        print(f"\n4️⃣ PROCESSANDO TODOS OS EMAILS...")
        resultado_processamento = _processar_todos_emails(processor, todos_emails)
        
        # ETAPA 5: Sincronização final
        print(f"\n5️⃣ SINCRONIZAÇÃO FINAL...")
        sync_final = processor.database_brk.forcar_sincronizacao_completa()
        
        # Resultado final
        resultado_final = {
            'status': 'sucesso',
            'mensagem': 'Reconstituição concluída',
            'emails_processados': resultado_processamento['emails_processados'],
            'pdfs_extraidos': resultado_processamento['pdfs_extraidos'],
            'faturas_salvas': resultado_processamento['faturas_salvas'],
            'backup_inicial': backup_ok,
            'sync_final': sync_final,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n✅ RECONSTITUIÇÃO CONCLUÍDA!")
        print(f"   📧 Emails: {resultado_final['emails_processados']:,}")
        print(f"   📎 PDFs: {resultado_final['pdfs_extraidos']:,}")  
        print(f"   💾 Faturas: {resultado_final['faturas_salvas']:,}")
        print(f"="*50)
        
        return resultado_final
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return {
            'status': 'erro',
            'mensagem': str(e)
        }


def _resetar_tabela_existente(database_brk):
    """
    ✅ REUTILIZAR: Conexão do DatabaseBRK para reset.
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


# ============================================================================
# FUNÇÕES PARA APP.PY (interface simples)
# ============================================================================

def executar_reconstituicao_simples(auth_manager):
    """
    Função simples para chamada do app.py.
    
    Args:
        auth_manager: MicrosoftAuth instance
        
    Returns:
        dict: Resultado da operação
    """
    return reconstituir_base_brk_completa(auth_manager)


def obter_estatisticas_pre_reconstituicao(auth_manager):
    """
    Obter estatísticas antes da reconstituição.
    
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

# ============================================================================
# BLOCO 2/3 - PROCESSAMENTO DE EMAILS
# ADICIONAR no processor/reconstituicao_brk.py após BLOCO 1
# ============================================================================

def _processar_todos_emails(processor, emails_lista):
    """
    ✅ REUTILIZAR: extrair_pdfs_do_email() para processar cada email.
    
    Args:
        processor: EmailProcessor instance (já testado)
        emails_lista: Lista de emails da busca
        
    Returns:
        dict: Estatísticas do processamento
    """
    try:
        total_emails = len(emails_lista)
        print(f"📧 Processando {total_emails:,} emails...")
        
        # Contadores
        emails_processados = 0
        pdfs_extraidos = 0
        faturas_salvas = 0
        duplicatas_detectadas = 0
        erros = 0
        
        for i, email in enumerate(emails_lista, 1):
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
                
                # Log de progresso a cada 100 emails
                if i % 100 == 0 or i <= 10 or i == total_emails:
                    progresso_pct = (i / total_emails) * 100
                    print(f"📊 {i:,}/{total_emails:,} ({progresso_pct:.1f}%) - {email_subject}")
                
            except Exception as e:
                erros += 1
                if erros <= 5:  # Log apenas primeiros erros
                    print(f"❌ Erro email {i}: {e}")
                continue
        
        # Resultado do processamento
        resultado = {
            'emails_processados': emails_processados,
            'pdfs_extraidos': pdfs_extraidos, 
            'faturas_salvas': faturas_salvas,
            'duplicatas_detectadas': duplicatas_detectadas,
            'erros': erros
        }
        
        print(f"\n📊 PROCESSAMENTO CONCLUÍDO:")
        print(f"   ✅ Emails processados: {emails_processados:,}")
        print(f"   📎 PDFs extraídos: {pdfs_extraidos:,}")
        print(f"   💾 Faturas salvas: {faturas_salvas:,}")
        print(f"   🔄 Duplicatas: {duplicatas_detectadas:,}")
        print(f"   ❌ Erros: {erros:,}")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro no processamento geral: {e}")
        return {
            'emails_processados': 0,
            'pdfs_extraidos': 0,
            'faturas_salvas': 0,
            'duplicatas_detectadas': 0,
            'erros': 1
        }


# ============================================================================
# FUNÇÕES DE INTERFACE WEB SIMPLES (opcional)
# ============================================================================

def gerar_interface_web_simples(estatisticas):
    """
    Interface web simples para reconstituição.
    
    Args:
        estatisticas (dict): Estatísticas do sistema
        
    Returns:
        str: HTML da interface
    """
    
    pasta_stats = estatisticas.get('pasta_brk', {})
    db_stats = estatisticas.get('database_atual', {})
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <title>🔄 Reconstituição BRK - MVP</title>
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
            .warning {{ 
                background: #fff3cd; 
                border: 1px solid #ffeaa7; 
                color: #856404; 
                padding: 20px; 
                border-radius: 8px; 
                margin: 20px 0; 
                border-left: 5px solid #f39c12; 
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
                background: #dc3545; 
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
            .button:hover {{ background: #c82333; }}
            .button-secondary {{ background: #6c757d; }}
            .button:disabled {{ background: #aaa; cursor: not-allowed; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔄 Reconstituição Total da Base BRK</h1>
            <p>Sistema MVP usando funções existentes testadas</p>
            
            <div class="warning">
                <h3>⚠️ OPERAÇÃO CRÍTICA</h3>
                <p><strong>Esta operação irá:</strong></p>
                <ul>
                    <li>🗑️ ZERAR completamente a base atual</li>
                    <li>📧 Reprocessar TODOS os emails históricos</li>
                    <li>💾 Reconstruir base com dados atualizados</li>
                    <li>⏱️ Pode demorar horas dependendo do volume</li>
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
                <form method="post" action="/executar-reconstituicao" onsubmit="return confirmarOperacao()">
                    <button type="submit" class="button" id="btnExecutar">
                        🚀 EXECUTAR RECONSTITUIÇÃO
                    </button>
                </form>
                <a href="/" class="button button-secondary">🏠 Voltar ao Dashboard</a>
            </div>
        </div>
        
        <script>
            function confirmarOperacao() {{
                const confirmacao1 = confirm('ATENÇÃO: Esta operação irá ZERAR toda a base atual.\\n\\nDeseja continuar?');
                if (!confirmacao1) return false;
                
                const confirmacao2 = confirm('ÚLTIMA CONFIRMAÇÃO:\\n\\nTem certeza que deseja executar a reconstituição total?');
                if (!confirmacao2) return false;
                
                // Desabilitar botão e mostrar progresso
                const btn = document.getElementById('btnExecutar');
                btn.disabled = true;
                btn.innerHTML = '⏳ EXECUTANDO... (NÃO FECHE A PÁGINA)';
                
                return true;
            }}
        </script>
    </body>
    </html>
    """
    
    return html


def gerar_resultado_final(resultado):
    """
    Página de resultado da reconstituição.
    
    Args:
        resultado (dict): Resultado da operação
        
    Returns:
        str: HTML do resultado
    """
    
    if resultado.get('status') == 'sucesso':
        cor = '#28a745'
        emoji = '✅'
        titulo = 'RECONSTITUIÇÃO CONCLUÍDA!'
    else:
        cor = '#dc3545'
        emoji = '❌' 
        titulo = 'OPERAÇÃO FALHOU'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{emoji} Resultado - Reconstituição BRK</title>
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
                <h3>📊 Resultado da Operação:</h3>
                <p><strong>Status:</strong> {resultado.get('status', 'desconhecido').title()}</p>
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
