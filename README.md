# 🏢 Sistema BRK - Controle Inteligente de Faturas (VERSÃO MODULAR)

Sistema automático avançado para processamento de faturas BRK com **estrutura modular completa**, monitor automático, detecção de duplicatas e organização no OneDrive.

## 🎯 Funcionalidades Avançadas

### 🗃️ **DatabaseBRK - Core do Sistema**
- **📊 SQLite organizado** no OneDrive com estrutura robusta
- **🔍 Lógica SEEK** estilo Clipper para detecção de duplicatas
- **⚠️ Classificação inteligente**: NORMAL / DUPLICATA / CUIDADO
- **📁 Estrutura automática**: `/BRK/Faturas/YYYY/MM/`
- **📝 Nomenclatura consistente** com padrão renomeia_brk10.py

### 📧 **Processamento Inteligente de Emails**
- **🤖 Extração completa** de dados das faturas PDF (SEM pandas)
- **🏪 Relacionamento automático** CDC → Casa de Oração
- **💧 Análise de consumo** com alertas (ALTO/NORMAL)
- **🔄 Detecção de renegociações** entre BRK e igrejas
- **📊 Logs estruturados** para monitoramento no Render

### 📊 **Monitor Automático (NOVA FUNCIONALIDADE)**
- **⏰ Verificação automática** a cada 10 minutos
- **📈 Estatísticas da pasta** BRK em tempo real
- **🔍 Processamento automático** de emails novos
- **📋 Logs detalhados** no Render com dados extraídos
- **🚨 Alertas visuais** para consumo elevado

### 🌐 **Interface Web Completa**
- **📋 Visualização de faturas** com filtros avançados
- **📈 Estatísticas do banco** em tempo real
- **⚙️ Processamento via interface** com resultados detalhados
- **🔧 Debug completo** do sistema
- **🚨 Alertas visuais** para consumo elevado

## 🚀 **Arquitetura Modular do Sistema**

```
🏢 Sistema BRK (ESTRUTURA MODULAR)
├── 📧 auth/ (Autenticação Microsoft)
│   ├── __init__.py
│   └── microsoft_auth.py (Token management, refresh, validação)
├── 📧 processor/ (Processamento Core)
│   ├── __init__.py
│   ├── email_processor.py (Extração PDF SEM pandas, relacionamento)
│   ├── database_brk.py (SQLite + OneDrive + lógica SEEK)
│   └── monitor_brk.py (Monitor automático - NOVA FUNCIONALIDADE)
├── 🔧 admin/ (Interface Administrativa)
│   ├── __init__.py
│   └── admin_server.py (Interface web, upload token, testes)
├── 🌐 app.py (Orquestração principal - LIMPO)
├── ⚙️ requirements.txt (Dependências mínimas)
└── 📋 render.yaml (Deploy automático)
```

## 🔧 Configuração e Deploy

### **📋 Variáveis de Ambiente Necessárias**

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `MICROSOFT_CLIENT_ID` | ✅ | Client ID da aplicação Microsoft |
| `MICROSOFT_TENANT_ID` | ⚠️ | Tenant ID (padrão: consumers) |
| `PASTA_BRK_ID` | ✅ | ID da pasta "BRK" no Outlook (emails) |
| `ONEDRIVE_BRK_ID` | ⚠️ | ID da pasta "/BRK/" no OneDrive (DatabaseBRK) |

### **🚀 Deploy no Render**

1. **Fork/Clone** este repositório
2. **Render.com** → New Web Service → Conectar repo
3. **Configurar build**:
   ```bash
   Build Command: pip install -r requirements.txt
   Start Command: python app.py
   ```
4. **Configurar Environment Variables** (tabela acima)
5. **Deploy automático** - pronto em ~3 minutos!

### **📊 Requirements.txt Atualizado**
```
Flask==3.0.3
requests==2.31.0
python-dateutil==2.8.2
pdfplumber==0.9.0
gunicorn==23.0.0
Werkzeug==3.0.3
Jinja2==3.1.4
MarkupSafe==3.0.2
itsdangerous==2.2.0
click==8.1.7
```

## 🔑 **Primeiro Acesso**

1. **Acesse**: `https://seu-app.onrender.com`
2. **Upload do token**: Sistema requer token.json válido:
   - Obtido via autenticação Microsoft OAuth
   - Salvo no persistent disk (/opt/render/project/storage/)
   - Renovado automaticamente quando necessário
3. **Sistema inicializa automaticamente**: 
   - DatabaseBRK + relacionamento CDC
   - Monitor automático ativo
   - Validação de dependências
4. **Logs automáticos**: Verificação a cada 10 minutos
5. **Interface web**: Disponível para processamento manual

### **🔐 Gerenciamento de Token:**
- **token.json** contém: access_token, refresh_token, expires_in
- **Renovação automática** via refresh_token
- **Persistent storage** no Render para sobreviver restarts
- **Fallback gracioso** se token expirar

## 📊 **Como Funciona na Prática**

### **📧 Monitor Automático (NOVA FUNCIONALIDADE):**

```
⏰ [14:35:00] MONITOR BRK - Verificação automática
📊 ESTATÍSTICAS PASTA BRK:
   📧 Total na pasta: 1,247 emails
   📅 Mês atual: 23 emails
   ⏰ Últimas 24h: 3 emails

🔍 Processando emails novos (últimos 10 min)...
📧 1 emails novos encontrados

📧 Email processado: Fatura BRK Janeiro 2025
  ✓ CDC encontrado: 513-01
  ✓ Casa encontrada: Igreja Central
  ✓ Valor: R$ 127,45
  ✓ Análise: Consumo acima do esperado (+25%)
🔍 SEEK: CDC 513-01 + Jan/2025 → NOT FOUND() → STATUS: NORMAL
✅ Fatura salva: Status NORMAL
📁 Nome padronizado: 15-02-BRK 02-2025 - Igreja Central - vc. 15-02-2025 - 127,45.pdf

  💾 Processado: CDC 513-01 → Igreja Central → R$ 127,45

✅ Processamento concluído:
   📧 Emails processados: 1
   📎 PDFs extraídos: 1
⏰ Próxima verificação em 10 minutos
```

### **🎯 Resultado Automático:**
- **📊 Dados extraídos**: CDC, Casa, Valor, Consumo, Alertas
- **🔍 Status definido**: NORMAL/DUPLICATA/CUIDADO  
- **📁 Arquivo organizado**: Estrutura /YYYY/MM/ automática
- **💾 Banco atualizado**: SQLite com histórico completo
- **📋 Logs estruturados**: Visibilidade completa no Render

## 🌐 **Endpoints Disponíveis**

### **🔧 Core do Sistema**
- `GET /` - Dashboard principal com status completo
- `GET /login` - Autenticação Microsoft automática
- `GET /diagnostico-pasta` - Diagnóstico pasta BRK + DatabaseBRK

### **⚙️ Processamento**
- `POST /processar-emails-novos` - Processa emails com salvamento automático
- `GET /processar-emails-form` - Interface web para processamento

### **📊 DatabaseBRK**
- `GET /estatisticas-database` - Estatísticas completas do SQLite
- `GET /faturas` - API listagem faturas (com filtros)
- `GET /faturas-html` - Interface visual navegação faturas

### **🔧 Manutenção**
- `POST /recarregar-relacionamento` - Força reload CDC → Casa
- `GET /debug-sistema` - Debug completo DatabaseBRK
- `GET /health` - Health check para Render

## 🗃️ **Estrutura DatabaseBRK**

### **📊 Tabela faturas_brk:**
```sql
- id, data_processamento, status_duplicata, observacao
- email_id, nome_arquivo_original, nome_arquivo, hash_arquivo  
- cdc, nota_fiscal, casa_oracao, data_emissao, vencimento
- competencia, valor, medido_real, faturado, media_6m
- porcentagem_consumo, alerta_consumo
- dados_extraidos_ok, relacionamento_usado
```

### **🔍 Índices de Performance:**
- `idx_cdc_competencia` - Busca SEEK principal
- `idx_status_duplicata` - Filtros por status
- `idx_casa_oracao` - Relatórios por igreja
- `idx_competencia` - Análises mensais

## 🛡️ **Contingência e Robustez**

### **🔄 OneDrive Indisponível:**
- Sistema detecta falha OneDrive
- Salva temporariamente local (Render)
- Sincroniza quando OneDrive volta
- Zero perda de dados

### **⚠️ Relacionamento CDC Falha:**
- Sistema continua funcionando
- Usa extração básica PDF
- Logs indicam problema
- Recarregamento manual disponível

### **🔧 Self-Healing:**
- Criação automática estrutura OneDrive
- Inicialização SQLite automática
- Renovação token automática
- Retry inteligente em falhas

### **📊 Monitor Automático Falha:**
- Sistema continua funcionando normalmente
- Interface web permanece ativa
- Logs indicam problema específico
- Processamento manual disponível

## 🎯 **Diferencial Técnico**

### **✅ Sem Pandas (Python 3.11):**
- Deploy sempre 3 minutos (sem compilação)
- Processamento Excel via XML nativo
- Menor uso memória
- Compatibilidade total

### **🔍 Lógica SEEK Clipper:**
- Performance otimizada (índices SQLite)
- Detecção duplicatas precisa
- Compatibilidade com desktop
- Escalabilidade garantida

### **📊 Monitor Automático:**
- Logs estruturados no Render
- Verificação contínua sem intervenção
- Estatísticas da pasta em tempo real
- Processamento transparente

### **📝 Estrutura Modular:**
- **auth/**: Isolado e reutilizável
- **processor/**: Core funcional independente
- **admin/**: Interface administrativa separada
- **app.py**: Orquestração limpa

## 📞 **Suporte e Manutenção**

### **👨‍💼 Desenvolvido por:**
**Sidney Gubitoso** - Auxiliar Tesouraria Administrativa Mauá

### **🔧 Versão Atual:**
DatabaseBRK v1.0 + Monitor Automático - Sistema modular completo

### **📊 Status:**
- ✅ Em produção ativa
- ✅ Monitoramento automático 24/7
- ✅ Backup automático
- ✅ Contingência implementada
- ✅ Estrutura modular escalável

## 🔧 **Guia para Novos Scripts**

### **📋 Padrão de Cabeçalho Obrigatório:**
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: pasta/nome_arquivo.py
💾 ONDE SALVAR: brk-monitor-seguro/pasta/nome_arquivo.py
📦 FUNÇÃO: Descrição breve da funcionalidade
🔧 DESCRIÇÃO: Detalhes técnicos e dependências
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
"""
```

### **🏗️ Estrutura de Pastas:**
- `auth/` → Autenticação e tokens
- `processor/` → Processamento core e lógica de negócio
- `admin/` → Interfaces administrativas
- `app.py` → Orquestração principal (MANTER LIMPO)

### **📝 Dependências:**
- Documentar TODAS as dependências no cabeçalho
- Validar dependências na inicialização
- Falhar rapidamente se dependências faltam
- Logs claros sobre problemas

### **🔍 Boas Práticas:**
- Métodos pequenos e focados
- Logs estruturados para Render
- Tratamento de erros robusto
- Compatibilidade com código existente
- Documentação inline clara

## ✅ **Validação de Consistência**

### **📋 README Auditado e Validado:**
- ✅ **Variáveis de ambiente** consistentes com código real
- ✅ **Estrutura modular** reflete implementação atual  
- ✅ **Dependências** atualizadas e testadas
- ✅ **Versão Python** correta (3.11.9)
- ✅ **Funcionalidades** documentadas existem no código
- ✅ **Endpoints** listados estão implementados
- ✅ **Autor e versionamento** consistentes
- ✅ **Guias de implementação** validados

### **🔍 Última Validação:**
- **Data**: Junho 2025
- **Código base**: Estrutura modular completa
- **Funcionalidades**: Monitor automático ativo
- **Deploy**: Testado no Render
- **Contingência**: Implementada e documentada

---

**🏆 Sistema BRK - Processamento inteligente de faturas com monitoramento automático**  
**🎯 Zero intervenção manual - Máxima precisão - Organização total - Logs contínuos**

> **Desenvolvido por Sidney Gubitoso** - Auxiliar Tesouraria Administrativa Mauá  
> **Versão Modular** - Estrutura escalável e maintível  
> **Deploy Time:** ⚡ 3 minutos | **Compatibilidade:** 🛡️ Python 3.11
