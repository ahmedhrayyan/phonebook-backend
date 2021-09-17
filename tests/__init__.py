import unittest
from io import BytesIO
from flask import json
from flask_jwt_extended import create_access_token
from app import create_app
from config import TestingConfig
from db import db
from db.models import Contact, Phone, Type, User


class TestCase(unittest.TestCase):
    ''' This class represents Sal test case '''

    def setUp(self):
        ''' Executes before each test. Inti the app and define test variables '''
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client
        # seed data
        self.user = User('Ahmed Hamed', 'test@test.com', 'secret')
        self.contact = Contact(self.user.id, 'Ali Hamed')
        self.type = Type('mobile')
        self.phone = Phone('010xxxxx', self.type.id, self.contact.id)
        self.user.contacts.append(self.contact)
        self.contact.phones.append(self.phone)
        self.phone.type = self.type
        self.user.insert()
        # push an application context as create_access_token function needs it
        # ref: https://flask.palletsprojects.com/en/2.0.x/appcontext/#lifetime-of-the-context
        self.app.app_context().push()
        # generate token
        token = create_access_token(self.user.id)
        self.auth_header = {'Authorization': 'Bearer %s' % token}

    def tearDown(self):
        ''' Executes after each test '''
        db.session.remove()
        db.drop_all()

    def test_422_upload(self):
        res = self.client().post('api/upload', headers=self.auth_header,
                                 data={'file': (BytesIO(b'IMAGE DATA'), 'file.jpg')})  # fake data
        self.assertEqual(res.status_code, 422)
        self.assertTrue(res.json['message'])

    def test_404_view_uploaded(self):
        res = self.client().get('/uploads/x')
        self.assertEqual(res.status_code, 404)

    def test_400_register(self):
        res = self.client().post('/api/register',
                                 json={
                                     'name': 'Ahmed',
                                     'email': self.user.email,
                                     'password': '12345678'})
        self.assertEqual(res.status_code, 400)
        self.assertIsInstance(res.json['errors'], dict)

    def test_register(self):
        res = self.client().post('/api/register',
                                 json={
                                     'name': 'Ahmed',
                                     'email': 'test2@test.com',
                                     'password': '12345678'})
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json['token'], str)

    def test_422_login(self):
        res = self.client().post('/api/login',
                                 json={
                                     'email': 'test@test.com',
                                     'password': 'top_secret'})
        self.assertEqual(res.status_code, 422)
        self.assertIsInstance(res.json['message'], str)

    def test_login(self):
        res = self.client().post('/api/login',
                                 json={
                                     'email': 'test@test.com',
                                     'password': 'secret'})
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json['token'], str)

    def test_401_get_contacts(self):
        res = self.client().get('/api/contacts')
        self.assertEqual(res.status_code, 401)
        self.assertIsInstance(res.json['message'], str)

    def test_get_contacts(self):
        res = self.client().get('/api/contacts', headers=self.auth_header)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json['data'], list)

    def test_400_post_contact(self):
        res = self.client().post('/api/contacts', headers=self.auth_header)
        self.assertEqual(res.status_code, 400)
        self.assertIsInstance(res.json['errors'], dict)

    def test_post_contact(self):
        res = self.client().post('/api/contacts', headers=self.auth_header,
                                 json={
                                     'name': 'Ali Hamed',
                                     'phones': []})
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json['data'], dict)

    def test_404_patch_contact(self):
        res = self.client().patch('/api/contacts/1000', headers=self.auth_header)
        self.assertEqual(res.status_code, 404)
        self.assertIsInstance(res.json['message'], str)

    def test_patch_contact(self):
        id = self.contact.id
        res = self.client().patch('/api/contacts/%i' % id, headers=self.auth_header, json={})
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json['data'], dict)

    def test_404_delete_contact(self):
        res = self.client().delete('/api/contacts/1000', headers=self.auth_header)
        self.assertEqual(res.status_code, 404)
        self.assertIsInstance(res.json['message'], str)

    def test_delete_contact(self):
        id = self.contact.id
        res = self.client().delete('/api/contacts/%i' % id, headers=self.auth_header)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json['deleted_id'], id)

    def test_400_post_phone(self):
        res = self.client().post('/api/phones', headers=self.auth_header)
        self.assertEqual(res.status_code, 400)
        self.assertIsInstance(res.json['errors'], dict)

    def test_post_phone(self):
        res = self.client().post('/api/phones', headers=self.auth_header,
                                 json={
                                     'type_id': self.type.id,
                                     'contact_id': self.contact.id,
                                     'value': '010xxxx'})
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json['data'], dict)

    def test_404_patch_phone(self):
        res = self.client().patch('/api/phones/1000', headers=self.auth_header)
        self.assertEqual(res.status_code, 404)
        self.assertIsInstance(res.json['message'], str)

    def test_patch_phone(self):
        id = self.phone.id
        res = self.client().patch('/api/phones/%i' % id, headers=self.auth_header, json={})
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json['data'], dict)

    def test_404_delete_phone(self):
        res = self.client().delete('/api/phones/1000', headers=self.auth_header)
        self.assertEqual(res.status_code, 404)
        self.assertIsInstance(res.json['message'], str)

    def test_delete_phone(self):
        id = self.phone.id
        res = self.client().delete('/api/phones/%i' % id, headers=self.auth_header)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json['deleted_id'], id)
