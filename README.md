# 🏢 Sistema BRK v6.0 - Controle Automático de Faturas

> **Sistema automatizado para processamento inteligente de faturas BRK com geração de planilhas Excel, alertas Telegram e organização completa no OneDrive.**

## 🌐 **Sistema em Produção**

**🔗 Acesso Principal:** https://brk-render-seguro.onrender.com  
**📊 Gerar Planilhas:** https://brk-render-seguro.onrender.com/gerar-planilha-brk  
**🗃️ Consultar Database:** https://brk-render-seguro.onrender.com/dbedit  

---

## 🎯 **O que o Sistema Faz**

### **📧 Monitora Emails Automaticamente**
- Verifica pasta BRK a cada 10 minutos, 24 horas por dia
- Baixa automaticamente PDFs de faturas anexados
- Extrai todos os dados importantes: CDC, Casa de Oração, valores, consumo

### **📊 Organiza Informações**
- Salva tudo em database seguro (SQLite + OneDrive)
- Relaciona CDC com Nome da Casa de Oração automaticamente
- Detecta faturas duplicadas ou renegociações da BRK
- Calcula alertas de consumo baseado na média histórica

### **📋 Gera Planilhas Excel Automáticas**
- **Planilhas mensais** baseadas no mês de vencimento das faturas
- **Separação bancária**: PIA (Conta A) e Casas de Oração (Conta B)
- **Geração automática** a cada 30 minutos
- **Backup inteligente**: Não sobrescreve planilhas abertas

### **📱 Envia Alertas Telegram**
- Alertas dirigidos para responsáveis específicos de cada Casa de Oração
- Classificação automática: Consumo Normal, Alto, Crítico, Emergência
- Sempre envia para administradores como backup

### **☁️ Organiza no OneDrive**
- Upload automático de PDFs em `/BRK/Faturas/YYYY/MM/`
- Nomenclatura padronizada dos arquivos
- Backup automático do database

---

## 📋 **Como Usar o Sistema**

### **🔄 Processamento Automático (Principal)**
O sistema funciona **sozinho** - não precisa fazer nada! Ele:
1. Monitora emails da BRK automaticamente
2. Processa faturas novas que chegam
3. Gera planilhas mensais a cada 30 minutos
4. Envia alertas para responsáveis

### **📊 Gerar Planilha Manual**
1. Acesse: https://brk-render-seguro.onrender.com/gerar-planilha-brk
2. Selecione o mês/ano desejado
3. Clique em "Gerar Planilha"
4. Baixe o arquivo Excel gerado
5. A planilha também é salva automaticamente no OneDrive

### **🗃️ Consultar Database**
1. Acesse: https://brk-render-seguro.onrender.com/dbedit
2. Use comandos estilo Clipper:
   - `TOP` - Primeiro registro
   - `SEEK 92213-27` - Buscar CDC específico
   - `SEEK "VILA"` - Buscar Casa de Oração
   - `NEXT` / `PREV` - Navegar

### **🔄 Reconstituir Base Completa**
1. Acesse a interface principal
2. Vá em "Reconstituição BRK"
3. Confirme a operação (reprocessa todos emails)
4. Aguarde conclusão (15-20 minutos)

---

## 📊 **Estrutura das Planilhas Excel**

### **📋 Seção PRINCIPAL (Entra nos Totais)**
- **PIA (Conta Bancária A)**: Sede administrativa
- **Casas de Oração (Conta Bancária B)**: Todas as casas, organizadas por vencimento
- **Casas Faltantes**: Casas esperadas mas sem fatura (baseado na base de 38 casas)

### **⚠️ Seção CONTROLE (Auditoria Manual)**
- **Duplicatas**: Faturas repetidas detectadas
- **Renegociações**: Mesmo CDC com valor diferente (BRK reenviou)
- **Problemas**: Faturas com dados inconsistentes

**💡 As faturas da seção CONTROLE NÃO entram nos totais para evitar erros financeiros**

---

## 🚨 **Sistema de Alertas Telegram**

### **🎯 Como Funcionam os Alertas**
Quando uma fatura é processada, o sistema:
1. Analisa o consumo vs. média dos últimos 6 meses
2. Classifica o tipo de alerta
3. Busca responsáveis da Casa de Oração específica
4. Envia alertas direcionados
5. Sempre envia cópia para administradores

### **📊 Tipos de Alerta**
| Tipo | Critério | Emoji | Ação Recomendada |
|------|----------|-------|------------------|
| **Normal** | Dentro da média | ✅ | Acompanhar normalmente |
| **Alto** | +20% a +50% | 🟡 | Verificar possíveis vazamentos |
| **Crítico** | +50% a +100% | 🟠 | Inspeção urgente |
| **Emergência** | +100% e ≥10m³ | 🔴 | Verificação imediata |
| **Baixo** | -50% ou mais | 📉 | Verificar se medição correta |

### **📱 Exemplo de Alerta**
```
🟡 AVISO IMPORTANTE 🟡
📢 ALERTA DE ALTO CONSUMO DE ÁGUA

📍 Casa de Oração: BR21-0774
📆 Vencimento: 15/07/2025
💰 Valor da Conta: R$ 150,75

📊 Consumo Atual: 25.0 m³
📉 Média (6 meses): 15.0 m³
📈 Aumento: +10.0 m³ (+66.7%)

⚠️ VERIFIQUE:
🔹 Possíveis vazamentos
🔹 Torneiras pingando
🔹 Boia da caixa d'água
```

---

## 🔧 **Configuração Inicial**

### **1. Variáveis de Ambiente (Render)**
```
CLIENT_ID = ID da aplicação Microsoft
CLIENT_SECRET = Chave secreta Microsoft
PASTA_BRK_ID = ID da pasta BRK no Outlook
ONEDRIVE_BRK_ID = ID da pasta /BRK/ no OneDrive
ONEDRIVE_ALERTA_ID = ID da pasta /Alerta/ no OneDrive
TELEGRAM_BOT_TOKEN = Token do bot CCB Alerta
ADMIN_IDS = IDs dos administradores Telegram
```

### **2. Primeiro Acesso**
1. Acesse o sistema pela primeira vez
2. Faça login com conta Microsoft (autorização única)
3. Sistema inicializa automaticamente:
   - Carrega base de 38 Casas de Oração
   - Inicia monitor automático
   - Ativa geração de planilhas
   - Conecta alertas Telegram

### **3. Deploy Automático**
- Deploy no Render: 3 minutos
- Sem necessidade de servidor próprio
- Backup automático no OneDrive
- Monitoramento 24/7 garantido

---

## 📈 **Estatísticas do Sistema**

### **📊 Dados Atuais (Produção)**
- **📧 Emails monitorados**: 258 emails na pasta BRK
- **🏠 Casas de Oração**: 38 registros ativos
- **📋 Faturas processadas**: 1.200+ registros
- **📊 Planilhas geradas**: Automáticas mensais
- **🚨 Alertas enviados**: 500+ notificações
- **⏰ Uptime**: 24/7 há 6 meses

### **🎯 Performance**
- **Processamento fatura**: 3-5 segundos
- **Geração planilha**: 30-60 segundos  
- **Upload OneDrive**: 2-10 segundos
- **Envio alerta**: 1-3 segundos
- **Verificação emails**: A cada 10 minutos

---

## 🛡️ **Segurança e Backup**

### **🔐 Segurança**
- Autenticação Microsoft OAuth2
- Tokens criptografados
- Acesso restrito por permissões
- Logs de auditoria completos

### **💾 Backup Automático**
- Database sincronizado OneDrive
- PDFs organizados por ano/mês
- Planilhas versionadas
- Logs de sistema preservados

### **🚨 Contingências**
- **OneDrive offline**: Sistema continua localmente
- **Telegram falha**: Admin sempre recebe alertas
- **Email indisponível**: Processamento pendente até voltar
- **Planilha aberta**: Backup automático criado

---

## 📞 **Suporte e Manutenção**

### **👨‍💼 Responsável Técnico**
**Sidney Gubitoso** - Auxiliar Tesouraria Administrativa Mauá

### **🔧 Versão Atual**
**Sistema BRK v6.0** (Julho 2025)
- Planilhas mensais automáticas baseadas no vencimento
- Backup inteligente de planilhas
- Detecção automática de renegociações BRK
- Alertas Telegram integrados
- Interface DBEDIT estilo Clipper

### **🆘 Resolução de Problemas**

| Problema | Solução |
|----------|---------|
| **Sistema não processa emails** | Verificar se pasta BRK tem emails novos |
| **Planilha não gera** | Verificar se há faturas no mês selecionado |
| **Alertas não chegam** | Verificar token Telegram nas configurações |
| **OneDrive não sincroniza** | Reautenticar conta Microsoft |
| **Dados inconsistentes** | Usar Reconstituição para reprocessar tudo |

### **📊 Monitoramento**
- **Status sistema**: Dashboard principal
- **Logs detalhados**: Interface administrativa
- **Estatísticas**: Métricas em tempo real
- **Health check**: Verificação automática

---

## 🚀 **Roadmap Futuro**

### **📈 Próximas Melhorias**
- Dashboard com gráficos de consumo
- Relatórios customizados por período
- Integração com sistemas bancários
- App mobile para consultas

### **🔮 Visão 2026**
- Análise preditiva de consumo
- Alertas preventivos automáticos
- API para integração terceiros
- Dashboards executivos

---

**💡 O Sistema BRK v6.0 automatiza 100% do processo de controle de faturas, desde o recebimento por email até a geração de planilhas Excel organizadas, com zero intervenção manual necessária.**

> **🎯 Resultado:** Economia de 20+ horas semanais de trabalho manual + Controle financeiro preciso + Alertas preventivos automáticos


# SISTEMA BRK v6.0 - ESPECIFICAÇÃO TÉCNICA

## DATABASE SCHEMAS

### faturas_brk (SQLite)
```sql
CREATE TABLE faturas_brk (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_processamento DATETIME DEFAULT CURRENT_TIMESTAMP,
    status_duplicata TEXT DEFAULT 'NORMAL',
    observacao TEXT,
    email_id TEXT UNIQUE,
    nome_arquivo_original TEXT,
    nome_arquivo TEXT,
    hash_arquivo TEXT,
    cdc TEXT,
    nota_fiscal TEXT,
    casa_oracao TEXT,
    data_emissao DATE,
    vencimento DATE,
    competencia TEXT,
    valor DECIMAL(10,2),
    medido_real DECIMAL(8,2),
    faturado DECIMAL(8,2),
    media_6m DECIMAL(8,2),
    porcentagem_consumo DECIMAL(5,2),
    alerta_consumo TEXT,
    dados_extraidos_ok BOOLEAN DEFAULT 1,
    relacionamento_usado TEXT,
    onedrive_upload BOOLEAN DEFAULT 0,
    onedrive_url TEXT,
    nome_onedrive TEXT,
    onedrive_pasta TEXT,
    alertas_enviados INTEGER DEFAULT 0,
    alertas_destinatarios TEXT,
    alertas_status TEXT
);

CREATE INDEX idx_cdc_competencia ON faturas_brk(cdc, competencia);
CREATE INDEX idx_status_duplicata ON faturas_brk(status_duplicata);
CREATE INDEX idx_casa_oracao ON faturas_brk(casa_oracao);
CREATE INDEX idx_vencimento ON faturas_brk(vencimento);
CREATE INDEX idx_email_id ON faturas_brk(email_id);
```

### alertas_bot.db (SQLite)
```sql
CREATE TABLE responsaveis_casa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_casa TEXT,
    user_id INTEGER,
    nome TEXT,
    funcao TEXT,
    ativo BOOLEAN DEFAULT 1,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE administradores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    nome TEXT,
    nivel TEXT DEFAULT 'ADMIN',
    ativo BOOLEAN DEFAULT 1
);

CREATE TABLE log_alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_casa TEXT,
    cdc TEXT,
    competencia TEXT,
    tipo_alerta TEXT,
    user_ids_enviados TEXT,
    message_ids TEXT,
    status_envio TEXT,
    data_envio DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### CDC_BRK_CCB.xlsx (OneDrive)
```
Colunas: CDC|CASA_ORACAO|CODIGO_CASA|ENDERECO|RESPONSAVEL|CONTA_BANCARIA|OBSERVACOES|ATIVO
Exemplo: 92213-27|BR 21-0774 - VILA MAGINI|BR21-0774|Rua X|João|B||S
Total: 38 registros ativos
```

## ENVIRONMENT VARIABLES
```
CLIENT_ID=<microsoft_app_id>
CLIENT_SECRET=<microsoft_app_secret>
PASTA_BRK_ID=<outlook_folder_id>
ONEDRIVE_BRK_ID=<onedrive_brk_folder_id>
ONEDRIVE_ALERTA_ID=<onedrive_alerta_folder_id>
TELEGRAM_BOT_TOKEN=<bot_token>
ADMIN_IDS=<comma_separated_telegram_ids>
```

## CORE ALGORITHMS

### SEEK Duplicata (database_brk.py)
```python
def seek_duplicata(self, cdc, competencia, valor_atual):
    cursor = self.conn.execute(
        "SELECT id, valor FROM faturas_brk WHERE cdc = ? AND competencia = ?",
        (cdc, competencia)
    )
    resultado = cursor.fetchone()
    
    if not resultado:
        return "NORMAL"
    
    valor_db = float(resultado[1])
    if abs(valor_db - float(valor_atual)) > 0.01:
        return "CUIDADO"  # Renegociação BRK
    
    return "DUPLICATA"
```

### Extração PDF (email_processor.py)
```python
def extrair_dados_fatura(self, pdf_bytes):
    import pdfplumber
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        texto = ""
        for page in pdf.pages:
            texto += page.extract_text()
    
    # Regex patterns
    cdc_match = re.search(r'(\d{5}-\d{2})', texto)
    valor_match = re.search(r'R\$\s*([\d.,]+)', texto)
    consumo_match = re.search(r'(\d+)\s*m³', texto)
    vencimento_match = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
    
    return {
        'cdc': cdc_match.group(1) if cdc_match else None,
        'valor': valor_match.group(1).replace(',', '.') if valor_match else None,
        'medido_real': consumo_match.group(1) if consumo_match else None,
        'vencimento': vencimento_match.group(1) if vencimento_match else None
    }
```

### Classificação Alertas (alertas/alert_processor.py)
```python
def classificar_alerta_consumo(self, medido_real, media_6m):
    if not media_6m or media_6m == 0:
        return ("NORMAL", "✅")
    
    variacao_pct = ((medido_real - media_6m) / media_6m) * 100
    
    if variacao_pct < -50:
        return ("BAIXO", "📉")
    elif variacao_pct <= 20:
        return ("NORMAL", "✅")
    elif variacao_pct <= 50:
        return ("ALTO", "🟡")
    elif variacao_pct <= 100:
        return ("CRÍTICO", "🟠")
    elif variacao_pct > 100 and medido_real >= 10:
        return ("EMERGÊNCIA", "🔴")
    else:
        return ("ALTO", "🟡")
```

### Geração Planilhas por Vencimento (excel_brk.py)
```python
def gerar_planilhas_por_vencimento(self):
    # Query faturas agrupadas por mês de vencimento
    query = """
        SELECT strftime('%Y-%m', vencimento) as mes_vencimento,
               casa_oracao, valor, status_duplicata, vencimento, cdc
        FROM faturas_brk 
        WHERE status_duplicata IN ('NORMAL', 'FALTANTE')
        ORDER BY mes_vencimento, vencimento, casa_oracao
    """
    
    faturas = self.db.execute(query).fetchall()
    
    # Agrupar por mês
    meses = {}
    for fatura in faturas:
        mes = fatura[0]
        if mes not in meses:
            meses[mes] = []
        meses[mes].append(fatura)
    
    # Gerar planilha para cada mês
    for mes, faturas_mes in meses.items():
        self._gerar_planilha_mensal(mes, faturas_mes)
```

### Backup Inteligente (excel_brk.py)
```python
def _verificar_planilha_aberta(self, caminho_planilha):
    try:
        # Tenta abrir arquivo para escrita
        with open(caminho_planilha, 'r+'):
            return False  # Planilha fechada
    except (IOError, PermissionError):
        return True  # Planilha aberta/em uso
```

## MICROSOFT GRAPH API CALLS

### Listar Emails
```
GET https://graph.microsoft.com/v1.0/me/mailFolders/{PASTA_BRK_ID}/messages
?$filter=hasAttachments eq true and receivedDateTime ge {timestamp}
?$select=id,subject,receivedDateTime,hasAttachments
```

### Download Anexo
```
GET https://graph.microsoft.com/v1.0/me/messages/{messageId}/attachments/{attachmentId}/$value
```

### Upload OneDrive
```
PUT https://graph.microsoft.com/v1.0/me/drive/items/{parent_id}:/{filename}:/content
Content-Type: application/octet-stream
Body: <file_bytes>
```

## TELEGRAM API CALLS

### Enviar Alerta
```python
def enviar_alerta(self, user_id, mensagem):
    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
    payload = {
        'chat_id': user_id,
        'text': mensagem,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, json=payload)
    return response.json()
```

## SCHEDULER JOBS

### Monitor 24/7 (monitor_brk.py)
```python
def job_monitor():
    while True:
        try:
            processar_emails_novos()
            time.sleep(600)  # 10 minutos
        except Exception as e:
            log_error(e)
            time.sleep(60)  # Retry em 1 min
```

### Geração Planilhas 30min (scheduler_brk.py)
```python
schedule.every(30).minutes.do(gerar_planilhas_automaticas)

def gerar_planilhas_automaticas():
    excel_generator = ExcelBRK()
    excel_generator.gerar_planilhas_por_vencimento()
```

## FILE STRUCTURE
```
/
├── auth/microsoft_auth.py          # MicrosoftAuth class
├── processor/
│   ├── email_processor.py          # EmailProcessor class
│   ├── database_brk.py             # DatabaseBRK class
│   ├── monitor_brk.py              # Monitor background thread
│   ├── excel_brk.py                # ExcelBRK class
│   ├── scheduler_brk.py            # SchedulerBRK class
│   ├── reconstituicao_brk.py       # ReconstitucaoBRK class
│   └── alertas/
│       ├── alert_processor.py      # AlertProcessor class
│       ├── ccb_database.py         # CCBDatabase class
│       ├── message_formatter.py    # MessageFormatter class
│       └── telegram_sender.py      # TelegramSender class
├── admin/
│   ├── admin_server.py             # AdminServer class
│   └── dbedit_server.py            # DbeditServer class
└── app.py                          # Flask app + threading
```

## DEPENDENCIES (requirements.txt)
```
Flask==3.0.3
requests==2.31.0
python-dateutil==2.8.2
pdfplumber==0.9.0
openpyxl==3.1.2
schedule==1.2.0
gunicorn==23.0.0
```

## KEY METHODS SIGNATURES

### EmailProcessor
```python
class EmailProcessor:
    def __init__(self, auth_manager, onedrive_brk_id, database_brk)
    def processar_emails_novos(self) -> dict
    def extrair_dados_fatura(self, pdf_bytes) -> dict
    def upload_fatura_onedrive(self, pdf_bytes, dados_fatura) -> str
    def _relacionar_cdc_casa(self, cdc) -> str
```

### DatabaseBRK
```python
class DatabaseBRK:
    def __init__(self, auth_manager, onedrive_brk_id)
    def salvar_fatura(self, dados_fatura) -> int
    def seek_duplicata(self, cdc, competencia, valor) -> str
    def get_connection(self) -> sqlite3.Connection
    def _gerar_nome_padronizado(self, dados_fatura) -> str
    def _extrair_ano_mes(self, data_vencimento) -> tuple
```

### ExcelBRK
```python
class ExcelBRK:
    def __init__(self, auth_manager, database_brk, onedrive_brk_id)
    def gerar_planilhas_por_vencimento(self) -> list
    def _gerar_planilha_mensal(self, mes, faturas) -> bytes
    def _verificar_planilha_aberta(self, caminho) -> bool
    def _criar_backup_temporario(self, caminho) -> str
```

### AlertProcessor
```python
class AlertProcessor:
    def processar_alerta_fatura(self, dados_fatura) -> dict
    def classificar_alerta_consumo(self, medido, media) -> tuple
    def buscar_responsaveis_casa(self, codigo_casa) -> list
    def enviar_alertas_multiplos(self, destinatarios, mensagem) -> dict
```

## CRITICAL BUSINESS RULES

### Status Duplicata
- NORMAL: Primeira ocorrência CDC+competência
- DUPLICATA: Mesmos dados exatos (ignorar)
- CUIDADO: Mesmo CDC+competência, valor diferente (renegociação BRK)
- FALTANTE: Casa esperada sem fatura (só planilhas)

### Planilhas Excel Estrutura
- PRINCIPAL: PIA (Conta A) + COs (Conta B) - ENTRA NOS TOTAIS
- CONTROLE: DUPLICATA/CUIDADO - NÃO ENTRA NOS TOTAIS

### Nomenclatura Arquivos
- PDF: DD-MM-BRK MM-YYYY - CASA - vc. DD-MM-YYYY - R$ XXX,XX.pdf
- Excel: BRK-Planilha-YYYY-MM.xlsx

### Threading
- Monitor: Thread separada infinita (10min loop)
- Scheduler: Thread separada schedule library (30min)
- Database: SQLite thread-safe mode
- Flask: Thread principal

## ERROR HANDLING

### OneDrive Offline
```python
try:
    upload_onedrive(file)
except ConnectionError:
    salvar_local_temp(file)
    marcar_upload_pendente(file_id)
```

### Telegram Falha
```python
try:
    enviar_telegram(user_id, mensagem)
except Exception:
    enviar_admin_fallback(mensagem)
    log_falha_alerta(user_id, erro)
```

### PDF Extração Falha
```python
try:
    dados = extrair_dados_pdf(bytes)
except Exception:
    dados = {'extraido': False, 'erro': str(e)}
    salvar_com_status_cuidado(dados)
```

## FLASK ROUTES
```python
@app.route('/')                           # Dashboard
@app.route('/processar-emails-form')     # Interface processamento
@app.route('/processar-emails-novos', methods=['POST'])  # API processar
@app.route('/gerar-planilha-brk')        # Interface Excel
@app.route('/dbedit')                    # DBEDIT Clipper
@app.route('/status-scheduler-brk')      # Status scheduler
@app.route('/reconstituicao-brk')        # Interface reconstituição
@app.route('/upload-token')              # Upload token Microsoft
```

## DEPLOYMENT (Render)
```yaml
Build: pip install -r requirements.txt
Start: python app.py
Environment: Set all ENV vars above
Storage: /opt/render/project/storage/ (persistent)
```
