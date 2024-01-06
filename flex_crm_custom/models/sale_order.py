from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('opportunity_id')
    def onchange_opportunity_id(self):
        for order in self:
            if order.opportunity_id and order.state == 'draft' and not order.order_line:
                new_order_lines = []
                for line in self.opportunity_id.order_line_ids:
                    new_order_line = self._prepare_order_line(line)
                    new_order_lines.append((0, 0, new_order_line))

                # Set the sale order lines in the result dictionary
                order.order_line = new_order_lines

    def _prepare_order_line(self, lead_line):
        return {
            'product_id': lead_line.product_id.id,
            'name': lead_line.name,
            'analytic_distribution': lead_line.analytic_distribution,
            'tax_id': [(6, 0, lead_line.tax_ids.ids)],
            'discount': lead_line.discount,
            'product_uom_qty': lead_line.quantity,
            'product_uom': lead_line.product_uom.id,
            'price_unit': lead_line.price_unit,
            'price_subtotal': lead_line.price_subtotal,
            'price_total': lead_line.price_total,
            'tax_country_id': lead_line.tax_country_id.id,
            # Add other fields as needed
        }
