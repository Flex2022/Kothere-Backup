from odoo import api, fields, models,_
from odoo.exceptions import UserError


class FlexPurchaseWeight(models.Model):
    _name = 'flex.purchase.weight'
    _description = 'Flex Purchase Weight'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'referenceId'

    referenceId = fields.Char(string='Reference', copy=False, readonly=True, tracking=True,
                              default=lambda self: _('New'))

    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                  default=lambda self: self.env.company)

    truck_no = fields.Many2one('fleet.vehicle', string='Truck No')
    product_id = fields.Many2one('product.product', string="Product Id", domain="[('company_id', '=', company_id)]")
    po_number = fields.Many2one('purchase.order', string="Purchase Order")
    temperature = fields.Integer(string="Temperature°C")
    date_order = fields.Datetime(string='Date', tracking=True, default=fields.Datetime.now())
    notes = fields.Text(string='Description')
    driver_id = fields.Many2one('flex.driver.details', string="Driver Name", tracking=True)
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
        if vals.get('referenceId', _('New')) == _('New'):
            vals['referenceId'] = self.env['ir.sequence'].next_by_code('weigh.po') or _('New')
            return super(FlexPurchaseWeight, self).create(vals)

    def action_confirm(self):
       self.filtered(lambda x: x.state == 'draft').write({'state': 'confirm'})
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


    def _compute_purchase_order_count(self):
        for rec in self:
            purchase_order = self.env['purchase.order'].search([('weight_po', '=', rec.id)])
            rec.purchase_order_count = 4





