# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    flex_employee_resignation_request_approval_type = fields.Many2one(
        'approval.category',
        string='Approval Category for Resignation Request',
        help='Select the approval category for handling resignation requests.',
    )
