from odoo import api, fields, models


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    total_sales = fields.Float(string='Total Sales', compute='_compute_total_sales', store=True)
    # invoice_ids = fields.Many2many('account.move', string='Invoices', compute='get_all_invoice_for_employee',
    #                                store=True)

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_total_sales(self):
        for payslip in self:
            all_invoice_for_employee = self.env['account.move'].search(
                [
                    ('sale_employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', payslip.date_from),
                    ('invoice_date', '<=', payslip.date_to)
                ]
            )

            total_sales = 0
            if all_invoice_for_employee:
                for invoice in all_invoice_for_employee:
                    total_sales += invoice.amount_total
            payslip.total_sales = total_sales


    def update_sale_total(self):
        for payslip in self:
            all_invoice_for_employee = self.env['account.move'].search(
                [
                    ('sale_employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', payslip.date_from),
                    ('invoice_date', '<=', payslip.date_to)
                ]
            )

            total_sales = 0
            if all_invoice_for_employee:
                for invoice in all_invoice_for_employee:
                    total_sales += invoice.amount_total
            payslip.total_sales = total_sales