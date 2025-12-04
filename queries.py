from db import get_db_connection

def verificar_cartao(chave_rfid):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT nome FROM cartoes WHERE chave_rfid = %s", (chave_rfid,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        cur.close()
        conn.close()

def obter_ocupacao_atual():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT total_pessoas FROM ocupacao ORDER BY data_hora DESC LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else 0
    finally:
        cur.close()
        conn.close()

def atualizar_ocupacao(nova_ocupacao):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO ocupacao (total_pessoas) VALUES (%s)", (nova_ocupacao,))
        conn.commit()
    finally:
        cur.close()
        conn.close()

def registar_temperatura(temperatura, humidade):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO leituras (temperatura, humidade) VALUES (%s, %s)", 
                    (temperatura, humidade))
        conn.commit()
    finally:
        cur.close()
        conn.close()

def ultima_temperatura():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT temperatura, humidade FROM leituras ORDER BY data_hora DESC LIMIT 1")
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()
