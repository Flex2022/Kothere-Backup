# -*- coding: utf-8 -*-
from odoo import fields, models, api, _, SUPERUSER_ID


# from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    vendor_type = fields.Selection([('local', 'Local'), ('international', 'International')],
                                   string="Vendor Type", default=False, compute="_compute_vendor_type", readonly=False,
                                   store=True)
    name_ar = fields.Char(string="Arabic Name")
    phone = fields.Char(string="Phone 1")
    mobile = fields.Char(string="Phone 2")
    fax = fields.Char(string="Fax")
    linkedin = fields.Char(string="LinkedIn Account")

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if not recs:
            recs = self.search(['|', ('name_ar', operator, name), ('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.depends('supplier')
    def _compute_vendor_type(self):
        for rec in self:
            if rec.supplier:
                rec.vendor_type = rec.vendor_type
            else:
                rec.vendor_type = False


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def create(self, vals):
        employee = super(HrEmployee, self).create(vals)
        if not employee.user_id:  # Ensure that this is not a system-generated employee
            # Create a new contact based on the employee's data
            contact_vals = {
                'name': employee.name,
                'phone': employee.mobile_phone,
                'mobile': employee.work_phone,
                'email': employee.work_email,
                'street': employee.address_id.street,
                'street2': employee.address_id.street2,
                'city': employee.address_id.city,
                'state_id': employee.address_id.state_id.id,
                'zip': employee.address_id.zip,
                'country_id': employee.address_id.country_id.id,
            }
            contact = self.env['res.partner'].create(contact_vals)
            # Link the contact to the employee
            employee.address_home_id = contact.id
        return employee
