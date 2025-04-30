from odoo import api, fields, models

class DriverDetails(models.Model):
    _name = "flex.driver.details"

    name = fields.Char(string="Driver Name")
    driver_license = fields.Char(string="Driver License No")
    native = fields.Many2one('res.country', string="Nationality")