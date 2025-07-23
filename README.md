# 💰 Sistema BRK - Proteção Financeira Automatizada

## 📋 Visão Geral

Sistema automático de processamento e controle financeiro para faturas da BRK, desenvolvido especificamente para a tesouraria. Monitora emails, detecta vazamentos, previne pagamentos duplicados e gera planilhas organizadas para tomada de decisão financeira.

**🎯 Objetivo Principal:** Automatizar controle de contas de água e prevenção de irregularidades nas 36 Casas de Oração + 2 prédios administrativos.

### **4. 🚨 Sistema de Alertas Inteligente** ✅ NOVO

#### **Alertas Direcionados por CO**
- **Notificação automática** para responsáveis específicos de cada Casa de Oração
- **Múltiplos usuários** podem ser cadastrados por CO (Tesoureiro, Encarregado, etc.)
- **Fallback automático** para administradores se CO não tem responsáveis
- **Rate limiting** inteligente para evitar bloqueio do bot Telegram

#### **5 Tipos de Alerta Personalizados**
1. **🟢 Consumo Normal:** Notificação informativa com dados da fatura
2. **🟡 Alto Consumo:** Aviso com instruções para verificação de vazamentos
3. **🔴 Crítico:** Alerta prioritário com ações específicas requeridas
4. **🚨 Emergência:** Alerta máximo com instrução de bloqueio débito automático
5. **📉 Consumo Baixo:** Notificação sobre consumo anormalmente reduzido

#### **Templates Profissionais**
- **Saudação personalizada** ("A Paz de Deus!")
- **Dados completos** da fatura (casa, vencimento, valor, consumo)
- **Análise comparativa** com média dos últimos 6 meses
- **Instruções específicas** por tipo de alerta
- **Identificação automática** do sistema BRK

#### **Arquitetura Distribuída**
- **Sistema Principal (BRK):** Processa faturas e detecta alertas
- **Sistema Auxiliar (CCB):** Gerencia cadastro de responsáveis por CO
- **Integração Automática:** Via OneDrive compartilhado e API Telegram
- **Backup e Fallback:** Admin sempre recebe cópia em caso de falha

---

## ✅ Status do Sistema

### **🟢 Funcionamento Atual**
- ✅ **Monitoramento Automático:** Verifica emails BRK a cada 60 minutos
- ✅ **Processamento Inteligente:** Extrai e analisa todas as faturas automaticamente  
- ✅ **Proteção Ativa:** Detecta e bloqueia débitos suspeitos
- ✅ **Planilhas Múltiplas:** Gera relatórios específicos por mês automaticamente
- ✅ **Interface Web:** Dashboard completo disponível 24/7
- ✅ **Backup Automático:** Dados salvos no OneDrive em tempo real
- ✅ **Alertas Direcionados:** Notifica responsáveis específicos por CO via Telegram ✅ NOVO
- ✅ **Sistema Distribuído:** Integração BRK + CCB para gestão completa ✅ NOVO

### **📊 Números Atuais**
- **39 instalações monitoradas** (100% de cobertura)
- **36 Casas de Oração + 2 prédios administrativos**
- **Até 39 faturas/mês processadas**
- **258+ emails processados** automaticamente
- **Detecção automática de vazamentos** com alertas direcionados
- **Múltiplos responsáveis** notificados automaticamente por CO ✅ NOVO
- **5 tipos de alerta** personalizados por consumo ✅ NOVO

---

## 🚀 Principais Funcionalidades

### **1. 🛡️ Proteção Financeira Ativa**

#### **Detecção de Vazamentos**
- Análise automática do consumo vs. média dos últimos 6 meses
- **4 níveis de alerta:** Normal, Alto, Crítico, Emergência
- **Bloqueio automático** de débitos quando detecta consumo anômalo
- Prevenção de custos desnecessários

#### **Controle de Duplicatas**
- Sistema SEEK impede processamento de faturas duplicadas
- Identificação por CDC + Competência (método Clipper)
- **Evita pagamento duplo** de forma automática
- Histórico completo para auditoria

### **2. 📊 Geração Inteligente de Planilhas**

#### **Múltiplas Planilhas Automáticas**
- **Sistema detecta automaticamente** todos os meses com faturas
- **Gera planilha específica** para cada período
- Organização por vencimento e separação PIA vs Casas de Oração
- Upload automático para OneDrive com nomenclatura padronizada

#### **Seções Organizadas**
- **Principais:** Faturas aprovadas (entram nos totais)
- **Controle:** Faturas que precisam verificação manual
- **CO's Sem Email:** Lista das 39 instalações que não enviaram fatura
- **Totais e Subtotais:** Base para decisões de pagamento

### **3. 🔄 Automação Completa**

#### **Monitor Integrado v2.0**
- **Ciclo automático a cada 60 minutos:**
  - Processamento de emails novos
  - Atualização de múltiplas planilhas
  - Backup automático dos dados
- **Thread não-bloqueante:** Não interfere no acesso web
- **Logs detalhados:** Rastreabilidade completa de operações

#### **Validações Automáticas**
- Verificação de dependências antes de executar
- Fallback automático em caso de falhas
- Sistema de recuperação em múltiplas camadas

---

## 💻 Como Usar o Sistema

### **🌐 Interface Web Principal**
Acesse: `https://[seu-dominio]/`

#### **Dashboard Principal**
- Visão geral do sistema e status do monitor
- Estatísticas das 39 instalações monitoradas
- Links rápidos para principais funções

#### **Processamento Manual**
- **Rota:** `/processar-emails-form`
- **Função:** Processar emails específicos sob demanda
- **Uso:** Quando precisar forçar processamento imediato

#### **Geração de Planilhas**
- **Rota:** `/gerar-planilha-brk`
- **Função:** Gerar planilha de qualquer mês/ano específico
- **Uso:** Relatórios históricos ou reprocessamento

#### **Interface DBEDIT**
- **Rota:** `/dbedit`
- **Função:** Visualização estilo Clipper dos dados
- **Uso:** Navegação e consulta detalhada das faturas

### **📋 Diagnósticos e Monitoramento**

#### **Status do Sistema**
- **Rota:** `/status-monitor-integrado`
- **Função:** Verificar se automação está funcionando
- **Uso:** Diagnóstico diário ou quando suspeitar de problemas

#### **Teste de Conectividade**
- **Rota:** `/test-onedrive`
- **Função:** Verificar conexão com OneDrive
- **Uso:** Validar backup e sincronização

---

## 🔧 Recursos de Proteção

### **🏦 Separação Bancária Automática**
- **PIA:** Faturas que devem ser pagas pela conta PIA
- **Casas de Oração:** Faturas das 39 instalações monitoradas
- **Subtotais separados** para cada conta bancária
- **Prevenção de confusão** entre contas

### **🚨 Alertas e Controles**
- **CO's Sem Email:** Detecta quando alguma das 39 instalações não enviou fatura
- **Consumo Anômalo:** Identifica vazamentos ou medições incorretas
- **Faturas Duplicadas:** Evita reprocessamento de emails reenviados
- **Seção Controle:** Separação de faturas que precisam verificação

### **💾 Backup e Segurança**
- **OneDrive Sync:** Backup automático após cada operação
- **Cache Local:** Fallback em caso de problemas de conexão
- **Logs Completos:** Rastreabilidade de todas as operações
- **Nomenclatura Padronizada:** Organização `/YYYY/MM/` no OneDrive

---

## ⚙️ Configuração e Requisitos

### **🔐 Autenticação Necessária**
- **Microsoft OAuth2:** Acesso aos emails e OneDrive
- **Pasta BRK:** Permissão de leitura na pasta específica
- **OneDrive BRK:** Acesso à pasta de backup das planilhas

### **📧 Configuração de Email**
- **Pasta monitorada:** Pasta específica BRK no Outlook
- **Tipos aceitos:** Anexos PDF com faturas da BRK
- **Processamento:** Extração automática de 15+ campos por fatura

### **🌍 Variáveis de Ambiente**
```
# Sistema BRK Principal:
MICROSOFT_CLIENT_ID=sua_client_id
PASTA_BRK_ID=id_da_pasta_email
ONEDRIVE_BRK_ID=id_da_pasta_onedrive

# Sistema Alertas (Integração CCB): ✅ NOVO
TELEGRAM_BOT_TOKEN=token_do_bot_telegram
ADMIN_IDS=id1,id2,id3
ONEDRIVE_ALERTA_ID=id_pasta_responsaveis_ccb
```

---

## 📈 Relatórios e Estatísticas

### **📊 Dados Disponíveis**
- **Total de faturas processadas** por período
- **Distribuição por CO** (39 instalações monitoradas)
- **Análise de consumo** (normal vs. alto vs. crítico)
- **Status de processamento** (sucesso vs. erro vs. pendente)

### **📋 Formatos de Saída**
- **Excel (.xlsx):** Planilhas organizadas por mês
- **Interface Web:** Visualização online dos dados
- **DBEDIT:** Interface Clipper para consultas detalhadas
- **Logs Estruturados:** Rastreabilidade completa

---

## 🎯 Benefícios Práticos

### **💰 Proteção Financeira**
- **Evita vazamentos não detectados** que podem gerar custos desnecessários
- **Previne pagamento duplicado** de faturas reenviadas
- **Controla 39 instalações automaticamente** sem perder nenhuma
- **Separa contas bancárias** para pagamento correto
- **Notifica responsáveis automaticamente** para ação preventiva ✅ NOVO

### **⏰ Economia de Tempo**
- **Automação completa:** Funciona 24/7 sem intervenção
- **Planilhas prontas:** Geradas automaticamente por período
- **Processamento inteligente:** Extrai dados sem digitação manual
- **Interface organizada:** Acesso rápido a todas as informações
- **Alertas direcionados:** Responsáveis notificados automaticamente ✅ NOVO

### **🔍 Controle e Auditoria**
- **Logs detalhados:** Rastreabilidade de cada operação
- **Seção controle:** Faturas que precisam verificação
- **Backup automático:** Dados sempre protegidos
- **Múltiplas planilhas:** Análise específica por período
- **Comunicação registrada:** Histórico de alertas enviados ✅ NOVO

### **📱 Comunicação Inteligente** ✅ NOVO
- **Responsáveis específicos:** Cada CO tem seus notificados
- **Alertas graduados:** 5 níveis de criticidade
- **Ação preventiva:** Instruções claras por situação
- **Fallback garantido:** Admin sempre recebe alertas críticos

---

## 🛠️ Suporte e Manutenção

### **🔄 Automação Ativa**
O sistema funciona automaticamente a cada 60 minutos:
1. **Verifica emails novos** na pasta BRK
2. **Processa faturas encontradas** automaticamente
3. **Atualiza planilhas** de todos os meses com dados
4. **Sincroniza backup** no OneDrive
5. **Gera logs** de todas as operações

### **⚠️ Quando Buscar Suporte**
- Monitor parado por mais de 1 hora
- Planilhas não sendo atualizadas
- Erros de conectividade com OneDrive
- CO's faltantes não sendo detectadas
- **Alertas não chegando aos responsáveis** ✅ NOVO
- **Bot Telegram não respondendo** ✅ NOVO
- **Responsáveis não cadastrados corretamente** ✅ NOVO

### **📞 Contato**
- **Desenvolvedor:** Sidney Gubitoso
- **Função:** Auxiliar Tesouraria - Administração Mauá
- **Sistema:** Implantado no Render com alta disponibilidade

---

## 📚 Histórico de Versões

### **v2.0 - Monitor Integrado (Atual)**
- ✅ Monitor automático 60min (emails + múltiplas planilhas)
- ✅ Detecção automática de meses com faturas
- ✅ Geração de planilha específica por período
- ✅ Orquestração inteligente sem duplicação de código
- ✅ Thread não-bloqueante para Flask
- ✅ Validação completa de dependências

### **v1.0 - Sistemas Separados (Anterior)**
- Monitor emails: 10 minutos
- Scheduler planilha: 06:00h apenas mês atual
- Sistemas independentes

---

## 🎯 Resumo Executivo

**O Sistema BRK v2.0 é uma solução completa de proteção financeira que:**

✅ **Monitora automaticamente** emails da BRK 24/7  
✅ **Detecta e previne vazamentos** rapidamente através de análise inteligente  
✅ **Evita pagamentos duplicados** através de controle SEEK  
✅ **Gera múltiplas planilhas** organizadas por período  
✅ **Controla 39 instalações** sem perder nenhuma fatura  
✅ **Funciona sem intervenção manual** com backup automático  
✅ **Notifica responsáveis automaticamente** via Telegram ✅ NOVO  
✅ **Integra sistemas BRK + CCB** para gestão completa ✅ NOVO  
✅ **Oferece 5 tipos de alerta** personalizados por criticidade ✅ NOVO  

**Resultado:** Controle automatizado de contas de água com redução drástica de trabalho manual, prevenção de vazamentos e comunicação automática para ação preventiva por responsáveis específicos de cada Casa de Oração.
