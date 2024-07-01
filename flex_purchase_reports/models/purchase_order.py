from odoo import models, fields, api
from hijri_converter import Gregorian
import calendar


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    date_approve_hijri = fields.Char('Confirmation Date (Hijri)', compute="compute_date_approve_hijri")
    partner_presenter_id = fields.Many2one('res.partner', compute="compute_partner_presenter_id", store=True)
    first_party_wishes = fields.Text('رغبات الطرف الأول')
    agreement_purpose = fields.Text('الغرض من العقد')
    agreement_expense = fields.Char('الصرف بعد')
    agreement_condition_ids = fields.One2many('purchase.order.agreement_condition', 'purchase_order_id',
                                              string='Agreement Conditions')
    user_ids = fields.Many2many('res.users', string="Buyers", compute="compute_user_ids", readonly=False, store=True)
    alternative_po_ids = fields.One2many(
        'purchase.order', related='purchase_group_id.order_ids', related_sudo=False, readonly=False,
        domain="[('id', '!=', id), ('state', 'in', ['draft', 'sent', 'to approve'])]",
        string="Alternative POs", check_company=True,
        help="Other potential purchase orders for purchasing products")

    @api.depends('user_id', 'user_ids')
    def compute_user_ids(self):
        for order in self:
            if not self.user_id.id in order.user_ids.ids:
                order.user_ids = [(4, order.user_id.id)] if order.user_id else []

    def compute_date_approve_hijri(self):
        for order in self:
            if order.date_approve:
                # Convert the Gregorian date to Hijri
                gregorian_date = order.date_approve.date()
                hijri_date = Gregorian(gregorian_date.year, gregorian_date.month, gregorian_date.day).to_hijri()
                # Format the Hijri date as a string (e.g., "1445-10-01")
                order.date_approve_hijri = f"{hijri_date.year}-{hijri_date.month:02}-{hijri_date.day:02}"
            else:
                order.date_approve_hijri = ''

    @api.depends('partner_id')
    def compute_partner_presenter_id(self):
        for order in self:
            order.partner_presenter_id = False
            if order.partner_id:
                child_ids = order.partner_id.child_ids.filtered(lambda contact: contact.type == 'contact')
                if child_ids:
                    order.partner_presenter_id = child_ids[0]

    @api.model
    def get_arabic_day_name(self, date):
        day_of_week_index = date.weekday()
        # List of weekday names
        weekday_names = ["الإثنين", "الثلثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        return weekday_names[day_of_week_index]


class PurchaseOrderAgreementCondition(models.Model):
    _name = 'purchase.order.agreement_condition'
    _description = 'Purchase Order Agreement Condition'

    name = fields.Text('Condition', required=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', ondelete='cascade')
