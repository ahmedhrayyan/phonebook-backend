from os import path, mkdir
from typing import BinaryIO
from uuid import uuid4
from marshmallow.exceptions import ValidationError
from flask import Flask, jsonify, request, abort, send_from_directory, render_template
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from flask_cors import CORS
import imghdr
from db import setup_db, db
from db.models import Contact, Phone, Type, User
from db.schemas import ContactSchema, PhoneSchema, user_schema, login_schema, contact_schema, phone_schema, type_schema
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
    jwt = JWTManager(app)
    CORS(app)
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
            'token': create_access_token(user.id)
        })

    @app.post("/api/register")
    def register():
        result = user_schema.load(request.json)
        new_user = User(**result)
        new_user.insert()

        return jsonify({
            'token': create_access_token(identity=new_user.id),
        })

    @app.get("/api/contacts")
    @jwt_required()
    def get_contacts():
        contacts = Contact.query.filter_by(user_id=get_jwt_identity()).order_by(Contact.id.desc()).all()
        return jsonify({
            'data': contact_schema.dump(contacts, many=True)
        })

    @app.post("/api/contacts")
    @jwt_required()
    def post_contact():
        data = contact_schema.load(request.json)
        name, phones, email = data['name'], data['phones'], data.get('email')

        new_contact = Contact(get_jwt_identity(), name, email)

        for phone in phones:
            new_phone = Phone(phone['value'], phone['type_id'], new_contact.id)
            new_contact.phones.append(new_phone)

        new_contact.insert()

        return jsonify({
            'data': contact_schema.dump(new_contact)
        })

    @app.patch("/api/contacts/<int:id>")
    @jwt_required()
    def update_contact(id):
        contact: Contact = Contact.query.get(id)
        if not contact:
            abort(404, 'Contact not found.')
        if contact.user_id != get_jwt_identity():
            abort(403)

        data = ContactSchema(exclude=['phones']).load(
            request.json, partial=True)
        for key, val in data.items():
            setattr(contact, key, val)

        contact.update()

        return jsonify({
            'data': ContactSchema(only=('id', 'phones', *data)).dump(contact)
        })

    @app.delete("/api/contacts/<int:id>")
    @jwt_required()
    def delete_contact(id):
        contact: Contact = Contact.query.get(id)
        if not contact:
            abort(404, 'Contact not found.')
        if contact.user_id != get_jwt_identity():
            abort(403)

        contact.delete()

        return jsonify({
            'deleted_id': id
        })

    @app.post("/api/phones")
    @jwt_required()
    def post_phone():
        data = phone_schema.load(request.json)
        contact: Contact = Contact.query.get(data['contact_id'])
        if contact.user_id != get_jwt_identity():
            abort(403)

        new_phone = Phone(**data)
        new_phone.insert()

        return jsonify({
            'data': phone_schema.dump(new_phone)
        })

    @app.patch("/api/phones/<int:id>")
    @jwt_required()
    def update_phone(id):
        phone: Phone = Phone.query.get(id)
        if not phone:
            abort(404, "Phone not found.")
        if phone.contact.user_id != get_jwt_identity():
            abort(403)

        data = PhoneSchema(exclude=['contact_id']).load(
            request.json, partial=True)
        for key, val in data.items():
            setattr(phone, key, val)

        phone.update()

        return jsonify({
            'data': PhoneSchema(only=('id', 'contact_id', *data)).dump(phone)
        })

    @app.delete("/api/phones/<int:id>")
    @jwt_required()
    def delete_phone(id):
        phone: Phone = Phone.query.get(id)
        if not phone:
            abort(404, "Phone not found.")
        if phone.contact.user_id != get_jwt_identity():
            abort(403)

        phone.delete()

        return jsonify({
            'deleted_id': id,
            'contact_id': phone.contact_id
        })

    @app.get("/api/types")
    def get_types():
        types = Type.query.all()
        return jsonify({
            'data': type_schema.dump(types, many=True)
        })

    ### HANDLING ERRORS ###

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        return jsonify(message=error_string), 401

    @app.errorhandler(Exception)
    def default_error_handler(error):
        if app.config['TESTING'] is not True:
            app.logger.exception(error)
        try:
            message = error.description
            code = error.code
        except AttributeError:
            message = "Something when wrong."
            code = 500

        return jsonify({
            'message': message,
        }), code

    @app.errorhandler(ValidationError)
    def marshmallow_error_handler(error):
        return jsonify({
            'message': 'The given data was invalid.',
            'errors': error.messages,
        }), 400

    ### COMMANDS ###

    @app.cli.command('db_seed')
    def db_seed():
        # create basic types
        types = [Type('mobile'), Type('home'), Type('work'), Type('Other')]
        try:
            db.session.add_all(types)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    return app
