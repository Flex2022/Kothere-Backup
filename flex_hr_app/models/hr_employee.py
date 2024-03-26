# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import json
import requests
import logging
_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    api_username = fields.Char(string='Username', groups='hr.group_hr_user')
    api_password = fields.Char(string='Password', groups='hr.group_hr_user')
    token_ids = fields.One2many(comodel_name="hr.token", inverse_name='employee_id', string="Tokens")

    _sql_constraints = [
        ('unique_api_username', 'UNIQUE(api_username)', 'Username must be unique!'),
    ]

    def _get_employee_timeoff_data(self):
        self.ensure_one()
        return self.env['hr.leave.type'].with_company(self.company_id).with_context(employee_id=self.id).get_allocation_data_request()

    def action_view_hr_token(self):
        return {
            'name': _('Access Tokens'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.token',
            'view_mode': 'tree,form',
            'domain': [('employee_id', 'in', self.ids)],
            'target': 'current',
        }

    def action_view_hr_notify(self):
        return {
            'name': _('App Notification'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.notify',
            'view_mode': 'tree,form',
            'domain': [('employee_id', 'in', self.ids)],
            'target': 'current',
        }

    def send_app_notification(self, title='HR Notification', body='', model_name=False, res_id=0):
        now = fields.Datetime.now()
        huawei_client_id = self.env["ir.config_parameter"].sudo().get_param("huawei_client_id")
        huawei_client_secret = self.env["ir.config_parameter"].sudo().get_param("huawei_client_secret")
        # android_server_key = self.env["ir.config_parameter"].sudo().get_param("android_server_key")
        # huawei_client_id = "-109269039"
        # huawei_client_secret = "-6324a22e3908f311ae1b607f70a9234af995df914c36dca4aa7596e8f3c55f25"
        # android_server_key = 'key=AAAAbZxgcqI:APA91bFvDOvPzREQo6gZEgqqTAOEm1aW6TIGwfwpPaXnB9uPuU_CSjFGjQ6LiXR2NSJKTPmFrP-OXwGjka5DA71_WOEoiXaYwort_C-QYyniPP8nrw2HUHrcGOwKHRAwRXz_KaiQFTg8'
        android_server_key = 'key=AAAAlvQMTqw:APA91bHEVyopYSrqwhJ0EVRgFP1BgMOrSXmGi_sUyjKCdBWCgNau8OyJJu5dT5GAtE7jMh1WRNvxr2R0e67pzMzl6_9DGy7Wtx2BqRuoF2cqQXBtu2-C4TAy0CHPB1vT9oU5ELellcy0'

        for employee in self:
            sendable_tokens = employee.token_ids.filtered(lambda t: t.device_token and t.date_expiry > now)
            huawei_tokens = sendable_tokens.filtered(lambda p: p.is_huawei)
            android_tokens = sendable_tokens - huawei_tokens
            if huawei_client_id and huawei_client_secret:
                if huawei_tokens:
                    huawei_tokens._send_huawei_notification(huawei_client_id, huawei_client_secret, title, body)
            else:
                _logger.info("\nCouldn't send huawei notification because huawei_client_id or huawei_client_secret not set in system parameters")
            if android_server_key:
                if android_tokens:
                    android_tokens._send_android_notification(android_server_key, title, body, model_name=model_name, res_id=res_id)
            else:
                _logger.info("\nCouldn't send android notification because android_server_key not set in system parameters")

