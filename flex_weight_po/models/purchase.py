from odoo import api, fields, models

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    weight_po = fields.Many2one('flex.purchase.weight', string="Weight PO")
    # truck_no = fields.Many2one('fleet.vehicle', string='Truck No')
    # temperature = fields.Integer(string="Temperature°C")
    # driver_id = fields.Many2one('flex.driver.details', string="Driver")
    # remarks_open = fields.Boolean(string="Acknowledgement")
    # remarks = fields.Text(string="Acknowledge",
    #                       default='I have received the above goods in good quality & above weight')
    its_weight = fields.Boolean(string="Weight PO", default=False)
    weight_po_count = fields.Integer(string="Weight PO Count", compute='_compute_weight_po_count')

    @api.depends('weight_po')
    def _compute_weight_po_count(self):
        for rec in self:
            rec.weight_po_count = self.env['flex.purchase.weight'].search_count([('po_number', '=', rec.id)])

    def action_view_weight_po(self):
        action = self.env.ref('flex_weight_po.action_po_weight_management_view').read()[0]
        action['domain'] = [('po_number', '=', self.id)]
        action['context'] = {'create': False}
        return action



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    weight = fields.Float(string="First Weight", help="Weight in K.G", tracking=True, required=False)
    weight1 = fields.Float(string="Second Weight", help="Weight in ", tracking=True, required=False)
