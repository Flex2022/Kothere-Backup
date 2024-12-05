from odoo import api, fields, models, _


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    requisition_purchase_ids = fields.One2many(
        'material.purchase.requisition',
        'repair_id',
        string="Requisition Purchases",
        help="List of related material purchase requisitions for this repair order."
    )



    def action_view_purchase_requisitions(self):
        """Opens a tree and form view for material purchase requisitions associated with this repair order."""
        return {
            'name': _('Requisition Purchase Orders'),
            'domain': [('id', 'in', self.requisition_purchase_ids.ids)],
            'view_mode': 'tree,form',
            'res_model': 'material.purchase.requisition',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_repair_id' : self.id,
                'default_requisition_type' : 'buy'
            },
        }


class MaterialRequisitionPurchase(models.Model):
    _inherit = 'material.purchase.requisition'

    repair_id = fields.Many2one(
        'repair.order',
        string="Repair Order",
        help="The repair order related to this material purchase requisition."
    )

class StockMoves(models.Model):
    _inherit = 'stock.move'

    # New fields related to repair order
    repair_vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', related="repair_id.vehicle_id", store=True)
    repair_license_plate = fields.Char(string='License Plate', related="repair_id.license_plate")
    repair_driver_id = fields.Many2one('res.partner', string='Driver', related="repair_id.driver_id")
    repair_maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance Request', related="repair_id.maintenance_request_id")
    repair_product_id = fields.Many2one('product.product', string='Product to Repair', related="repair_id.product_id")
    product_valuation = fields.Monetary(
        string="Product Valuation",
        compute='_compute_product_valuation',
        currency_field='product_valuation_currency_id',
        store=True,
        help="Latest valuation for the product based on stock valuation layers."
    )
    product_valuation_currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        compute='_compute_product_valuation',
        store=True,
        help="Currency of the product valuation"
    )

    @api.depends('product_id', 'repair_id.state')
    def _compute_product_valuation(self):
        for order in self:
            # Ensure there's a product_id and avoid unnecessary searches if no product exists
            if order.product_id:
                # Get the latest stock valuation layer for each product_id related to the repair order
                latest_valuation = self.env['stock.valuation.layer'].search(
                    [('product_id', '=', order.product_id.id)],
                    order='create_date desc',
                    limit=1
                )

                if latest_valuation:
                    # Set the product valuation as the value of the most recent stock valuation layer
                    order.product_valuation = latest_valuation.value
                    # Set the currency to the same as the stock valuation layer's currency
                    order.product_valuation_currency_id = latest_valuation.currency_id
                else:
                    order.product_valuation = 0.0
                    order.product_valuation_currency_id = self.env.company.currency_id  # default to company currency
            else:
                order.product_valuation = 0.0
                order.product_valuation_currency_id = self.env.company.currency_id  # default to company currency