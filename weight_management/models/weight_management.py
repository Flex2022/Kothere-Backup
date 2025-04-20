from odoo import fields, models, api, _
from odoo.osv import expression


class Vehicle(models.Model):
    _name = "vehicle.details"

    name = fields.Char(string="Vehicle Name")
    number_plate = fields.Integer(string="Number Plate", tracking=True)

    def name_get(self):
        result = []
        for rec in self:
            name = str(rec.number_plate) + '[' + rec.name + ']'
            result.append((rec.id, name))
        return result
    #
    # @api.model
    # def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = args or []
    #     domain = []
    #     if name:
    #         domain = [('number_plate', operator, name)]
    #     return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)


class VehicleTypes(models.Model):
    _name = "vehicle.types"

    name = fields.Char(string="Transport Types")


class DriverDetails(models.Model):
    _name = "driver.details"

    name = fields.Char(string="Driver Name")
    driver_license = fields.Char(string="Driver License No")
    native = fields.Many2one('res.country', string="Nationality")


class WeightManagement(models.Model):
    _name = 'weight.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Weight Bridge Calculation'

    name = fields.Many2one('vehicle.details', string="Truck NO", tracking=True, required=True)
    temperature = fields.Integer(string="Temperature°C")
    notes = fields.Text(string='Description')
    picking_orgin = fields.Char(string="Source Document")
    sale_id = fields.Many2one('stock.picking', string="Sale Id")
    order_quantity = fields.Float(string="Order Quantity", default="0", compute='_compute_order_quantity')
    sequenceid = fields.Char(string='Reference', copy=False, readonly=True, tracking=True,
                             default=lambda self: _('New'))
    referenceid = fields.Char('Reference', default='/', track_visibility="onchange", copy=False)
    vehicle_type = fields.Many2one('vehicle.types', string="Vehicle Type", tracking=True)
    approver = fields.Many2one('res.partner', string="WB Handled By", tracking=True)
    driver_id = fields.Many2one('driver.details', string="Driver Name", tracking=True)
    drv_id = fields.Char(related="driver_id.driver_license", string="License No", tracking=True)
    native_id = fields.Many2one(related="driver_id.native", string="Driver's Nationality", tracking=True)
    vehicle = fields.Char(string='Vehicle No', tracking=True, required=True)
    weight = fields.Float(string="First Weight", help="Weight in K.G", tracking=True, required=True)
    weight1 = fields.Float(string="Second Weight", help="Weight in ", tracking=True, required=True)
    weight2 = fields.Float(string="Net Weight", help="weight in K.G", tracking=True)
    date_order = fields.Datetime(string='Date', tracking=True, default=fields.Datetime.now())
    origin_count = fields.Integer(string="Ready for Delivery")
    weight_uom = fields.Selection([
        ('kg', 'Kg'),
        ('ton', 'Ton'),
    ], default="ton")
    product_uom = fields.Many2one('uom.uom', string='Uom')
    remarks = fields.Text(string="Acknowledge",
                          default='I have received the above goods in good quality & above weight')
    product_id = fields.Many2one('product.product', string="Product Id")

    # Calculate product weight
    @api.onchange('weight1')
    def _compute_total(self):
        for rec in self:
            rec.weight2 = float(rec.weight1 or 0.0) - float(rec.weight or 0.0)

    def action_approved(self):
        self.sudo().write({'state': 'appr'})

    def update_shipped(self):
        purchase_sr = self.env['stock.picking'].search([('name', '=', self.picking_orgin)])
        for line in purchase_sr.move_ids_without_package:
            line.update({
                'quantity_done': self.weight2,
            })
        return True

    @api.model
    def create(self, vals):
        if vals.get('sequenceid', _('New')) == _('New'):
            vals['sequenceid'] = self.env['ir.sequence'].next_by_code('weight.management') or _('New')
            rec = super(WeightManagement, self).create(vals)

    @api.onchange('weight1')
    def _compute_order_quantity(self):
        stock_picking = self.env['stock.picking'].search([('name', '=', self.picking_orgin)])
        sale_order = self.env['sale.order'].search([('name', '=', stock_picking.origin)])
        for rec in self:
            for sale in sale_order.order_line:
                rec.order_quantity = sale.product_uom_qty - sale.qty_delivered
