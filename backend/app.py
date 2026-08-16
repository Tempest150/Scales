

from quart import Quart, jsonify, request
from quart_cors import cors

from constants import Constants
from routes.auth import auth_bp
from routes.emails import emails_bp
app = Quart(__name__)
app = cors(app, allow_origin="http://localhost:5173",allow_credentials=True,)  # Allow CORS for React frontend
app.config['SECRET_KEY'] =  Constants.SECRET_KEY  # Set the secret key for session management
app.register_blueprint(auth_bp)  # Register the auth blueprint
app.register_blueprint(emails_bp)  # Register the emails blueprint
@app.route('/')
async def index():
    return jsonify({"message": "Welcome to the Scales API"})

@app.route('/emails', methods=['POST'])
async def classify_emails():
    data = await request.get_json()
    
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5010)
    
    
