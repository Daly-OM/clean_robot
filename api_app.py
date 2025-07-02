from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_httpauth import HTTPTokenAuth

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/daly/projects/cleaner-backend/instance/robot_data.db'
db = SQLAlchemy(app)

# =====================
# Models (used by Alembic)
# =====================

class Telemetry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    acc_x = db.Column(db.Float)
    acc_y = db.Column(db.Float)
    acc_z = db.Column(db.Float)
    roll = db.Column(db.Float)
    pitch = db.Column(db.Float)
    yaw = db.Column(db.Float)
    battery = db.Column(db.Integer)
    state = db.Column(db.String)
    # temperature = db.Column(db.Float)  # Example: future field

class Command(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    command = db.Column(db.String)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Acknowledgment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    command = db.Column(db.String)
    status = db.Column(db.String)
    timestamp = db.Column(db.String)

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=False)
    level = db.Column(db.String, nullable=False)  # 'info', 'warning', 'error'
    robot_state = db.Column(db.String)  # Optional: state when log was created
    battery_level = db.Column(db.Integer)  # Optional: battery when log was created

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(32), default='user')  # 'user', 'admin'
    token = db.Column(db.String(128), index=True)
    token_expiration = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Authentication setup
auth = HTTPTokenAuth(scheme='Bearer')

# =====================
# REST API
# =====================

from datetime import datetime, timedelta
import secrets

@app.route('/api/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 415
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Generate new token (invalidates any existing token)
    token = secrets.token_urlsafe(32)
    expires_in = 3600  # 1 hour
    user.token = token
    user.token_expiration = datetime.utcnow() + timedelta(seconds=expires_in)
    db.session.commit()

    return jsonify({
        'token': token,
        'expires_in': expires_in,
        'role': user.role
    }), 200

@auth.verify_token
def verify_token(token):
    if not token:
        return None
    user = User.query.filter_by(token=token).first()
    if user is None or user.token_expiration < datetime.utcnow():
        return None
    return user

@app.route('/api/protected', methods=['GET'])
#@auth.login_required
def protected_route():
    current_user = auth.current_user()
    return jsonify({
        'message': f'Hello {current_user.username}',
        'role': current_user.role
    }), 200

@app.route('/api/users', methods=['POST'])
#@auth.login_required
def create_user():
    
    #if auth.current_user().role != 'admin':
    #    return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    user = User(username=data['username'], role=data.get('role', 'user'))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User created', 'id': user.id}), 201

# 1. POST /api/telemetry
@app.route('/api/telemetry', methods=['POST'])
def upload_telemetry():
    data = request.get_json()
    t = Telemetry(
        timestamp=data['timestamp'],
        lat=data['position']['lat'],
        lon=data['position']['lon'],
        acc_x=data['acceleration']['x'],
        acc_y=data['acceleration']['y'],
        acc_z=data['acceleration']['z'],
        roll=data['angle']['roll'],
        pitch=data['angle']['pitch'],
        yaw=data['angle']['yaw'],
        battery=data['battery'],
        state=data['state']
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({"message": "Telemetry saved"}), 200

# 2. GET /api/command
@app.route('/api/command', methods=['GET'])
def get_command():
    cmd = Command.query.order_by(Command.id.desc()).first()
    if cmd:
        return jsonify({"command": cmd.command})
    return jsonify({"command": "inactive"})  # fallback

# 3. POST /api/command
@app.route('/api/command', methods=['POST'])
def set_command():
    data = request.get_json()
    cmd = Command(command=data['command'])
    db.session.add(cmd)
    db.session.commit()
    return jsonify({"message": "Command updated", "command": cmd.command})

# 4. POST /api/command/ack
@app.route('/api/command/ack', methods=['POST'])
def acknowledge_command():
    data = request.get_json()
    ack = Acknowledgment(
        command=data['command'],
        status=data['status'],
        timestamp=data['timestamp']
    )
    db.session.add(ack)
    db.session.commit()
    return jsonify({"message": "Acknowledgment saved"})

@app.route('/api/telemetry/latest', methods=['GET'])
def get_latest_telemetry():
    latest = Telemetry.query.order_by(Telemetry.id.desc()).first()
    
    if not latest:
        return jsonify({"error": "No telemetry data available"}), 404
    
    return jsonify({
        "timestamp": latest.timestamp,
        "battery": latest.battery,
        "state": latest.state,
        "position": {
            "lat": latest.lat,
            "lon": latest.lon
        },
        "angle": {
            "roll": latest.roll,
            "pitch": latest.pitch,
            "yaw": latest.yaw
        },
        "acceleration": {
            "x": latest.acc_x,
            "y": latest.acc_y,
            "z": latest.acc_z
        }
    }), 200

@app.route('/api/telemetry/history', methods=['GET'])
def get_telemetry_history():
    try:
        # Get query parameters with defaults
        limit = min(int(request.args.get('limit', 10)), 100)  # Max 100 records
        fields = request.args.get('fields', '').split(',')
        
        # Query database
        telemetry_data = Telemetry.query.order_by(
            Telemetry.id.desc()
        ).limit(limit).all()
        
        if not telemetry_data:
            return jsonify([]), 200
        
        # Available fields mapping
        field_mapping = {
            'timestamp': lambda t: t.timestamp,
            'battery': lambda t: t.battery,
            'state': lambda t: t.state,
            'position': lambda t: {'lat': t.lat, 'lon': t.lon},
            'angle': lambda t: {'roll': t.roll, 'pitch': t.pitch, 'yaw': t.yaw},
            'acceleration': lambda t: {'x': t.acc_x, 'y': t.acc_y, 'z': t.acc_z}
        }
        
        # If no specific fields requested, return all standard fields
        if not fields or fields == ['']:
            standard_fields = ['timestamp', 'battery', 'state']
            result = [{
                'timestamp': t.timestamp,
                'battery': t.battery,
                'state': t.state
            } for t in telemetry_data]
        else:
            # Filter by requested fields
            result = []
            for t in telemetry_data:
                entry = {}
                for field in fields:
                    if field in field_mapping:
                        entry[field] = field_mapping[field](t)
                if entry:  # Only add if we have at least one valid field
                    result.append(entry)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/log', methods=['POST'])
def add_log_entry():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'timestamp' not in data or 'message' not in data or 'level' not in data:
            return jsonify({'error': 'Missing required fields (timestamp, message, level)'}), 400
        
        # Create new log entry
        log_entry = Log(
            timestamp=data['timestamp'],
            message=data['message'],
            level=data['level'],
            robot_state=data.get('robot_state'),
            battery_level=data.get('battery_level')
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({'message': 'Log entry added', 'id': log_entry.id}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_log_entries():
    try:
        level_filter = request.args.get('level')
        limit = min(int(request.args.get('limit', 50)), 1000)
        since = request.args.get('since')
        
        query = Log.query.order_by(Log.id.desc())
        
        if level_filter:
            query = query.filter(Log.level == level_filter.lower())
        if since:
            query = query.filter(Log.timestamp >= since)
            
        logs = query.limit(limit).all()
        
        return jsonify([{
            'timestamp': log.timestamp,
            'message': log.message,
            'level': log.level,
            'robot_state': log.robot_state,
            'battery_level': log.battery_level
        } for log in logs]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def serialize_model(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


# Optional admin route
@app.route('/admin/data', methods=['GET'])
def get_all_data():
    telemetry = [serialize_model(t) for t in Telemetry.query.all()]
    commands = [serialize_model(c) for c in Command.query.all()]
    acks = [serialize_model(a) for a in Acknowledgment.query.all()]
    return jsonify({
        "telemetry": telemetry,
        "commands": commands,
        "acknowledgments": acks
    })

if __name__ == '__main__':
    app.run(debug=True)
