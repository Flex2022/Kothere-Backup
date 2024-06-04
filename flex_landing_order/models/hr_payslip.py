from odoo import fields, models, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    reward_amount = fields.Monetary(string='Reward Amount', compute='_compute_reward_amount', store=True)

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_reward_amount(self):
        for rec in self:
            rec.reward_amount = 0
            landing_order = rec.env['landing.order'].search(
                [
                    ('driver_employee', '=', rec.employee_id.id),
                    ('delivery_date', '>=', rec.date_from),
                    ('delivery_date', '<=', rec.date_to),
                    ('state', '=', 'done'),
                ]
            )
            reward_amount = sum(landing_order.mapped('reward_amount'))
            self.reward_amount = reward_amount

    def update_reward_amount(self):
        for rec in self:
            rec.reward_amount = 0
            landing_order = rec.env['landing.order'].search(
                [
                    ('driver_employee', '=', rec.employee_id.id),
                    ('delivery_date', '>=', rec.date_from),
                    ('delivery_date', '<=', rec.date_to),
                    ('state', '=', 'done'),
                ],
            )
            reward_amount = sum(landing_order.mapped('reward_amount'))
            self.reward_amount = reward_amount