# -*- coding: utf-8 -*-
import os
from odoo import models, fields, api
from datetime import timedelta
import hashlib
import json
import requests
import logging
_logger = logging.getLogger(__name__)


class HrToken(models.Model):
    _name = "hr.token"
    _description = "HR Access Token"

    @api.model
    def _token(self, length=40, prefix="token"):
        rbytes = os.urandom(length)
        return f"{prefix}{hashlib.sha1(rbytes).hexdigest()}"

    @api.model
    def _expiry(self):
        return fields.Datetime.now() + timedelta(seconds=3000)

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=True)
    token = fields.Char(string="Access Token", required=True, default=lambda s: s._token())
    device_token = fields.Text(string="Device Token")
    is_huawei = fields.Boolean(string="Huawei")
    date_expiry = fields.Datetime(string="Valid Until", required=True, default=lambda s: s._expiry())

    @api.model
    def get_valid_token(self, employee_id=False, device_token=False, create=False):
        _logger.info(f"device_token: {device_token}")
        if not employee_id:
            return False
        now = fields.Datetime.now()
        domain = [('employee_id', '=', employee_id), ('date_expiry', '>', now)]
        if device_token:
            domain += [('device_token', '=', device_token)]
        access_token = self.sudo().search(domain, order="id DESC", limit=1)
        if access_token:
            return access_token[0].token
        elif create:
            return self.sudo().create({"employee_id": employee_id, "device_token": device_token}).token
        return False

    def _update_token(self):
        self.ensure_one()
        self.sudo().write({"token": self._token(), "date_expiry": self._expiry()})
        return self.token

    # =========================[ Notifications ]=========================
    def _send_huawei_notification(self, huawei_client_id, huawei_client_secret, title, body):
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
            return False
        web_base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        access_token = response.json().get('access_token')
        # "Content-Type": "application/x-www-form-urlencoded",
        data = {}
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
                    "body": body
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
                "token": self.mapped('device_token')  # in hr.employee we filtered huawei tokens
            }
        }
        url = f"https://push-api.cloud.huawei.com/v1/{huawei_client_id}/messages:send"
        response = requests.post(url, headers=headers, data=json.dumps(body))
        if response.status_code != 200:
            _logger.info(f"\nCouldn't send huawei notification ({response.text})")
            return False
        # self.env['user.notifications'].create([{
        #     'user_id': p.id,
        #     'name': self.name,
        #     'body': self.body,
        #     'date': datetime.datetime.now(),
        #     'action_data': json.dumps(data),
        # } for p in partners_with_device_token])
        return True

    def _send_android_notification(self, android_server_key, title, body, model_name=False, res_id=0):
        request_headers = {
            'Content-Type': 'application/json',
            'Authorization': f"key={android_server_key}",
        }
        for token in self.filtered('device_token'):
            request_body = {
                'notification': {
                    'title': title,
                    'body': body
                },
                "data": {},
                'to': token.device_token,
                'priority': 'high',
            }
            response = requests.post("https://fcm.googleapis.com/fcm/send", headers=request_headers, data=json.dumps(request_body))
            if response.status_code == 200:
                if response.json()['success'] == 1:
                    self.env['hr.notify'].sudo().create({
                        'employee_id': token.employee_id.id,
                        'name': title,
                        'body': body,
                        'date': fields.Datetime.now(),
                        'model_name': model_name,
                        'res_id': res_id,
                    })
                else:
                    _logger.info(f"\nCouldn't send android notification - not success - ({response.text})")
            else:
                _logger.info(f"\nCouldn't send android notification ({response.text})")
        return True



