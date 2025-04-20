# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError


class WeightManagementWizard(models.Model):
    _name = 'weight.management.wizard'
    _description = 'Weight Bridge Calculations Wizard'

    name = fields.Many2one('vehicle.details', string="Truck NO", tracking=True,required=False)
    temperature = fields.Integer(string="Temperature°C")
    picking_orgin = fields.Char(string="Source Document", store=True)
    # sale_orgin = fields.Char(string="Sale Reference")
    sale_id = fields.Many2one('stock.picking', string="Sale Id")
    product_id = fields.Many2one('product.product', string="Product Id")
    referenceid = fields.Char(string='Reference', copy=False, readonly=True, tracking=True,
                              default=lambda self: _('New'))
    # customer_id = fields.Many2one('stock.picking', string="Customer/Vendor", required=True)
    vehicle_type = fields.Many2one('vehicle.types', string="Vehicle Type", tracking=True)
    approver = fields.Many2one('res.partner', string="Supplier", tracking=True)
    # approver = fields.Many2one('res.company',string="Supplier", tracking=True,store=True)
    driver_id = fields.Many2one('driver.details', string="Driver Name", tracking=True)
    drv_id = fields.Char(related="driver_id.driver_license", string="License No", tracking=True)
    native_id = fields.Many2one(related="driver_id.native", string="Driver's Nationality", tracking=True)
    vehicle = fields.Char(string='Vehicle No', tracking=True, required=False)
    weight = fields.Float(string="First Weight", help="Weight in K.G", tracking=True, required=False)
    weight1 = fields.Float(string="Second Weight", help="Weight in ", tracking=True, required=False)
    weight2 = fields.Float(string="Net Weight", help="weight in K.G", tracking=True, compute='_compute_total')
    date_order = fields.Datetime(string='Date', tracking=True, default=fields.Datetime.now())
    transport_type = fields.Selection([
        ('po', 'As per the Purchase Order'),
        ('srn', 'As per the Sales Order'),
    ], string="Transport Type", tracking=True)
    notes = fields.Text(string='Description')
    state = fields.Selection([
        ('pen', 'Pending'),
        ('appr', 'Approved'),
    ], string="Transport Type", default='pen', tracking=True)
    origin_count = fields.Integer(string="Ready for Delivery")
    weight_uom = fields.Selection([
        ('ton', 'Ton'),
    ], default="ton")
    product_uom = fields.Many2one('uom.uom', string='Uom')
    weighbridge_ids = fields.One2many('weight.management.wizard.line', 'weight_management_id', store_true=True,
                                      readonly=True)
    order_quantity = fields.Float(string="Order Quantity", default="0", compute='_compute_order_quantity')
    remarks = fields.Text(string="Acknowledge",
                          default='I have received the above goods in good quality & above weight')
    remarks_open = fields.Boolean(string="Acknowledgement")

    def get_driver_acknowledgement(self):
        self.write({
            'remarks_open': True
        })

    @api.onchange('weight1')
    def _compute_order_quantity(self):
        qty = 0.00
        stock_picking = self.env['stock.picking'].search([('name', '=', self.picking_orgin)])
        sale_order = self.env['sale.order'].search([('name', '=', stock_picking.origin)])
        if sale_order:
            for sale in sale_order.order_line:
                qty = sale.product_uom_qty - sale.qty_delivered
                self.order_quantity = qty
        elif stock_picking:
            for picking in stock_picking.move_ids:
                print(':::::::::::::::::::::::::::::::::::::;', picking, picking.product_uom_qty)
                qty = picking.product_uom_qty
                self.order_quantity = qty

    def weight_mgnt_reference_wizard(self):
        weight_mgnt = self.env['weight.management']
        weight_mgnt.sudo().write({
            'picking_orgin': self.id})

    def action_print_report(self):
        data = self.env["weight.management.wizard"].search(
            [
                "&",
                # ("name", "=", 0),
                "|",
                ("weight", "!=", 0),
                ("weight1", "!=", 0),
                ("weight2", "!=", 0),
                ("order_quantity", "!=", 0),
            ]
        )
        return self.env.ref(
            "weight_management.weight_management_report"
        ).report_action(data)

    # Calculate product weight
    @api.onchange('weight1')
    def _compute_total(self):
        for rec in self:
            if rec.weight <= rec.weight1:
                rec.weight2 = float(rec.weight1 or 0.0) - float(rec.weight or 0.0)
            else:
                raise UserError('The Loaded Vehicle Weight Should Not be Smaller Than the Empty Vehicle Weight')

    # button Function#
    def get_line_items(self):
        line_vals = []
        for line in self:
            if line:
                vals = [0, 0, {
                    'qty_done': line.weight2,
                }]
                line_vals.append(vals)
        return line_vals

    def action_split(self):
        requisition_created = False
        new_requisition_id = False
        requisition_obj = self.env['weight.management']
        purchase_sr = self.env['stock.picking'].search([('name', '=', self.picking_orgin)])
        for line in self:
            new_requisition_id = requisition_obj.create({
                'name': line.name.id and line.name.id or '',
                'weight_uom': line.weight_uom and line.weight_uom or '',
                'picking_orgin': line.picking_orgin and line.picking_orgin or '',
                'driver_id': line.driver_id.id and line.driver_id.id or '',
                'date_order': line.date_order and line.date_order or '',
                'vehicle': line.vehicle and line.vehicle or '',
                'vehicle_type': line.vehicle_type.id and line.vehicle_type.id or '',
                'weight': line.weight and line.weight or '',
                'weight2': line.weight2 and line.weight2 or '',
                'weight1': line.weight1 and line.weight1 or '',
                'notes': line.notes and line.notes or '',
                'temperature': line.temperature and line.temperature or '',
                'approver': line.approver.id and line.approver.id or '',
                'remarks': line.remarks and line.remarks or '',
                'product_uom': line.product_uom.id and line.product_uom.id or '',
                'product_id': line.product_id.id and line.product_id.id or '',
            })
            for picking in purchase_sr.move_ids_without_package:
                picking.update({
                    'quantity': line.weight2 and line.weight2 or '',
                })
            purchase_sr.update({
                'wizard': True
            })
            if self.remarks_open:
                purchase_sr.update({
                    'remarks': line.remarks and line.remarks or '',
                })
            else:
                purchase_sr.update({
                    'remarks': line.notes and line.notes or '',
                })

            return True

    @api.model
    def create(self, vals):
        if vals.get('referenceid', _('New')) == _('New'):
            vals['referenceid'] = self.env['ir.sequence'].next_by_code('weight.management.wizard') or _('New')
            return super(WeightManagementWizard, self).create(vals)


class WeightManagementWizardLine(models.TransientModel):
    _name = 'weight.management.wizard.line'
    _description = 'Weight Bridge Calculations Wizard Line'

    weight_management_id = fields.Many2one('weight.management.wizard')
    product_id = fields.Many2one('product.product', string='Product')
