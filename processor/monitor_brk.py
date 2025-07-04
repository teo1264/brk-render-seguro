#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/monitor_brk.py
💾 ONDE SALVAR: brk-monitor-seguro/processor/monitor_brk.py
📦 FUNÇÃO: Monitor automático BRK - orquestração simples
🔧 DESCRIÇÃO: Usa métodos que JÁ EXISTEM em EmailProcessor
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua

🚨 DEPENDÊNCIAS OBRIGATÓRIAS:
   📁 Este módulo DEPENDE de outros módulos na pasta processor/:
   
   ✅ processor/email_processor.py (OBRIGATÓRIO)
      └─ Métodos usados:
         • diagnosticar_pasta_brk() - estatísticas da pasta
         • buscar_emails_novos() - busca emails por período  
         • extrair_pdfs_do_email() - extração completa PDFs
         • log_consolidado_email() - logs estruturados bonitos
         • obter_estatisticas_avancadas() - stats do sistema
   
   ✅ processor/database_brk.py (OPCIONAL - via EmailProcessor)
      └─ Usado indiretamente se EmailProcessor tem DatabaseBRK integrado
      └─ Métodos: salvar_fatura(), obter_estatisticas()
   
   ⚠️ IMPORTANTE:
   - Este monitor NÃO cria funcionalidades novas
   - Apenas ORQUESTRA métodos que já existem
   - Se EmailProcessor falhar, este monitor falha também
   - Estrutura modular: auth/ + processor/ + admin/

📋 FUNCIONAMENTO:
   • Roda em thread daemon (não bloqueia Flask)
   • Verifica emails a cada 10 minutos automaticamente
   • Exibe logs estruturados no Render
   • Usa apenas métodos seguros e testados
"""

import time
import threading
from datetime import datetime
from typing import Optional


class MonitorBRK:
    """
    Monitor automático para emails BRK.
    
    USA APENAS métodos que JÁ EXISTEM:
    - diagnosticar_pasta_brk()
    - buscar_emails_novos() 
    - extrair_pdfs_do_email()
    - log_consolidado_email()
    
    NÃO cria funcionalidades novas, só ORQUESTRA.
    """
    
    def __init__(self, email_processor):
        """
        Inicializar monitor com processador existente.
        
        Args:
            email_processor: Instância de EmailProcessor já configurada
        """
        self.processor = email_processor
        self.ativo = False
        self.thread_monitor = None
        self.intervalo_minutos = 30
        
        # 🔍 VALIDAR DEPENDÊNCIAS OBRIGATÓRIAS
        self._validar_dependencias()
        
        print(f"📊 Monitor BRK inicializado")
        print(f"   ⏰ Intervalo: {self.intervalo_minutos} minutos")
        print(f"   🔧 Usando métodos existentes do EmailProcessor")
        print(f"   ✅ Dependências validadas com sucesso")

    def _validar_dependencias(self):
        """
        Valida se EmailProcessor tem todos os métodos necessários.
        Falha rapidamente se dependências não estão disponíveis.
        """
        metodos_obrigatorios = [
            'diagnosticar_pasta_brk',
            'buscar_emails_novos', 
            'extrair_pdfs_do_email',
            'log_consolidado_email',
            'obter_estatisticas_avancadas'
        ]
        
        metodos_faltando = []
        
        for metodo in metodos_obrigatorios:
            if not hasattr(self.processor, metodo):
                metodos_faltando.append(metodo)
        
        if metodos_faltando:
            erro_msg = f"❌ EmailProcessor está faltando métodos obrigatórios: {', '.join(metodos_faltando)}"
            erro_msg += f"\n💡 Verifique se processor/email_processor.py está completo e consistente"
            raise AttributeError(erro_msg)
        
        # Validação adicional - instância não None
        if not self.processor:
            raise ValueError("❌ EmailProcessor não pode ser None")
        
        # Validação adicional - autenticação
        if not hasattr(self.processor, 'auth') or not self.processor.auth:
            raise ValueError("❌ EmailProcessor deve ter autenticação configurada")

    def exibir_estatisticas_pasta(self):
        """
        Exibe estatísticas da pasta BRK usando método existente.
        USA: diagnosticar_pasta_brk() que JÁ EXISTE
        """
        try:
            print(f"📊 ESTATÍSTICAS PASTA BRK:")
            
            # ✅ USAR método que JÁ EXISTE
            stats = self.processor.diagnosticar_pasta_brk()
            
            if stats.get('status') == 'sucesso':
                print(f"   📧 Total na pasta: {stats.get('total_geral', 0):,} emails")
                print(f"   📅 Mês atual: {stats.get('mes_atual', 0)} emails")
                print(f"   ⏰ Últimas 24h: {stats.get('ultimas_24h', 0)} emails")
            else:
                print(f"   ❌ Erro obtendo estatísticas: {stats.get('erro', 'Desconhecido')}")
                
        except Exception as e:
            print(f"   ❌ Erro nas estatísticas: {e}")

    def processar_emails_novos(self):
        """
        Processa emails novos dos últimos 10 minutos.
        USA: buscar_emails_novos() + extrair_pdfs_do_email() que JÁ EXISTEM
        """
        try:
            print(f"🔍 Processando emails novos (últimos {self.intervalo_minutos} min)...")
            
            # ✅ USAR método que JÁ EXISTE - 10 minutos = 0.0069 dias
            dias_atras = self.intervalo_minutos / (24 * 60)  # Converter minutos para dias
            emails = self.processor.buscar_emails_novos(dias_atras)
            
            if not emails:
                print(f"📭 Nenhum email novo encontrado")
                return
            
            print(f"📧 {len(emails)} emails novos encontrados")
            
            # Processar cada email
            emails_processados = 0
            pdfs_processados = 0
            
            for email in emails:
                try:
                    # ✅ USAR método que JÁ EXISTE
                    pdfs_dados = self.processor.extrair_pdfs_do_email(email)
                    
                    if pdfs_dados:
                        # ✅ USAR método que JÁ EXISTE para logs bonitos
                        self.processor.log_consolidado_email(email, pdfs_dados)
                        
                        emails_processados += 1
                        pdfs_processados += len(pdfs_dados)
                        
                        # Log resumido adicional
                        for pdf in pdfs_dados:
                            if pdf.get('dados_extraidos_ok', False):
                                cdc = pdf.get('Codigo_Cliente', 'N/A')
                                casa = pdf.get('Casa de Oração', 'N/A')
                                valor = pdf.get('Valor', 'N/A')
                                print(f"  💾 Processado: CDC {cdc} → {casa} → R$ {valor}")
                    
                except Exception as e:
                    print(f"  ❌ Erro processando email: {e}")
                    continue
            
            # Resumo final
            print(f"✅ Processamento concluído:")
            print(f"   📧 Emails processados: {emails_processados}")
            print(f"   📎 PDFs extraídos: {pdfs_processados}")
            
        except Exception as e:
            print(f"❌ Erro no processamento: {e}")

   def executar_ciclo_completo(self):
    """
    Executa ciclo completo: emails + planilha integrada
    ✅ NOVO: Inclui atualização automática da planilha
    """
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"\n🔄 [{timestamp}] MONITOR BRK INTEGRADO - Ciclo completo")
    print(f"=" * 55)
    
    try:
        # 1. ETAPA EMAILS (lógica existente)
        print("📧 ETAPA 1: Processamento de emails")
        self.exibir_estatisticas_pasta()
        print()
        self.processar_emails_novos()
        
        # 2. ETAPA PLANILHA (NOVA)
        print(f"\n📊 ETAPA 2: Atualização planilha BRK")
        self.atualizar_planilha_automatica()
        
    except Exception as e:
        print(f"❌ Erro no ciclo integrado: {e}")
    
    print(f"=" * 55)
    print(f"⏰ Próximo ciclo em {self.intervalo_minutos} minutos")

    def atualizar_planilha_automatica(self):
    """
    NOVA FUNÇÃO: Atualizar planilha com sistema backup inteligente
    """
    try:
        print("📊 Gerando planilha atualizada...")
        
        # Importar módulos necessários
        from processor.excel_brk import ExcelGeneratorBRK
        from processor.planilha_backup import salvar_planilha_inteligente
        
        # Gerar dados da planilha
        excel_generator = ExcelGeneratorBRK()
        dados_planilha = excel_generator.gerar_excel_bytes()
        
        if dados_planilha:
            print("📊 Dados da planilha gerados com sucesso")
            
            # Usar sistema backup inteligente
            sucesso = salvar_planilha_inteligente(self.processor.auth, dados_planilha)
            
            if sucesso:
                print("✅ Planilha atualizada com sucesso")
            else:
                print("❌ Falha no salvamento da planilha")
        else:
            print("❌ Erro gerando dados da planilha")
            
    except ImportError as e:
        print(f"❌ Módulo não encontrado: {e}")
        print("⚠️ Verifique se processor/excel_brk.py e processor/planilha_backup.py existem")
    except Exception as e:
        print(f"❌ Erro atualizando planilha: {e}")      

    def iniciar_monitoramento(self):
        """
        Inicia monitoramento em background.
        Thread não-blocking para não travar Flask.
        """
        if self.ativo:
            print(f"⚠️ Monitor já está ativo")
            return
        
        try:
            self.ativo = True
            
            # Criar thread daemon (não impede shutdown do app)
            self.thread_monitor = threading.Thread(
                target=self.loop_monitoramento,
                daemon=True,
                name="MonitorBRK"
            )
            
            self.thread_monitor.start()
            print(f"✅ Monitor BRK iniciado em background")
            
            # Executar primeiro ciclo imediatamente (opcional)
            # threading.Thread(target=self.executar_ciclo_completo, daemon=True).start()
            
        except Exception as e:
            print(f"❌ Erro iniciando monitor: {e}")
            self.ativo = False

    def parar_monitoramento(self):
        """
        Para o monitoramento.
        """
        if not self.ativo:
            print(f"⚠️ Monitor não está ativo")
            return
        
        print(f"🛑 Parando monitor BRK...")
        self.ativo = False
        
        # Aguardar thread terminar (máximo 5 segundos)
        if self.thread_monitor and self.thread_monitor.is_alive():
            self.thread_monitor.join(timeout=5)
        
        print(f"✅ Monitor BRK parado")

    def status_monitor(self):
        """
        Retorna status atual do monitor.
        
        Returns:
            Dict: Status do monitoramento
        """
        return {
            "ativo": self.ativo,
            "intervalo_minutos": self.intervalo_minutos,
            "thread_viva": self.thread_monitor.is_alive() if self.thread_monitor else False,
            "processador_ok": bool(self.processor),
            "metodos_disponiveis": {
                "diagnosticar_pasta_brk": hasattr(self.processor, 'diagnosticar_pasta_brk'),
                "buscar_emails_novos": hasattr(self.processor, 'buscar_emails_novos'),
                "extrair_pdfs_do_email": hasattr(self.processor, 'extrair_pdfs_do_email'),
                "log_consolidado_email": hasattr(self.processor, 'log_consolidado_email')
            }
        }

    def executar_ciclo_manual(self):
        """
        Executa um ciclo manual para testes.
        Útil para debug sem aguardar timer.
        """
        print(f"🧪 EXECUÇÃO MANUAL - Teste do monitor")
        self.executar_ciclo_completo()


# ============================================================================
# FUNÇÕES DE UTILIDADE PARA APP.PY
# ============================================================================
def verificar_dependencias_monitor(email_processor) -> dict:
    """
    Verifica dependências para monitor integrado (emails + planilha)
    ✅ ATUALIZADO: Inclui verificação de planilha
    """
    metodos_obrigatorios = [
        'diagnosticar_pasta_brk',
        'buscar_emails_novos',
        'extrair_pdfs_do_email', 
        'log_consolidado_email'
    ]
    
    resultado = {
        "dependencias_ok": True,
        "email_processor_valido": bool(email_processor),
        "autenticacao_ok": False,
        "excel_generator_ok": False,
        "planilha_backup_ok": False,
        "onedrive_brk_ok": False,
        "metodos_disponivel": {},
        "metodos_faltando": [],
        "observacoes": []
    }
    
    # Verificações básicas existentes...
    if not email_processor:
        resultado["dependencias_ok"] = False
        resultado["observacoes"].append("❌ EmailProcessor é None")
        return resultado
    
    # Verificar autenticação
    if hasattr(email_processor, 'auth') and email_processor.auth:
        resultado["autenticacao_ok"] = True
    else:
        resultado["observacoes"].append("⚠️ Autenticação não configurada")
    
    # Verificar métodos obrigatórios
    for metodo in metodos_obrigatorios:
        disponivel = hasattr(email_processor, metodo)
        resultado["metodos_disponivel"][metodo] = disponivel
        
        if not disponivel:
            resultado["metodos_faltando"].append(metodo)
            resultado["dependencias_ok"] = False
    
    # NOVAS VERIFICAÇÕES: Planilha
    try:
        from processor.excel_brk import ExcelGeneratorBRK
        resultado["excel_generator_ok"] = True
        resultado["observacoes"].append("✅ ExcelGeneratorBRK disponível")
    except ImportError:
        resultado["observacoes"].append("❌ ExcelGeneratorBRK não encontrado")
    
    try:
        from processor.planilha_backup import salvar_planilha_inteligente
        resultado["planilha_backup_ok"] = True
        resultado["observacoes"].append("✅ Sistema backup planilha disponível")
    except ImportError:
        resultado["observacoes"].append("❌ Sistema backup planilha não encontrado")
    
    # Verificar ONEDRIVE_BRK_ID
    import os
    if os.getenv('ONEDRIVE_BRK_ID'):
        resultado["onedrive_brk_ok"] = True
        resultado["observacoes"].append("✅ ONEDRIVE_BRK_ID configurado")
    else:
        resultado["observacoes"].append("❌ ONEDRIVE_BRK_ID não configurado")
    
    # Avaliação final
    planilha_ok = (resultado["excel_generator_ok"] and 
                   resultado["planilha_backup_ok"] and 
                   resultado["onedrive_brk_ok"])
    
    if not planilha_ok:
        resultado["observacoes"].append("⚠️ Funcionalidade planilha não disponível")
    
    return resultado

def criar_monitor_brk(email_processor) -> MonitorBRK:
    """
    Factory function para criar monitor.
    
    Args:
        email_processor: Instância configurada de EmailProcessor
        
    Returns:
        MonitorBRK: Monitor pronto para uso
    """
    return MonitorBRK(email_processor)


def iniciar_monitoramento_automatico(email_processor) -> Optional[MonitorBRK]:
    """
    Função de conveniência para app.py.
    Cria e inicia monitor em uma linha.
    
    Args:
        email_processor: EmailProcessor configurado
        
    Returns:
        MonitorBRK: Monitor ativo ou None se erro
    """
    try:
        monitor = criar_monitor_brk(email_processor)
        monitor.iniciar_monitoramento()
        return monitor
        
    except Exception as e:
        print(f"❌ Erro criando monitor automático: {e}")
        return None


# ============================================================================
# EXEMPLO DE USO (para testes e debug)
# ============================================================================

if __name__ == "__main__":
    print(f"🧪 TESTE DO MONITOR BRK")
    print(f"Este módulo deve ser importado pelo app.py")
    print(f"")
    print(f"📋 DEPENDÊNCIAS NECESSÁRIAS:")
    print(f"   ✅ processor/email_processor.py → métodos de processamento")
    print(f"   ✅ processor/database_brk.py → integração database (opcional)")
    print(f"   ✅ auth/microsoft_auth.py → autenticação Microsoft")
    print(f"")
    print(f"🔧 EXEMPLO DE USO NO APP.PY:")
    print(f"")
    print(f"  # 1. Import no topo")
    print(f"  from processor.monitor_brk import verificar_dependencias_monitor, iniciar_monitoramento_automatico")
    print(f"  ")
    print(f"  # 2. Verificar dependências (opcional - para debug)")
    print(f"  processor = EmailProcessor(auth_manager)")
    print(f"  deps = verificar_dependencias_monitor(processor)")
    print(f"  if not deps['dependencias_ok']:")
    print(f"      print('❌ Dependências faltando:', deps['observacoes'])")
    print(f"  ")
    print(f"  # 3. Iniciar monitor automático")
    print(f"  monitor = iniciar_monitoramento_automatico(processor)")
    print(f"")
    print(f"📊 LOGS ESPERADOS NO RENDER:")
    print(f"   🔄 [14:35:00] MONITOR BRK - Verificação automática")
    print(f"   📊 ESTATÍSTICAS PASTA BRK: 1,247 emails total, 23 mês atual")
    print(f"   📧 Email processado: CDC 513-01 → Igreja Central → R$ 127,45")
    print(f"   ✅ Processamento concluído: 1 email, 1 PDF")
    print(f"   ⏰ Próxima verificação em 10 minutos")
