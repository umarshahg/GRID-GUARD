from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook-receiver', methods=['POST'])
def receive():
    data = request.get_json()
    print(f"[Receiver] Got webhook: {data}")
    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    app.run(port=9999)
