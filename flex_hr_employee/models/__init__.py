from odoo import api, fields, models


class NewModule(models.Model):
    _inherit = 'hr.employee'

    mcj = fields.Char(string="MCJ")
    iqama_id = fields.Char(string="Iqama ID")
    end_of_iqama = fields.Date(string="End of Iqama")
