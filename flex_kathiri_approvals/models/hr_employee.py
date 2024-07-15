from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    medical_insurance_id = fields.One2many('flex.approval.renew_medical_insurance', 'employee_id',
                                           string='Medical Insurance')
    medical_insurance_sponsored_ids = fields.One2many('flex.approval.renew_medical_insurance.sponsored', 'employee_id')


