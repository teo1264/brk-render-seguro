#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📱 MESSAGE FORMATTER - Formatação Mensagens Alerta Telegram
📧 FUNÇÃO: Formatar mensagens usando lógica do script criar_alerta21.py
👨‍💼 RESPONSÁVEL: Sidney Gubitoso - Auxiliar Tesouraria Administrativa Mauá
📅 DATA CRIAÇÃO: 04/07/2025
📁 SALVAR EM: processor/alertas/message_formatter.py
"""

def formatar_mensagem_alerta(dados_fatura):
    """
    Formatar mensagem usando lógica do script criar_alerta21.py
    Baseado nos modelos definidos no documento de integração
    
    Args:
        dados_fatura (dict): Dados completos da fatura do Sistema BRK
    
    Returns:
        str: Mensagem formatada para Telegram
    """
    try:
        print(f"📝 Formatando mensagem para Telegram...")
        
        # Extrair dados principais
        casa = dados_fatura.get('casa_oracao', 'Casa não identificada')
        venc = fmt_data(dados_fatura.get('vencimento', ''))
        valor = fmt_valor(dados_fatura.get('valor', ''))
        cons = fmt_m3(dados_fatura.get('medido_real', 0))
        media = fmt_m3(dados_fatura.get('media_6m', 0))
        
        print(f"   🏠 Casa: {casa}")
        print(f"   📅 Vencimento: {venc}")
        print(f"   💰 Valor: {valor}")
        print(f"   📊 Consumo: {cons}")
        print(f"   📉 Média: {media}")
        
        # Determinar tipo de alerta
        tipo_alerta = determinar_tipo_alerta(dados_fatura)
        print(f"   🎯 Tipo alerta: {tipo_alerta}")
        
        # Formatar mensagem baseada no tipo
        if tipo_alerta == "Consumo Normal":
            mensagem = f"""*A Paz de Deus!* 🕊️

📍 Casa de Oração: {casa}  
📆 Vencimento: {venc}  
💰 Valor da Conta: {valor}  

━━━━━━━━━━━━━━━━  
📊 *Consumo Atual:* {cons}  
📉 *Média (6 meses):* {media}  
✅ *Consumo dentro do padrão*  
━━━━━━━━━━━━━━━━  

🤖 *Sistema BRK Automático*
🙏 *Deus abençoe!*"""
            
        elif tipo_alerta == "Alto Consumo":
            perc = dados_fatura.get('porcentagem_consumo', 'N/A')
            dif_str = calcular_diferenca_m3(dados_fatura)
            
            mensagem = f"""*A Paz de Deus!* 🕊️

🟡 AVISO IMPORTANTE 🟡  
📢 ALERTA DE ALTO CONSUMO DE ÁGUA  

📍 Casa de Oração: {casa}  
📆 Vencimento: {venc}  
💰 Valor da Conta: {valor}  

━━━━━━━━━━━━━━━━  
📊 *Consumo Atual:* {cons}  
📉 *Média (6 meses):* {media}  
📈 *Aumento:* {dif_str} ({perc})  
━━━━━━━━━━━━━━━━  

⚠️ *VERIFIQUE:*  
🔹 Possíveis vazamentos  
🔹 Torneiras pingando  
🔹 Boia da caixa d'água  
🔹 Uso maior devido a evento ou outra necessidade?  

🤖 *Sistema BRK Automático*
🙏 *Deus abençoe!*"""
            
        elif tipo_alerta == "Crítico" or tipo_alerta == "Emergência":
            perc = dados_fatura.get('porcentagem_consumo', 'N/A')
            dif_str = calcular_diferenca_m3(dados_fatura)
            
            mensagem = f"""*A Paz de Deus!* 🕊️

🔴 EMERGÊNCIA 🔴  
📢 ALERTA DE EMERGÊNCIA DE CONSUMO DE ÁGUA  

📍 Casa de Oração: {casa}  
📆 Vencimento: {venc}  
💰 Valor da Conta: {valor}  

━━━━━━━━━━━━━━━━  
📊 *Consumo Atual:* {cons}  
📉 *Média (6 meses):* {media}  
📈 *Aumento:* {dif_str} ({perc})  
━━━━━━━━━━━━━━━━  

⚠️ *VERIFIQUE IMEDIATAMENTE:*  
🔹 Possíveis vazamentos  
🔹 Torneiras pingando  
🔹 Boia da caixa d'água  
🔹 Uso maior devido a evento ou outra necessidade?  

📎 *Solicitamos ao encarregado da manutenção a verificação da fatura BRK para análise dos últimos consumos. Caso identifique algum vazamento, favor informar imediatamente para que possamos bloquear o débito automático e solicitar revisão da conta.*

🤖 *Sistema BRK Automático*
🙏 *Deus abençoe!*"""
            
        elif tipo_alerta == "Consumo Baixo":
            perc = dados_fatura.get('porcentagem_consumo', 'N/A')
            dif_str = calcular_diferenca_m3(dados_fatura)
            
            mensagem = f"""*A Paz de Deus!* 🕊️

📉 *AVISO DE CONSUMO REDUZIDO*  

📍 Casa de Oração: {casa}  
📆 Vencimento: {venc}  
💰 Valor da Conta: {valor}  

━━━━━━━━━━━━━━━━  
📊 *Consumo Atual:* {cons}  
📉 *Média (6 meses):* {media}  
📉 *Redução:* {dif_str} ({perc})  
━━━━━━━━━━━━━━━━  

⚠️ *VERIFICAR POSSÍVEIS CAUSAS:*  
🔹 Hidrômetro com funcionamento irregular  
🔹 Edifício sem utilização no período  
🔹 Mudança sazonal no uso da água  

🤖 *Sistema BRK Automático*
🙏 *Deus abençoe!*"""
            
        else:
            # Fallback para casos não identificados
            mensagem = f"""*A Paz de Deus!* 🕊️

📍 Casa de Oração: {casa}  
📆 Vencimento: {venc}  
💰 Valor da Conta: {valor}  

━━━━━━━━━━━━━━━━  
📊 *Consumo Atual:* {cons}  
📉 *Média (6 meses):* {media}  
━━━━━━━━━━━━━━━━  

🤖 *Sistema BRK Automático*
🙏 *Deus abençoe!*"""
        
        print(f"✅ Mensagem formatada: {len(mensagem)} caracteres")
        return mensagem
        
    except Exception as e:
        print(f"❌ Erro formatando mensagem: {e}")
        return "Erro na formatação da mensagem"

def determinar_tipo_alerta(dados_fatura):
    """
    Determinar tipo de alerta baseado no consumo
    Lógica baseada no script criar_alerta21.py
    
    Args:
        dados_fatura (dict): Dados da fatura
    
    Returns:
        str: Tipo do alerta
    """
    try:
        medido_real = float(dados_fatura.get('medido_real', 0))
        media_6m = float(dados_fatura.get('media_6m', 0))
        
        if media_6m == 0:
            return "Consumo Normal"  # Evitar divisão por zero
        
        # Calcular variação percentual
        variacao_percentual = ((medido_real - media_6m) / media_6m) * 100
        variacao_absoluta = medido_real - media_6m
        
        print(f"   📊 Medido: {medido_real} m³")
        print(f"   📉 Média: {media_6m} m³")
        print(f"   📈 Variação: {variacao_percentual:.1f}% ({variacao_absoluta:.1f} m³)")
        
        # Lógica de determinação (baseada no documento)
        if medido_real <= media_6m:
            return "Consumo Normal"
        elif variacao_percentual <= 50:
            return "Alto Consumo"
        elif variacao_percentual <= 100:
            if variacao_absoluta >= 5:  # Crítico se variação ≥5m³
                return "Crítico"
            else:
                return "Alto Consumo"
        else:  # variação > 100%
            if variacao_absoluta >= 10:  # Emergência se variação ≥10m³
                return "Emergência"
            else:
                return "Crítico"
        
        # Verificar consumo baixo
        if variacao_percentual < -50:
            if variacao_absoluta <= -10:  # Consumo muito baixo
                return "Consumo Baixo"
            else:
                return "Consumo Baixo"
                
    except Exception as e:
        print(f"❌ Erro determinando tipo alerta: {e}")
        return "Alto Consumo"  # Fallback seguro

def fmt_data(data):
    """Formatar data para exibição"""
    if not data:
        return "N/A"
    return str(data)

def fmt_valor(valor):
    """Formatar valor monetário"""
    if not valor:
        return "N/A"
    # Se já vem formatado (R$ X,XX), manter
    if isinstance(valor, str) and 'R$' in valor:
        return valor
    # Senão, formatar
    try:
        if isinstance(valor, (int, float)):
            return f"R$ {valor:.2f}".replace('.', ',')
        else:
            return f"R$ {valor}"
    except:
        return str(valor)

def fmt_m3(valor):
    """Formatar consumo em m³"""
    try:
        num_valor = float(valor)
        return f"{num_valor:.1f} m³"
    except:
        return "N/A"

def calcular_diferenca_m3(dados_fatura):
    """Calcular diferença em m³ para exibição"""
    try:
        medido = float(dados_fatura.get('medido_real', 0))
        media = float(dados_fatura.get('media_6m', 0))
        dif = medido - media
        
        if dif > 0:
            return f"+{dif:.1f} m³"
        else:
            return f"{dif:.1f} m³"
    except:
        return "N/A"
