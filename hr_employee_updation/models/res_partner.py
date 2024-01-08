# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    signup_token = fields.Char(copy=False, groups="base.group_erp_manager,hr.group_hr_manager")
    signup_type = fields.Char(string='Signup Token Type', copy=False, groups="base.group_erp_manager,hr.group_hr_manager")
    signup_expiration = fields.Datetime(copy=False, groups="base.group_erp_manager,hr.group_hr_manager")
