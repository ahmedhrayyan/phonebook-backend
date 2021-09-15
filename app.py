from os import path, mkdir
from typing import BinaryIO
from uuid import uuid4
from flask import Flask, jsonify, request, abort, send_from_directory, render_template
from flask_cors import CORS
from db import setup_db
from sqlalchemy.exc import IntegrityError
import imghdr
import re
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

    setup_db(app)

    ### ENDPOINTS ###

    @app.route("/")
    def index():
        return render_template('index.html')

    @app.post("/api/upload")
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
