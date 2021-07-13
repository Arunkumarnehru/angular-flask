from flask import Flask, config, request, jsonify
import json
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import uuid
from werkzeug.utils import secure_filename
import pyrebase
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from flask_bcrypt import Bcrypt

# local uploads or temp 
UPLOAD_FOLDER = "./uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# filter min-types
def allowed_files(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.secret_key = "Secret Key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Arun123@localhost/posturl'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
db.init_app(app)
# app.config["MYSQL_HOST"] = "localhost"
# app.config["MYSQL_USER"] = "root"
# app.config["MYSQL_PASSWORD"] = "Arun123"
# app.config["MYSQL_DB"] = "flaskposturl"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# mysql = MySQL(app)
CORS(app)
class Postdata(db.Model):
    __tablename__ = 'postdata'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.String(100))
    cover = db.Column(db.Text)
    covername = db.Column(db.Text, nullable=True)

    def __init__(self, title, content, cover, covername):
        self.title = title
        self.content = content
        self.cover = cover
        self.covername = covername

    def to_json(self):
        return (
            self.id,
            self.title,
            self.content,
            self.cover,
            self.covername,
        )

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=True, unique=True)
    password = db.Column(db.String(80), nullable=True)

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "Arun123"
app.config["MYSQL_DB"] = "posturl"
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
mysql = MySQL(app)
# Password
bcrypt =Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

config = {
    "apiKey": "AIzaSyD4l5AnVgaFGlQkYNaxeGROxeTRQ4hYvvs",
    "authDomain": "flask-post-98f3a.firebaseapp.com",
    "projectId": "flask-post-98f3a",
    "databaseURL": "https://flask-post-98f3a.firebaseio.com",
    "storageBucket": "flask-post-98f3a.appspot.com",
    "messagingSenderId": "761143956166",
    "appId": "1:761143956166:web:418dab5daa93be29d97dc7",
    "measurementId": "G-6L2684LDJB",
    "serviceaccount":"./keyfile.json",

}
# init firebase app 
firebase = pyrebase.initialize_app(config)
#firebase storage
storage = firebase.storage()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/api/login', methods=['GET', 'POST'])
def login():
    if request.method =="POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user:
            if bcrypt.check_password_hash(user.password, password):
                login_user(user)
                return jsonify(data = "The User was created successfully")
        else:
            return jsonify(data="username incorrect")

@app.route("/api/signup", methods=["POST"])
def adduser():
    if request.method =="POST":
        print(request.form, flush=True)
    username = request.form.get("username")
    password = request.form.get("password")
    existing_user_username = User.query.filter_by(
            username=username).first()
    if existing_user_username:
        error = "That username already exists, Please choose a different one."
        print(error)
        return jsonify(data=error)
    else:
        hashed_password = bcrypt.generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        print("success")
        return jsonify(data = "The User was created successfully")


@app.route("/api/posts", methods=["GET"])
def index():
    if request.method == "GET":
        records = [z.to_json() for z in Postdata.query]
        return jsonify(data= tuple(records))

@app.route("/api/addpost", methods=["POST"])
def addpost():
    if request.method =="POST":
        print(request.form, flush=True)
    title = request.form.get("title")
    content = request.form.get("content")
    cover = request.files["cover"]

    if cover and allowed_files(cover.filename):
        filename = str(uuid.uuid4())
        filename += "."
        filename += cover.filename.split(".")[1]

        #create secure name
        filename_secure = secure_filename(filename)
        #save the file inside the uploads folder
        cover.save(os.path.join(app.config["UPLOAD_FOLDER"], filename_secure))

        #local file
        local_filename = "./uploads/"
        local_filename += filename_secure    

        #firebase filename
        firebase_filename = "uploads/"
        firebase_filename += filename_secure

        #upload the file
        storage.child(firebase_filename).put(local_filename)
        #get the url of the file
        cover_image = storage.child(firebase_filename).get_url(None)
        
        #get cursor to exec the mysql functions
        my_data = Postdata(title, content, cover_image, filename_secure)
        db.session.add(my_data)
        db.session.commit()
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename_secure))

        return jsonify(data = "The post was created successfully")

@app.route("/api/post/<id>", methods=["GET"])
def singlepost(id):
    my_data = Postdata.query.get(id)
    records = my_data.to_json()
    print(records)
    return jsonify(data= tuple(records))

@app.route("/api/editfullpost/<id>", methods=["PUT"])
def editfullpost(id):
    if request.method == "PUT":
        print(request.form, flush=True)
        postid = request.form.get("id")
        title = request.form.get("title")
        content = request.form.get("content")
        oldcover = request.form.get("oldcover")
        covername = request.form.get("covername")

        if request.files["cover"]:
            if allowed_files(request.files["cover"].filename):
                cover = request.files["cover"]
                #creating the filename
                filename =str(uuid.uuid4())
                filename +="."
                filename += cover.filename.split(".")[1]

                #create a secure name
                filename_secure = secure_filename(filename)
                #save the file inside the folder specified
                cover.save(os.path.join(app.config["UPLOAD_FOLDER"], filename_secure)) 

                #local file
                local_filename = "./uploads/"
                local_filename += filename_secure

                #firebase file name
                firebase_filename = "uploads/"
                firebase_filename += filename_secure

                #upload the file
                storage.child(firebase_filename).put(local_filename);


                #get the url
                cover_image = storage.child(firebase_filename).get_url(None)
                #get the cursor to exec the mysql functions
                my_data = Postdata.query.get(postid)
                my_data.title = title
                my_data.content = content
                my_data.cover = cover_image
                my_data.covername = covername
                db.session.commit()
                #delete the current image
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename_secure))

                #path of the image to delete inside firebase
                firebase_filename_delete = "uploads/"
                firebase_filename_delete += covername 

                # storage.delete(firebase_filename_delete)   

                return jsonify(data= "the post was updated successfully")

@app.route("/api/editpost/<id>", methods=["PUT"])
def editpost(id):
    if request.method == "PUT":
        postid = request.form.get("id")
        title = request.form.get("title")
        content = request.form.get("content")
        my_data = Postdata.query.get(postid)
        my_data.title = title
        my_data.content = content
        db.session.commit()
        return jsonify(data="The post was updated successfully") 


@app.route("/api/deletepost/<id>", methods=["DELETE"])
def deletepost(id):
    my_data = Postdata.query.get(id)
    print('my_data', my_data)
    db.session.delete(my_data)
    db.session.commit()
    return jsonify(data = "post was deleted successfully")

if __name__ == "__main__":
    app.run(debug=True)