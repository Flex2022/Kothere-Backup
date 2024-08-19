from odoo import api, fields, models


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'


    in_mode = fields.Selection(selection_add=[('other', 'Other')], string='In Mode')
    out_mode = fields.Selection(selection_add=[('other', 'Other')], string='Out Mode')