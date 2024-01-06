# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class InventoryCountSettings(models.Model):
    _name = 'inventory.count.settings'
    _description = """
            This model is used to Auto Adjust Inventory.
        """

    name = fields.Char(string="Inventory Count Configuration", default="Inventory Count Configuration")
    auto_inventory_adjustment = fields.Boolean(string="Auto Inventory Adjustment?")
    group_include_expiry_counting = fields.Boolean(string="Include Expiry Counting?",
                                                   implied_group="setu_inventory_count_management.group_include_expiry_counting")
    group_include_damage_counting = fields.Boolean(string="Include Damage Counting?",
                                                   implied_group="setu_inventory_count_management.group_include_damage_counting")
    expiry_location_id = fields.Many2one('stock.location', string="Expiry Location")
    damage_location_id = fields.Many2one('stock.location', string="Damage Location")
    inventory_count_days = fields.Integer(string="Inventory Count Days")
    approver_id = fields.Many2one(comodel_name="res.users",string="Approver")
    use_barcode_scanner = fields.Boolean(default=False,string="Use barcode scanner")
    session_user_ids = fields.Many2many(comodel_name='res.users',string="Users")

    @api.model
    def open_record_action(self):
        view_id = self.env.ref('setu_inventory_count_management.inventory_count_settings_view_form').id
        record = self.env['inventory.count.settings'].search([]).id
        return {'type': 'ir.actions.act_window',
                'name': _('Settings - Inventory Count'),
                'res_model': 'inventory.count.settings',
                'target': 'current',
                'res_id': record,
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                }

    # @api.onchange('group_include_expiry_counting')
    # def onchange_include_expiry_counting(self):
    #     group_user = self.env.ref('base.group_user').sudo()
    #     if self._origin.group_include_expiry_counting:
    #         group_user._apply_group(self.env.ref('setu_inventory_count_management.group_include_expiry_counting'))
    #     else:
    #         group_user._remove_group(self.env.ref('setu_inventory_count_management.group_include_expiry_counting'))

    def write(self, vals):
        res = super().write(vals)
        group_user = self.env.ref('base.group_user').sudo()
        if self.group_include_expiry_counting:
            group_user._apply_group(self.env.ref('setu_inventory_count_management.group_include_expiry_counting'))
        else:
            group_user._remove_group(self.env.ref('setu_inventory_count_management.group_include_expiry_counting'))
        if self.group_include_damage_counting:
            group_user._apply_group(self.env.ref('setu_inventory_count_management.group_include_damage_counting'))
        else:
            group_user._remove_group(self.env.ref('setu_inventory_count_management.group_include_damage_counting'))
        return res
