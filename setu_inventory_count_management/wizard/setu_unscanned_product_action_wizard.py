from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class SetuUnscannedProductActionWizard(models.TransientModel):
    _name = 'setu.unscanned.product.action.wizard'
    _description = "setu unscanned product action wizard"

    unscanned_product_line_ids = fields.Many2many('setu.unscanned.product.lines', 'unscanned_product_lines_rel',
                                                  string="Unscanned Product Lines")
    action = fields.Selection(
        [('make_it_0', 'Make It Zero'), ('do_nothing', ' Do Nothing')])

    def action_open_wizard(self):
        records = self.env['setu.unscanned.product.lines'].browse(self.env.context.get('active_ids', []))
        action = {
            'name': 'Unscanned Products',
            'type': 'ir.actions.act_window',
            "view_mode": "form",
            'res_model': 'setu.unscanned.product.action.wizard',
            'target': 'new',
            'context': {'default_unscanned_product_line_ids': records.ids}
        }
        return action

    def set_action(self):
        if self.unscanned_product_line_ids.inventory_count_id.state not in ['Approved', 'Inventory Adjusted', 'Cancel']:
            self.unscanned_product_line_ids.write({'action': self.action})
            count_lines = []
            for line in self.unscanned_product_line_ids:
                if self.action == 'make_it_0':
                    product_found = self.unscanned_product_line_ids.inventory_count_id.line_ids.filtered(
                        lambda x: x.product_id.id == line.product_id.id and x.location_id.id == line.location_id.id)
                    lot_found = product_found.filtered(lambda x: x.lot_id.id == line.lot_id.id)
                    serial_found = product_found.filtered(lambda x: line.lot_id.id in x.serial_number_ids.ids or
                                                                    line.lot_id.id in x.expired_serial_number_ids.ids or
                                                                    line.lot_id.id in x.damaged_serial_number_ids.ids or
                                                                    line.lot_id.id in x.not_found_serial_number_ids.ids
                                                                    or line.lot_id.id in x.new_count_lot_ids.ids)
                    if not product_found or (line.product_id.tracking == 'lot' and not lot_found) or (
                            line.product_id.tracking == 'serial' and not serial_found):
                        serial_not_found = next((item for item in count_lines if
                                                 item.get('product_id') == line.product_id.id and item.get(
                                                     'location_id') == line.location_id.id and item[
                                                     'not_found_serial_number_ids'] and line.lot_id.id not in
                                                 item['not_found_serial_number_ids'][0][
                                                     2]), None)
                        if serial_not_found:
                            serial_not_found['not_found_serial_number_ids'][0][2].append(line.lot_id.id)
                            serial_not_found.update({'theoretical_qty': serial_not_found['theoretical_qty'] + 1,
                                                     'qty_in_stock': serial_not_found['qty_in_stock'] + 1})
                        else:
                            new_line = {'inventory_count_id': line.inventory_count_id.id,
                                        'product_id': line.product_id.id,
                                        'tracking': line.product_id.tracking,
                                        'not_found_serial_number_ids': [(6, 0, [
                                            line.lot_id.id])] if line.product_id.tracking == 'serial' else False,
                                        'location_id': line.location_id.id,
                                        'theoretical_qty': line.quantity,
                                        'qty_in_stock': line.quantity,
                                        'counted_qty': 0,
                                        'user_calculation_mistake': True,
                                        'unscanned_product_line_id': line}
                            if line.product_id.tracking == 'lot':
                                new_line.update({'lot_id': line.lot_id.id or False})
                            count_lines.append(new_line)
                    elif serial_found:
                        if line.lot_id.id not in serial_found.not_found_serial_number_ids.ids:
                            serial_found.not_found_serial_number_ids = [(4, line.lot_id.id)]
                            serial_found.new_count_lot_ids = [(3, line.lot_id.id)]
                else:
                    if line.product_id.tracking != 'serial':
                        line.inventory_count_line_id.unlink()
                    else:
                        if not line.inventory_count_line_id:
                            count_line = line.inventory_count_id.line_ids.filtered(lambda
                                                                                       x: x.product_id.id == line.product_id.id and line.lot_id.id in x.not_found_serial_number_ids.ids)
                        else:
                            count_line = line.inventory_count_line_id
                        count_line.write({'not_found_serial_number_ids': [(3, line.lot_id.id)],
                                          'new_count_lot_ids': [(4, line.lot_id.id)]})
            self.create_count_lines(count_lines)
        else:
            raise UserError(_("Count Is Already Approved"))

    def create_count_lines(self, count_lines):
        for line in count_lines:
            count_line_id = self.env['setu.stock.inventory.count.line'].create({
                'inventory_count_id': line['inventory_count_id'],
                'product_id': line['product_id'],
                'tracking': line['tracking'],
                'not_found_serial_number_ids': line['not_found_serial_number_ids'],
                'lot_id': line['lot_id'] if 'lot_id' in line else False,
                'location_id': line['location_id'],
                'theoretical_qty': line['theoretical_qty'],
                'qty_in_stock': line['qty_in_stock'],
                'counted_qty': line['counted_qty'],
                'user_calculation_mistake': line['user_calculation_mistake'],
                'unscanned_product_line_id': line['unscanned_product_line_id'].id
            })
            line['unscanned_product_line_id'].write({'inventory_count_line_id': count_line_id.id})
