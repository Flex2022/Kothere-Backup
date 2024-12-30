# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class DeliveryNote(models.Model):
    _name = "delivery.note"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Delivery Note"

    name = fields.Char(
        string='Reference',
        required=True,
        default=_('New'),
        copy=False,
        readonly=True,
    )
    state = fields.Selection(
        selection=[('draft', 'New'),
                   ('deliver', 'Delivered'),
                   ('manufacture', 'Manufactured'),
                   ('output', 'Stock Output'),
                   ('done', 'Received'),
                   ('cancel', 'Cancelled')],
        string='Status',
        readonly=True,
        default='draft',
        copy=False,
        tracking=1
    )
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', tracking=1)
    partner_street = fields.Char(string='Address', related='partner_id.street')
    product_ids = fields.Many2many(
        comodel_name='product.product',
        relation='delivery_note_product_rel',
        string='Products',
        tracking=2
    )
    quantity = fields.Float(string='Quantity', digits='Product Unit of Measure', tracking=2, compute='_compute_quantity', store=True)
    previous_qty = fields.Float(string='Previous Quantity', digits='Product Unit of Measure', tracking=2, compute='_compute_previous_qty', store=True)
    delivery_date = fields.Datetime(string='Delivery Date', tracking=3)

    vehicle_id = fields.Many2one('fleet.vehicle', string='Car Model', tracking=2)
    driver_id = fields.Many2one(comodel_name='res.partner', string='Driver', related='vehicle_id.driver_id', store=True)
    driver_phone = fields.Char(string='Address', related='partner_id.street')
    license_plate = fields.Char(string='Car ID', related="vehicle_id.license_plate", store=True)

    picking_id = fields.Many2one(comodel_name='stock.picking', string='Transfer', required=True, tracking=1)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        related='picking_id.company_id',
    )

    project_name = fields.Char(string='Project Name / Location')
    cement_in_truck = fields.Float(string='Cement In Truck')
    cement_content = fields.Float(string='Cement Content')
    specified_slump = fields.Float(string='Specified slump')
    pump_no = fields.Char(string='Pump No')
    plant_no = fields.Char(string='Plant No')
    admixtures = fields.Char(string='Admixtures')
    max_aggr_size = fields.Char(string='Max Aggr Size')
    time_in_pant = fields.Datetime(string='Time In Plant')
    time_off_site = fields.Datetime(string='Time Off Site')
    time_on_site = fields.Datetime(string='Time On Site')
    time_out_plant = fields.Datetime(string='Time Out Plant')
    screed = fields.Boolean(string='Screed')
    substructures = fields.Boolean(string='Substructures')
    columns = fields.Boolean(string='Columns')
    slab = fields.Boolean(string='Slab')
    others = fields.Boolean(string='Others')

    workcenter_id = fields.Many2one('mrp.workcenter')


    @api.depends('picking_id', 'create_date')
    def _compute_previous_qty(self):
        for rec in self:
            previous_notes = rec.picking_id.delivery_note_ids.filtered(lambda n: not rec.create_date or n.create_date < rec.create_date)
            rec.previous_qty = sum(previous_notes.mapped('cement_in_truck'))

    @api.depends('previous_qty', 'cement_in_truck')
    def _compute_quantity(self):
        for rec in self:
            rec.quantity = rec.previous_qty + rec.cement_in_truck

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('delivery.note.seq') or _('New')
        return super(DeliveryNote, self).create(vals_list)

    def unlink(self):
        if self.filtered(lambda p: p.state != 'draft'):
            raise UserError(_('You cannot remove records which is not draft.'))
        return super(DeliveryNote, self).unlink()

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_deliver(self):
        self._make_activity(groups='flex_delivery_note.group_manufacture')
        self.write({'state': 'deliver', 'delivery_date': fields.Datetime.now()})

    def action_manufacture(self):
        # self.activity_ids.action_feedback()
        self.activity_ids.action_done()
        self._make_activity(groups='flex_delivery_note.group_output')
        self.write({'state': 'manufacture'})

    def action_output(self):
        self.activity_ids.action_done()
        self.write({'state': 'output'})

    def action_done(self):
        self.write({'state': 'done'})

    def _make_activity(self, groups=False):
        if not groups:
            return
        if not isinstance(groups, list):
            groups = [groups]
        users = self.env['res.users'].sudo()
        for group in groups:
            users |= self.env.ref(group).users
        activities = [{
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'res_id': rec.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', self._name)], limit=1).id,
            'icon': 'fa-pencil-square-o',
            'date_deadline': fields.Date.today(),
            'user_id': user.id,
            'note': 'Kindly review and approve'
        } for user in users for rec in self]
        self.env['mail.activity'].create(activities)

