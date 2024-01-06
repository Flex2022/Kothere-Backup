from odoo import api, fields, models


class Requisitions(models.Model):
    _inherit = 'material.purchase.requisition'

    requisition_type = fields.Selection(
        string='Requisition Type',
        selection=[('buy', 'Buy'),
                   ('internal_picking', 'Internal Picking'),
                   ('sample', 'Sample')],
        required=False)

    @api.onchange('requisition_type')
    def _chech_if_the_user_have_access_to_the_requisition_type(self):
        for rec in self:
            if rec.requisition_type == 'buy':
                if self.env.user.has_group('flex_material_purchase_requisitions.flex_material_purchase_requisitions_buy'):
                    pass
                else:
                    rec.requisition_type = False
                    return {'warning': {
                        'title': 'Warning!',
                        'message': 'You do not have access to this requisition type',
                    }}
            elif rec.requisition_type == 'internal_picking':
                if self.env.user.has_group('flex_material_purchase_requisitions.flex_material_purchase_requisitions_internal'):
                    pass
                else:
                    rec.requisition_type = False
                    return {'warning': {
                        'title': 'Warning!',
                        'message': 'You do not have access to this requisition type',
                    }}
            elif rec.requisition_type == 'sample':
                if self.env.user.has_group('flex_material_purchase_requisitions.flex_material_purchase_requisitions_sample'):
                    pass
                else:
                    rec.requisition_type = False
                    return {'warning': {
                        'title': 'Warning!',
                        'message': 'You do not have access to this requisition type',
                    }}



class RequisitionsLine(models.Model):
    _inherit = 'material.purchase.requisition.line'

    requisition_type = fields.Selection(
        selection=[
            ('internal', 'Internal Picking'),
            ('purchase', 'Purchase Order'),
        ],
        deafult='internal',
        string='Requisition Action',
        required=True,
    )

    @api.onchange('requisition_type')
    def onchange_requisition_type(self):
        for rec in self:
            if rec.requisition_id.requisition_type == 'buy':
                rec.requisition_type = 'purchase'
            elif rec.requisition_id.requisition_type == 'internal_picking':
                rec.requisition_type = 'internal'
            elif rec.requisition_id.requisition_type == 'sample':
                rec.requisition_type = 'internal'
            else:
                rec.requisition_type = 'internal'