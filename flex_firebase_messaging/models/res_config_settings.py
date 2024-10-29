# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    firebase_key_file = fields.Binary(string='Firebase Private Key')
    firebase_project_key = fields.Char(string='Firebase Project ID')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    firebase_key_file = fields.Binary(
        string='Firebase Private Key',
        related='company_id.firebase_key_file',
        readonly=False,
    )
    firebase_project_key = fields.Char(
        string='Firebase Project ID',
        related='company_id.firebase_project_key',
        readonly=False,
    )
