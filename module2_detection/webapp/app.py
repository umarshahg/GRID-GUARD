# webapp/app.py
# ─────────────────────────────────────────────────────────────
# Flask backend — serves HTML pages and REST API endpoints
# that the frontend JavaScript calls to get live model data.
# ─────────────────────────────────────────────────────────────

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import (
    Flask, render_template, jsonify,
    request, session, redirect, url_for
)
from functools import wraps
from predictor import predictor

# ── App Setup ──────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'gridguard-secret-key-2024'

# ── Hardcoded credentials (no DB needed for FYP demo) ─────────
USERS = {
    "admin@gridguard.com": {
        "password": "gridguard123",
        "name":     "System Administrator",
        "role":     "Administrator"
    },
    "operator@gridguard.com": {
        "password": "operator123",
        "name":     "Security Operator",
        "role":     "Operator"
    },
    "analyst@gridguard.com": {
        "password": "analyst123",
        "name":     "Security Analyst",
        "role":     "Analyst"
    }
}

# ── Auth Decorator ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════
#  PAGE ROUTES — serve HTML templates
# ══════════════════════════════════════════════════════════════

@app.route('/', methods=['GET'])
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if email in USERS and USERS[email]['password'] == password:
            session['user'] = {
                'email': email,
                'name':  USERS[email]['name'],
                'role':  USERS[email]['role'],
            }
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid email or password.'

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template(
        'dashboard.html',
        user=session['user']
    )


@app.route('/traffic')
@login_required
def traffic():
    return render_template(
        'traffic.html',
        user=session['user']
    )


@app.route('/botnet')
@login_required
def botnet():
    return render_template(
        'botnet.html',
        user=session['user']
    )


# ══════════════════════════════════════════════════════════════
#  API ROUTES — called by JavaScript via fetch()
# ══════════════════════════════════════════════════════════════

@app.route('/api/status')
@login_required
def api_status():
    """
    Returns system status — are models loaded and ready?
    Called by dashboard on page load.
    """
    return jsonify({
        "status":        "online" if predictor.loaded else "offline",
        "models_loaded": predictor.loaded,
        "feature_count": len(predictor.features) if predictor.features else 0,
        "test_rows":     len(predictor.X_test) if predictor.X_test is not None else 0,
    })


@app.route('/api/summary')
@login_required
def api_summary():
    """
    Returns full evaluation metrics from test set.
    Used by Dashboard and Botnet Detection pages.
    Accuracy, Detection Rate, FPR, F1, AUC, confusion matrix,
    tier distribution, feature importance, risk histogram.
    """
    try:
        data = predictor.get_summary()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/traffic')
@login_required
def api_traffic():
    """
    Returns traffic monitoring statistics.
    Used by Traffic Monitor page.
    Protocol distribution, flow counts, risk means.
    """
    try:
        data = predictor.get_traffic_stats()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/flows')
@login_required
def api_flows():
    """
    Returns scored sample of test flows for table display.
    Query param: n = number of flows (default 50, max 200)
    Used by Botnet Detection page live flow table.
    """
    try:
        n    = min(int(request.args.get('n', 50)), 200)
        data = predictor.predict_sample(n=n)
        return jsonify({"flows": data, "count": len(data)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scan', methods=['POST'])
@login_required
def api_scan():
    """
    Simulates scanning a single smart meter.
    POST body: { "meter_id": "SM-1234" } (optional)
    Returns risk score, tier, action for that meter.
    Used by Dashboard scan button.
    """
    try:
        body     = request.get_json(silent=True) or {}
        meter_id = body.get('meter_id', None)
        data     = predictor.scan_meter(meter_id=meter_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/timeline')
@login_required
def api_timeline():
    """
    Returns anomaly score timeline for chart rendering.
    Used by Botnet Detection anomaly chart.
    """
    try:
        summary  = predictor.get_summary()
        return jsonify({
            "timeline": summary.get("timeline", []),
            "count":    len(summary.get("timeline", []))
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/features')
@login_required
def api_features():
    """
    Returns feature importance ranking from Random Forest.
    Used by Botnet Detection top features bar chart.
    """
    try:
        summary = predictor.get_summary()
        return jsonify(summary.get("feature_importance", {}))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/histogram')
@login_required
def api_histogram():
    """
    Returns risk score distribution histogram data.
    Used by Dashboard risk distribution chart.
    """
    try:
        summary = predictor.get_summary()
        return jsonify(summary.get("histogram", {}))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/user')
@login_required
def api_user():
    """
    Returns current logged in user info.
    """
    return jsonify(session.get('user', {}))


# ══════════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("="*55)
    print("  GRID GUARD — Flask Web Application")
    print("="*55)
    print(f"  Models loaded : {predictor.loaded}")
    print(f"  Test rows     : {len(predictor.X_test) if predictor.X_test is not None else 0:,}")
    print()
    print("  Open in browser: http://127.0.0.1:5000")
    print("="*55)
    print()
    print("  Login credentials:")
    print("  admin@gridguard.com    / gridguard123")
    print("  operator@gridguard.com / operator123")
    print("  analyst@gridguard.com  / analyst123")
    print("="*55)
    app.run(debug=True, host='0.0.0.0', port=5000)
