from odoo import api, fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    date_of_examination = fields.Date(string='Date of Examination', tracking=True)
    insurance_date = fields.Date(string='Insurance date', tracking=True)
    operation_date = fields.Date(string='Operation date', tracking=True)