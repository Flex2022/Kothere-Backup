from odoo import api, fields, models

AVAILABLE_PRIORITIES = [
    ('0', 'Normal'),
    ('1', 'Good'),
    ('2', 'Very Good'),
    ('3', 'Excellent')
]


class EvaluationRate(models.Model):
    _name = 'evaluation.rate'
    _description = 'Evaluation'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Evaluation', default='0')


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    evaluation_rate = fields.One2many('evaluation.applicant', 'hr_application', string='Evaluation Rate')


class EvaluationApplicant(models.Model):
    _name = 'evaluation.applicant'
    _description = 'Evaluation Applicant'
    _rec_name = 'evaluation_rate'

    evaluation_rate = fields.Many2one('evaluation.rate', string='Evaluation Name', required=True)
    hr_application = fields.Many2one('hr.applicant', string='HR Application')
    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Evaluation', related='evaluation_rate.priority',
                                readonly=False, store=True)
