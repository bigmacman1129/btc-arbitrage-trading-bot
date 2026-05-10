import os

from bitcoin_arbitrage.app import app


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG"), use_reloader=False)

