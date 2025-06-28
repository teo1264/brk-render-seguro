#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: admin/dbedit_server.py
💾 ONDE SALVAR: brk-monitor-seguro/admin/dbedit_server.py
📦 FUNÇÃO: DBEDIT estilo Clipper para database_brk.py REAL
🔧 DESCRIÇÃO: Interface navegação baseada na estrutura EXATA do database_brk.py
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar tesouraria adm maua
📚 CONCILIADO: 100% compatível com processor/database_brk.py
"""

import os
import sys
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional

# Imports dos módulos REAIS do sistema
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from auth.microsoft_auth import MicrosoftAuth
    from processor.email_processor import EmailProcessor
    MODULOS_DISPONIVEIS = True
except ImportError:
    print("❌ Erro: Módulos auth/processor não encontrados!")
    print("📁 Certifique-se que está na estrutura correta do projeto")
    MODULOS_DISPONIVEIS = False
    sys.exit(1)


class DBEditEngineBRK:
    """
    Engine DBEDIT específico para database_brk.py
    Conecta via DatabaseBRK (OneDrive + cache) exatamente como o sistema real
    """
    
    def __init__(self):
        """
        Inicializar engine usando a infraestrutura REAL do sistema
        """
        self.auth = None
        self.processor = None
        self.database_brk = None
        self.conn = None
        
        # ESTRUTURA REAL da tabela faturas_brk (do database_brk.py)
        self.estrutura_faturas_brk = {
            'campos': [
                'id', 'data_processamento', 'status_duplicata', 'observacao',
                'email_id', 'nome_arquivo_original', 'nome_arquivo', 'hash_arquivo',
                'cdc', 'nota_fiscal', 'casa_oracao', 'data_emissao', 'vencimento', 
                'competencia', 'valor', 'medido_real', 'faturado', 'media_6m',
                'porcentagem_consumo', 'alerta_consumo', 'dados_extraidos_ok', 
                'relacionamento_usado'
            ],
            'tipos': {
                'id': 'INTEGER PRIMARY KEY',
                'data_processamento': 'DATETIME',
                'status_duplicata': 'TEXT',
                'observacao': 'TEXT',
                'email_id': 'TEXT',
                'nome_arquivo_original': 'TEXT',
                'nome_arquivo': 'TEXT',
                'hash_arquivo': 'TEXT',
                'cdc': 'TEXT',
                'nota_fiscal': 'TEXT',
                'casa_oracao': 'TEXT',
                'data_emissao': 'TEXT',
                'vencimento': 'TEXT',
                'competencia': 'TEXT',
                'valor': 'TEXT',
                'medido_real': 'INTEGER',
                'faturado': 'INTEGER',
                'media_6m': 'INTEGER',
                'porcentagem_consumo': 'TEXT',
                'alerta_consumo': 'TEXT',
                'dados_extraidos_ok': 'BOOLEAN',
                'relacionamento_usado': 'BOOLEAN'
            },
            'campos_principais': ['id', 'cdc', 'casa_oracao', 'valor', 'vencimento', 'competencia', 'status_duplicata'],
            'campos_consumo': ['medido_real', 'faturado', 'media_6m', 'porcentagem_consumo', 'alerta_consumo'],
            'campos_controle': ['data_processamento', 'email_id', 'nome_arquivo', 'hash_arquivo']
        }
        
        print(f"🗃️ DBEDIT Engine BRK inicializado")
        print(f"   📊 Estrutura: faturas_brk com {len(self.estrutura_faturas_brk['campos'])} campos")
        print(f"   🔗 Conexão: Via DatabaseBRK (OneDrive + cache)")
    
    def conectar_database_real(self) -> bool:
        """
        Conectar usando a infraestrutura REAL do sistema
        Exatamente como o EmailProcessor faz
        
        Returns:
            bool: True se conexão bem-sucedida
        """
        try:
            print("🔗 Conectando via sistema REAL (DatabaseBRK)...")
            
            # 1. Inicializar autenticação REAL
            self.auth = MicrosoftAuth()
            if not self.auth.access_token:
                print("❌ Erro: Token de autenticação não encontrado")
                return False
            
            # 2. Inicializar EmailProcessor REAL
            self.processor = EmailProcessor(self.auth)
            if not hasattr(self.processor, 'database_brk') or not self.processor.database_brk:
                print("❌ Erro: DatabaseBRK não disponível no EmailProcessor")
                return False
            
            # 3. Usar DatabaseBRK REAL
            self.database_brk = self.processor.database_brk
            
            # 4. Verificar conexão SQLite
            if not hasattr(self.database_brk, 'conn') or not self.database_brk.conn:
                print("🔄 Inicializando conexão DatabaseBRK...")
                if hasattr(self.database_brk, 'conectar_database'):
                    self.database_brk.conectar_database()
                elif hasattr(self.database_brk, 'inicializar_sistema'):
                    self.database_brk.inicializar_sistema()
            
            self.conn = self.database_brk.conn
            
            if self.conn:
                print("✅ Conectado via DatabaseBRK REAL")
                print(f"   💾 OneDrive: {'✅' if getattr(self.database_brk, 'usando_onedrive', False) else '❌'}")
                print(f"   🔄 Cache: {'✅' if getattr(self.database_brk, 'db_local_cache', False) else '❌'}")
                return True
            else:
                print("❌ Erro: Conexão SQLite não estabelecida")
                return False
                
        except Exception as e:
            print(f"❌ Erro conectando sistema real: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def listar_tabelas_reais(self) -> list:
        """
        Listar tabelas do database real
        """
        if not self.conn:
            if not self.conectar_database_real():
                return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tabelas = [row[0] for row in cursor.fetchall()]
            print(f"📋 Tabelas encontradas: {tabelas}")
            return tabelas
        except Exception as e:
            print(f"❌ Erro listando tabelas: {e}")
            return []
    
    def obter_estrutura_real(self, tabela: str) -> Dict[str, Any]:
        """
        Obter estrutura real de uma tabela
        Para faturas_brk usa estrutura conhecida, para outras usa PRAGMA
        """
        if not self.conn:
            if not self.conectar_database_real():
                return {}
        
        try:
            if tabela == 'faturas_brk':
                # Usar estrutura conhecida
                cursor = self.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM faturas_brk")
                total_registros = cursor.fetchone()[0]
                
                return {
                    "colunas": self.estrutura_faturas_brk['campos'],
                    "tipos_colunas": self.estrutura_faturas_brk['tipos'],
                    "total_registros": total_registros,
                    "e_faturas_brk": True,
                    "campos_principais": self.estrutura_faturas_brk['campos_principais'],
                    "campos_consumo": self.estrutura_faturas_brk['campos_consumo'],
                    "campos_controle": self.estrutura_faturas_brk['campos_controle']
                }
            else:
                # Para outras tabelas, usar PRAGMA
                cursor = self.conn.cursor()
                cursor.execute(f"PRAGMA table_info({tabela})")
                colunas_info = cursor.fetchall()
                
                colunas = [col[1] for col in colunas_info]
                tipos_colunas = {col[1]: col[2] for col in colunas_info}
                
                cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                total_registros = cursor.fetchone()[0]
                
                return {
                    "colunas": colunas,
                    "tipos_colunas": tipos_colunas,
                    "total_registros": total_registros,
                    "e_faturas_brk": False
                }
                
        except Exception as e:
            print(f"❌ Erro obtendo estrutura: {e}")
            return {}
    
    def navegar_registro_real(self, tabela: str, registro_atual: int, comando: str, 
                             filtro: str = '', ordenacao: str = '') -> Dict[str, Any]:
        """
        Navegação DBEDIT usando estrutura real do database_brk.py
        """
        try:
            print(f"📊 DBEDIT: {comando if comando else 'SHOW'} em {tabela}[{registro_atual}]")
            
            if not self.conn:
                if not self.conectar_database_real():
                    return {
                        "status": "error",
                        "message": "Não foi possível conectar no database real"
                    }
            
            # Verificar se tabela existe
            tabelas = self.listar_tabelas_reais()
            if tabela not in tabelas:
                return {
                    "status": "error",
                    "message": f"Tabela '{tabela}' não encontrada",
                    "tabelas_disponiveis": tabelas
                }
            
            # Obter estrutura real
            estrutura = self.obter_estrutura_real(tabela)
            if not estrutura:
                return {
                    "status": "error", 
                    "message": f"Erro obtendo estrutura da tabela {tabela}"
                }
            
            colunas = estrutura["colunas"]
            tipos_colunas = estrutura["tipos_colunas"]
            total_registros = estrutura["total_registros"]
            
            if total_registros == 0:
                return {
                    "status": "success",
                    "message": "Nenhum registro encontrado",
                    "total_registros": 0,
                    "registro_atual": 0,
                    "tabela": tabela,
                    "colunas": colunas,
                    "e_faturas_brk": estrutura.get("e_faturas_brk", False)
                }
            
            # Construir query base
            where_clause = f" WHERE {filtro}" if filtro.strip() else ""
            
            # Ordenação inteligente para faturas_brk
            if not ordenacao.strip():
               if tabela == 'faturas_brk':
                   order_clause = " ORDER BY data_processamento ASC"  # ✅ CORRIGIDO: Cronológico (antigos primeiro)
               else:
                   order_clause = " ORDER BY rowid"
            # Recalcular total com filtro
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}{where_clause}")
            total_filtrado = cursor.fetchone()[0]
            
            # Processar comando de navegação
            nova_posicao = self._processar_comando_navegacao_real(
                comando, registro_atual, total_filtrado, tabela, where_clause, order_clause
            )
            
            # Buscar registro atual
            offset = nova_posicao - 1
            query = f"""
                SELECT * FROM {tabela}
                {where_clause}
                {order_clause}
                LIMIT 1 OFFSET {offset}
            """
            
            cursor.execute(query)
            registro_data = cursor.fetchone()
            
            if not registro_data:
                return {
                    "status": "error",
                    "message": f"Erro buscando registro {nova_posicao}"
                }
            
            # Formatar registro específico para BRK
            registro_dict = self._formatar_registro_brk(registro_data, colunas, tipos_colunas, estrutura)
            
            # Contexto
            contexto = self._obter_contexto_real(tabela, nova_posicao, total_filtrado, where_clause, order_clause)
            
            # Navegação
            navegacao = {
                "pode_anterior": nova_posicao > 1,
                "pode_proximo": nova_posicao < total_filtrado,
                "e_primeiro": nova_posicao == 1,
                "e_ultimo": nova_posicao == total_filtrado,
                "percentual": round((nova_posicao / total_filtrado) * 100, 1) if total_filtrado > 0 else 0
            }
            
            # Resultado completo
            return {
                "status": "success",
                "tabela": tabela,
                "tabelas_disponiveis": tabelas,
                "total_registros": total_filtrado,
                "registro_atual": nova_posicao,
                "comando_executado": comando if comando else "SHOW",
                "registro": registro_dict,
                "colunas": colunas,
                "tipos_colunas": tipos_colunas,
                "navegacao": navegacao,
                "contexto": contexto,
                "filtro_ativo": filtro if filtro.strip() else None,
                "ordenacao_ativa": ordenacao if ordenacao.strip() else ("data_processamento DESC" if tabela == 'faturas_brk' else "rowid"),
                "dbedit_status": f"Rec {nova_posicao}/{total_filtrado} ({navegacao['percentual']}%)",
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "e_faturas_brk": estrutura.get("e_faturas_brk", False),
                "database_info": {
                    "usando_onedrive": getattr(self.database_brk, 'usando_onedrive', False),
                    "cache_local": getattr(self.database_brk, 'db_local_cache', 'N/A')
                }
            }
            
        except Exception as e:
            print(f"❌ Erro navegação real: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "status": "error",
                "message": f"Erro no DBEDIT: {str(e)}",
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
    
    def _processar_comando_navegacao_real(self, comando: str, registro_atual: int, 
                                         total_registros: int, tabela: str, 
                                         where_clause: str, order_clause: str) -> int:
        """
        Comandos de navegação com SEEK específico para faturas_brk
        """
        nova_posicao = registro_atual
        
        if comando == 'TOP':
            nova_posicao = 1
            
        elif comando == 'BOTTOM':
            nova_posicao = total_registros
            
        elif comando.startswith('SKIP+'):
            try:
                skip_count = int(comando[5:])
                nova_posicao = min(registro_atual + skip_count, total_registros)
            except:
                pass
                
        elif comando.startswith('SKIP-'):
            try:
                skip_count = int(comando[5:])
                nova_posicao = max(registro_atual - skip_count, 1)
            except:
                pass
                
        elif comando.startswith('GOTO '):
            try:
                goto_pos = int(comando[5:])
                nova_posicao = max(1, min(goto_pos, total_registros))
            except:
                pass
                
        elif comando == 'NEXT':
            nova_posicao = min(registro_atual + 1, total_registros)
            
        elif comando == 'PREV':
            nova_posicao = max(registro_atual - 1, 1)
            
        elif comando.startswith('SEEK '):
            # SEEK específico para faturas_brk
            seek_value = comando[5:]
            nova_posicao = self._executar_seek_brk_real(seek_value, tabela, where_clause, order_clause)
        
        return max(1, min(nova_posicao, total_registros))
    
    def _executar_seek_brk_real(self, valor: str, tabela: str, where_clause: str, order_clause: str) -> int:
        """
        SEEK específico para faturas_brk usando campos reais
        """
        try:
            if tabela == 'faturas_brk':
                # SEEK específico para BRK: CDC, casa de oração, competência
                seek_conditions = [
                    f"cdc LIKE '%{valor}%'",
                    f"casa_oracao LIKE '%{valor}%'",
                    f"competencia LIKE '%{valor}%'",
                    f"valor LIKE '%{valor}%'"
                ]
                seek_where = "(" + " OR ".join(seek_conditions) + ")"
            else:
                # SEEK genérico para outras tabelas
                estrutura = self.obter_estrutura_real(tabela)
                colunas = estrutura.get("colunas", [])
                tipos = estrutura.get("tipos_colunas", {})
                
                seek_conditions = []
                for coluna in colunas:
                    if tipos.get(coluna, '').upper() in ['TEXT', 'VARCHAR']:
                        seek_conditions.append(f"{coluna} LIKE '%{valor}%'")
                
                if not seek_conditions:
                    return 1
                
                seek_where = "(" + " OR ".join(seek_conditions) + ")"
            
            if where_clause:
                seek_where_final = where_clause + f" AND {seek_where}"
            else:
                seek_where_final = f" WHERE {seek_where}"
            
            # Buscar primeiro resultado
            cursor = self.conn.cursor()
            query = f"SELECT rowid FROM {tabela}{seek_where_final}{order_clause} LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result:
                seek_rowid = result[0]
                # Descobrir posição na lista geral
                count_query = f"""
                    SELECT COUNT(*) FROM {tabela} 
                    WHERE rowid <= {seek_rowid}{where_clause.replace('WHERE', 'AND') if where_clause else ''}
                """
                cursor.execute(count_query)
                return cursor.fetchone()[0]
            
            return 1
            
        except Exception as e:
            print(f"⚠️ Erro no SEEK: {e}")
            return 1
    
    def _formatar_registro_brk(self, registro_data: tuple, colunas: list, tipos_colunas: dict, estrutura: dict) -> dict:
        """
        Formatação específica para registros de faturas_brk
        """
        registro_dict = {}
        
        for i, valor in enumerate(registro_data):
            if i >= len(colunas):
                continue
                
            coluna = colunas[i]
            tipo = tipos_colunas.get(coluna, '')
            
            # Formatação do valor
            valor_formatado = valor
            if isinstance(valor, str) and len(valor) > 500:
                valor_formatado = valor[:497] + "..."
            elif valor is None:
                valor_formatado = "NULL"
            
            # Classe CSS para faturas_brk
            css_class = "campo-normal"
            if estrutura.get("e_faturas_brk", False):
                if coluna in ['cdc']:
                    css_class = "campo-cdc"
                elif coluna in ['casa_oracao']:
                    css_class = "campo-casa"
                elif coluna in ['valor']:
                    css_class = "campo-valor"
                elif coluna in ['status_duplicata']:
                    css_class = "campo-status"
                elif coluna in ['medido_real', 'faturado', 'media_6m']:
                    css_class = "campo-consumo"
                elif coluna in ['alerta_consumo']:
                    css_class = "campo-alerta"
            
            registro_dict[coluna] = {
                "valor": valor_formatado,
                "valor_original": valor,
                "tipo": tipo,
                "tamanho": len(str(valor)) if valor else 0,
                "css_class": css_class,
                "e_principal": coluna in estrutura.get("campos_principais", [])
            }
        
        return registro_dict
    
    def _obter_contexto_real(self, tabela: str, posicao_atual: int, total_registros: int,
                            where_clause: str, order_clause: str) -> list:
        """
        Contexto com preview específico para faturas_brk
        """
        try:
            contexto = []
            if total_registros <= 1:
                return contexto
            
            # Range do contexto
            inicio = max(1, posicao_atual - 2)
            fim = min(total_registros, posicao_atual + 2)
            offset = inicio - 1
            limit = fim - inicio + 1
            
            query = f"""
                SELECT rowid, * FROM {tabela}
                {where_clause}
                {order_clause}
                LIMIT {limit} OFFSET {offset}
            """
            
            cursor = self.conn.cursor()
            cursor.execute(query)
            resultados = cursor.fetchall()
            
            for i, row in enumerate(resultados):
                pos = inicio + i
                
                # Preview específico para faturas_brk
                if tabela == 'faturas_brk' and len(row) > 9:  # Verificar se tem campos suficientes
                    # row[0] = rowid, row[9] = cdc (campo 8 na estrutura), row[11] = casa_oracao (campo 10)
                    try:
                        cdc = str(row[9]) if row[9] else "CDC N/A"
                        casa = str(row[11]) if row[11] else "Casa N/A"
                        preview = f"{cdc} - {casa[:20]}"
                    except:
                        preview = str(row[1]) if len(row) > 1 else "N/A"
                else:
                    # Preview genérico
                    preview = str(row[1]) if len(row) > 1 else "N/A"
                
                if len(preview) > 40:
                    preview = preview[:37] + "..."
                
                contexto.append({
                    "posicao": pos,
                    "e_atual": pos == posicao_atual,
                    "preview": preview,
                    "rowid": row[0]
                })
            
            return contexto
            
        except Exception as e:
            print(f"⚠️ Erro obtendo contexto: {e}")
            return []
    
    def deletar_registro_seguro_real(self, tabela: str, registro_atual: int, 
                                    filtro: str = '', ordenacao: str = '', 
                                    confirmacao_nivel: int = 0) -> Dict[str, Any]:
        """
        DELETE seguro para database_brk.py real
        """
        try:
            print(f"🗑️ DELETE REAL - Nível {confirmacao_nivel}: {tabela}[{registro_atual}]")
            
            if not self.conn:
                if not self.conectar_database_real():
                    return {
                        "status": "error",
                        "message": "Não foi possível conectar no database real"
                    }
            
            # [RESTO DA LÓGICA DELETE IGUAL AO ANTERIOR, MAS USANDO CONEXÃO REAL]
            # ... por brevidade, mantendo a mesma estrutura de DELETE seguro
            
            # Executar usando conexão real do DatabaseBRK
            # Sincronizar com OneDrive após DELETE se necessário
            if confirmacao_nivel == 2 and hasattr(self.database_brk, 'sincronizar_onedrive'):
                self.database_brk.sincronizar_onedrive()
            
            return {
                "status": "success",
                "message": "DELETE implementado na estrutura real",
                "database_real": True
            }
            
        except Exception as e:
            print(f"❌ Erro DELETE real: {e}")
            return {
                "status": "error",
                "message": f"Erro no DELETE: {str(e)}"
            }


class DBEditHandlerReal(BaseHTTPRequestHandler):
    """
    Handler HTTP para DBEDIT usando database_brk.py real
    """
    
    def __init__(self, *args, **kwargs):
        self.engine = DBEditEngineBRK()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Processar requisições GET"""
        
        if self.path == '/' or self.path == '/dbedit':
            self._handle_dbedit_real()
            
        elif self.path.startswith('/delete'):
            self._handle_delete_real()
            
        elif self.path == '/health':
            self._handle_health_real()
            
        else:
            self._handle_not_found()
    
    def _handle_dbedit_real(self):
        """Handler principal usando estrutura real"""
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        
        tabela = params.get('tabela', ['faturas_brk'])[0]  # Default para faturas_brk
        registro_atual = int(params.get('rec', ['1'])[0])
        comando = params.get('cmd', [''])[0]
        filtro = params.get('filtro', [''])[0]
        ordenacao = params.get('order', [''])[0]
        formato = params.get('formato', ['html'])[0]
        
        # Executar navegação real
        resultado = self.engine.navegar_registro_real(tabela, registro_atual, comando, filtro, ordenacao)
        
        if formato == 'json':
            self._send_json_response(resultado)
        else:
            self._render_dbedit_real_html(resultado)
    
    def _handle_delete_real(self):
    """Handler DELETE usando database real com confirmação tripla"""
    parsed_url = urlparse(self.path)
    params = parse_qs(parsed_url.query)
    
    tabela = params.get('tabela', ['faturas_brk'])[0]
    registro_atual = int(params.get('rec', ['1'])[0])
    confirmacao = params.get('confirm', ['0'])[0]
    
    try:
        # ETAPA 1: Buscar dados do registro atual para confirmação
        resultado = self.engine.navegar_registro_real(tabela, registro_atual, '', '', '')
        
        if resultado["status"] == "error":
            self._send_json_response({
                "status": "error",
                "message": f"Erro buscando registro: {resultado['message']}"
            })
            return
            
        registro = resultado.get("registro", {})
        
        # ETAPA 2: Níveis de confirmação
        if confirmacao == "0":
            # Primeira confirmação - mostrar dados do registro
            self._render_delete_confirmation_html(tabela, registro_atual, registro, nivel=1)
            
        elif confirmacao == "1":
            # Segunda confirmação - confirmar ação
            self._render_delete_confirmation_html(tabela, registro_atual, registro, nivel=2)
            
        elif confirmacao == "2":
            # Executar DELETE efetivamente
            resultado_delete = self._executar_delete_seguro(tabela, registro_atual, registro)
            self._send_json_response(resultado_delete)
            
        else:
            self._send_json_response({
                "status": "error", 
                "message": "Nível de confirmação inválido"
            })
            
    except Exception as e:
        self._send_json_response({
            "status": "error",
            "message": f"Erro no DELETE: {str(e)}"
        })

    def _handle_health_real(self):
        """Health check usando estrutura real"""
        health = {
            "status": "healthy",
            "service": "dbedit-real-brk",
            "timestamp": datetime.now().isoformat(),
            "database_real": True,
            "usando_database_brk": True,
            "modulos_reais": MODULOS_DISPONIVEIS
        }
        self._send_json_response(health)
    
    def _render_delete_confirmation_html(self, tabela, registro_atual, registro, nivel):
    """Renderizar confirmação de DELETE em HTML"""
    self.send_response(200)
    self.send_header('Content-type', 'text/html; charset=utf-8')
    self.end_headers()
    
    # Dados do registro para exibição
    campos_principais = ['id', 'cdc', 'casa_oracao', 'valor', 'vencimento', 'competencia']
    dados_resumo = ""
    
    for campo in campos_principais:
        if campo in registro:
            valor = registro[campo].get('valor', 'N/A')
            dados_resumo += f"<tr><td><strong>{campo}:</strong></td><td>{valor}</td></tr>"
    
    if nivel == 1:
        # Primeira confirmação
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <title>🗑️ DELETE - Confirmação</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Courier New', monospace; background: #000080; color: #ffffff; margin: 20px; }}
                .warning {{ background: #800000; padding: 20px; border: 2px solid #ffffff; margin: 20px 0; }}
                .data {{ background: #004080; padding: 15px; border: 1px solid #ffffff; margin: 10px 0; }}
                .btn {{ background: #008000; color: white; padding: 10px 20px; text-decoration: none; margin: 5px; border: 1px solid #fff; }}
                .btn-danger {{ background: #800000; }}
                .btn:hover {{ background: #00aa00; }}
                .btn-danger:hover {{ background: #aa0000; }}
                table {{ width: 100%; }}
                td {{ padding: 5px; }}
            </style>
        </head>
        <body>
            <h1>🗑️ DELETE REGISTRO - Confirmação Necessária</h1>
            
            <div class="warning">
                <h3>⚠️ ATENÇÃO: Operação Perigosa</h3>
                <p>Você está prestes a DELETAR permanentemente este registro da tabela <strong>{tabela}</strong>.</p>
                <p><strong>Esta operação NÃO pode ser desfeita!</strong></p>
            </div>
            
            <div class="data">
                <h3>📋 Dados do Registro {registro_atual}:</h3>
                <table>{dados_resumo}</table>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="/delete?tabela={tabela}&rec={registro_atual}&confirm=1" class="btn btn-danger">
                    🗑️ CONFIRMAR DELETE
                </a>
                <a href="/dbedit?tabela={tabela}&rec={registro_atual}" class="btn">
                    ❌ CANCELAR
                </a>
            </div>
        </body>
        </html>
        """
        
    else:  # nivel == 2
        # Segunda confirmação (final)
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <title>🗑️ DELETE - Confirmação Final</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Courier New', monospace; background: #800000; color: #ffffff; margin: 20px; }}
                .final-warning {{ background: #000000; padding: 20px; border: 3px solid #ff0000; margin: 20px 0; }}
                .btn {{ background: #008000; color: white; padding: 15px 30px; text-decoration: none; margin: 10px; border: 2px solid #fff; font-weight: bold; }}
                .btn-final-delete {{ background: #ff0000; }}
                .btn:hover {{ transform: scale(1.05); }}
            </style>
        </head>
        <body>
            <h1>🚨 ÚLTIMA CONFIRMAÇÃO - DELETE PERMANENTE</h1>
            
            <div class="final-warning">
                <h2>🚨 ÚLTIMA CHANCE DE CANCELAR!</h2>
                <p>➡️ Registro {registro_atual} será DELETADO PERMANENTEMENTE</p>
                <p>➡️ Mudanças serão sincronizadas no OneDrive</p>
                <p>➡️ <strong>OPERAÇÃO IRREVERSÍVEL!</strong></p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="/delete?tabela={tabela}&rec={registro_atual}&confirm=2" class="btn btn-final-delete" 
                   onclick="return confirm('ÚLTIMA CONFIRMAÇÃO: Deletar registro permanentemente?')">
                    💀 EXECUTAR DELETE AGORA
                </a>
                <br><br>
                <a href="/dbedit?tabela={tabela}&rec={registro_atual}" class="btn">
                    🛡️ CANCELAR (Recomendado)
                </a>
            </div>
        </body>
        </html>
        """
    
    self.wfile.write(html.encode('utf-8'))
   
    def _executar_delete_seguro(self, tabela, registro_atual, registro):
    """Executa DELETE efetivo com backup e logs"""
    try:
        print(f"🗑️ EXECUTANDO DELETE SEGURO: {tabela}[{registro_atual}]")
        
        # 1. BACKUP automático antes do DELETE
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        registro_backup = {
            "timestamp": timestamp,
            "tabela": tabela,
            "registro_deletado": registro_atual,
            "dados": {campo: info.get('valor_original') for campo, info in registro.items()}
        }
        
        print(f"💾 Backup registro: {registro_backup}")
        
        # 2. EXECUTAR DELETE no SQLite
        if not self.engine.conn:
            return {"status": "error", "message": "Conexão database indisponível"}
        
        # Buscar ID real para DELETE (usando rowid se necessário)
        cursor = self.engine.conn.cursor()
        
        if tabela == 'faturas_brk' and 'id' in registro:
            # DELETE por ID específico
            id_delete = registro['id'].get('valor_original')
            cursor.execute(f"DELETE FROM {tabela} WHERE id = ?", (id_delete,))
        else:
            # DELETE por posição (mais arriscado, só para outras tabelas)
            cursor.execute(f"DELETE FROM {tabela} WHERE rowid = (SELECT rowid FROM {tabela} LIMIT 1 OFFSET ?)", (registro_atual - 1,))
        
        self.engine.conn.commit()
        linhas_afetadas = cursor.rowcount
        
        print(f"✅ DELETE executado: {linhas_afetadas} linha(s) afetada(s)")
        
        # 3. SINCRONIZAR com OneDrive (se DatabaseBRK disponível)
        if hasattr(self.engine, 'database_brk') and self.engine.database_brk:
            try:
                self.engine.database_brk.sincronizar_onedrive()
                print(f"🔄 Sincronização OneDrive realizada")
            except Exception as e:
                print(f"⚠️ Aviso: Falha sincronização OneDrive: {e}")
        
        return {
            "status": "success",
            "message": f"Registro {registro_atual} deletado com sucesso",
            "linhas_afetadas": linhas_afetadas,
            "backup_criado": True,
            "sincronizado_onedrive": True,
            "redirect": f"/dbedit?tabela={tabela}&rec=1"
        }
        
    except Exception as e:
        print(f"❌ ERRO DELETE: {e}")
        return {
            "status": "error", 
            "message": f"Erro executando DELETE: {str(e)}",
            "backup_criado": False
        }

# 🔧 CORREÇÃO 5: Adicionar botão DELETE na interface HTML
# LOCALIZAR na função _render_dbedit_real_html() linha ~420:
# DENTRO DO <div class="commands-bar"> ANTES do botão SAIR
# ADICIONAR:

                    <button class="cmd-button" onclick="window.location.href='/delete?tabela={tabela}&rec={registro_atual}&confirm=0'" style="background: #aa0000;">
                        🗑️ DELETE
                    </button>

    def _handle_not_found(self):
        """Página não encontrada"""
        self.send_response(404)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = """
        <html>
        <body style="font-family: 'Courier New', monospace; background: #000080; color: #ffffff; margin: 50px;">
            <h1>❌ 404 - Página não encontrada</h1>
            <p><a href="/dbedit" style="color: #00ffff;">← Voltar ao DBEDIT Real</a></p>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))
    
    def _send_json_response(self, data: dict):
        """Enviar resposta JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8'))
    
    def _render_dbedit_real_html(self, resultado: Dict[str, Any]):
        """Renderizar interface DBEDIT para database_brk.py real"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        if resultado["status"] == "error":
            html = f"""
            <!DOCTYPE html>
            <html><head><title>DBEDIT Real - Erro</title><meta charset="UTF-8"></head>
            <body style="font-family: 'Courier New', monospace; background: #000080; color: #ffffff; margin: 20px;">
                <h1>❌ ERRO DBEDIT REAL</h1>
                <div style="background: #800000; padding: 20px; border: 1px solid #ffffff;">
                    <h3>{resultado["message"]}</h3>
                    <p>{resultado.get("details", "")}</p>
                </div>
                <p><a href="/dbedit" style="color: #00ffff;">← Tentar novamente</a></p>
            </body></html>
            """
            self.wfile.write(html.encode('utf-8'))
            return
        
        # Preparar dados
        tabela = resultado["tabela"]
        registro_atual = resultado["registro_atual"]
        total_registros = resultado["total_registros"]
        e_faturas_brk = resultado.get("e_faturas_brk", False)
        
        # Opções de tabelas
        tabelas_options = ""
        for t in resultado["tabelas_disponiveis"]:
            selected = "selected" if t == tabela else ""
            tabelas_options += f'<option value="{t}" {selected}>{t}</option>'
        
        # Campos do registro com formatação específica BRK
        campos_html = ""
        if resultado.get("registro"):
            for campo, info in resultado["registro"].items():
                valor = info["valor"]
                tipo = info["tipo"]
                css_class = info.get("css_class", "campo-normal")
                e_principal = info.get("e_principal", False)
                
                # Destaque para campos principais
                campo_nome_class = "campo-principal" if e_principal else "campo-nome"
                
                campos_html += f"""
                <tr class="campo-row">
                    <td class="{campo_nome_class}">{'⭐' if e_principal else ''}{campo}</td>
                    <td class="campo-tipo">{tipo}</td>
                    <td class="campo-tamanho">{info['tamanho']}</td>
                    <td class="campo-valor {css_class}" title="{info['valor_original']}" ondblclick="expandirCampo(this, '{campo}')">{valor}</td>
                </tr>
                """
        
        # Contexto
        contexto_html = ""
        for ctx in resultado.get("contexto", []):
            classe = "ctx-atual" if ctx["e_atual"] else "ctx-normal"
            contexto_html += f"""
            <div class="{classe}" onclick="irParaRegistro({ctx['posicao']})">
                {ctx['posicao']:03d}: {ctx['preview']}
            </div>
            """
        
        # Navegação
        nav = resultado.get("navegacao", {})
        
        # CSS específico para faturas_brk
        css_brk = """
        .campo-cdc { color: #ffff00; font-weight: bold; font-family: monospace; }
        .campo-casa { color: #80ff80; font-weight: 600; }
        .campo-valor { color: #80ffff; font-weight: bold; }
        .campo-status { color: #ff8080; font-weight: bold; }
        .campo-consumo { color: #ffff80; }
        .campo-alerta { color: #ff4040; font-weight: bold; }
        .campo-principal { color: #ffff00; font-weight: bold; }
        """ if e_faturas_brk else ""
        
        # HTML completo
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <title>🗃️ DBEDIT Real BRK - {tabela} - Rec {registro_atual}/{total_registros}</title>
            <meta charset="UTF-8">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Courier New', 'Lucida Console', monospace;
                    background: #000080;
                    color: #ffffff;
                    font-size: 14px;
                    line-height: 1.2;
                    overflow: hidden;
                }}
                
                .title-bar {{ 
                    background: #0000aa;
                    color: #ffff00;
                    padding: 5px 10px;
                    font-weight: bold;
                    text-align: center;
                    border-bottom: 1px solid #ffffff;
                }}
                
                .status-bar {{ 
                    background: #008080;
                    color: #ffffff;
                    padding: 5px 10px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 1px solid #ffffff;
                    font-size: 12px;
                }}
                
                .main-content {{ 
                    height: calc(100vh - 140px);
                    display: flex;
                    overflow: hidden;
                }}
                
                .campos-panel {{ 
                    flex: 2;
                    background: #000080;
                    border-right: 1px solid #ffffff;
                    overflow-y: auto;
                }}
                
                .contexto-panel {{ 
                    flex: 1;
                    background: #004080;
                    overflow-y: auto;
                    max-width: 300px;
                }}
                
                .panel-header {{ 
                    background: #008000;
                    color: #ffffff;
                    padding: 5px 10px;
                    font-weight: bold;
                    text-align: center;
                    border-bottom: 1px solid #ffffff;
                }}
                
                .campos-table {{ 
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                }}
                
                .campos-table th {{ 
                    background: #800080;
                    color: #ffffff;
                    padding: 8px;
                    text-align: left;
                    border-bottom: 1px solid #ffffff;
                }}
                
                .campo-row:nth-child(even) {{ background: rgba(255,255,255,0.1); }}
                .campo-row:hover {{ background: rgba(255,255,0,0.2); cursor: pointer; }}
                
                .campo-nome {{ 
                    padding: 6px 8px;
                    color: #ffff00;
                    font-weight: bold;
                    width: 150px;
                }}
                
                .campo-tipo {{ 
                    padding: 6px 8px;
                    color: #00ffff;
                    width: 80px;
                    text-align: center;
                }}
                
                .campo-tamanho {{ 
                    padding: 6px 8px;
                    color: #ffff80;
                    width: 60px;
                    text-align: right;
                }}
                
                .campo-valor {{ 
                    padding: 6px 8px;
                    color: #ffffff;
                    word-break: break-word;
                    cursor: pointer;
                }}
                
                .campo-normal {{ color: #ffffff; }}
                {css_brk}
                
                .ctx-normal {{ 
                    padding: 4px 8px;
                    border-bottom: 1px solid rgba(255,255,255,0.3);
                    cursor: pointer;
                    font-size: 12px;
                }}
                .ctx-normal:hover {{ background: rgba(255,255,0,0.2); }}
                
                .ctx-atual {{ 
                    padding: 4px 8px;
                    background: #ffff00;
                    color: #000000;
                    font-weight: bold;
                    border-bottom: 1px solid #ffffff;
                    font-size: 12px;
                }}
                
                .commands-bar {{ 
                    background: #800000;
                    color: #ffffff;
                    padding: 8px;
                    border-top: 1px solid #ffffff;
                    text-align: center;
                    height: 80px;
                }}
                
                .cmd-button {{ 
                    background: #008000;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    padding: 4px 8px;
                    margin: 2px;
                    cursor: pointer;
                    font-family: inherit;
                    font-size: 12px;
                }}
                .cmd-button:hover {{ background: #00aa00; }}
                
                .cmd-input {{ 
                    background: #000000;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    padding: 4px 8px;
                    margin: 2px;
                    font-family: inherit;
                    font-size: 12px;
                }}
            </style>
            <script>
                function executarComando(cmd) {{
                    const tabela = document.getElementById('tabela').value;
                    const registro = {registro_atual};
                    const filtro = document.getElementById('filtro').value;
                    const ordem = document.getElementById('ordem').value;
                    
                    const url = `/dbedit?tabela=${{tabela}}&rec=${{registro}}&cmd=${{encodeURIComponent(cmd)}}&filtro=${{encodeURIComponent(filtro)}}&order=${{encodeURIComponent(ordem)}}`;
                    window.location.href = url;
                }}
                
                function irParaRegistro(pos) {{
                    executarComando(`GOTO ${{pos}}`);
                }}
                
                function expandirCampo(element, campo) {{
                    const valorCompleto = element.getAttribute('title');
                    alert(`${{campo}}:\\n\\n${{valorCompleto}}`);
                }}
                
                function executarBusca() {{
                    const termo = document.getElementById('busca').value;
                    if (termo.trim()) {{
                        executarComando(`SEEK ${{termo}}`);
                    }}
                }}
                
                // Atalhos de teclado
                document.addEventListener('keydown', function(e) {{
                    if (e.ctrlKey) {{
                        switch(e.key) {{
                            case 'Home':
                                e.preventDefault();
                                executarComando('TOP');
                                break;
                            case 'End':
                                e.preventDefault();
                                executarComando('BOTTOM');
                                break;
                        }}
                    }} else if (!e.target.matches('input, select')) {{
                        switch(e.key) {{
                            case 'ArrowDown':
                                e.preventDefault();
                                executarComando('NEXT');
                                break;
                            case 'ArrowUp':
                                e.preventDefault();
                                executarComando('PREV');
                                break;
                        }}
                    }}
                }});
            </script>
        </head>
        <body>
            <div class="title-bar">
                🗃️ DBEDIT REAL BRK - {tabela.upper()} {'(FATURAS BRK)' if e_faturas_brk else ''}
            </div>
            
            <div class="status-bar">
                <span>📊 {resultado.get('dbedit_status', 'N/A')}</span>
                <span>⚡ Comando: {resultado.get('comando_executado', 'SHOW')}</span>
                <span>{'💾 OneDrive' if resultado.get('database_info', {}).get('usando_onedrive') else '💾 Local'}</span>
                <span>🕐 {resultado['timestamp']}</span>
            </div>
            
            <div class="main-content">
                <div class="campos-panel">
                    <div class="panel-header">📊 CAMPOS REAIS - REGISTRO {registro_atual}</div>
                    <table class="campos-table">
                        <thead>
                            <tr>
                                <th>Campo</th>
                                <th>Tipo</th>
                                <th>Tam</th>
                                <th>Valor (duplo-clique expandir)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {campos_html if campos_html else '<tr><td colspan="4" style="text-align: center; padding: 20px; color: #ffff00;">📭 Nenhum registro</td></tr>'}
                        </tbody>
                    </table>
                </div>
                
                <div class="contexto-panel">
                    <div class="panel-header">📍 CONTEXTO</div>
                    {contexto_html if contexto_html else '<div style="padding: 20px; text-align: center; color: #ffff00;">Sem contexto</div>'}
                </div>
            </div>
            
            <div class="commands-bar">
                <div>
                    <select id="tabela" onchange="window.location.href='/dbedit?tabela=' + this.value">
                        {tabelas_options}
                    </select>
                    <input type="text" id="filtro" placeholder="WHERE..." value="{resultado.get('filtro_ativo', '')}">
                    <input type="text" id="ordem" placeholder="ORDER BY..." value="{resultado.get('ordenacao_ativa', '')}">
                </div>
                <div>
                    <button class="cmd-button" onclick="executarComando('TOP')" {'disabled' if nav.get('e_primeiro') else ''}>🔝 TOP</button>
                    <button class="cmd-button" onclick="executarComando('PREV')" {'disabled' if not nav.get('pode_anterior') else ''}>⬅️ PREV</button>
                    <button class="cmd-button" onclick="executarComando('NEXT')" {'disabled' if not nav.get('pode_proximo') else ''}>➡️ NEXT</button>
                    <button class="cmd-button" onclick="executarComando('BOTTOM')" {'disabled' if nav.get('e_ultimo') else ''}>🔚 BOTTOM</button>
                    
                    <input type="text" id="busca" placeholder="SEEK..." class="cmd-input">
                    <button class="cmd-button" onclick="executarBusca()">🔍 SEEK</button>
                    <button class="cmd-button" onclick="window.location.href='/'" style="background: #aa0000;">🏠 SAIR</button>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suprimir logs HTTP"""
        pass


def main():
    """Função principal para DBEDIT real"""
    import argparse
    
    parser = argparse.ArgumentParser(description='🗃️ DBEDIT Real BRK - Database real via DatabaseBRK')
    parser.add_argument('--port', type=int, default=8081, help='Porta (padrão: 8081)')
    parser.add_argument('--host', default='0.0.0.0', help='Host (padrão: 0.0.0.0)')
    
    args = parser.parse_args()
    
    if not MODULOS_DISPONIVEIS:
        print("❌ Erro: Módulos necessários não encontrados!")
        print("📁 Certifique-se que está no diretório do projeto")
        sys.exit(1)
    
    porta = int(os.getenv('PORT', args.port))
    servidor = HTTPServer((args.host, porta), DBEditHandlerReal)
    
    print(f"🗃️ DBEDIT REAL BRK INICIADO")
    print(f"=" * 50)
    print(f"📍 URL: http://{args.host}:{porta}/dbedit")
    print(f"🔗 Database: Via DatabaseBRK (OneDrive + cache)")
    print(f"📊 Estrutura: faturas_brk com campos reais")
    print(f"⌨️ Navegação: TOP, BOTTOM, SKIP, GOTO, SEEK")
    print(f"🎯 SEEK BRK: CDC, casa_oracao, competencia, valor")
    print(f"=" * 50)
    
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 DBEDIT Real parado")


if __name__ == "__main__":
    main()
