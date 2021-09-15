import unittest
from io import BytesIO
from flask_jwt_extended import create_access_token
from app import create_app
from config import TestingConfig
from db import db
from db.models import User


class TestCase(unittest.TestCase):
    ''' This class represents Sal test case '''

    def setUp(self):
        ''' Executes before each test. Inti the app and define test variables '''
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client
        # seed data
        self.user = User('Ahmed Hamed', 'test@test.com', 'secret')
        self.user.insert()
        # push an application context as create_access_token function needs it
        # ref: https://flask.palletsprojects.com/en/2.0.x/appcontext/#lifetime-of-the-context
        self.app.app_context().push()
        # generate token
        self.token = create_access_token(self.user.id)

    def tearDown(self):
        ''' Executes after each test '''
        db.session.remove()
        db.drop_all()

    def test_422_upload(self):
        res = self.client().post('api/upload',
                                 headers={
                                     'Authorization': 'Bearer %s' % self.token},
                                 data={'file': (BytesIO(b'IMAGE DATA'), 'file.jpg')})  # fake data
        json_data = res.get_json()
        print(json_data)
        self.assertEqual(res.status_code, 422)
        self.assertFalse(json_data['success'])
        self.assertTrue(json_data['message'])

    def test_404_view_uploaded(self):
        res = self.client().get('/uploads/x')
        self.assertEqual(res.status_code, 404)

    def test_422_register(self):
        res = self.client().post('/api/register',
                                 json={
                                     'name': 'Ahmed',
                                     'email': 'test@test.com',
                                     'password': '12345678'
                                 })
        res_data = res.get_json()
        self.assertEqual(res.status_code, 422)
        self.assertFalse(res_data['success'])
        self.assertTrue(res_data['message'])

    def test_register(self):
        res = self.client().post('/api/register',
                                 json={
                                     'name': 'Ahmed',
                                     'email': 'test2@test.com',
                                     'password': '12345678'
                                 })
        res_data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res_data['success'])
        self.assertIsInstance(res_data['token'], str)

    def test_422_login(self):
        res = self.client().post('/api/login',
                                 json={
                                     'email': 'test@test.com',
                                     'password': 'top_secret'
                                 })
        res_data = res.get_json()
        self.assertEqual(res.status_code, 422)
        self.assertFalse(res_data['success'])
        self.assertTrue(res_data['message'])

    def test_login(self):
        res = self.client().post('/api/login',
                                 json={
                                     'email': 'test@test.com',
                                     'password': 'secret'
                                 })
        res_data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res_data['success'])
        self.assertIsInstance(res_data['token'], str)
