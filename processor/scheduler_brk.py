#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scheduler BRK - Jobs Automáticos
Executa geração automática de planilhas Excel às 06:00h
"""

import schedule
import time
import threading
import logging
from datetime import datetime
from processor.excel_brk import job_automatico_06h

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulerBRK:
    """Scheduler para jobs automáticos do sistema BRK"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        
    def iniciar_scheduler(self):
        """Iniciar scheduler em thread separada"""
        if self.running:
            logger.warning("Scheduler já está rodando")
            return
            
        try:
            # Configurar jobs
            self._configurar_jobs()
            
            # Iniciar em thread separada
            self.running = True
            self.thread = threading.Thread(target=self._executar_scheduler, daemon=True)
            self.thread.start()
            
            logger.info("✅ Scheduler BRK iniciado com sucesso")
            logger.info("📅 Job configurado: Planilha Excel às 06:00h diariamente")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar scheduler: {e}")
            self.running = False
    
    def _configurar_jobs(self):
        """Configurar jobs automáticos"""
        # Job diário às 06:00h - Gerar planilha mês atual
        schedule.every().day.at("06:00").do(self._executar_job_planilha)
        
        logger.info("Jobs configurados:")
        logger.info("- 06:00h: Geração automática planilha BRK (mês atual)")
    
    def _executar_job_planilha(self):
        """Executar job de geração de planilha"""
        try:
            logger.info("🚀 Executando job automático: Geração planilha BRK")
            
            # Executar função do excel_brk.py
            job_automatico_06h()
            
            logger.info("✅ Job planilha concluído com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro no job planilha: {e}")
    
    def _executar_scheduler(self):
        """Loop principal do scheduler"""
        logger.info("Scheduler iniciado - aguardando jobs...")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
                
            except Exception as e:
                logger.error(f"Erro no loop scheduler: {e}")
                time.sleep(60)
    
    def parar_scheduler(self):
        """Parar scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("Scheduler BRK parado")
    
    def status_scheduler(self):
        """Retornar status do scheduler"""
        next_runs = []
        
        for job in schedule.get_jobs():
            next_run = job.next_run
            next_runs.append({
                "job": str(job.job_func.__name__),
                "next_run": next_run.strftime("%d/%m/%Y %H:%M:%S") if next_run else "N/A"
            })
        
        return {
            "running": self.running,
            "jobs_count": len(schedule.get_jobs()),
            "next_runs": next_runs
        }


# Instância global do scheduler
scheduler_brk = SchedulerBRK()

def inicializar_scheduler_automatico():
    """Inicializar scheduler automaticamente (chamado no app.py)"""
    try:
        scheduler_brk.iniciar_scheduler()
        return True
    except Exception as e:
        logger.error(f"Falha ao inicializar scheduler: {e}")
        return False

def obter_status_scheduler():
    """Obter status do scheduler (para endpoints)"""
    return scheduler_brk.status_scheduler()
