from os import path, mkdir
from typing import BinaryIO
from uuid import uuid4
from marshmallow.exceptions import ValidationError
from flask import Flask, jsonify, request, abort, send_from_directory, render_template
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from flask_cors import CORS
import imghdr
from db import setup_db
from db.models import User
from db.schemas import user_schema, login_schema
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
        data = login_schema.load(request.json)
        user: User = User.query.filter_by(email=data['email']).scalar()
        if not user or not user.checkpw(data['password']):
            abort(422, 'Email or password is not correct.')

        return jsonify({
            'success': True,
            'token': create_access_token(user.id)
        })

    @app.post("/api/register")
    def register():
        result = user_schema.load(request.json)
        new_user = User(**result)
        new_user.insert()

        return jsonify({
            'success': True,
            'token': create_access_token(identity=new_user.id),
        })

    ### HANDLING ERRORS ###

    @app.errorhandler(Exception)
    def default_error_handler(error):
        app.logger.exception(error)
        try:
            message = error.description
            code = error.code
        except AttributeError:
            message = "Something when wrong."
            code = 500

        return jsonify({
            'success': False,
            'message': message,
        }), code

    @app.errorhandler(ValidationError)
    def marshmallow_error_handler(error):
        return jsonify({
            'success': False,
            'message': 'The given data was invalid.',
            'errors': error.messages,
        }), 422

    return app
