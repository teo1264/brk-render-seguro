#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/monitor_brk.py - VERSÃO LIMPA
💾 ONDE SALVAR: brk-monitor-seguro/processor/monitor_brk.py
📦 FUNÇÃO: Monitor automático BRK - orquestração simples
🔧 DESCRIÇÃO: Usa métodos que JÁ EXISTEM em EmailProcessor
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
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
        Processa emails novos dos últimos minutos.
        USA: buscar_emails_novos() + extrair_pdfs_do_email() que JÁ EXISTEM
        """
        try:
            print(f"🔍 Processando emails novos (últimos {self.intervalo_minutos} min)...")
            
            # ✅ USAR método que JÁ EXISTE - converter minutos para dias
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
        🆕 FUNÇÃO CORRIGIDA: Atualizar MÚLTIPLAS planilhas automaticamente
        
        ANTES: Gerava apenas planilha do mês atual
        AGORA: Detecta TODOS os meses com faturas e gera planilha para cada um
        """
        try:
            print("📊 Iniciando atualização MÚLTIPLAS planilhas BRK...")
            
            # Importar módulos necessários
            from processor.excel_brk import ExcelGeneratorBRK
            from processor.planilha_backup import salvar_planilha_inteligente
            
            # ✅ Verificar se DatabaseBRK está disponível
            if not hasattr(self.processor, 'database_brk') or not self.processor.database_brk:
                print("❌ DatabaseBRK não disponível - não é possível detectar meses")
                print("⚠️ Usando fallback: apenas mês atual")
                self._atualizar_planilha_mes_atual_fallback()
                return
            
            # ✅ NOVA LÓGICA: Detectar TODOS os meses com faturas
            print("🔍 Detectando meses com faturas no database...")
            meses_com_faturas = self.processor.database_brk.obter_meses_com_faturas()
            
            if not meses_com_faturas:
                print("❌ Nenhum mês com faturas detectado")
                print("⚠️ Usando fallback: apenas mês atual")
                self._atualizar_planilha_mes_atual_fallback()
                return
            
            print(f"✅ {len(meses_com_faturas)} mês(es) com faturas detectado(s)")
            
            # ✅ Criar generator COM autenticação
            excel_generator = ExcelGeneratorBRK()
            excel_generator.auth = self.processor.auth
            
            # ✅ PROCESSAR CADA MÊS INDIVIDUALMENTE
            planilhas_processadas = 0
            planilhas_com_erro = 0
            
            for mes, ano in meses_com_faturas:
                try:
                    print(f"\n📊 PROCESSANDO MÊS: {self._nome_mes(mes)}/{ano}")
                    print(f"=" * 50)
                    
                    # Obter estatísticas do mês para validação
                    stats_mes = self.processor.database_brk.obter_estatisticas_por_mes(mes, ano)
                    if stats_mes.get('status') == 'sucesso':
                        print(f"📈 Faturas encontradas: {stats_mes.get('total_faturas', 0)} (Normais: {stats_mes.get('normais', 0)})")
                    
                    # Gerar dados da planilha específica do mês
                    print(f"🔄 Gerando planilha {mes:02d}/{ano}...")
                    dados_planilha = excel_generator.gerar_planilha_mensal(mes, ano)
                    
                    if dados_planilha:
                        print(f"✅ Planilha {mes:02d}/{ano} gerada: {len(dados_planilha)} bytes")
                        
                        # ✅ USAR SISTEMA BACKUP INTELIGENTE ESPECÍFICO PARA O MÊS
                        print(f"💾 Salvando planilha {mes:02d}/{ano}...")
                        sucesso = salvar_planilha_inteligente(
                            self.processor.auth, 
                            dados_planilha, 
                            mes, 
                            ano
                        )
                        
                        if sucesso:
                            print(f"✅ Planilha {mes:02d}/{ano} atualizada com sucesso")
                            planilhas_processadas += 1
                        else:
                            print(f"❌ Falha salvando planilha {mes:02d}/{ano}")
                            planilhas_com_erro += 1
                    else:
                        print(f"❌ Erro gerando dados da planilha {mes:02d}/{ano}")
                        planilhas_com_erro += 1
                        
                except Exception as e:
                    print(f"❌ Erro processando mês {mes:02d}/{ano}: {e}")
                    planilhas_com_erro += 1
                    continue
            
            # ✅ RESUMO FINAL
            print(f"\n📊 RESUMO ATUALIZAÇÃO MÚLTIPLAS PLANILHAS:")
            print(f"=" * 50)
            print(f"📈 Meses detectados: {len(meses_com_faturas)}")
            print(f"✅ Planilhas atualizadas: {planilhas_processadas}")
            print(f"❌ Planilhas com erro: {planilhas_com_erro}")
            
            # Listar planilhas processadas
            if planilhas_processadas > 0:
                print(f"\n📄 PLANILHAS ATUALIZADAS:")
                for i, (mes, ano) in enumerate(meses_com_faturas):
                    if i < planilhas_processadas:
                        nome_arquivo = f"BRK-Planilha-{ano}-{mes:02d}.xlsx"
                        pasta_destino = f"/BRK/Faturas/{ano}/{mes:02d}/"
                        print(f"   📊 {self._nome_mes(mes)}/{ano} → {pasta_destino}{nome_arquivo}")
            
            if planilhas_processadas > 0:
                print(f"🎯 MISSÃO CUMPRIDA: {planilhas_processadas} planilha(s) atualizada(s)")
            else:
                print(f"⚠️ NENHUMA PLANILHA FOI ATUALIZADA")
                
        except ImportError as e:
            print(f"❌ Módulo não encontrado: {e}")
            print("⚠️ Verifique se processor/excel_brk.py e processor/planilha_backup.py existem")
        except Exception as e:
            print(f"❌ Erro geral atualização múltiplas planilhas: {e}")

    def _atualizar_planilha_mes_atual_fallback(self):
        """
        🔄 FALLBACK: Atualizar apenas planilha do mês atual (lógica original)
        Usado quando detector de meses falha ou DatabaseBRK indisponível
        """
        try:
            print("🔄 FALLBACK: Atualizando apenas planilha do mês atual...")
            
            from processor.excel_brk import ExcelGeneratorBRK
            from processor.planilha_backup import salvar_planilha_inteligente
            
            excel_generator = ExcelGeneratorBRK()
            excel_generator.auth = self.processor.auth
            
            # Usar mês atual (lógica original)
            from datetime import datetime
            hoje = datetime.now()
            dados_planilha = excel_generator.gerar_planilha_mensal(hoje.month, hoje.year)
            
            if dados_planilha:
                print("📊 Planilha mês atual gerada com sucesso")
                
                # Sistema backup (sem especificar mês/ano = usa atual)
                sucesso = salvar_planilha_inteligente(self.processor.auth, dados_planilha)
                
                if sucesso:
                    print("✅ Planilha mês atual atualizada com sucesso")
                else:
                    print("❌ Falha no salvamento da planilha mês atual")
            else:
                print("❌ Erro gerando dados da planilha mês atual")
                
        except Exception as e:
            print(f"❌ Erro fallback planilha mês atual: {e}")

    def _nome_mes(self, numero_mes):
        """Helper: Converte número do mês para nome"""
        meses = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        return meses.get(numero_mes, f"Mês{numero_mes}")

    def diagnosticar_multiplas_planilhas(self):
        """
        🆕 NOVA FUNÇÃO: Diagnóstico das múltiplas planilhas
        Útil para debug e validação do sistema
        """
        try:
            print(f"\n🔍 DIAGNÓSTICO MÚLTIPLAS PLANILHAS BRK")
            print(f"=" * 55)
            
            if not hasattr(self.processor, 'database_brk') or not self.processor.database_brk:
                print("❌ DatabaseBRK não disponível")
                return
            
            # Detectar meses
            meses_detectados = self.processor.database_brk.obter_meses_com_faturas()
            
            print(f"📊 Meses detectados: {len(meses_detectados)}")
            
            for mes, ano in meses_detectados:
                stats = self.processor.database_brk.obter_estatisticas_por_mes(mes, ano)
                nome_arquivo = f"BRK-Planilha-{ano}-{mes:02d}.xlsx"
                pasta = f"/BRK/Faturas/{ano}/{mes:02d}/"
                
                print(f"\n📊 {self._nome_mes(mes)}/{ano}:")
                print(f"   📁 Arquivo: {pasta}{nome_arquivo}")
                print(f"   📈 Faturas: {stats.get('total_faturas', 0)} total")
                print(f"   ✅ Normais: {stats.get('normais', 0)}")
                print(f"   🔄 Duplicatas: {stats.get('duplicatas', 0)}")
                print(f"   ❌ Faltantes: {stats.get('faltantes', 0)}")
            
            print(f"=" * 55)
            
        except Exception as e:
            print(f"❌ Erro diagnóstico múltiplas planilhas: {e}")
           
    def loop_monitoramento(self):
        """
        Loop principal do monitoramento.
        Roda em thread separada.
        """
        print(f"🔄 Loop monitoramento iniciado (intervalo: {self.intervalo_minutos} min)")
        
        while self.ativo:
            try:
                self.executar_ciclo_completo()
                
            except Exception as e:
                print(f"❌ Erro no ciclo de monitoramento: {e}")
                
            # Aguardar próximo ciclo (com verificação de status a cada 30 segundos)
            tempo_restante = self.intervalo_minutos * 60  # Converter para segundos
            
            while tempo_restante > 0 and self.ativo:
                time.sleep(min(30, tempo_restante))  # Dormir em chunks de 30s
                tempo_restante -= 30

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
            
        except Exception as e:
            print(f"❌ Erro iniciando monitor: {e}")
            self.ativo = False

    def parar_monitoramento(self):
        """Para o monitoramento."""
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
