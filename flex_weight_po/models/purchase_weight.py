from odoo import api, fields, models,_
from odoo.exceptions import UserError


class FlexPurchaseWeight(models.Model):
    _name = 'flex.purchase.weight'
    _description = 'Flex Purchase Weight'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', copy=False, readonly=True, tracking=True, default=lambda self: _('New'))

    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                  default=lambda self: self.env.company)

    # todo: remove the following field (truck_no) once ensure that there is no live data will affected (done)
    # truck_no = fields.Many2one('fleet.vehicle', string='Truck No', tracking=1)
    truck_number = fields.Char(string='Truck No')
    product_id = fields.Many2one('product.product', string="Product Id")
    product_domain = fields.Binary(string="Product Domain", compute="_compute_product_domain")
    po_number = fields.Many2one('purchase.order', string="Purchase Order", domain="[('company_id', '=', company_id)]")
    picking_ids = fields.One2many('stock.picking', 'purchase_weight_id', string="Receipts")
    picking_count = fields.Integer(string="Receipts", compute="_compute_picking_count")
    temperature = fields.Integer(string="Temperature°C")
    date_order = fields.Datetime(string='Date', tracking=True, default=fields.Datetime.now())
    notes = fields.Text(string='Description')
    # todo: remove the following field (driver_id) once ensure that there is no live data will affected (done)
    # driver_id = fields.Many2one('flex.driver.details', string="Driver Name", tracking=True)
    driver_name = fields.Char(string="Driver Name", tracking=1)
    remarks = fields.Text(string="Acknowledge",
                          default='I have received the above goods in good quality & above weight')
    remarks_open = fields.Boolean(string="Acknowledgement")
    approver = fields.Many2one('res.partner', string="Supplier", tracking=True)
    weight = fields.Float(string="First Weight", help="Weight in K.G", tracking=True, required=False)
    weight1 = fields.Float(string="Second Weight", help="Weight in ", tracking=True, required=False)
    weight2 = fields.Float(string="Net Weight", help="weight in K.G", tracking=True, compute='_compute_total')
    product_uom = fields.Many2one('uom.uom', string='Uom',related='product_id.uom_id')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('cancel', 'Cancelled')],
                                string="Status", default='draft', tracking=True)
    purchase_order_count = fields.Integer(string="Purchase Order Count", compute='_compute_purchase_order_count')
    receipt_number = fields.Char(string="Receipt Number", tracking=1)

    @api.onchange('po_number')
    def onchange_po_number(self):
        if self.po_number:
            self.approver = self.po_number.partner_id
            if self.product_id and self.product_id not in self.po_number.order_line.product_id:
                self.product_id = False
        else:
            self.approver = False

    @api.depends('po_number', 'company_id')
    def _compute_product_domain(self):
        for rec in self:
            if rec.po_number:
                po_products = rec.po_number.order_line.product_id
                rec.product_domain = [('id', 'in', po_products.ids), ('company_id', 'in', [rec.company_id.id, False])]
            else:
                rec.product_domain = [('company_id', 'in', [rec.company_id.id, False])]

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.picking_ids)

    def get_last_base_weight(self):
        """
        This method retrieves the last base weight record for the current user.
        :return: The last base weight record or None if no records exist.
        """
        for rec in self:
            last_base_weight = self.env['base.weight.po'].search([
                ('user_id', '=', self.env.user.id),
                ('active', '=', True)], order='id desc')
            last_record_in_last_base_weight = last_base_weight[0] if last_base_weight else None

            if last_record_in_last_base_weight:
                if rec.weight == 0.0:
                    rec.weight = last_record_in_last_base_weight.weight
                else:
                    if rec.weight1 == 0.0:
                        rec.weight1 = last_record_in_last_base_weight.weight
                    else:
                        raise UserError('You Have Already Loaded The Vehicle Weight')

                for rec in last_base_weight:
                    rec.active = False

            else:
                raise UserError(f'Dose Not Found Any Weight Record For {self.env.user.name}')




    @api.depends('weight', 'weight1')
    def _compute_total(self):
        for rec in self:
            if rec.weight >= rec.weight1:
                rec.weight2 =  float(rec.weight or 0.0) - float(rec.weight1 or 0.0)
            else:
                raise UserError('The Loaded Vehicle Weight Should Not be Smaller Than the Empty Vehicle Weight')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('weigh.po') or _('New')
            return super(FlexPurchaseWeight, self).create(vals)

    def action_confirm(self):
        self = self.filtered(lambda x: x.state == 'draft')
        with_linked_po = self.filtered('po_number')
        self.write({'state': 'confirm'})
        (self - with_linked_po)._create_po()
        return with_linked_po._receive_po()

    def _receive_po(self):
        for rec in self:
            picking = rec.po_number.picking_ids[:1]
            target_move_lines = picking.move_ids_without_package.filtered(lambda sm: sm.state not in ['done', 'cancel'] and sm.product_id == rec.product_id)
            if target_move_lines:
                target_move_lines[0].quantity = rec.weight2
                target_move_lines[0].write({'quantity': rec.weight2, 'picked': True})
                picking.write({'purchase_weight_id': rec.id})
                return picking.with_context(skip_backorder=True).button_validate()
            # remaining_qty = rec.weight2
            # for line in target_move_lines:
            #     if remaining_qty <= 0:
            #         break
            #     if line.quantity < line.product_uom_qty:
            #         line_needed_qty = line.product_uom_qty - line.quantity
            #         line.write({'quantity': line.quantity + min(line_needed_qty, remaining_qty)})
            #         remaining_qty -= min(line_needed_qty, remaining_qty)
            # if remaining_qty > 0 and target_move_lines:
            #     target_move_lines[-1].quantity += remaining_qty
            # if all(sm.quantity == sm.product_uom_qty for sm in picking.move_ids_without_package):
            #     picking.button_validate()


    def _create_po(self):
       for rec in self:
          purchase_order = self.env['purchase.order'].sudo().create({
            'partner_id': rec.approver.id,
            'date_order': rec.date_order,
            'state': 'draft',
            'weight_po': rec.id,
            "its_weight" : True,
            'company_id': rec.company_id.id,
            'order_line': [(0, 0, {
                 'product_id': rec.product_id.id,
                 'name': rec.notes,
                 'product_qty': rec.weight2,
                'weight': rec.weight,
                'weight1': rec.weight1,
            })]
          })
          rec.po_number = purchase_order.id
          purchase_order.message_post(body="Purchase Order Created from Weight PO")

    def action_cancel(self):
        self.filtered(lambda x: x.state == 'confirm').write({'state': 'cancel'})

    def action_draft(self):
        self.filtered(lambda x: x.state == 'cancel').write({'state': 'draft'})

    def action_view_purchase_order(self):
        return {
            'name': _('Purchase Order'),
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': self.po_number.id,
            'type': 'ir.actions.act_window',
        }

    def action_view_pickings(self):
        return {
            'name': _('Transfers'),
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('purchase_weight_id', 'in', self.ids)],
            'type': 'ir.actions.act_window',
        }

    def _compute_purchase_order_count(self):
        for rec in self:
            purchase_order = self.env['purchase.order'].search([('weight_po', '=', rec.id)])
            rec.purchase_order_count = 4





