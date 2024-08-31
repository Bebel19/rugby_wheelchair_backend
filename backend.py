from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging

app = Flask(__name__)

# Configuration de la base de données SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shocks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Définition du modèle de la base de données
class ShockData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    accelX = db.Column(db.Float, nullable=False)
    accelY = db.Column(db.Float, nullable=False)
    accelZ = db.Column(db.Float, nullable=False)
    shockDetected = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Shock {self.id}: X={self.accelX}, Y={self.accelY}, Z={self.accelZ}, Detected={self.shockDetected}>'


# Endpoint pour recevoir les données de choc
@app.route('/data', methods=['POST'])
def receive_data():
    if request.is_json:
        data = request.get_json()

        # Log the received data
        logger.info(f"Received data: {data}")

        # Création d'un nouvel enregistrement dans la base de données
        new_shock = ShockData(
            accelX=data['accelX'],
            accelY=data['accelY'],
            accelZ=data['accelZ'],
            shockDetected=data['shockDetected']
        )
        db.session.add(new_shock)
        db.session.commit()

        return jsonify({"message": "Data received successfully"}), 200
    else:
        logger.warning("Request must be JSON")
        return jsonify({"message": "Request must be JSON"}), 400


# Endpoint pour récupérer les données de choc
@app.route('/shocks', methods=['GET'])
def get_shocks():
    shocks = ShockData.query.all()
    output = []
    for shock in shocks:
        shock_data = {
            'id': shock.id,
            'accelX': shock.accelX,
            'accelY': shock.accelY,
            'accelZ': shock.accelZ,
            'shockDetected': shock.shockDetected,
            'timestamp': shock.timestamp
        }
        output.append(shock_data)

    # Log the action of fetching data
    logger.info("Fetched all shocks data")

    return jsonify(output)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Création des tables dans la base de données
    app.run(debug=True, host='0.0.0.0', port=5000)

