from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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

# =====================
# REST API
# =====================

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
