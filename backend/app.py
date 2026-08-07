

from quart import Quart, jsonify, request
from quart_cors import cors
from db import Rimiru
from EmailClassifier import Duro
from constants import Constants
app = Quart(__name__)
app = cors(app, allow_origin="http://localhost:5173",allow_credentials=True,
)  # Allow CORS for React frontend
app.config['SECRET_KEY'] =  Constants.SECRET_KEY  # Set the secret key for session management

@app.route('/')
async def index():
    return jsonify({"message": "Welcome to the Scales API"})

@app.route('/emails', methods=['POST'])
async def classify_emails():
    data = await request.get_json()
    classifier = Duro()
    classification = await classifier.classify(data.get("text", ""))
    data["classification"] = classification
    return jsonify(classification)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
