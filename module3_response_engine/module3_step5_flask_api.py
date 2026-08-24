"""
GRID GUARD — Module 3: Graduated Response Engine
STEP 5: Flask REST API

Exposes ResponseDecisions (actions taken by Module 3) via REST API
so the Dashboard can query and display them.

Runs on port 5002 and provides endpoints:
  GET /api/actions/recent        - Latest actions
  GET /api/actions/meter/<id>    - Actions for specific meter
  GET /api/actions/counts        - Summary counts by action type
  GET /api/actions/by-tier       - Count by tier

This is what the Dashboard queries to show action history.

Requires: pip install flask flask-cors
"""

import os
import sys
from datetime import datetime, timedelta

from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.append(os.path.dirname(__file__))
from module3_step4_database_logger import DatabaseLogger

# ── Flask App Setup ────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard to access API

# ── Database Logger Instance ────────────────────────────────────────
db_logger = None


# ── REST API Endpoints ──────────────────────────────────────────────

@app.route('/api/actions/recent', methods=['GET'])
def get_recent_actions():
    """
    GET /api/actions/recent?limit=50
    
    Returns the most recent actions taken by Module 3.
    
    Query Parameters:
        limit: Number of actions to return (default: 50, max: 500)
    
    Response:
        {
            "actions": [
                {
                    "log_id": 1,
                    "actor": "Module3",
                    "action_type": "ALERT",
                    "meter_id": "meter_002",
                    "payload": {...},
                    "created_at": "2026-08-19T15:30:49Z"
                },
                ...
            ],
            "count": 3
        }
    """
    limit = request.args.get('limit', 50, type=int)
    limit = min(limit, 500)  # Cap at 500
    
    if not db_logger.connected:
        return jsonify({"error": "Database not connected"}), 503
    
    actions = db_logger.get_recent_actions(limit=limit)
    
    return jsonify({
        "actions": actions,
        "count": len(actions),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/actions/meter/<meter_id>', methods=['GET'])
def get_meter_actions(meter_id):
    """
    GET /api/actions/meter/meter_002?limit=20
    
    Returns all actions for a specific meter.
    
    Path Parameters:
        meter_id: The meter identifier
    
    Query Parameters:
        limit: Number of actions to return (default: 20, max: 100)
    
    Response:
        {
            "meter_id": "meter_002",
            "actions": [
                {
                    "log_id": 1,
                    "action_type": "ALERT",
                    "payload": {...},
                    "created_at": "2026-08-19T15:30:49Z"
                },
                ...
            ],
            "count": 3
        }
    """
    limit = request.args.get('limit', 20, type=int)
    limit = min(limit, 100)  # Cap at 100
    
    if not db_logger.connected:
        return jsonify({"error": "Database not connected"}), 503
    
    actions = db_logger.get_actions_by_meter(meter_id, limit=limit)
    
    return jsonify({
        "meter_id": meter_id,
        "actions": actions,
        "count": len(actions),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/actions/counts', methods=['GET'])
def get_action_counts():
    """
    GET /api/actions/counts
    
    Returns count of each action type (for dashboard summary).
    
    Response:
        {
            "counts": {
                "LOG": 1000,
                "ALERT": 50,
                "RATE_LIMIT": 10,
                "FULL_ISOLATION": 2
            },
            "total": 1062
        }
    """
    if not db_logger.connected:
        return jsonify({"error": "Database not connected"}), 503
    
    counts = db_logger.get_action_counts()
    total = sum(counts.values())
    
    return jsonify({
        "counts": counts,
        "total": total,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/actions/by-tier', methods=['GET'])
def get_actions_by_tier():
    """
    GET /api/actions/by-tier
    
    Groups actions by response tier (Tier 1-4).
    
    Response:
        {
            "tier_1": {"count": 1000, "action": "LOG"},
            "tier_2": {"count": 50, "action": "ALERT"},
            "tier_3": {"count": 10, "action": "RATE_LIMIT"},
            "tier_4": {"count": 2, "action": "FULL_ISOLATION"}
        }
    """
    if not db_logger.connected:
        return jsonify({"error": "Database not connected"}), 503
    
    counts = db_logger.get_action_counts()
    
    tier_mapping = {
        "LOG": ("tier_1", "NORMAL"),
        "ALERT": ("tier_2", "ALERT"),
        "RATE_LIMIT": ("tier_3", "RATE_LIMIT"),
        "FULL_ISOLATION": ("tier_4", "FULL_ISOLATION")
    }
    
    result = {}
    for action_type, (tier_key, tier_name) in tier_mapping.items():
        result[tier_key] = {
            "count": counts.get(action_type, 0),
            "action": action_type,
            "tier_name": tier_name
        }
    
    return jsonify(result)


@app.route('/api/actions/timeline', methods=['GET'])
def get_actions_timeline():
    """
    GET /api/actions/timeline?hours=24
    
    Returns actions grouped by time (for timeline visualization).
    
    Query Parameters:
        hours: Look back this many hours (default: 24)
    
    Response:
        {
            "timeline": [
                {"timestamp": "2026-08-19T15:00:00Z", "count": 5},
                {"timestamp": "2026-08-19T16:00:00Z", "count": 12},
                ...
            ]
        }
    """
    hours = request.args.get('hours', 24, type=int)
    
    if not db_logger.connected:
        return jsonify({"error": "Database not connected"}), 503
    
    # For now, return recent actions as timeline
    # In production, group by time window
    actions = db_logger.get_recent_actions(limit=100)
    
    return jsonify({
        "timeline": actions,
        "hours_back": hours,
        "count": len(actions)
    })


@app.route('/api/health', methods=['GET'])
def health():
    """
    GET /api/health
    
    Check if Module 3 API is running.
    """
    return jsonify({
        "status": "healthy",
        "service": "Module3_ResponseEngine",
        "database_connected": db_logger.connected,
        "timestamp": datetime.now().isoformat()
    })


# ── Error Handlers ────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ── Initialization ────────────────────────────────────────────────

def init_logger():
    """Initialize database logger on startup"""
    global db_logger
    db_logger = DatabaseLogger()
    
    if not db_logger.connect():
        print("❌ Warning: Could not connect to database")
        print("   API will return 503 until database is available")
    else:
        print("✅ Database connected")


# ── Main Entry Point ────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 60)
    print("Module 3: Graduated Response Engine - STEP 5")
    print("Flask REST API")
    print("=" * 60)
    print()
    
    # Initialize logger
    init_logger()
    
    print()
    print("API Endpoints:")
    print("  GET  /api/actions/recent           - Latest actions")
    print("  GET  /api/actions/meter/<id>       - Actions for meter")
    print("  GET  /api/actions/counts           - Summary counts")
    print("  GET  /api/actions/by-tier          - Count by tier")
    print("  GET  /api/actions/timeline         - Timeline view")
    print("  GET  /api/health                   - Health check")
    print()
    
    # Start Flask app
    print("🚀 Starting Flask API on http://0.0.0.0:5002")
    app.run(host='0.0.0.0', port=5002, debug=False)

# ═════════════════════════════════════════════════════════════════════════
# FE-5: STATE MANAGEMENT ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════

from redis_state_manager import RedisStateManager
from prometheus_client import Counter, Gauge, generate_latest, REGISTRY

state_manager = RedisStateManager()

# Prometheus Metrics
alerts_by_tier = Counter('gridguard_alerts_generated_total', 'Total alerts', ['tier'])
isolated_gauge = Gauge('gridguard_isolated_meters_current', 'Currently isolated')
avg_risk_gauge = Gauge('gridguard_average_risk_score', 'Average risk')
critical_gauge = Gauge('gridguard_critical_meters', 'Critical meters')

@app.route('/api/module3/meter-state/<meter_id>', methods=['GET'])
def get_meter_state(meter_id):
    """Get current state of a specific meter"""
    try:
        state = state_manager.get_meter_state(meter_id)
        if state:
            return jsonify({'status': 'success', 'meter_id': meter_id, 'state': state})
        return jsonify({'status': 'not_found', 'message': f'No state for {meter_id}'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/module3/all-meter-states', methods=['GET'])
def get_all_meter_states():
    """Get all meters' current states"""
    try:
        states = state_manager.get_all_meter_states()
        return jsonify({'status': 'success', 'total': len(states), 'states': states})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/module3/system-metrics', methods=['GET'])
def get_system_metrics():
    """Get system-wide metrics"""
    try:
        metrics = state_manager.get_system_metrics()
        return jsonify({'status': 'success', 'metrics': metrics})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/module3/isolated-meters', methods=['GET'])
def get_isolated_meters():
    """Get currently isolated meters"""
    try:
        isolated = state_manager.get_isolated_meters()
        states = {mid: state_manager.get_meter_state(mid) for mid in isolated}
        return jsonify({'status': 'success', 'count': len(isolated), 'isolated_meters': states})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/metrics', methods=['GET'])
def prometheus_metrics():
    """Prometheus metrics endpoint"""
    metrics = state_manager.get_system_metrics()
    isolated_gauge.set(metrics.get('isolation_count', 0))
    avg_risk_gauge.set(metrics.get('average_risk_score', 0))
    critical_gauge.set(metrics.get('critical_count', 0))
    return generate_latest(REGISTRY), 200, {'Content-Type': 'text/plain'}
