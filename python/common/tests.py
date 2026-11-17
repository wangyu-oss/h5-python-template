import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from common.security import mask_phone
from server.seed import PASSWORD, run


class ApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        run()

    def setUp(self):
        self.client = Client()

    def login(self, username='admin'):
        response = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'username': username, 'password': PASSWORD}),
            content_type='application/json',
        )
        body = response.json()
        self.assertEqual(body['code'], 0, body)
        token = body['data']['access_token']
        return token, {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    def test_health(self):
        response = self.client.get('/api/v1/health')
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['data']['status'], 'up')

    def test_login_refresh_logout(self):
        token, headers = self.login()
        me = self.client.get('/api/v1/auth/me', **headers)
        self.assertTrue(me.json()['data']['account']['is_super'])
        refreshed = self.client.post('/api/v1/auth/refresh')
        self.assertEqual(refreshed.json()['code'], 0)
        self.client.post('/api/v1/auth/logout', **headers)
        again = self.client.get('/api/v1/auth/me', **headers)
        self.assertEqual(again.status_code, 401)

    def test_sms_login_and_mask(self):
        sent = self.client.post(
            '/api/v1/auth/sms/send',
            data=json.dumps({'phone': '13900001111'}),
            content_type='application/json',
        )
        code = sent.json()['data']['debug_code']
        logged = self.client.post(
            '/api/v1/auth/sms/login',
            data=json.dumps({'phone': '13900001111', 'code': code}),
            content_type='application/json',
        )
        self.assertEqual(logged.json()['code'], 0)
        self.assertEqual(logged.json()['data']['account']['phone'], mask_phone('13900001111'))

    def test_guest_cannot_pay(self):
        logged = self.client.post(
            '/api/v1/auth/guest',
            data=json.dumps({'device_id': 'device-a'}),
            content_type='application/json',
        )
        token = logged.json()['data']['access_token']
        denied = self.client.post(
            '/api/v1/pay/orders',
            data=json.dumps({'amount': 100, 'subject': 'guest'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(denied.status_code, 403)

    def test_mock_pay_and_idempotent(self):
        token, headers = self.login('zhangsan')
        payload = json.dumps({'amount': 88, 'subject': '演示', 'channel': 'mock'})
        first = self.client.post('/api/v1/pay/orders', data=payload, content_type='application/json', HTTP_IDEMPOTENCY_KEY='pay-1', **headers)
        self.assertEqual(first.json()['code'], 0, first.json())
        order_no = first.json()['data']['order']['order_no']
        second = self.client.post('/api/v1/pay/orders', data=payload, content_type='application/json', HTTP_IDEMPOTENCY_KEY='pay-1', **headers)
        self.assertEqual(second.status_code, 409)
        notified = self.client.post(f'/api/v1/pay/orders/{order_no}/mock-notify', **headers)
        self.assertEqual(notified.json()['data']['status'], 'paid')

    def test_public_config_hot_update(self):
        _, headers = self.login()
        saved = self.client.post(
            '/api/v1/admin/settings/save',
            data=json.dumps({'key': 'h5_title', 'value': '新的标题'}),
            content_type='application/json',
            **headers,
        )
        self.assertEqual(saved.json()['code'], 0)
        public = self.client.get('/api/v1/config/public')
        self.assertEqual(public.json()['data']['settings']['h5_title'], '新的标题')

    def test_upload_checkin_survey(self):
        _, headers = self.login('zhangsan')
        uploaded = self.client.post(
            '/api/v1/files/upload',
            data={'file': SimpleUploadedFile('note.txt', b'hello')},
            **headers,
        )
        self.assertEqual(uploaded.json()['code'], 0, uploaded.json())
        checkin = self.client.post('/api/v1/plugins/checkin', **headers)
        self.assertEqual(checkin.json()['code'], 0)
        again = self.client.post('/api/v1/plugins/checkin', **headers)
        self.assertEqual(again.json()['code'], 400)
        surveys = self.client.get('/api/v1/plugins/surveys', **headers)
        survey_id = surveys.json()['data']['items'][0]['id']
        submitted = self.client.post(
            f'/api/v1/plugins/surveys/{survey_id}/submit',
            data=json.dumps({'answers': {'1': '浏览器'}}),
            content_type='application/json',
            **headers,
        )
        self.assertEqual(submitted.json()['code'], 0)

    def test_user_cannot_manage_users(self):
        _, headers = self.login('zhangsan')
        response = self.client.get('/api/v1/admin/users', **headers)
        self.assertEqual(response.status_code, 403)

    def test_tenant_admin_scope(self):
        _, headers = self.login('tenant')
        me = self.client.get('/api/v1/auth/me', **headers)
        self.assertEqual(me.json()['data']['scope'], 'tenant')
        users = self.client.get('/api/v1/admin/users', **headers)
        names = [item['username'] for item in users.json()['data']['items']]
        self.assertIn('zhangsan', names)
        self.assertNotIn('admin', names)
        denied = self.client.get('/api/v1/admin/tenants', **headers)
        self.assertEqual(denied.status_code, 403)
