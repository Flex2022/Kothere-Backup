from odoo import models, fields


class HrJob(models.Model):
    _inherit = 'hr.job'

    approval_job_id = fields.Many2one('approval.request', string='Approval Request')
