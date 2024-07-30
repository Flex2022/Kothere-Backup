from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    partner_id = fields.Many2one('res.partner', string="Partner", default=lambda self: self.move_id.partner_id)

    def get_partner_values(self):
        self.partner_id = self.move_id.partner_id
