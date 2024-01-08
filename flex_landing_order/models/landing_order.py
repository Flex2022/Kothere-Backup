from odoo import api, fields, models, _


class LandingOrder(models.Model):
    _name = 'landing.order'
    _description = 'LandingOrder'
    _rec_name = 'name'

    order_id = fields.Many2one('sale.order', string='Sale Order')

    name = fields.Char(string="Partner Reference", required=False, copy=False, readonly=True,
                       default=lambda self: _('New'))
    date = fields.Date(string='Date', default=fields.Date.today())
    h_date = fields.Date(string='H', default=fields.Date.today())
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('is_driver', '=', False)])
    partner_code = fields.Char(string='Customer Code')
    driver_id = fields.Many2one('res.partner', string='Driver', domain=[('is_driver', '=', True)])
    car_id = fields.Char(string='Car ID')

    quantity = fields.Float(string='Quantity')
    kind = fields.Selection([
        ('kind1', 'عادي'),
        ('kind2', 'مقاوم'),
        ('kind3', 'سايب')],
        string='Kind',
        default=False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('move', 'Move'),
        ('done', 'Done')],
        string='State',
        default='draft')

    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)

    @api.onchange('partner_id')
    def _onchange(self):
        if self.partner_id:
            self.car_id = self.driver_id.car_id



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('landing.order')
        return super(LandingOrder, self).create(vals_list)

    def print_report(self):
        return self.env.ref('flex_landing_orders.report_invoice_34').report_action(self)