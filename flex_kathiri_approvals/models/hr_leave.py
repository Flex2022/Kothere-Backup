from odoo import fields, models, api


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    employee_nationality = fields.Many2one('res.country', string='Nationality (country)',
                                           related="employee_id.country_id")
    needs_visa = fields.Boolean(string='Needs Visa')
    visa_for = fields.Selection([
        ('vacation', 'Vacation'),
        ('mission', 'Mission')
    ], string='Visa For', default="vacation")

    # @api.onchange('request_unit_half')
    # def request_unit_half(self):
    #     for leave in self:
    #         if leave.state == 'draft':
    #             if leave.request_unit_half:
    #                 leave.needs_visa = False

    def action_approve(self):
        res = super(HrLeave, self).action_approve()
        for leave in self:
            for employee_id in leave.employee_ids:
                self.env['flex.approval.exit_return_visa'].sudo().create({
                    'employee_id': employee_id.id,
                    'visa_for': leave.visa_for,
                    'visa_date_from': leave.request_date_from,
                    'visa_date_to': leave.request_date_to,
                    'company_id': leave.company_id.id,
                    'state': 'draft',
                    'leave_id': leave.id,
                })
        return res
