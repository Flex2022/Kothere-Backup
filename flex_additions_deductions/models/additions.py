from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DeductionsLines(models.Model):
    _name = 'additions.lines'
    _description = 'AdditionsLines'

    invoice_id = fields.Many2one('account.move', string='Invoice')
    name = fields.Char()
    # additions_id = fields.Selection([('1', 'دفعة مؤخرة'),], string='Additions')
    additions_id = fields.Many2one('additions.deductions', string='Deductions', domain="[('type', '=', '1')]")

    is_percentage = fields.Boolean()
    amount = fields.Float('Amount', compute='_compute_amount', store=True)
    percentage_or_value = fields.Float('Percentage Or Value')
    tax_id = fields.Many2one('account.tax', string='Tax')

    @api.onchange('additions_id')
    def onchange_additions_id(self):
        if self.additions_id:
            self.name = 'دفعة مؤخرة'

    @api.depends('is_percentage', 'percentage_or_value')
    def _compute_amount(self):
        for record in self:
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

    @api.constrains('is_percentage', 'percentage_or_value')
    def _check_is_percentage(self):
        for record in self:
            if record.is_percentage and record.percentage_or_value > 1:
                raise ValidationError('You can not select percentage more than 100%')
            elif not record.is_percentage and record.percentage_or_value > 0:
                raise ValidationError('You can not select value more than 0')