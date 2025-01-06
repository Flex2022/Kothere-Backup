from odoo import api, fields, models


class NewModule(models.Model):
    _inherit = 'hr.employee'

    mcj = fields.Char(string="MCJ")
    iqama_id = fields.Char(string="Iqama ID")
    end_of_iqama = fields.Date(string="End of Iqama")

    type_of_insurance = fields.Char(string="Type Of Insurance")
    bank_name = fields.Char(string="Bank")
    bank_number = fields.Char(string="Bank Number")
    identification_expiry = fields.Date(string="Identification Expiry")
    passport_expiry = fields.Date(string="Passport Expiry")
