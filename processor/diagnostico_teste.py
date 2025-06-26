"""
Diagnóstico de Teste para Sistema BRK
=====================================

Script separado para diagnóstico detalhado de emails teste
Mantém app.py limpo e código organizadamente modular

Uso:
    from processor.diagnostico_teste import ativar_diagnostico
    ativar_diagnostico(email_processor)
"""

import json
import os
from datetime import datetime


def ativar_diagnostico(email_processor):
    """
    Ativar diagnóstico detalhado no EmailProcessor
    
    Args:
        email_processor: Instância do EmailProcessor para diagnosticar
    
    Returns:
        bool: True se diagnóstico foi ativado com sucesso
    """
    try:
        print("\n" + "="*70)
        print("🧪 DIAGNÓSTICO TESTE EMAIL - SCRIPT SEPARADO")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Verificar se email_processor foi fornecido
        if not email_processor:
            print("❌ ERRO: email_processor é None")
            return False
        
        # Executar diagnóstico inicial
        sucesso_diagnostico = _executar_diagnostico_inicial(email_processor)
        
        if sucesso_diagnostico:
            # Instalar monitoramento de emails
            sucesso_monitor = _instalar_monitor_emails(email_processor)
            
            if sucesso_monitor:
                print("\n✅ DIAGNÓSTICO ATIVADO COM SUCESSO!")
                print("📧 Sistema pronto para receber email teste")
                print("🔍 Logs detalhados serão exibidos automaticamente")
                print("="*70)
                return True
            else:
                print("\n❌ Falha ao instalar monitor de emails")
                return False
        else:
            print("\n❌ Falha no diagnóstico inicial")
            return False
            
    except Exception as e:
        print(f"\n❌ ERRO ATIVANDO DIAGNÓSTICO: {e}")
        import traceback
        traceback.print_exc()
        return False


def _executar_diagnostico_inicial(email_processor):
    """
    Diagnóstico inicial do EmailProcessor e DatabaseBRK
    """
    try:
        print("\n🔍 1. DIAGNÓSTICO INICIAL:")
        print(f"   ✅ EmailProcessor tipo: {type(email_processor).__name__}")
        
        # Verificar database_brk
        tem_database = hasattr(email_processor, 'database_brk')
        print(f"   📋 Tem atributo database_brk: {tem_database}")
        
        if tem_database:
            db_valor = getattr(email_processor, 'database_brk', None)
            db_tipo = type(db_valor).__name__ if db_valor else 'None'
            print(f"   📊 database_brk tipo: {db_tipo}")
            
            if db_valor:
                # Verificar métodos essenciais
                metodos_essenciais = [
                    'salvar_fatura', 
                    'status_sistema', 
                    'debug_status_completo'
                ]
                
                print("   🔧 Métodos disponíveis:")
                for metodo in metodos_essenciais:
                    tem_metodo = hasattr(db_valor, metodo)
                    status = "✅" if tem_metodo else "❌"
                    print(f"      {status} {metodo}")
                
                # Tentar executar debug_status_completo
                if hasattr(db_valor, 'debug_status_completo'):
                    print("\n   🔍 Executando debug_status_completo:")
                    try:
                        db_valor.debug_status_completo()
                        print("   ✅ debug_status_completo executado")
                    except Exception as e:
                        print(f"   ❌ Erro debug_status_completo: {e}")
                
            else:
                print("   ⚠️ PROBLEMA: database_brk é None")
                return False
        else:
            print("   ❌ PROBLEMA: database_brk não existe")
            return False
        
        # Verificar método processar_email_fatura
        tem_processar = hasattr(email_processor, 'processar_email_fatura')
        print(f"   🔄 Método processar_email_fatura: {'✅' if tem_processar else '❌'}")
        
        if not tem_processar:
            print("   ❌ PROBLEMA: método processar_email_fatura não existe")
            return False
        
        print("   ✅ Diagnóstico inicial: APROVADO")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro diagnóstico inicial: {e}")
        return False


def _instalar_monitor_emails(email_processor):
    """
    Instalar monitor detalhado para emails de teste
    """
    try:
        print("\n💾 2. BACKUP E INSTALAÇÃO MONITOR:")
        
        # Fazer backup do método original
        if not hasattr(email_processor, '_processar_original_diagnostico'):
            email_processor._processar_original_diagnostico = email_processor.processar_email_fatura
            print("   ✅ Backup método original criado")
        else:
            print("   ⚠️ Backup já existe")
        
        # Instalar monitor
        email_processor.processar_email_fatura = lambda email_data: _processar_email_com_diagnostico(
            email_processor, email_data
        )
        
        print("   ✅ Monitor de emails instalado")
        
        # Criar pasta para logs
        pasta_logs = "/opt/render/project/storage/diagnostico_teste/"
        os.makedirs(pasta_logs, exist_ok=True)
        print(f"   📁 Pasta logs criada: {pasta_logs}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro instalando monitor: {e}")
        return False


def _processar_email_com_diagnostico(email_processor, email_data):
    """
    Processamento de email com diagnóstico detalhado
    """
    timestamp_inicio = datetime.now()
    
    print(f"\n{'='*60}")
    print(f"📧 TESTE EMAIL DETECTADO")
    print(f"🕐 {timestamp_inicio.strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        # Informações básicas do email
        subject = email_data.get('subject', 'N/A')
        print(f"📨 Subject: {subject}")
        print(f"📊 Email data keys: {list(email_data.keys())}")
        
        # ETAPA 1: Verificar DatabaseBRK antes do processamento
        print(f"\n🗃️ ETAPA 1: Verificação DatabaseBRK PRÉ-PROCESSAMENTO")
        
        database_status = _verificar_database_brk(email_processor)
        
        # ETAPA 2: Executar processamento original
        print(f"\n🔄 ETAPA 2: PROCESSAMENTO ORIGINAL")
        
        resultado_original = None
        if hasattr(email_processor, '_processar_original_diagnostico'):
            try:
                print("   🚀 Executando método original...")
                resultado_original = email_processor._processar_original_diagnostico(email_data)
                print(f"   📊 Resultado: {resultado_original}")
            except Exception as e:
                print(f"   ❌ Erro no processamento original: {e}")
                resultado_original = {'success': False, 'error': str(e)}
        else:
            print("   ❌ Método original não disponível")
            resultado_original = {'success': False, 'error': 'Método backup não existe'}
        
        # ETAPA 3: Verificar DatabaseBRK após processamento
        print(f"\n🔍 ETAPA 3: Verificação DatabaseBRK PÓS-PROCESSAMENTO")
        
        database_status_pos = _verificar_database_brk(email_processor)
        
        # ETAPA 4: Teste extração de dados independente
        print(f"\n📋 ETAPA 4: TESTE EXTRAÇÃO DADOS INDEPENDENTE")
        
        dados_extraidos = _testar_extracao_dados(email_processor, email_data)
        
        # ETAPA 5: Salvar log completo
        print(f"\n💾 ETAPA 5: SALVANDO LOG COMPLETO")
        
        log_completo = _salvar_log_teste(
            email_data, 
            resultado_original, 
            database_status, 
            database_status_pos,
            dados_extraidos,
            timestamp_inicio
        )
        
        # RESULTADO FINAL
        print(f"\n🏁 RESULTADO FINAL:")
        print(f"   📧 Email processado: {'✅' if resultado_original.get('success') else '❌'}")
        print(f"   🗃️ DatabaseBRK funcional: {'✅' if database_status['funcional'] else '❌'}")
        print(f"   📊 Dados extraídos: {'✅' if dados_extraidos else '❌'}")
        print(f"   💾 Log salvo: {'✅' if log_completo else '❌'}")
        print(f"   ⏱️ Duração: {(datetime.now() - timestamp_inicio).total_seconds():.2f}s")
        
        print(f"{'='*60}")
        print(f"📧 DIAGNÓSTICO CONCLUÍDO")
        print(f"{'='*60}\n")
        
        return resultado_original
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO NO DIAGNÓSTICO: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': f'Erro diagnóstico: {e}'}


def _verificar_database_brk(email_processor):
    """
    Verificação detalhada do DatabaseBRK
    """
    status = {
        'existe_atributo': False,
        'valor_nao_none': False,
        'metodos_disponiveis': [],
        'funcional': False,
        'status_sistema': None,
        'erro': None
    }
    
    try:
        # Verificar atributo
        status['existe_atributo'] = hasattr(email_processor, 'database_brk')
        print(f"   📋 Atributo database_brk: {'✅' if status['existe_atributo'] else '❌'}")
        
        if status['existe_atributo']:
            db_valor = getattr(email_processor, 'database_brk', None)
            status['valor_nao_none'] = db_valor is not None
            print(f"   📊 Valor não é None: {'✅' if status['valor_nao_none'] else '❌'}")
            
            if status['valor_nao_none']:
                # Verificar métodos
                metodos_verificar = ['salvar_fatura', 'status_sistema', 'debug_status_completo']
                for metodo in metodos_verificar:
                    if hasattr(db_valor, metodo):
                        status['metodos_disponiveis'].append(metodo)
                
                print(f"   🔧 Métodos: {status['metodos_disponiveis']}")
                
                # Tentar status_sistema
                if 'status_sistema' in status['metodos_disponiveis']:
                    try:
                        status['status_sistema'] = db_valor.status_sistema()
                        status['funcional'] = True
                        print(f"   📈 Status sistema: {status['status_sistema']}")
                    except Exception as e:
                        status['erro'] = str(e)
                        print(f"   ❌ Erro status_sistema: {e}")
                        
    except Exception as e:
        status['erro'] = str(e)
        print(f"   ❌ Erro verificação: {e}")
    
    return status


def _testar_extracao_dados(email_processor, email_data):
    """
    Teste independente de extração de dados
    """
    try:
        if hasattr(email_processor, 'extrair_dados_fatura'):
            print("   🔍 Testando extração de dados...")
            dados = email_processor.extrair_dados_fatura(email_data)
            
            if dados:
                print("   ✅ Dados extraídos com sucesso:")
                for key, value in dados.items():
                    print(f"      📊 {key}: {value}")
                return dados
            else:
                print("   ⚠️ Nenhum dado extraído")
                return None
        else:
            print("   ❌ Método extrair_dados_fatura não encontrado")
            return None
            
    except Exception as e:
        print(f"   ❌ Erro extração dados: {e}")
        return None


def _salvar_log_teste(email_data, resultado, db_pre, db_pos, dados, timestamp_inicio):
    """
    Salvar log completo do teste
    """
    try:
        timestamp_fim = datetime.now()
        
        log_completo = {
            'timestamp_inicio': timestamp_inicio.isoformat(),
            'timestamp_fim': timestamp_fim.isoformat(),
            'duracao_segundos': (timestamp_fim - timestamp_inicio).total_seconds(),
            'email_subject': email_data.get('subject', 'N/A'),
            'email_keys': list(email_data.keys()),
            'resultado_processamento': resultado,
            'database_brk_pre': db_pre,
            'database_brk_pos': db_pos,
            'dados_extraidos': dados,
            'diagnostico_versao': '1.0'
        }
        
        # Salvar arquivo
        pasta_logs = "/opt/render/project/storage/diagnostico_teste/"
        arquivo_log = f"{pasta_logs}teste_{timestamp_inicio.strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(arquivo_log, 'w', encoding='utf-8') as f:
            json.dump(log_completo, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 Log salvo: {os.path.basename(arquivo_log)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro salvando log: {e}")
        return False


def desativar_diagnostico(email_processor):
    """
    Desativar diagnóstico e restaurar método original
    """
    try:
        if hasattr(email_processor, '_processar_original_diagnostico'):
            email_processor.processar_email_fatura = email_processor._processar_original_diagnostico
            delattr(email_processor, '_processar_original_diagnostico')
            print("✅ Diagnóstico desativado - método original restaurado")
            return True
        else:
            print("⚠️ Diagnóstico não estava ativo")
            return False
            
    except Exception as e:
        print(f"❌ Erro desativando diagnóstico: {e}")
        return False


# Função de conveniência para verificação rápida
def verificar_sistema_rapido(email_processor):
    """
    Verificação rápida do sistema sem instalar monitor
    """
    print("\n🔍 VERIFICAÇÃO RÁPIDA SISTEMA:")
    print("-" * 40)
    
    if not email_processor:
        print("❌ EmailProcessor é None")
        return False
    
    # Verificações básicas
    checks = [
        ("EmailProcessor existe", email_processor is not None),
        ("Tem database_brk", hasattr(email_processor, 'database_brk')),
        ("database_brk não é None", hasattr(email_processor, 'database_brk') and email_processor.database_brk is not None),
        ("Método processar_email_fatura", hasattr(email_processor, 'processar_email_fatura')),
    ]
    
    for nome, status in checks:
        print(f"   {'✅' if status else '❌'} {nome}")
    
    todos_ok = all(status for _, status in checks)
    print(f"\n{'✅ SISTEMA OK' if todos_ok else '❌ PROBLEMAS DETECTADOS'}")
    print("-" * 40)
    
    return todos_ok
