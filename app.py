import select
from flask import Flask, request,jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime
from flask_marshmallow import Marshmallow
from flask_cors import CORS
import os
import requests
import uuid
from flask_migrate import Migrate
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

ALLOWED_IP = "127.0.0.1"  
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')

# Set SQLAlchemy database URI
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)
ma = Marshmallow(app)
migrate = Migrate(app, db)
class Users(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    nom =db.Column(db.String(20))
    prenom = db.Column(db.String(20))
    code_apogee = db.Column(db.String(20))
    CNE=db.Column(db.String(15))
    CIN=db.Column(db.String(15))

    def __init__(self,fname,lname,code_app,cne,cin):
        self.nom=fname
        self.prenom=lname
        self.code_apogee=code_app
        self.CNE=cne
        self.CIN=cin
        self.id_carte = None


class User_uid(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    id_user =db.Column(db.Integer)
    id_carte = db.Column(db.String(15))

    def __init__(self,id_u,id_c):
        self.id_user=id_u
        self.id_carte=id_c

class Presence(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    id_user =db.Column(db.Integer)
    date = db.Column(db.Date)

    def __init__(self,id_u):
        self.id_user=id_u
        self.date=datetime.date.today()

class Guest(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    nom =db.Column(db.String(20))
    prenom = db.Column(db.String(20))
    date = db.Column(db.Date)

    def __init__(self,nom1,prenom1):
        self.nom=nom1
        self.prenom=prenom1
        self.date=datetime.date.today()
    

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id','nom','prenom','code_apogee','CNE','CIN','id_carte')

class User_uidSchema(ma.Schema):
    class Meta:
        fields = ('id','id_user','id_carte')


user_schema=UserSchema()
users_schema=UserSchema(many=True)

User_uid_schema=User_uidSchema()


te = ""
a = 1
b = 1
registrations = {}

@app.route('/api/rfid/register', methods=['POST'])
def submit():
    global te
    data = request.get_json()
    te = data.get('rfid_uid')
    print(te)
    return "register"


@app.route('/api/getuid', methods=['GET'])
def getuid():
    global te
    return jsonify({"data":te})

@app.route('/api/rest-uid', methods=['GET'])
def restuid():
    global te
    te=""
    return jsonify({"data":te})


@app.route('/api/registration', methods=['POST'])
def register_user():
    """
    Handle registration form data and return a unique registration ID.
    """
    try:
        data = request.json
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        registration_date = data.get('registrationDate')

        # Validate inputs
        if not first_name or not last_name or not registration_date:
            return jsonify({"error": "All fields are required."}), 400
        article2 = Guest.query.filter_by(nom=first_name,prenom=last_name,date=datetime.date.today()).first()
        if article2:
            return jsonify({"error": "deja registrer"})

        article = Guest(first_name,last_name)
        db.session.add(article)
        db.session.commit()
        article1 = Guest.query.filter_by(nom=first_name,prenom=last_name,date=datetime.date.today()).first()
        registration_id = article1.id
        data["id"]=registration_id
        # Debug: Print the registration for verification (remove in production)
        print(f"New Registration: {data}")

        # Return the registration ID
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/api/qrcode/generate/<registrationId>', methods=['GET'])
def get_qr_code_data(registrationId):
    print(f"Received registrationId: {registrationId}")

    # Rest of your logic
    client_ip = request.remote_addr  # Get the IP address of the client
    print(f"Client IP: {client_ip}")

    if client_ip != ALLOWED_IP:
        return jsonify({"error": "Access denied"}), 403

    try:
        # Simulate fetching data (replace with a database query in production)
        article1 = Guest.query.filter_by(id=registrationId).first()
        print(article1)
        data= {
            "registration_id":article1.id,
            "guest_name":article1.nom+" "+article1.prenom,
            "registration_date":article1.date
        }
        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/add-card', methods=['POST'])
def addcard():
    global te
    data = request.get_json()
    id_user = data.get('id_user')
    uid = data.get('uid')
    user_uid= User_uid(id_user,uid)
    db.session.add(user_uid)
    db.session.commit()
    return jsonify({"data":"success"})


@app.route('/add',methods = ['POST'])
def add_articales():
    data = request.get_json()
    nom = data.get('nom')
    prenom = data.get('prenom')
    code_apogee = data.get('code_apogee')
    code_carte = data.get('code_carte')
    CNEe = data.get('CNE')
    CINe = data.get('CIN')
    articales = Users(nom,prenom,code_apogee,code_carte,CNEe,CINe)
    db.session.add(articales)
    db.session.commit()
    return jsonify({"message": "Données reçues avec succès", "data": data}), 200

@app.route('/search/<code_car>', methods=['GET'])
def search_for(code_car):
    article = Users.query.filter_by(code_carte=code_car).first()
    if article:
        return jsonify({'status': 'success','id':article.id,'nom':article.nom})
    else:
        return jsonify({'status': 'refuse'})

@app.route('/api/data/<carte_rf>', methods=['GET'])
def get_data(carte_rf):
    data = request.get_json()
    mac_address = data.get('mac_address')
    rfid_uid = data.get('rfid_uid')
    event_id = data.get('event_id')
    print(rfid_uid)
    if not mac_address or not rfid_uid or not event_id:
        return jsonify({"error": "Missing required fields"}), 400
    return jsonify({"msg": "diha frask"}), 200


@app.route('/api/setdata', methods=['POST'])
def set_data():
    data = request.get_json()
    mac_address = data.get('mac_address')
    rfid_uid = data.get('rfid_uid')
    event_id = data.get('event_id')
    print(rfid_uid)
    article = User_uid.query.filter_by(id_carte=rfid_uid).first()
    if article:
        article1 = Presence.query.filter_by(id_user=article.id_user).first()
        if not article1:
            articales = Presence(article.id_user)
            db.session.add(articales)
            db.session.commit()
        return "green"
    else:
        return "red"
    
@app.route('/listuser', methods=['GET'])
def listuser():
    all_users = Users.query.all()  # Assuming this returns a list of user objects
    for user in all_users:
        user_uid = User_uid.query.filter_by(id_user=user.id).first()  # Fetch the associated User_uid
        if user_uid:  # Make sure a User_uid is found
            user.id_carte = user_uid.id_carte 
        else:
            user.id_carte = None # Update the user's id_carte field

    results = users_schema.dump(all_users) 
    # Add a flag indicating whether id_carte is missing
    for result in results:
        result['has_id_carte'] = result['id_carte'] is not None # Serialize the updated user objects
        
    return jsonify(results)
    


@app.route('/api/fetch-uid', methods=['GET'])
def fetch():
    esp8266_ip = '192.168.52.36'  # Remplacez par l'IP de votre module ESP8266
    url = f'http://{esp8266_ip}/'

    params = {'param': 'register'}
    response = requests.get(url, params=params)

    content = response.text
    return jsonify({"data":"tset"})

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)
