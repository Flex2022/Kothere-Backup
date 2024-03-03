# -*- coding: utf-8 -*-
import os
from odoo import models, fields, api
from datetime import timedelta
import hashlib


class HrToken(models.Model):
    _name = "hr.token"
    _description = "HR Access Token"

    @api.model
    def _token(self, length=40, prefix="token"):
        rbytes = os.urandom(length)
        return f"{prefix}{hashlib.sha1(rbytes).hexdigest()}"

    @api.model
    def _expiry(self):
        return fields.Datetime.now() + timedelta(seconds=300000000)

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=True)
    token = fields.Char(string="Access Token", required=True, default=lambda s: s._token())
    date_expiry = fields.Datetime(string="Valid Until", required=True, default=lambda s: s._expiry())

    @api.model
    def get_valid_token(self, employee_id=False, create=False):
        if not employee_id:
            return False
        now = fields.Datetime.now()
        access_token = self.sudo().search([('employee_id', '=', employee_id), ('date_expiry', '>', now)], order="id DESC", limit=1)
        if access_token:
            return access_token[0].token
        elif create:
            return self.sudo().create({"employee_id": employee_id}).token
        return False

    def _update_token(self):
        self.ensure_one()
        self.sudo().write({"token": self._token(), "date_expiry": self._expiry()})
        return self.token

