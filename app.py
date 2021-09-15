from os import path, mkdir
from typing import BinaryIO
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from flask import Flask, jsonify, request, abort, send_from_directory, render_template
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from flask_cors import CORS
import imghdr
import re
from db import setup_db
from db.models import User
from config import ProductionConfig


def validate_image(stream: BinaryIO):
    ''' Return correct image extension '''
    # check file format
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    # jpeg normally uses jpg file extension
    return format if format != "jpeg" else "jpg"

def create_app(config=ProductionConfig):
    ''' create and configure the app '''
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config)
    CORS(app)
    JWTManager(app)
    setup_db(app)

    ### ENDPOINTS ###

    @app.route("/")
    def index():
        return render_template('index.html')

    @app.post("/api/upload")
    @jwt_required()
    def upload():
        if 'file' not in request.files:
            abort(400, "No file founded")
        file = request.files['file']
        if file.filename == '':
            abort(400, 'No selected file')
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        if file_ext not in app.config['ALLOWED_EXTENSIONS']:
            abort(422, 'You cannot upload %s files' % file_ext)
        if file_ext != validate_image(file.stream):
            abort(422, 'Fake data was uploaded')

        # generate unique filename
        filename = uuid4().hex + "." + file_ext

        # Create upload folder if it doesnot exist
        if not path.isdir(app.config['UPLOAD_FOLDER']):
            mkdir(app.config['UPLOAD_FOLDER'])

        file.save(path.join(app.config['UPLOAD_FOLDER'], filename))

        return jsonify({
            'success': True,
            'path': filename
        })

    @app.get("/uploads/<filename>")
    def uploaded_file(filename):
        try:
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        except Exception:
            abort(404, "File not found")

    @app.post("/api/login")
    def login():
        data = request.get_json() or {}
        if 'email' not in data or 'password' not in data:
            abort(400, 'email and password expected in request body')
        email = str(data.get('email'))
        password = str(data.get('password'))
        user: User = User.query.filter_by(email=email).one_or_none()
        if not user or not user.checkpw(password):
            abort(422, 'username or password is not correct')

        return jsonify({
            'success': True,
            'token': create_access_token(user.id)
        })

    @app.post("/api/register")
    def register():
        data = request.get_json() or {}
        required_fields = ['name', 'email', 'password']
        # abort if any required field doesnot exist in request body
        for field in required_fields:
            if field not in data:
                abort(400, '%s is required' % field)

        name = str(data.get('name')).lower().strip()
        email = str(data.get('email')).lower().strip()
        password = str(data.get('password')).lower()

        # validating data
        if re.match(app.config['EMAIL_PATTERN'], email) is None:
            abort(422, 'Email is not valid')
        if len(password) < 8:
            abort(422, 'Password have to be at least 8 characters in length')

        new_user = User(name, email, password)

        try:
            new_user.insert()
        except IntegrityError:
            # Integrity error means a unique value already exist in a different record
            abort(422, "Email is already in use")

        return jsonify({
            'success': True,
            'token': create_access_token(identity=new_user.id)
        })

    ### HANDLING ERRORS ###

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': error.description,
            'error': 404
        }), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'message': error.description,
            'error': 400
        }), 400

    @app.errorhandler(422)
    def un_processable(error):
        return jsonify({
            'success': False,
            'message': error.description,
            'error': 422
        }), 422

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'message': error.description,
            'error': 405
        }), 405

    @app.errorhandler(413)
    def too_large(error):
        return jsonify({
            'success': False,
            'message': error.description,
            'error': 413
        }), 413

    return app
