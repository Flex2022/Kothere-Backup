from odoo import api, fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    date_of_examination = fields.Date(string='Date of Examination', track_visibility='onchange')
    insurance_date = fields.Date(string='Insurance date', track_visibility='onchange')
    operation_date = fields.Date(string='Operation date', track_visibility='onchange')