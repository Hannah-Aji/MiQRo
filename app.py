from flask import Flask, render_template, request
from PIL import Image
import io
import tempfile
import os
from peewee import *
import re

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, send_from_directory
from authlib.integrations.base_client.errors import OAuthError
from flask_session import Session

from Scanner.MicroQRCodeScanner import do_stuff
import base64

from database import *
from crypto import *

import os
from peewee import *

from os import environ as env
from playhouse.shortcuts import model_to_dict
from dotenv import load_dotenv

import shutil
import json

from collections import defaultdict
from redis import Redis

load_dotenv()


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

upload_folder = './uploads'

app.config['UPLOAD_FOLDER'] = upload_folder
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = Redis(host='redis', port=6379)
app.config['SESSION_PERMANENT'] = False

oauth = OAuth(app)
server_session = Session(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


# Controllers API
@app.route("/")
def main():
    error = None
    if 'error' in session: 
        error = session['error']
        session.pop('error')
    return render_template(
        "login.html",

    )

        #session=session.get("user"),
        #pretty=json.dumps(session.get("user"), indent=4),
        #error=error,
@app.route("/callback", methods=["GET", "POST"])
def callback():
    try: 
        token = oauth.auth0.authorize_access_token()
    except OAuthError as e:
        if e.error == "access_denied":
            session['error'] = "You must sign in with a kent.edu email!"
            return redirect(url_for("main"))
    session["user"] = token
    return redirect(url_for("homepage"))


@app.route("/login")
def login():
    session['labs'] = []
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/register")
def register():
    return render_template('register.html')

@app.route("/labhome")
def lab_home():
    return render_template('labhome.html')

@app.route("/addlab")
def lab_add():
    return render_template('addlab.html')

@app.route("/createlab")
def lab_create():
    return render_template('createlab.html')

@app.route("/creategroup")
def render_create_group():
    return render_template('creategroup.html')

@app.route("/editdata")
def edit_data():
    return render_template('editdata.html')


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("main", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

#Hompage that allows uploading of files to be extracted and decoded
@app.route('/home', methods=['GET', 'POST'])
def homepage():
    if 'user' not in session:
        return redirect(url_for("main"))
    '''
    if request.method == 'POST' :
        file = request.files['file']
        if file:
            image_bytes = file.read()
            image = Image.open(io.BytesIO(image_bytes))
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, 'temp.png')
            image.save(temp_file_path)
            img, ids, coordinate_map = do_stuff(temp_file_path, "./outputs")

            os.remove(temp_file_path)
            shutil.rmtree(temp_dir, ignore_errors=True)
            with open('./outputs/temp.svg', 'r') as file:
                data = file.read()
                encoded = base64.b64encode(data.encode()).decode()

            return render_template('index.html', message='File uploaded successfully', session = session.get("user"), img = encoded, ids=ids, squares = coordinate_map)

    
    '''
    if 'labs' not in session: 
        session['labs'] = []
    if 'groups' not in session: 
        session['groups'] = defaultdict(list)

    session["labs"].append("lab1")
    session["labs"].append("lab2")
    session["labs"].append("lab3")
    session["labs"].append("lab4")

    session['groups']['lab1'].append("Group1lab1")
    session['groups']['lab1'].append("Group2lab1")
    session['groups']['lab1'].append("Group3lab1")
    session['groups']['lab2'].append("Group1lab2")
    session['groups']['lab3'].append("Group1lab3")
    session['groups']['lab3'].append("Group2lab3")
    session['groups']['lab4'].append("Group1lab4")
    session['groups']['lab4'].append("Group2lab4")

    return render_template('home.html', session = session)


@app.route('/scan', methods=['GET', 'POST'])
def scan():
    if 'user' not in session: 
        return redirect(url_for("main"))
    if request.method == 'POST' :
        file = request.files['file']
        if file:
            image_bytes = file.read()
            image = Image.open(io.BytesIO(image_bytes))
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, 'temp.png')
            image.save(temp_file_path)
            img, ids, coordinate_map = do_stuff(temp_file_path, "./outputs")

            os.remove(temp_file_path)
            shutil.rmtree(temp_dir, ignore_errors=True)
            with open('./outputs/temp.svg', 'r') as file:
                data = file.read()
                encoded = base64.b64encode(data.encode()).decode()


            qr_values = ids.values()



            qr_data = QRs.select().where(QRs.qr_id.in_(qr_values) and QRs.group_id == session["selectedGroup"])
            qr_data = qr_data.execute()

            session['img'] = encoded
            session['ids'] = ids
            session['squares'] = coordinate_map


            

            
            return render_template('fetch.html', message='File uploaded successfully', session = session.get("user"), img = encoded, ids=ids, squares = coordinate_map, qr_data = qr_data, selected_group = session["selectedGroup"], selected_lab=session["selectedLab"])
    
    if 'img' in session and 'ids' in session and 'squares' in session :
        qr_data = QRs.select().where(QRs.qr_id.in_(session['ids'].values()) and QRs.group_id == session["selectedGroup"])
        qr_data = qr_data.execute()
        return render_template('fetch.html', session=session.get("user"), img = session['img'], ids = session['ids'], squares = session['squares'], qr_data = qr_data, selected_group = session.get("selectedGroup"), selected_lab=session.get("selectedLab"))
    
    return render_template('fetch.html', selected_group = session.get("selectedGroup"), selected_lab=session.get("selectedLab"))


@app.route('/set/labandgroup', methods=['POST'])
def setLabandGroup() :
    if 'user' not in session: 
        return redirect(url_for("main"))
    if request.method == 'POST' :
        lab = request.form['labSelect']
        group = request.form['grpSelect']

        session['selectedLab'] = lab
        session['selectedGroup'] = group

        return redirect(url_for('scan'))


@app.route('/editQRData', methods=['POST'])
def editQRData() :
    if 'user' not in session: 
        return redirect(url_for("main"))
    if request.method == 'POST' :

        qr_id = request.form['QR_ID']
        group = session['selectedGroup']

        qr = QRs.get((QRs.qr_id == qr_id) and (QRs.group_id == group))

        if request.form['attr_0'] != "" :
            qr.attr_0 = request.form['attr_0']
        if request.form['attr_1'] != "" :
            qr.attr_1 = request.form['attr_1']
        if request.form['attr_2'] != "" :
            qr.attr_2 = request.form['attr_2']
        if request.form['attr_3'] != "" :
            qr.attr_3 = request.form['attr_3']
        if request.form['attr_4'] != "" :
            qr.attr_4 = request.form['attr_4']
        if request.form['attr_5'] != "" :
            qr.attr_5 = request.form['attr_5']
        if request.form['attr_6'] != "" :
            qr.attr_6 = request.form['attr_6']
        if request.form['attr_7'] != "" :
            qr.attr_7 = request.form['attr_7']
        if request.form['attr_8'] != "" :
            qr.attr_8 = request.form['attr_8']
        if request.form['attr_9'] != "" :
            qr.attr_9 = request.form['attr_9']

        qr.save()

        return redirect(url_for("scan"))
        

        


# ==========================================================================
# CREATING ENDPOINTS FOR USER REGISTRATION
@app.route('/api/register', methods=['POST'])
def postUserCreated():
    email = request.form.get('email')
    password = hash_password(request.form.get('password'))
    if not email:
        return {'error': 'Invalid email'}, 400
    if not password:
        return {'error': 'Invalid email'}, 400
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {'error': 'Invalid Email: Please provide a valid email address.'}, 400


    user = Users.create(email = email, password = password)
    userinfo = {
        "email": user.email,
        "user_id": user.user_id
    }
    session["user"] = userinfo


    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def userLogin():
    email = request.form.get('email')
    password = hash_password(request.form.get('password'))
    if not email:
        return {'error': 'Invalid email'}, 400
    if not password:
        return {'error': 'Invalid email'}, 400
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {'error': 'Invalid Email: Please provide a valid email address.'}, 400
    
    try:
        user = Users.get(Users.email == email, Users.password == password)
        
        userinfo = {
            "email": user.email,
            "user_id": user.user_id
        }

        # Need to input session data appropriately
        session["user"] = userinfo


        return render_template('index.html')
        return {'message': 'User logged in successfully'}
    except Users.DoesNotExist:
        return {'message': 'User not found'}
    


@app.route('/api/user', methods=['GET'])
def getUserCreated():
   
    users_created = [
        model_to_dict(p)
        for p in Users
    ]

    if not users_created:
        return {'users_created': len(users_created)}

    return {'users_created': users_created}


@app.route('/api/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = Users.get_by_id(user_id)
        user.delete_instance()
        return {'message': 'User deleted successfully'}
    except Users.DoesNotExist:
        return {'error': 'User with that id not found'}
    
@app.route('/api/labs/', methods=['GET'])
def get_labs():
    labs_created = [
        model_to_dict(l)
        for l in Labs
    ]

    if not labs_created:
        return {'labs_create: ': len(labs_created)}
    
    return {'labs_create: ': labs_created}

@app.route('/api/lab_permissions/', methods=['GET'])
def get_lab_permissions():
    lab_permissions_created = [
        model_to_dict(p)
        for p in Lab_Permissions
    ]

    if not lab_permissions_created:
        return {'lab_permissions: ': len(lab_permissions_created)}
    
    return {'lab_permissions: ': lab_permissions_created}

@app.route("/api/create_lab", methods=['GET', 'POST'])
def create_lab():
    lab_name = request.form.get('lab_name')

    if not lab_name:
        return {'error': 'Invalid lab name'}, 400

    lab = Labs.create(lab_name = lab_name)

    user_id = int(session.get('user').get('user_id'))

    Lab_Permissions.create(lab_user = user_id, lab_id = lab.lab_id, lab_admin = True)
    

    return render_template('labhome.html')

@app.route("/api/create_group", methods=['GET', 'POST'])
def create_group():

    group_name = request.form.get('group_name')

    if not group_name:
        return {'error': 'Invalid group name'}, 400
    
    lab_id = session.get('user').get('lab_id')

    group = Groups.create(lab_id = lab_id, group_name = group_name)

    userinfo = {
        "email": session.get('email'),
        "user_id": session.get('user_id'),
        "lab_id": session.get('lab_id'),
        "group_id": group.group_id
    }

    session["user"] = userinfo

    return render_template("labhome.html")

@app.route("/api/groups", methods=['GET'])
def get_groups():
    groups_created = [
        model_to_dict(g)
        for g in Groups
    ]
    return None

# ==========================================================================
if __name__ == "__main__":
    app.run(debug=True)
