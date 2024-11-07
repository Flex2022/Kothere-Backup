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
