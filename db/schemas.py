from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from sqlalchemy.sql.expression import true
from db.models import Contact, Type, User


class UserSchema(Schema):
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True,
                          validate=validate.Length(min=8))
    created_at = fields.DateTime(dump_only=True)

    @validates('email')
    def validate_email(self, value):
        if User.query.filter_by(email=value).scalar():
            raise ValidationError("Already in use.")

    @post_load
    def clean_data(self, data, **kwargs):
        data['name'] = data['name'].strip()
        return data


user_schema = UserSchema()


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


login_schema = LoginSchema()


class PhoneSchema(Schema):
    id = fields.Int(dump_only=True)
    value = fields.Str(required=True)
    type_id = fields.Int(required=True)
    contact_id = fields.Int(required=True)

    @validates('type_id')
    def validate_type(self, value):
        if not Type.query.get(value):
            raise ValidationError("Do not exist.")

    @validates('contact_id')
    def validate_type(self, value):
        if not Contact.query.get(value):
            raise ValidationError("Do not exist.")


phone_schema = PhoneSchema()


class ContactSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Email(required=False)
    phones = fields.List(fields.Nested(
        PhoneSchema(exclude=['contact_id'])), required=True)


contact_schema = ContactSchema()
