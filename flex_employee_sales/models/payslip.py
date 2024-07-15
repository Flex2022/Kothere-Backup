from odoo import api, fields, models


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    total_sales = fields.Float(string='Total Sales Employee', compute='_compute_total_sales', store=True)
    total_all_sales = fields.Float(string='Total Sales', compute='_compute_all_total_sales', store=True)
    total_sale_quantity = fields.Float(string='Total Sale Quantity', compute='_compute_all_total_sales', store=True)

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

            all_invoice_based_on_date_range = self.env['account.move'].search(
                [
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
            total_sales_2 = 0
            if all_invoice_based_on_date_range:
                for invoice in all_invoice_based_on_date_range:
                    total_sales_2 += invoice.amount_total
            payslip.total_all_sales = total_sales_2

            total_sale_quantity = 0
            if all_invoice_based_on_date_range:
                for invoice in all_invoice_based_on_date_range:
                    lines = invoice.invoice_line_ids
                    for line in lines:
                        total_sale_quantity += line.quantity
            payslip.total_sale_quantity = total_sale_quantity




    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_all_total_sales(self):
        for payslip in self:
            all_invoice_for_employee = self.env['account.move'].search(
                [
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', payslip.date_from),
                    ('invoice_date', '<=', payslip.date_to)
                ]
            )

            total_sales = 0
            if all_invoice_for_employee:
                for invoice in all_invoice_for_employee:
                    total_sales += invoice.amount_total
            payslip.total_all_sales = total_sales

            total_sale_quantity = 0
            if all_invoice_for_employee:
                for invoice in all_invoice_for_employee:
                    lines = invoice.invoice_line_ids
                    for line in lines:
                        total_sale_quantity += line.quantity
            payslip.total_sale_quantity = total_sale_quantity