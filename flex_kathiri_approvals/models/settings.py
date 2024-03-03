# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    flex_employee_resignation_request_approval_type = fields.Many2one(
        'approval.category',
        string='Approval Category for Resignation Request',
        related='company_id.flex_employee_resignation_request_approval_type',
        readonly=False,
        help='Select the approval category for handling resignation requests.',
    )
