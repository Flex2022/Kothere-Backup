from odoo import models, api, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    department_id = fields.Many2one('hr.department')
    attention = fields.Char('Attention')

    tac_en_delivery_location = fields.Char('Delivery Location (English)', placeholder="Delivery location (English)")
    tac_ar_delivery_location = fields.Char('Delivery Location (Arabic)', placeholder="مككان التسليم باللغة العربية")



    # sale_order_cancel_reason.py
    def action_cancel(self):
        # Call the original cancel action
        result = super(SaleOrder, self).action_cancel()

        # Open your custom wizard
        return {
            'name': 'Cancel Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.cancel.reason.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('flex_sale.view_sale_order_cancel_reason_wizard').id,
            'context': {
                'default_order_id': self.id,
            },
            'target': 'new',
        }

    def action_confirm(self):
        # Call the original confirm action
        result = super(SaleOrder, self).action_confirm()

        #transfer trilla_load_per_pill to stock move
        for line in self.order_line:
            for move in line.move_ids:
                move.trilla_load_per_pill = line.trilla_load_per_pill
        return result


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_id_arabic = fields.Char(string='Arabic Name', compute="compute_product_id_arabic")
    trilla_load_per_pill = fields.Char('Trilla load per pill')

    @api.depends('product_id')
    def compute_product_id_arabic(self):
        for line in self:
            line.product_id_arabic = line.product_id.with_context(lang='ar_001').name

