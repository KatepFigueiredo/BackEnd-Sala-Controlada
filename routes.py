from flask import request, jsonify
from queries import *
import time


LOTACAO_MAXIMA = 3
last_saida_pendente = False


ultimo_evento = {
    "tipo": None,
    "dados": None,
    "timestamp": None
}


def init_all_routes(app):
    global last_saida_pendente
    global ultimo_evento

    # ========== ENDPOINT: /ultimo_evento ==========
    @app.route('/ultimo_evento', methods=['GET'])
    def obter_ultimo_evento():
        """Frontend faz polling para obter eventos do Arduino"""
        if ultimo_evento["tipo"] is None:
            return "", 204
        
        evento = {
            "tipo": ultimo_evento["tipo"],
            "dados": ultimo_evento["dados"]
        }
        
        ultimo_evento["tipo"] = None
        ultimo_evento["dados"] = None
        
        return jsonify(evento)

    # ========== ENDPOINT: /botao_saida ==========
    @app.route('/botao_saida', methods=['POST'])
    def botao_saida():
        global last_saida_pendente
        ocupacao_atual = obter_ocupacao_atual()

        if ocupacao_atual <= 0:
            print("BOTAO SAIDA: Sala vazia!")
            return jsonify({"status": "erro", "mensagem": "Sala vazia"}), 403

        last_saida_pendente = True
        print(f"BOTAO SAIDA: Ativado! Ocupacao: {ocupacao_atual}/{LOTACAO_MAXIMA}")
        return jsonify({
            "status": "ok",
            "mensagem": "Processo de saída iniciado",
            "ocupacao": ocupacao_atual
        })

    # ========== ENDPOINT: /botao_saida_status ==========
    @app.route('/botao_saida_status', methods=['GET'])
    def botao_saida_status():
        global last_saida_pendente

        if not last_saida_pendente:
            return "", 204

        last_saida_pendente = False
        return jsonify({"permitir_saida": True})
    
    # ========== ENDPOINT: /verificar_rfid ==========
    @app.route('/verificar_rfid', methods=['POST'])
    def verificar_rfid():
        global ultimo_evento
        
        data = request.get_json()
        chave_rfid = data.get('chave_rfid', '')
        
        print(f"RFID recebido: {chave_rfid}")
        
        nome_cartao = verificar_cartao(chave_rfid)
        ocupacao = obter_ocupacao_atual()
        
        if nome_cartao:
            if ocupacao >= LOTACAO_MAXIMA:
                resultado = 'lotacao_maxima'
                print(f"  Sala CHEIA ({ocupacao}/{LOTACAO_MAXIMA})")
                ultimo_evento = {
                    "tipo": "rfid_lotacao",
                    "dados": {"nome": nome_cartao, "ocupacao": ocupacao},
                    "timestamp": time.time()
                }
            else:
                resultado = 'permitido'
                print(f"  PERMITIDO: {nome_cartao} (Ocupacao: {ocupacao}/{LOTACAO_MAXIMA})")
                ultimo_evento = {
                    "tipo": "rfid_permitido",
                    "dados": {"nome": nome_cartao, "ocupacao": ocupacao},
                    "timestamp": time.time()
                }
        else:
            resultado = 'negado'
            print(f"  NEGADO (cartao invalido: {chave_rfid})")
            ultimo_evento = {
                "tipo": "rfid_negado",
                "dados": {"chave_rfid": chave_rfid},
                "timestamp": time.time()
            }
        
        return jsonify({"status": resultado})

    # ========== ENDPOINT: /ocupacao ==========
    @app.route('/ocupacao', methods=['GET', 'POST'])
    def ocupacao():
        global ultimo_evento
        
        if request.method == 'POST':
            data = request.get_json()
            variacao = data.get('variacao')
            ocupacao_atual = obter_ocupacao_atual()
            
            if variacao == 1 and ocupacao_atual >= LOTACAO_MAXIMA:
                return jsonify({"status": "erro"}), 403
            
            nova_ocupacao = max(0, ocupacao_atual + variacao)
            atualizar_ocupacao(nova_ocupacao)
            print(f"Ocupacao: {ocupacao_atual} -> {nova_ocupacao}")
            
            if variacao == 1:
                tipo_evento = "entrada"
            else:
                tipo_evento = "saida"
            
            ultimo_evento = {
                "tipo": tipo_evento,
                "dados": {"ocupacao": nova_ocupacao, "variacao": variacao},
                "timestamp": time.time()
            }
            
            return jsonify({
                "status": "ok",
                "ocupacao": nova_ocupacao,
                "lotacao_maxima": LOTACAO_MAXIMA
            })
        
        ocupacao_atual = obter_ocupacao_atual()
        return jsonify({
            "ocupacao_atual": ocupacao_atual,
            "lotacao_maxima": LOTACAO_MAXIMA,
            "disponivel": LOTACAO_MAXIMA - ocupacao_atual
        })

    # ========== ENDPOINT: /temperatura ==========
    @app.route('/temperatura', methods=['GET', 'POST'])
    def temperatura():
        global ultimo_evento
        
        if request.method == 'POST':
            data = request.get_json()
            registar_temperatura(data['temperatura'], data['humidade'])
            
            ultimo_evento = {
                "tipo": "temperatura",
                "dados": {
                    "temperatura": data['temperatura'],
                    "humidade": data['humidade']
                },
                "timestamp": time.time()
            }
            
            return jsonify({"status": "ok"})
        
        row = ultima_temperatura()
        if row:
            return jsonify({
                "temperatura": float(row[0]),
                "humidade": float(row[1])
            })
        return jsonify({"erro": "Sem dados"}), 404

    # ========== ENDPOINT: /cartoes ==========
    @app.route('/cartoes', methods=['GET'])
    def listar_cartoes():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT chave_rfid, nome FROM cartoes")
        cartoes = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({
            "cartoes": [{"chave_rfid": c[0], "nome_utilizador": c[1]} for c in cartoes]
        })