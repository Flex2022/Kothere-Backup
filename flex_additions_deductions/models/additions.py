from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DeductionsLines(models.Model):
    _name = 'additions.lines'
    _description = 'AdditionsLines'

    invoice_id = fields.Many2one('account.move', string='Invoice')
    name = fields.Char()
    # additions_id = fields.Selection([('1', 'دفعة مؤخرة'),], string='Additions')
    additions_id = fields.Many2one('additions.deductions', string='Additions', domain="[('type', '=', '1')]")
    invoice_move_type = fields.Selection(related='invoice_id.move_type', string='Invoice Type')
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    amount_deductions = fields.Float('Amount Deductions')
    is_percentage = fields.Boolean()
    amount = fields.Float('Amount', compute='_compute_amount', store=True)
    percentage_or_value = fields.Float('Percentage Or Value')
    tax_id = fields.Many2one('account.tax', string='Tax')

    @api.onchange('additions_id')
    def onchange_additions_id(self):
        if self.additions_id:
            self.name = 'دفعة مؤخرة'


    @api.depends('is_percentage', 'percentage_or_value', 'amount_deductions', 'invoice_id.amount_total','tax_id')
    def _compute_amount(self):
        for record in self:
            if record.invoice_move_type == 'in_invoice':
                if record.is_percentage:
                    if record.tax_id:
                        tax_id = record.tax_id.amount / 100 + 1
                    else:
                        tax_id = 1
                    record.amount = record.percentage_or_value * record.amount_deductions * tax_id
                else:

                    if record.tax_id:
                        tax_id = record.tax_id.amount / 100 + 1
                    else:
                        tax_id = 1
                    record.amount = record.percentage_or_value * tax_id
            elif record.invoice_move_type == 'out_invoice':
                if record.is_percentage:
                    if record.tax_id:
                        tax_id = record.tax_id.amount / 100 + 1
                    else:
                        tax_id = 1
                    record.amount = record.percentage_or_value * self.invoice_id.amount_total * tax_id
                else:

                    if record.tax_id:
                        tax_id = record.tax_id.amount / 100 + 1
                    else:
                        tax_id = 1
                    record.amount = record.percentage_or_value * tax_id
            elif record.purchase_id:
                if record.is_percentage:
                    if record.tax_id:
                        tax_id = record.tax_id.amount / 100 + 1
                    else:
                        tax_id = 1
                    record.amount = record.percentage_or_value * record.amount_deductions * tax_id
                else:

                    if record.tax_id:
                        tax_id = record.tax_id.amount / 100 + 1
                    else:
                        tax_id = 1
                    record.amount = record.percentage_or_value * tax_id

    @api.constrains('is_percentage', 'percentage_or_value')
    def _check_is_percentage(self):
        for record in self:
            if record.is_percentage:
                if record.percentage_or_value > 1:
                    raise ValidationError('You can not select percentage more than 100%')
                elif record.percentage_or_value < 0:
                    raise ValidationError('You can not select value less than 0')