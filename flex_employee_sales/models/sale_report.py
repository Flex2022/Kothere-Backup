from odoo import api, fields, models

class SaleReport(models.Model):
    _inherit = 'sale.report'

    sale_employee_id = fields.Many2one('hr.employee', string='Salesperson Employee')


    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['sale_employee_id'] = "s.sale_employee_id"
        return res


    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """,
            s.sale_employee_id"""
        return res

