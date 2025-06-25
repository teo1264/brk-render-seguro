# 🚀 BRK Monitor Seguro

Sistema automático para monitoramento de emails BRK com processamento de PDFs e armazenamento seguro.

## 🎯 Funcionalidades

- **📧 Monitor automático** de emails da pasta BRK
- **📊 Diagnóstico em tempo real** (total, 24h, mês)
- **💾 Armazenamento SQLite** com persistent disk
- **📤 Upload simulado** OneDrive
- **🌐 Interface web** para status e configuração
- **🔒 Segurança total** - sem dados hardcoded

## 🔧 Configuração Local

### 1. Clonar repositório
```bash
git clone https://github.com/SEU_USER/brk-monitor-seguro.git
cd brk-monitor-seguro
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente
```bash
# Criar arquivo .env
echo "MICROSOFT_CLIENT_ID=seu_client_id_aqui" > .env
echo "PASTA_BRK_ID=seu_pasta_id_aqui" >> .env
echo "MICROSOFT_TENANT_ID=consumers" >> .env
```

### 4. Executar localmente
```bash
python app.py
```

Acesse: http://localhost:8080

## ☁️ Deploy no Render

### 1. Conectar repositório
- Render.com → New Web Service
- Conectar este repositório GitHub
- Nome: `brk-monitor`

### 2. Configurar build
```bash
Build Command: pip install -r requirements.txt
Start Command: python app.py
```

### 3. Configurar variáveis de ambiente
No Render Dashboard → Environment:

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `MICROSOFT_CLIENT_ID` | `seu_client_id` | Client ID da aplicação Microsoft |
| `PASTA_BRK_ID` | `seu_pasta_id` | ID da pasta BRK no Outlook |
| `MICROSOFT_TENANT_ID` | `consumers` | Tenant Microsoft (opcional) |
| `PORT` | `8080` | Porta do servidor (automático) |

### 4. Habilitar Persistent Disk
- Render Dashboard → Service → Storage
- Add Disk: `/opt/render/project/storage` (1GB)

## 🔑 Setup Inicial Token

### 1. Via interface web
1. Acesse: `https://seu-app.onrender.com/upload-token`
2. Cole o conteúdo do seu `token.json` local
3. Clique "Salvar Token"

### 2. Arquivo token.json local
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJub...",
  "refresh_token": "0.ARwA6WgJJ9X2qE...",
  "expires_in": 3600
}
```

## 📊 Monitoramento

### Logs esperados (a cada 10 minutos):
```
🚀 INICIANDO PROCESSAMENTO BRK
========================================
📊 DIAGNÓSTICO PASTA BRK:
   📧 Total: 1,247
   📅 24h: 3
   📆 Mês: 45

📧 Encontrados 2 emails
📎 Processando 1 PDFs...
✅ fatura_brk_123.pdf

📊 RESULTADO:
   Emails: 1
   PDFs: 1
   Tempo: 2.3s
   Total DB: 15
✅ EXECUÇÃO CONCLUÍDA
========================================
```

### Endpoints disponíveis:
- `/` - Status principal
- `/upload-token` - Upload inicial do token
- `/health` - Health check JSON

## 🛡️ Segurança

### ✅ Implementado:
- **Sem hardcoded values** - todas as credenciais via ENV
- **Logs seguros** - IDs ocultados (`fea6ce2a******`)
- **Validação obrigatória** - sistema para se ENV faltando
- **Token renovação automática** - refresh_token gerenciado
- **Interface web segura** - dados sensíveis protegidos

### 🔒 Dados protegidos:
- `MICROSOFT_CLIENT_ID`
- `PASTA_BRK_ID`
- `token.json` (access/refresh tokens)

## 📁 Estrutura do Projeto

```
brk-monitor-seguro/
├── app.py              # Aplicação principal
├── requirements.txt    # Dependências Python
├── README.md          # Esta documentação
├── .gitignore         # Arquivos ignorados
└── .env.example       # Exemplo de configuração
```

## 🔄 Fluxo de Funcionamento

1. **Background Process**: Executa a cada 10 minutos
2. **Diagnóstico**: Conta emails (total, 24h, mês)
3. **Busca**: Emails novos (últimas 24h)
4. **Processamento**: Extrai PDFs dos anexos
5. **Armazenamento**: SQLite + OneDrive simulado
6. **Controle**: Evita duplicatas por hash SHA256

## 🐛 Troubleshooting

### Token expirado
```
🔄 Token expirado, renovando...
✅ Token renovado com sucesso
```

### Variáveis não configuradas
```
❌ VARIÁVEIS FALTANDO: ['MICROSOFT_CLIENT_ID (Client ID Microsoft)']
Configure no Render → Environment → Add Variable
⚠️ SISTEMA PARADO POR SEGURANÇA
```

### Pasta BRK não encontrada
- Verificar `PASTA_BRK_ID` no Render Environment
- Conferir permissões da aplicação Microsoft

## 📈 Próximas Versões

- [ ] Extração real de dados dos PDFs (OCR)
- [ ] OneDrive API real (não simulado)
- [ ] Dashboard web com gráficos
- [ ] Notificações por email/Slack
- [ ] Processamento de outros tipos de anexo

## 📝 Logs e Debug

### Verificar funcionamento:
```bash
# Logs do Render
tail -f /var/log/render.log

# Status do banco
sqlite3 /opt/render/project/storage/brk_basico.db "SELECT COUNT(*) FROM faturas_brk_basico;"

# Arquivos salvos
ls -la /opt/render/project/storage/onedrive_simulado/BRK/
```

---

**🔒 Versão segura - Dados sensíveis protegidos via variáveis de ambiente**
# Deploy test
