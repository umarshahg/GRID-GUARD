from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit
import redis
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app, cors_allowed_origins="*")

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='gridguard',
        user='gridguard',
        password='gridguard',
        port=5432,
        cursor_factory=RealDictCursor
    )

@app.route('/')
def index():
    return render_template('ids_ips.html')

@app.route('/api/actions/parsed', methods=['GET'])
def api_actions_parsed():
    """Tier 2 ALERT flows (40-80%) with email/webhook status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT target_entity, payload, email_sent, webhook_sent, created_at 
            FROM audit_log 
            WHERE action_type = 'ALERT' 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        actions = []
        for r in rows:
            risk_score = 0
            if r['payload']:
                try:
                    import ast
                    p = ast.literal_eval(r['payload']) if isinstance(r['payload'], str) else r['payload']
                    risk_score = float(p.get('risk_score', 0))
                except:
                    pass
            
            if 40 <= risk_score <= 80:
                email_status = 'Sent' if r['email_sent'] else 'Failed'
                webhook_status = 'Sent' if r['webhook_sent'] else 'Failed'
                
                actions.append({
                    'meter_id': r['target_entity'],
                    'risk_score': round(risk_score, 1),
                    'email_sent': email_status,
                    'webhook_sent': webhook_status,
                })
        
        return jsonify({'actions': actions[:5]})
    except Exception as e:
        return jsonify({'error': str(e), 'actions': []})

@app.route('/api/rate-limits', methods=['GET'])
def api_rate_limits():
    """Tier 3 RATE_LIMIT flows (80-95%) with real IPs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT target_entity, payload, rate_limit_ip 
            FROM audit_log 
            WHERE action_type = 'RATE_LIMIT' 
            AND rate_limit_ip IS NOT NULL 
            AND rate_limit_ip != 'None'
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        actions = []
        for r in rows:
            risk_score = 0
            if r['payload']:
                try:
                    import ast
                    p = ast.literal_eval(r['payload']) if isinstance(r['payload'], str) else r['payload']
                    risk_score = float(p.get('risk_score', 0))
                except:
                    pass
            
            if 80 <= risk_score <= 95:
                actions.append({
                    'meter_id': r['target_entity'],
                    'risk_score': round(risk_score, 1),
                    'rate_limit_ip': r['rate_limit_ip'],
                })
        
        return jsonify({'actions': actions})
    except Exception as e:
        return jsonify({'error': str(e), 'actions': []})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
