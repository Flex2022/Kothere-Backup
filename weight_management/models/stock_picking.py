from odoo import fields, models, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools.float_utils import float_is_zero, float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_approval_count = fields.Integer(compute='_compute_sale_approval_count', string='Weigh Bridge',
                                         default=0)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('waiting_for_delivery_approval', 'Waiting For Delivery Approval'),
        ('approved_for_delivery', 'Delivery Approved'),
        ('refused_for_delivery', 'Delivery Refused'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False)
    delivery_approved = fields.Boolean(string="Delivery Approved")
    waiting_for_delivery_approval = fields.Boolean(string="Waiting for Delivery Approval")
    weight_button = fields.Boolean(string="Weight button")
    wizard = fields.Boolean()
    method = fields.Selection(
        [('no', 'No'), ('yes', 'Yes')],
        string='Validate the Stock without Weight Bridge Calculations?')
    remarks = fields.Text('Remarks')
    approve = fields.Boolean(string='Need Approval?')
    approved = fields.Boolean(string='Delivery Approved')
    validation_done = fields.Boolean(string='validation done')

    def open_new_wb_wizard(self):
        view_id = self.env['weigh.bridge.alert.wizard']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Weigh Bridge Alert Remarks',
            'res_model': 'weigh.bridge.alert.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': view_id.id,
            'view_id': self.env.ref('weight_management.view_weigh_bridge_alert_remarks_wizard', False).id,
            'target': 'new',
            'context': {
                'default_name': self.id,
            }
        }

    def button_validate(self):
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        if self.picking_type_code == 'outgoing' and self.method != 'yes' and not self.remarks:
            raise AccessError(
                _('Alert!!,The "%s" You cannot transfer the Materials without Weigh Bridge Calculation!!!.') %
                self.origin)
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # Sanity checks.
        if not self.env.context.get('skip_sanity_check', False):
            self._sanity_check()

        self.message_subscribe([self.env.user.partner_id.id])

        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        if not self.env.context.get('button_validate_picking_ids'):
            self = self.with_context(button_validate_picking_ids=self.ids)
        res = self._pre_action_done_hook()
        if res is not True:
            return res

        # Call `_action_done`.
        pickings_not_to_backorder = self.filtered(lambda p: p.picking_type_id.create_backorder == 'never')
        if self.env.context.get('picking_ids_not_to_backorder'):
            pickings_not_to_backorder |= self.browse(self.env.context['picking_ids_not_to_backorder']).filtered(
                lambda p: p.picking_type_id.create_backorder != 'always'
            )
        pickings_to_backorder = self - pickings_not_to_backorder
        pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
        pickings_to_backorder.with_context(cancel_backorder=False)._action_done()

        if self.user_has_groups('stock.group_reception_report') \
                and self.picking_type_id.auto_show_reception_report:
            lines = self.move_ids.filtered(lambda
                                               m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
            if lines:
                # don't show reception report if all already assigned/nothing to assign
                wh_location_ids = self.env['stock.location']._search(
                    [('id', 'child_of', self.picking_type_id.warehouse_id.view_location_id.id),
                     ('usage', '!=', 'supplier')])
                if self.env['stock.move'].search([
                    ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
                    ('product_qty', '>', 0),
                    ('location_id', 'in', wh_location_ids),
                    ('move_orig_ids', '=', False),
                    ('picking_id', 'not in', self.ids),
                    ('product_id', 'in', lines.product_id.ids)], limit=1):
                    action = self.action_view_reception_report()
                    action['context'] = {'default_picking_ids': self.ids}
                    return action
        return True

    def get_approval(self):
        for rec in self:
            return self.write({'waiting_for_delivery_approval': True, 'state': 'waiting_for_delivery_approval'})

    def action_sale_approve(self):
        return self.write({'delivery_approved': True, 'approved': True, 'state': 'approved_for_delivery'})

    def action_sale_refuse(self):
        for rec in self:
            rec.state = 'refused_for_delivery'

    def open_weight_mgnt_wizard_form(self):
        global result
        print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL", len(self.move_ids_without_package) == 1,
              len(self.move_ids_without_package) > 1)
        if len(self.move_ids_without_package) == 1:
            action = self.sudo().env.ref('weight_management.action_wizard_weight_management_wizard_view')
            result = action.read()[0]
            order_line = []
            for line in self:
                result['context'] = {
                    'default_picking_orgin': line.name,
                    'default_weighbridge_ids': order_line,
                    'default_product_id': line.move_ids_without_package.product_id.id,
                    'default_approver': line.partner_id.id,
                    'default_product_uom': line.move_ids_without_package.product_uom.id,
                }
                line.sudo().create_order()
            return result
        elif len(self.move_ids_without_package) > 1:
            print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
            raise ValidationError(_("Alert!!!. Weigh bridge calculation can't be done for multiple products\n"
                                    "NOTE(weigh bridge suits only for single product.)"))

    def create_order(self):
        management_wizard = self.env['weight.management.wizard']
        management_wizard.create({
            'picking_orgin': self.name,
        })
        return True

    def weight_mgnt_reference(self):
        weight_mgnt = self.env['weight.management']
        weight_mgnt.sudo().write({
            'picking_orgin': self.name})

    # count method#
    def _compute_sale_approval_count(self):
        for record in self:
            record.sale_approval_count = record.env['weight.management'].sudo().search_count(
                [('picking_orgin', '=', record.name)])
            record.weight_mgnt_reference()
            record.new_sale_approval_create_request()

    # smart Button Function#
    def new_sale_approval_create_request(self):
        self.sudo().ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        form_view = self.sudo().env.ref('weight_management.view_sale_approval_form')
        tree_view = self.sudo().env.ref('weight_management.view_sale_approval_tree')
        return {
            'name': _('Weight Bridge Calculations'),
            'res_model': 'weight.management',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('picking_orgin', '=', self.name)],
        }

    # button Function#
    def create_new_sale_approval(self):
        approvals = self.sudo().env['weight.management'].create({
            'picking_orgin': self.name,
        })
        self.sudo().write({'state': 'assigned'})
        return True


class WeighBridgeAlert(models.TransientModel):
    _name = 'weigh.bridge.alert.wizard'
    _description = 'Weigh Bridge Alert'
    _inherit = ['mail.thread']

    name = fields.Many2one('stock.picking', string='Remarks')
    approve = fields.Boolean(string='Need Approval?')
    method = fields.Selection(
        [('no', 'No'), ('yes', 'Yes')],
        string='Validate the Stock without Weight Bridge Calculations?', required=True, default='yes')
    remarks = fields.Text('Remarks',
                          default='The Stock Validation will proceed without Weight Bridge Calculations')

    def tick_ok(self):
        pick = self.env['stock.picking'].search([('name', '=', self.name.name)])
        if self.method == 'yes':
            pick.write({'method': self.method, 'validation_done': True, 'remarks': self.remarks})
        else:
            pick.write({'method': self.method, 'validation_done': True, 'approve': self.approve})
            return True

    class StockBackorderConfirmation(models.TransientModel):
        _inherit = 'stock.backorder.confirmation'

        def process(self):
            pickings_to_do = self.env['stock.picking']
            pickings_not_to_do = self.env['stock.picking']
            for line in self.backorder_confirmation_line_ids:
                if line.to_backorder is True:
                    pickings_to_do |= line.picking_id
                else:
                    pickings_not_to_do |= line.picking_id

            for pick_id in pickings_not_to_do:
                moves_to_log = {}
                for move in pick_id.move_lines:
                    if float_compare(move.product_uom_qty,
                                     move.quantity_done,
                                     precision_rounding=move.product_uom.rounding) > 0:
                        moves_to_log[move] = (move.quantity_done, move.product_uom_qty)
                pick_id._log_less_quantities_than_expected(moves_to_log)

            pickings_to_validate = self.env.context.get('button_validate_picking_ids')
            if pickings_to_do.picking_type_code == 'outgoing':
                pickings_to_do.waiting_for_delivery_approval = False
                pickings_to_do.delivery_approved = False
            if pickings_to_validate:
                pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate).with_context(
                    skip_backorder=True)
                if pickings_not_to_do:
                    pickings_to_validate = pickings_to_validate.with_context(
                        picking_ids_not_to_backorder=pickings_not_to_do.ids)
                return pickings_to_validate.button_validate()
            return True
