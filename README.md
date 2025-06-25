# 🏢 Sistema BRK - Controle Inteligente de Faturas

Sistema automático avançado para processamento de faturas BRK com **DatabaseBRK integrado**, detecção de duplicatas e organização completa no OneDrive.

## 🎯 Funcionalidades Avançadas

### 🗃️ **DatabaseBRK - Core do Sistema**
- **📊 SQLite organizado** no OneDrive com estrutura robusta
- **🔍 Lógica SEEK** estilo Clipper para detecção de duplicatas
- **⚠️ Classificação inteligente**: NORMAL / DUPLICATA / CUIDADO
- **📁 Estrutura automática**: `/BRK/Faturas/YYYY/MM/`
- **📝 Nomenclatura consistente** com script renomeia_brk10.py

### 📧 **Processamento Inteligente de Emails**
- **🤖 Extração completa** de dados das faturas PDF
- **🏪 Relacionamento automático** CDC → Casa de Oração
- **💧 Análise de consumo** com alertas (ALTO/NORMAL)
- **🔄 Detecção de renegociações** entre BRK e igrejas
- **📊 Logs estruturados** para monitoramento no Render

### 🌐 **Interface Web Completa**
- **📋 Visualização de faturas** com filtros avançados
- **📈 Estatísticas do banco** em tempo real
- **⚙️ Processamento via interface** com resultados detalhados
- **🔧 Debug completo** do sistema
- **🚨 Alertas visuais** para consumo elevado

## 🚀 **Arquitetura do Sistema**

```
🏢 Sistema BRK
├── 📧 EmailProcessor (SEM pandas - Python 3.13)
│   ├── 🔍 Extração completa PDF (pdfplumber)
│   ├── 🏪 Relacionamento CDC → Casa OneDrive
│   ├── 💧 Análise consumo automática
│   └── 📊 Logs estruturados Render
├── 🗃️ DatabaseBRK (SQLite + OneDrive)
│   ├── 🔍 Lógica SEEK (CDC + Competência)
│   ├── ⚠️ Detecção duplicatas inteligente
│   ├── 📁 Estrutura /Faturas/YYYY/MM/
│   └── 📝 Nomenclatura padronizada
└── 🌐 Interface Web Flask
    ├── 📋 Visualização faturas
    ├── 📈 Estatísticas avançadas
    ├── ⚙️ Processamento interativo
    └── 🔧 Debug sistema
```

## 🔧 Configuração e Deploy

### **📋 Variáveis de Ambiente Necessárias**

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `CLIENT_ID` | ✅ | Client ID da aplicação Microsoft |
| `CLIENT_SECRET` | ✅ | Client Secret da aplicação Microsoft |
| `REDIRECT_URI` | ✅ | URL de callback (render app + /callback) |
| `PASTA_BRK_ID` | ✅ | ID da pasta "BRK" no Outlook |
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
```

## 🔑 **Primeiro Acesso**

1. **Acesse**: `https://seu-app.onrender.com`
2. **Clique "Login"** → Autenticação Microsoft automática
3. **Sistema inicializa**: DatabaseBRK + relacionamento CDC
4. **Pronto para usar**: Processamento completo ativo

## 📊 **Como Funciona na Prática**

### **📧 Quando chega email BRK:**

```
📧 Email → 🔍 PDF extraído → 🏪 Casa relacionada → 💧 Consumo analisado
                ↓
🔍 SEEK: CDC + Competência na DatabaseBRK
                ↓
✅ NORMAL: Fatura nova → Salva organizada
🔄 DUPLICATA: Email duplicado → Marca status  
⚠️ CUIDADO: Dados diferentes → Alerta renegociação
                ↓
📁 /BRK/Faturas/2025/02/15-02-BRK 02-2025 - Igreja Central - vc. 15-02-2025 - 127,45.pdf
📊 SQLite: Registro completo com alertas e análises
```

### **🎯 Resultado Automático:**
- **📊 Dados extraídos**: CDC, Casa, Valor, Consumo, Alertas
- **🔍 Status definido**: NORMAL/DUPLICATA/CUIDADO  
- **📁 Arquivo organizado**: Estrutura /YYYY/MM/ automática
- **💾 Banco atualizado**: SQLite com histórico completo

## 🌐 **Endpoints Disponíveis**

### **🔧 Core do Sistema**
- `GET /` - Dashboard principal com status completo
- `GET /login` - Autenticação Microsoft automática
- `GET /diagnostico-pasta` - Diagnóstico pasta BRK + DatabaseBRK

### **⚙️ Processamento**
- `POST /processar-emails-novos` - Processa emails com salvamento automático
- `GET /processar-emails-form` - Interface web para processamento

### **📊 DatabaseBRK**
- `GET /estatisticas-banco` - Estatísticas completas do SQLite
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

## 📈 **Logs Esperados (Render)**

### **✅ Inicialização Sucesso:**
```
🚀 Sistema BRK iniciado com DatabaseBRK integrado
   📧 Pasta emails: 1234567890******
   📁 OneDrive BRK: 987654321098765******
   🗃️ DatabaseBRK: Ativo
✅ Microsoft Auth configurado
✅ Relacionamento disponível: 248 registros
📊 Registros extraídos do Excel: 248
📋 Estrutura confirmada: Coluna A=Casa, Coluna B=CDC
```

### **⚙️ Processamento Automático:**
```
🔄 Processando emails dos últimos 1 dia(s)
✅ DatabaseBRK ativo - faturas serão salvas automaticamente
📧 Processando email: Fatura BRK Janeiro 2025
📄 Texto extraído: 2847 caracteres
  ✓ CDC encontrado: 513-01
  ✓ Casa encontrada: Igreja Central
  ✓ Valor: R$ 127,45
  ✓ Análise: Consumo acima do esperado (+25%)
🔍 SEEK: CDC 513-01 + Jan/2025 → NOT FOUND() → STATUS: NORMAL
✅ Fatura salva: Status NORMAL
📁 Nome padronizado: 15-02-BRK 02-2025 - Igreja Central - vc. 15-02-2025 - 127,45.pdf
```

## 🚨 **Detecção de Cenários Críticos**

### **⚠️ Renegociação Detectada:**
```
🔍 SEEK: CDC 513-01 + Jan/2025 → FOUND()
⚠️ Valores diferentes → STATUS: CUIDADO
📊 Diferenças: VALOR, VENCIMENTO
🚨 ALERTA: Possível renegociação - verificar com BRK
```

### **🔄 Email Duplicado:**
```
🔍 SEEK: CDC 513-01 + Jan/2025 → FOUND()
✅ Dados idênticos → STATUS: DUPLICATA
📝 Email duplicado - dados idênticos
```

### **📊 Alto Consumo:**
```
💧 Medido Real: 25m³
📈 Média 6M: 12m³
📊 Variação: +108.33% em relação à média
🚨 **ALTO CONSUMO DETECTADO!** 🚨
```

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

## 🎯 **Diferencial Técnico**

### **✅ Sem Pandas (Python 3.13):**
- Deploy sempre 3 minutos (sem compilação)
- Processamento Excel via XML nativo
- Menor uso memória
- Compatibilidade total

### **🔍 Lógica SEEK Clipper:**
- Performance otimizada (índices SQLite)
- Detecção duplicatas precisa
- Compatibilidade com desktop
- Escalabilidade garantida

### **📝 Nomenclatura Consistente:**
- Mesmo padrão script renomeia_brk10.py
- Organização visual intuitiva
- Compatibilidade ferramentas existentes

## 📞 **Suporte e Manutenção**

### **👨‍💼 Desenvolvido por:**
Sidney Gubitoso - Auxiliar Tesouraria Administrativa Mauá

### **🔧 Versão Atual:**
DatabaseBRK v1.0 - Sistema completo com detecção duplicatas

### **📊 Status:**
- ✅ Em produção ativa
- ✅ Monitoramento 24/7
- ✅ Backup automático
- ✅ Contingência implementada

---

**🏆 Sistema BRK - Processamento inteligente de faturas com DatabaseBRK integrado**  
**🎯 Zero intervenção manual - Máxima precisão - Organização total**
