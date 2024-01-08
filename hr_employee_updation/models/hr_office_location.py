# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.addons.base.models.res_partner import _tz_get


class HrOfficeLocation(models.Model):
    _name = 'hr.employee.office.location'
    _description = 'Hr Employee Office Location Management'

    name = fields.Char(string='Name', copy=False, help="Name")
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one('res.country.state', string='State', required=True)
    company_id = fields.Many2one('res.company', 'Company', help="Company", default=lambda self: self.env.user.company_id)
    resource_calendar_id = fields.Many2one('resource.calendar', 'Working Schedule', copy=False, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    tz = fields.Selection(_tz_get, string='Timezone', required=True)
    contract_notification_before = fields.Integer('Expiry Contract alert Before (Day)')
    allocation_per_year = fields.Integer('Yearly Leave Allocation (Day)')
    request_leave_before = fields.Integer('Request Leave before (Day)')
    allow_minus_leave = fields.Boolean('Allow Minus Leave?')
    calculate_weekend = fields.Boolean('Weekend within leave?')
    allow_send_allocation_email = fields.Boolean('Allow Allocation Email?')
    financial_resignation = fields.Boolean('Financial Resignation?')
    number_of_minus_leave = fields.Integer('Number of Minus Leave')

    _sql_constraints = [('name_uniq', 'unique(name)', _('Office name should be unique!'))]
