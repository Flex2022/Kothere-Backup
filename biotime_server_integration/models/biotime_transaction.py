from odoo import fields, models
from odoo import _


class BiotimeTransaction(models.Model):
    _name = 'biotime.transaction'
    _order = 'punch_time'

    server_id = fields.Many2one('biotime.server', string="Server Name")
    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_code = fields.Char(string="Employee Code")
    punch_state = fields.Selection([
        ('I', 'Check in'),
        ('O', 'Check out'),
        ('0', 'Check in'),
        ('1', 'Check out'),
        ('2', 'Break out'),
        ('3', 'Break in'),
        ('4', 'Overtime in'),
        ('5', 'Overtime out')
    ], string='Punch state')
    verify_type = fields.Selection([
        ('0', 'Password'),
        ('1', 'Fingerprint'),
        ('4', 'Card'),
        ('15', 'Face'),
        ('25', 'Palm')
    ], string='Verification Type')
    punch_time = fields.Datetime(string='Punching Time')
