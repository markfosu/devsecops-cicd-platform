from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "healthy",
            "service": "devsecops-cicd-platform",
        }
    ), 200


@app.route("/api/v1/status", methods=["GET"])
def status():
    return jsonify(
        {
            "status": "operational",
            "version": "1.0.0",
        }
    ), 200


@app.route("/api/v1/info", methods=["GET"])
def info():
    return jsonify(
        {
            "application": "DevSecOps CI/CD Platform",
            "environment": "development",
            "version": "1.0.0",
        }
    ), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
