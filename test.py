import unittest
import json
from app import app, db

class UserTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_user(self):
        # Test creating a user
        response = self.app.post('/user', json={"unique_metadata": "test_user", "non_unique_metadata": "Test User"})
        data = json.loads(response.data.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('user_id', data)
        self.assertIn('user_key', data)

    def test_create_user_missing_data(self):
        # Test creating a user with missing data
        response = self.app.post('/user', json={"non_unique_metadata": "Test User"})
        self.assertEqual(response.status_code, 400)

    def test_create_user_invalid_data(self):
        # Test creating a user with invalid data
        response = self.app.post('/user', json={"unique_metadata": 123, "non_unique_metadata": "Test User"})
        self.assertEqual(response.status_code, 400)

    def test_edit_user_metadata(self):
        # Test editing user metadata
        response = self.app.put('/user/1/edit', json={"user_key": "user_key", "non_unique_metadata": "Updated User"})
        data = json.loads(response.data.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['user_id'], 1)
        self.assertEqual(data['username'], "test_user")
        self.assertEqual(data['email'], "Updated User")

    def test_edit_user_missing_key(self):
        # Test editing user metadata without providing the user key
        response = self.app.put('/user/1/edit', json={"non_unique_metadata": "Updated User"})
        self.assertEqual(response.status_code, 400)

    def test_edit_user_invalid_key(self):
        # Test editing user metadata with an invalid user key
        response = self.app.put('/user/1/edit', json={"user_key": "invalid_key", "non_unique_metadata": "Updated User"})
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()
