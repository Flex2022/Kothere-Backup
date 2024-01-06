from odoo import models, fields, _
from odoo.exceptions import ValidationError


class PosSession(models.Model):
    _inherit = "pos.session"

    inventory_count_id = fields.Many2one("setu.stock.inventory.count", string="Inventory Count")

    def action_pos_session_closing_control(self):
        for rec in self:
            # orders = rec.order_ids.filtered(lambda x: x.state not in ('draft', 'cancel'))
            # products = orders.mapped("lines.product_id").filtered(lambda x: x.detailed_type == 'product')
            if not (rec.sudo().inventory_count_id and rec.sudo().inventory_count_id.state == 'Approved'):
                raise ValidationError(_("Inventory Count has not been conducted for this session, please create and "
                                        "complete it first and try to submit the session."))
        return super().action_pos_session_closing_control()

    def create_count_from_session_end(self):
        self.ensure_one()
        products = self.env['product.product'].sudo().search([('detailed_type', '=', 'product')])
        orders = self.order_ids.filtered(lambda x: x.state not in ('draft', 'cancel'))
        operation_type_id = self.config_id.picking_type_id
        warehouse_id = operation_type_id and operation_type_id.warehouse_id
        # products = orders.mapped("lines.product_id").filtered(lambda x: x.detailed_type == 'product')
        products = products.filtered(lambda x: x.with_context(location=warehouse_id.lot_stock_id.id).qty_available > 0)
        if not products:
            raise ValidationError(_("No Products has been sold in this session."))
        # products = orders.mapped("lines.product_id")

        if not warehouse_id:
            raise ValidationError(_("No Warehouse Found for this session."))
        data = {}
        auto_inventory = self.env['inventory.count.settings'].sudo().search([])
        users = auto_inventory.session_user_ids.ids
        if not users:
            users = self.user_id.ids
        for product in products:
            record = {'product_id': product.id,
                      'location_id': warehouse_id.lot_stock_id.id}
            if warehouse_id.id in data:
                data[warehouse_id.id].append(record)
            else:
                data[warehouse_id.id] = [record]
        count_ids = self.env['setu.stock.inventory.count'].sudo().with_context(from_pos_session=True).auto_create_inventory_count_as_per_configuration(data, auto_inventory, users)
        self.sudo().write({'inventory_count_id': count_ids and count_ids[0]})
        return True

    def show_inv_count(self):
        return {
            'name': _('Inventory Count'),
            'type': 'ir.actions.act_window',
            'res_model': 'setu.stock.inventory.count',
            'view_mode': 'form',
            'res_id': self.inventory_count_id.id
        }

