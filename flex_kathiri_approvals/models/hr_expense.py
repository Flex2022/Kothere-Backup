from odoo import models, fields


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    flex_approval_resignation_id = fields.Many2one('flex.approval.resignation', string='Employee Resignation',
                                                   copy=False)
    flex_approval_transfer_id = fields.Many2one('flex.approval.employee_transfer', string='Employee Transfer',
                                                copy=False)
    flex_approval_iqama_id = fields.Many2one('flex.approval.renew_iqama', string='Employee Transfer', copy=False)
    flex_approval_business_trip_id = fields.Many2one('flex.approval.business_trip', string='Employee Transfer',
                                                     copy=False)

    flex_approval_medical_insurance_id = fields.Many2one('flex.approval.renew_medical_insurance',
                                                         string='Employee medical insurance',
                                                         copy=False)
    flex_approval_exit_return_visa_id = fields.Many2one('flex.approval.exit_return_visa',
                                                        string='Employee Exit Return Visa',
                                                        copy=False)

    flex_approval_renew_driving_license_id = fields.Many2one('flex.approval.renew_driving_license',
                                                             string='Employee renewal driving license',
                                                             copy=False)
