from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from db.models import User


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
