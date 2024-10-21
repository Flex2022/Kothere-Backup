from odoo import api, fields, models

class Project(models.Model):
    _inherit = 'project.project'


    project_number = fields.Char(string='Project Number')
    project_owner = fields.Many2one('res.partner', string='Project Owner')
    contact_value = fields.Monetary(string='Contact Value')
    expected_dry_cost = fields.Monetary(string='Expected Dry Cost')
    preliminaries = fields.Monetary(string='Preliminaries')
    contingency_reserve = fields.Monetary(string='Contingency reserve')
    expected_salaries = fields.Monetary(string='Expected Salaries')
    expected_net_profit = fields.Monetary(string='Expected Net Profit')


