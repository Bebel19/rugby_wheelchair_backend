#Backend
from flask import Flask, request, jsonify, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS  # Importer CORS
import requests

#Database
from flask_sqlalchemy import SQLAlchemy
from dateutil.parser import parse
#Utils
from datetime import datetime
import logging



app = Flask(__name__)

CORS(app)  # Activer CORS pour toutes les routes

socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration de la base de données SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shocks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)  # <-- L'instance de SQLAlchemy est directement liée à l'application Flask

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Définition des modèles de base de données
class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100))
    established_year = db.Column(db.Integer)
    championships = db.relationship('Championship', backref='club', lazy=True)
    players = db.relationship('Player', backref='club', lazy=True)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    photo_url = db.Column(db.String(200))  # URL de la photo du joueur
    rating = db.Column(db.Float)  # Note entre 0.5 et 3.5
    position = db.Column(db.String(50))  # Position sur le terrain
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    player_championships = db.relationship('PlayerChampionshipStats', backref='player', lazy=True)

class Championship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    division = db.Column(db.String(10), nullable=False)  # Nationale I, II, III
    champion_club_id = db.Column(db.Integer, db.ForeignKey('club.id'))  # Club qui a remporté le championnat
    matches = db.relationship('Match', backref='championship', lazy=True)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    championship_id = db.Column(db.Integer, db.ForeignKey('championship.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    team_1_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    team_2_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    team_1_score = db.Column(db.Integer)
    team_2_score = db.Column(db.Integer)

    # Relationships
    team_1 = db.relationship('Club', foreign_keys=[team_1_id])
    team_2 = db.relationship('Club', foreign_keys=[team_2_id])




class PlayerMatchStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    heart_rate = db.Column(db.Float)
    temperature = db.Column(db.Float)
    average_speed = db.Column(db.Float)
    distance_covered = db.Column(db.Float)
    position_rating = db.Column(db.Float)  # Note de positionnement
    fatigue = db.Column(db.Boolean, default=False)

class PlayerChampionshipStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    championship_id = db.Column(db.Integer, db.ForeignKey('championship.id'), nullable=False)
    total_matches = db.Column(db.Integer, default=0)
    total_distance_covered = db.Column(db.Float, default=0.0)
    total_goals = db.Column(db.Integer, default=0)
    average_heart_rate = db.Column(db.Float)
    average_speed = db.Column(db.Float)
    average_position_rating = db.Column(db.Float)
    best_position_rating = db.Column(db.Float)
    fatigue_count = db.Column(db.Integer, default=0)

class Award(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    year = db.Column(db.Integer, nullable=False)
    recipient_club_id = db.Column(db.Integer, db.ForeignKey('club.id'))
    recipient_player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    championship_id = db.Column(db.Integer, db.ForeignKey('championship.id'), nullable=False)

class ShockData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensorID = db.Column(db.String(50), nullable=False)  # Ensure this matches your front-end or data input source
    accelX = db.Column(db.Float, nullable=False)
    accelY = db.Column(db.Float, nullable=False)
    accelZ = db.Column(db.Float, nullable=False)
    shockDetected = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


    def __repr__(self):
        return f'<Shock {self.id}: Sensor={self.sensorID}, X={self.accelX}, Y={self.accelY}, Z={self.accelZ}, Detected={self.shockDetected}>'

class TemperatureHumidityData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensorID = db.Column(db.String(50), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<TemperatureHumidityData {self.id}: Sensor={self.sensorID}, Temp={self.temperature}, Humidity={self.humidity}>'


modes = [
    {'label': 'Current Game', 'active': True},
    {'label': 'Games', 'active': False},
    {'label': 'Players', 'active': False},
    {'label': 'Sensor data', 'active': False},
    {'label': 'Select Table', 'active': False}
]

# Adresse IP du Raspberry Pi et URL du flux vidéo
PI_VIDEO_STREAM_URL = "http://192.168.17.45:5000/video_feed"


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


@app.route('/temperature_data', methods=['POST'])
def receive_temperature_data():
    if request.is_json:
        data = request.get_json()

        # Log the received data
        logger.info(f"Received temperature and humidity data: {data}")

        # Adapt to match the ESP32 data structure (A2302_Temperature, A2302_Humidity)
        new_data = TemperatureHumidityData(
            sensorID=data['sensorID'],
            temperature=data['A2302_Temperature'],  # Match with ESP32 key
            humidity=data['A2302_Humidity']  # Match with ESP32 key
        )
        db.session.add(new_data)
        db.session.commit()

        return jsonify({"message": "Temperature and humidity data received successfully"}), 200
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

@app.route('/sensors', methods=['GET'])
def get_sensors():
    # Query temperature and shock sensor IDs
    temperature_sensors = db.session.query(TemperatureHumidityData.sensorID).distinct().all()
    shock_sensors = db.session.query(ShockData.sensorID).distinct().all()

    # Log the raw data fetched from the database
    logger.info(f"Fetched temperature sensors: {temperature_sensors}")
    logger.info(f"Fetched shock sensors: {shock_sensors}")

    # Flatten the sensor list and remove duplicates
    all_sensors = list(set([sensor[0] for sensor in temperature_sensors + shock_sensors]))

    # Log the final list of unique sensors
    logger.info(f"All unique sensors: {all_sensors}")

    return jsonify(all_sensors)



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


@app.route('/sensor_data/<sensor_id>', methods=['GET'])
def get_sensor_data(sensor_id):
    temperature_data = TemperatureHumidityData.query.filter_by(sensorID=sensor_id).all()
    shock_data = ShockData.query.filter_by(sensorID=sensor_id).all()

    # Combine the data into a structured format where each entry has its associated timestamp
    sensor_data = []

    # Add temperature and humidity data
    for data in temperature_data:
        sensor_data.append({
            'timestamp': data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': data.temperature,
            'humidity': data.humidity,
            'shock': None  # No shock data for this timestamp
        })

    # Add shock data (filling in shock data where applicable)
    for shock in shock_data:
        sensor_data.append({
            'timestamp': shock.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': None,  # No temperature data for this timestamp
            'humidity': None,     # No humidity data for this timestamp
            'shock': 1 if shock.shockDetected else 0
        })

    # Sort the data by timestamp to maintain chronological order
    sensor_data = sorted(sensor_data, key=lambda x: x['timestamp'])
    logger.info(f"Fetched shocks data from sensors dba {sensor_data}")
    return jsonify(sensor_data)

#Endpoint for video feed
@app.route('/video_feed')
def video_feed():
    def generate():
        with requests.get(PI_VIDEO_STREAM_URL, stream=True) as r:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


#DB modifications :

@app.route('/add_club', methods=['POST'])
def add_club():
    data = request.json
    # Log the received data
    logger.info(f"Received club data: {data}")
    new_club = Club(name=data['name'], city=data.get('city'), established_year=data.get('established_year'))
    db.session.add(new_club)
    db.session.commit()
    return jsonify({"message": "Club added successfully!", "club_id": new_club.id}), 201


@app.route('/add_player', methods=['POST'])
def add_player():
    data = request.json
    # Log the received data
    logger.info(f"Received player data: {data}")

    new_player = Player(
        first_name=data['first_name'],
        last_name=data['last_name'],
        photo_url=data.get('photo_url', None),
        rating=data.get('rating', None),
        position=data.get('position', None),
        club_id=data['club_id']
    )
    db.session.add(new_player)
    db.session.commit()
    return jsonify({"message": "Player added successfully!"}), 201


@app.route('/add_championship', methods=['POST'])
def add_championship():
    data = request.json
    # Log the received data
    logger.info(f"Received championship data: {data}")

    new_championship = Championship(
        year=data['year'],
        division=data['division'],
        champion_club_id=data.get('champion_club_id', None)
    )
    db.session.add(new_championship)
    db.session.commit()
    return jsonify({"message": "Championship added successfully!"}), 201


@app.route('/add_match', methods=['POST'])
def add_match():
    data = request.json
    logger.info(f"Received match data: {data}")

    try:
        # Using dateutil to parse date flexibly
        match_date = parse(data['date'])
    except ValueError as e:
        logger.error(f"Date parsing error: {e}")
        return jsonify({"error": "Invalid date format"}), 400

    new_match = Match(
        championship_id=data.get('championship_id'),
        date=match_date,
        team_1_id=data['team_1_id'],
        team_2_id=data['team_2_id'],
        team_1_score=data.get('team_1_score', 0),  # Default score to 0 if not provided
        team_2_score=data.get('team_2_score', 0)
    )

    db.session.add(new_match)
    try:
        db.session.commit()
        return jsonify({"message": "Match added successfully!"}), 201
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.session.rollback()
        return jsonify({"error": "Database error"}), 500


@app.route('/add_player_match_stats', methods=['POST'])
def add_player_match_stats():
    data = request.json
    # Log the received data
    logger.info(f"Received player match stats data: {data}")

    new_stats = PlayerMatchStats(
        match_id=data['match_id'],
        player_id=data['player_id'],
        heart_rate=data.get('heart_rate', None),
        temperature=data.get('temperature', None),
        average_speed=data.get('average_speed', None),
        distance_covered=data.get('distance_covered', None),
        position_rating=data.get('position_rating', None),
        fatigue=data.get('fatigue', False)
    )
    db.session.add(new_stats)
    db.session.commit()
    return jsonify({"message": "Player match stats added successfully!"}), 201


@app.route('/clubs', methods=['GET'])
def get_clubs():
    clubs = Club.query.all()
    output = [{'id': club.id, 'name': club.name, 'city': club.city, 'established_year': club.established_year} for club in clubs]
    return jsonify(output)

@app.route('/clubs/<int:club_id>/players', methods=['GET'])
def get_players(club_id):
    logger.info(f"Fetching players for club_id: {club_id}")

    players = Player.query.filter_by(club_id=club_id).all()
    club_name = Club.query.filter_by(id=club_id).first().name
    output = []
    for player in players:
        player_data = {
            'id': player.id,
            'first_name': player.first_name,
            'last_name': player.last_name,
            'rating': player.rating,
            'photo_url': player.photo_url,
            'position': player.position,
            'club_name': club_name  # Add the club name to the response
        }
        output.append(player_data)

    # Log the entire response data, including the photo URLs
    logger.info(f"Response data for club_id {club_id}: {output}")

    logger.info(f"Found {len(players)} players for club_id: {club_id}")

    return jsonify(output)





@app.route('/championships', methods=['GET'])
def get_championships():
    championships = Championship.query.all()
    output = [{'id': champ.id, 'year': champ.year, 'division': champ.division} for champ in championships]
    return jsonify(output)



@app.route('/championships/<int:championship_id>/matches', methods=['GET'])
def get_matches(championship_id):
    logger.info(f"Fetching matches for championship_id: {championship_id}")

    matches = Match.query.filter_by(championship_id=championship_id).all()
    output = []

    for match in matches:
        match_data = {
            'id': match.id,
            'date': match.date.strftime("%Y-%m-%d %H:%M:%S"),
            'team_1_id': match.team_1_id,
            'team_1_name': match.team_1.name,  # Assuming 'name' is a column in the Club model
            'team_2_id': match.team_2_id,
            'team_2_name': match.team_2.name,  # Assuming 'name' is a column in the Club model
            'team_1_score': match.team_1_score,
            'team_2_score': match.team_2_score
        }
        output.append(match_data)

    logger.info(f"Found {len(matches)} matches for championship_id: {championship_id}")
    logger.info(f"Match data: {output}")

    return jsonify(output)




if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Création des tables dans la base de données
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

