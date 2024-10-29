# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
import json
import requests
import argparse
import tempfile
import binascii
import google.auth.transport.requests
from google.oauth2 import service_account
import logging
_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _get_firebase_access_token(self):
        """Retrieve a valid access token that can be used to authorize requests.
        :return: Access token.
        """
        SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']
        company = self.company_id or self.env.company
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        fp.write(binascii.a2b_base64(company.firebase_key_file))
        fp.seek(0)
        credentials = service_account.Credentials.from_service_account_file(fp.name, scopes=SCOPES)
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        print(f"company: {company}")
        print(f"project_id: {company.firebase_project_key}")
        print(f"token: {credentials.token}")
        return company.firebase_project_key, credentials.token

    def _send_fcm_message(self, fcm_message, project_id, access_token):
        """Send HTTP request to FCM with given message.
        Args:
          fcm_message: JSON object that will make up the body of the request.
        """
        BASE_URL = 'https://fcm.googleapis.com'
        FCM_ENDPOINT = 'v1/projects/' + project_id + '/messages:send'
        FCM_URL = BASE_URL + '/' + FCM_ENDPOINT
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json; UTF-8',
        }
        try:
            resp = requests.post(FCM_URL, data=json.dumps(fcm_message), headers=headers)
            if resp.status_code == 200:
                _logger.info('Message sent to Firebase for delivery, response:')
                _logger.info(resp.text)
                # print('Message sent to Firebase for delivery, response:')
                # print(resp.text)
                return True
            else:
                _logger.info('Unable to send message to Firebase')
                _logger.info(resp.text)
                # print('Unable to send message to Firebase')
                # print(resp.text)
                return False
        except:
            return False

    def _employee_notify(self, title='', message='', **kw):
        sent = 0
        for employee in self:
            sent += employee._employee_notify_android(title, message, **kw)
            sent += employee._employee_notify_huawei(title, message, **kw)
        return sent

    def _employee_notify_android(self, title='', message='', **kw):
        try:
            project_id, token = self._get_firebase_access_token()
        except:
            return 0
        sent = 0
        for employee in self:
            is_sent = False
            # target_device_tokens = list(set(partner.app_tokens.filtered(lambda t: not t.is_huawei).mapped('device_token')))
            target_device_tokens = list(
                set(
                    employee.token_ids.filtered(
                        lambda t: not t.is_huawei and t.date_expiry > fields.Datetime.now()
                    ).mapped('device_token')
                )
            )
            for device_token in target_device_tokens:
                action_data = kw.get('action_data', '{}')
                body = {
                    'message': {
                        'notification': {
                            'title': title,
                            'body': message,
                            # 'body': 'With us, make your orders easily'
                        },
                        "data": {k: str(v) for k, v in json.loads(action_data).items()},
                        'token': device_token,
                    }
                }
                is_sent = self._send_fcm_message(body, project_id, token) or is_sent
            if is_sent:
                sent += 1
                _logger.info(f"Notification sent to {employee.name}")
                self.env['hr.notify'].sudo().create({
                    'employee_id': employee.id,
                    'name': title,
                    'body': message,
                    'date': fields.Datetime.now(),
                    # 'model_name': model_name,
                    # 'res_id': res_id,
                    **kw
                })
        return sent

    def _employee_notify_huawei(self, title='', message='', **kw):
        huawei_client_id = self.env["ir.config_parameter"].sudo().get_param("huawei_client_id")
        huawei_client_secret = self.env["ir.config_parameter"].sudo().get_param("huawei_client_secret")
        if not (huawei_client_id and huawei_client_secret):
            return 0
        huawei_token_headers = {
            "Host": "oauth-login.cloud.huawei.com",
            "POST": "/oauth2/v3/token   HTTP/1.1",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        huawei_token_body = {
            "grant_type": "client_credentials",
            "client_id": huawei_client_id,
            "client_secret": huawei_client_secret
        }
        token_url = "https://oauth-login.cloud.huawei.com/oauth2/v3/token"
        response = requests.post(token_url, headers=huawei_token_headers, data=huawei_token_body)
        if response.status_code != 200:
            return 0
        access_token = response.json().get('access_token')
        sent = 0
        for employee in self:
            # target_device_tokens = list(set(partner.app_tokens.filtered('is_huawei').mapped('device_token')))
            target_device_tokens = list(
                set(
                    employee.token_ids.filtered(
                        lambda t: t.is_huawei and t.date_expiry > fields.Datetime.now()
                    ).mapped('device_token')
                )
            )
            if len(target_device_tokens) < 1:
                continue
            # action_data = kw.get('action_data', '{}')
            # data = {k: str(v) for k, v in json.loads(action_data).items()}
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Host": "oauth-login.cloud.huawei.com",
                "POST": "/oauth2/v3/token   HTTP/1.1",
            }
            body = {
                "validate_only": False,
                "message": {
                    "notification": {
                        "title": title,
                        "body": message
                    },
                    "android": {
                        "notification": {
                            "click_action": {
                                "type": 1,
                                "intent": "intent://com.huawei.codelabpush/deeplink?#Intent;scheme=pushscheme;launchFlags=0x04000000;i.age=180;S.name=abc;end",
                                "url": ""
                            }
                        }
                    },
                    "token": target_device_tokens
                }
            }
            url = f"https://push-api.cloud.huawei.com/v1/{huawei_client_id}/messages:send"
            response = requests.post(url, headers=headers, data=json.dumps(body))
            if response.status_code != 200:
                continue
            sent += 1
            self.env['hr.notify'].sudo().create({
                'employee_id': employee.id,
                'name': title,
                'body': message,
                'date': fields.Datetime.now(),
                # 'model_name': model_name,
                # 'res_id': res_id,
                **kw
            })
        return sent

