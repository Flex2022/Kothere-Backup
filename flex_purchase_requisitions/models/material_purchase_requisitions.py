from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

class MaterialPurchaseRequisitions(models.Model):
    _inherit = 'material.purchase.requisition'

    @api.onchange('custom_picking_type_id')
    def _get_deafult_location_id_and_dest_location_id(self):
        for rec in self:
            rec.location_id = rec.custom_picking_type_id.default_location_src_id.id
            rec.dest_location_id = rec.custom_picking_type_id.default_location_dest_id.id