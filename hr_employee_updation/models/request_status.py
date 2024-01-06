# -*- coding: utf-8 -*-

from odoo import fields, models


class HRRequestStatus(models.Model):
    _name = 'hr.request.status'
    _description = 'Hr Request Status'

    name = fields.Char(string='Name', copy=False, help="Name", translate=True)
