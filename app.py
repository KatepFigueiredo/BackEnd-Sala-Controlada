from flask import Flask
from flask_cors import CORS
from routes import init_all_routes

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

init_all_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)