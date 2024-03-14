from odoo import api, fields, models


class Invoice(models.Model):
    _inherit = 'account.move'

    po_number = fields.Many2one('purchase.order', string='PO Order')
    # po_date = fields.Date(string='PO Date', related='po_number.date_order', store=True)
