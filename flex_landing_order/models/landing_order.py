from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LandingOrder(models.Model):
    _name = 'landing.order'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'LandingOrder'
    _rec_name = 'name'

    order_id = fields.Many2one('sale.order', string='Sale Order')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking')

    name = fields.Char(string="Partner Reference", required=False, copy=False, readonly=True,
                       default=lambda self: _('New'))
    state = fields.Selection([
        ('new', 'New'),
        ('receive', 'Receive'),
        ('delivery', 'Delivery'),
        ('done', 'Done'),
        ('canceled', 'Canceled')],
        string='State',
        default='new')
    date = fields.Date(string='Date', default=fields.Date.today())
    h_date = fields.Date(string='H', default=fields.Date.today())
    partner_id = fields.Many2one('res.partner', string='Vendor/Customer', )
    partner_code = fields.Char(string='Vendor/Customer Code', related='partner_id.partner_code')

    # Fleet
    car_model_id = fields.Many2one('fleet.vehicle', string='Car Model')
    driver_id = fields.Many2one('res.partner', string='Driver', compute="compute_car_model_details", store=True)
    driver_employee = fields.Many2one('hr.employee', string='Driver Employee', compute="compute_car_model_details",
                                      store=True)
    car_id = fields.Char(string='Car ID', compute="compute_car_model_details", store=True)

    cancelation_reason = fields.Text(string='Cancelation Reason')

    quantity = fields.Char(string='Quantity')
    kind = fields.Selection([
        ('kind1', 'عادي'),
        ('kind2', 'مقاوم'),
        ('kind3', 'سايب')],
        string='Kind',
        default=False)
    size = fields.Selection([
        ('size1', 'طن'),
        ('size2', 'كيس')],
        string='Size',
        default=False)
    receive_date = fields.Datetime(string='Receive Date')
    delivery_date = fields.Datetime(string='Delivery Date')
    from_receive_to_delivery_h = fields.Float(string='From Receive To Delivery',
                                              compute='_compute_from_receive_to_delivery', digits=(6, 2), store=True)
    from_receive_to_delivery_d = fields.Integer(string='From Receive To Delivery',
                                                compute='_compute_from_receive_to_delivery', store=True)
    from_receive_to_delivery_h_hour = fields.Float(string='From Receive To Delivery',
                                                   compute='_compute_from_receive_to_delivery', digits=(6, 2),
                                                   store=True)
    reward_amount = fields.Float(string='Reward Amount')

    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)

    @api.onchange('car_model_id')
    def onchange_car_model_id(self):
        for order in self:
            order.driver_id = order.car_model_id.driver_id.id if order.car_model_id.driver_id else False
            order.driver_employee = order.car_model_id.employee_id_dr.id if order.car_model_id.employee_id_dr else False
            order.car_id = order.car_model_id.license_plate

    def action_state(self):
        if self.state == 'new':
            self.state = 'receive'
            self.receive_date = fields.Date.today()
        elif self.state == 'receive':
            self.state = 'delivery'
            self.delivery_date = fields.Date.today()
        elif self.state == 'delivery':
            self.state = 'done'

    def cancel_order_action(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Reason',
            'res_model': 'cancel.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id,
                        'default_partner_id': self.partner_id.id}
        }

    def set_as_new(self):
        self.state = 'new'

    @api.depends('receive_date', 'delivery_date')
    def _compute_from_receive_to_delivery(self):
        for order in self:
            if order.receive_date and order.delivery_date:
                order.from_receive_to_delivery_h = (order.delivery_date - order.receive_date).total_seconds() / 3600
                order.from_receive_to_delivery_d = (order.delivery_date - order.receive_date).days
                order.from_receive_to_delivery_h_hour = order.from_receive_to_delivery_h - (
                        order.from_receive_to_delivery_d * 24)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('landing.order')
        return super(LandingOrder, self).create(vals_list)

    def print_report(self):
        return self.env.ref('flex_landing_orders.report_invoice_34').report_action(self)

    def write(self, values):
        old_values = {field: self[field] for field in values if field in self}
        result = super(LandingOrder, self).write(values)
        new_values = {field: values[field] for field in values if field in self}

        changed_fields = [field for field in old_values if new_values.get(field) is not None]

        if changed_fields:
            changes_message = "\n".join([
                f"{self._format_field_value(field, old_values[field])} \u2794 {self._format_field_value(field, new_values.get(field))}  ({self._fields[field].string})\n"
                for field in changed_fields
            ])
            self.message_post(body=f"\n{changes_message}")

        return result

    def _format_field_value(self, field_name, field_value):
        if field_name in self._fields and isinstance(self._fields[field_name], fields.Many2one):
            related_model = self._fields[field_name].comodel_name
            # string_field = self._fields[field_name].string
            if isinstance(field_value, self.env[related_model].browse([]).__class__):
                return field_value.name
            elif isinstance(field_value, int):
                related_record = self.env[related_model].sudo().browse(field_value)
                return related_record.name if related_record else field_value
        return field_value


class CancelReasonWizard(models.TransientModel):
    _name = 'cancel.reason.wizard'
    _description = 'Cancel Reason Wizard'

    reason = fields.Text(string='Reason', required=True)

    def action_cancel(self):
        self.ensure_one()
        landing_order = self.env['landing.order'].browse(self.env.context.get('active_id'))
        landing_order.write({
            'cancelation_reason': self.reason,
            'state': 'canceled',
            'delivery_date': '',
            'receive_date': '',
        })
