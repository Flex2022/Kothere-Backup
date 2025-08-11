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
    location_latitude = fields.Float(string='Location Latitude', tracking=True)
    location_longitude = fields.Float(string='Location Longitude', tracking=True)
    check_location_attendances = fields.Boolean(string='Check Location Attendances', default=False, tracking=True)
    location_range = fields.Float(string='Range m', default=150.0, tracking=True)

    _sql_constraints = [
        ('unique_api_username', 'UNIQUE(api_username)', 'Username must be unique!'),
    ]

    def get_location_link(self):
        self.ensure_one()
        if self.location_latitude and self.location_longitude:
            return f"https://www.google.com/maps/search/?api=1&query={self.location_latitude},{self.location_longitude}"
        else:
            raise UserError(_("Location not set for this employee."))

    def open_location_link_in_new_tab(self):
        self.ensure_one()
        location_link = self.get_location_link()
        if not location_link:
            raise UserError(_("Location not set for this employee."))
        return {
            'type': 'ir.actions.act_url',
            'url': location_link,
            'target': 'new',
        }

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

    def send_app_notification(self, title='HR Notification', message='', model_name=False, res_id=0):
        self._employee_notify(title=title, message=message, model_name=model_name, res_id=res_id)
        # now = fields.Datetime.now()
        # huawei_client_id = self.env["ir.config_parameter"].sudo().get_param("huawei_client_id")
        # huawei_client_secret = self.env["ir.config_parameter"].sudo().get_param("huawei_client_secret")
        # android_server_key = self.env["ir.config_parameter"].sudo().get_param("android_server_key")
        # for employee in self:
        #     sendable_tokens = employee.token_ids.filtered(lambda t: t.device_token and t.date_expiry > now)
        #     huawei_tokens = sendable_tokens.filtered(lambda p: p.is_huawei)
        #     android_tokens = sendable_tokens - huawei_tokens
        #     if huawei_client_id and huawei_client_secret:
        #         if huawei_tokens:
        #             huawei_tokens._send_huawei_notification(huawei_client_id, huawei_client_secret, title, body)
        #     else:
        #         _logger.info("\nCouldn't send huawei notification because huawei_client_id or huawei_client_secret not set in system parameters")
        #     if android_server_key:
        #         if android_tokens:
        #             android_tokens._send_android_notification(android_server_key, title, body, model_name=model_name, res_id=res_id)
        #     else:
        #         _logger.info("\nCouldn't send android notification because android_server_key not set in system parameters")

