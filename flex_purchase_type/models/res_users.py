# -*- coding: utf-8 -*-
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    allowed_purchase_types = fields.Many2many(comodel_name='purchase.type', string='Allowed Purchase Type')
