from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging
from flask_socketio import SocketIO, emit
from flask_cors import CORS  # Importer CORS

app = Flask(__name__)
CORS(app)  # Activer CORS pour toutes les routes

socketio = SocketIO(app, cors_allowed_origins="*")

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
    sensorID = db.Column(db.String(50), nullable=False)  # Ajout du champ sensorID
    accelX = db.Column(db.Float, nullable=False)
    accelY = db.Column(db.Float, nullable=False)
    accelZ = db.Column(db.Float, nullable=False)
    shockDetected = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Shock {self.id}: Sensor={self.sensorID}, X={self.accelX}, Y={self.accelY}, Z={self.accelZ}, Detected={self.shockDetected}>'


modes = [
    {'label': 'Current Game', 'active': True},
    {'label': 'Games', 'active': False},
    {'label': 'Players', 'active': False}
]


@socketio.on('change_mode')
def handle_change_mode(data):
    global modes
    requested_mode_label = data['label']

    # Désactiver tous les modes, puis activer le mode demandé
    for mode in modes:
        mode['active'] = (mode['label'] == requested_mode_label)

    # Émettre la liste mise à jour des modes à tous les clients
    emit('modes_updated', modes, broadcast=True)
    print(f"Mode changed to {requested_mode_label}")


@app.route('/current_mode')
def get_current_mode():
    print("Asked for current mode")
    return jsonify(next((mode for mode in modes if mode['active']), None))


@app.route('/available_modes')
def get_available_modes():
    print("Asked for available modes")
    return jsonify(modes)


# Endpoint pour recevoir les données de choc
@app.route('/data', methods=['POST'])
def receive_data():
    if request.is_json:
        data = request.get_json()

        # Log the received data
        logger.info(f"Received data: {data}")

        # Création d'un nouvel enregistrement dans la base de données
        new_shock = ShockData(
            sensorID=data['sensorID'],  # Capture l'identifiant du capteur
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
            'sensorID': shock.sensorID,  # Inclure sensorID dans la réponse
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


# Endpoint pour récupérer les données de choc par capteur spécifique
@app.route('/shocks/<sensor_id>', methods=['GET'])
def get_shocks_by_sensor(sensor_id):
    shocks = ShockData.query.filter_by(sensorID=sensor_id).all()
    output = []
    for shock in shocks:
        shock_data = {
            'id': shock.id,
            'sensorID': shock.sensorID,
            'accelX': shock.accelX,
            'accelY': shock.accelY,
            'accelZ': shock.accelZ,
            'shockDetected': shock.shockDetected,
            'timestamp': shock.timestamp
        }
        output.append(shock_data)

    # Log the action of fetching data for a specific sensor
    logger.info(f"Fetched shocks data for sensor {sensor_id}")

    return jsonify(output)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Création des tables dans la base de données
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

