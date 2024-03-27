from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DeductionsLines(models.Model):
    _name = 'deductions.lines'
    _description = 'DeductionsLines'

    invoice_id = fields.Many2one('account.move', string='Invoice')
    name = fields.Char()
    deductions_id = fields.Many2one('additions.deductions', string='Deductions', domain="[('type', '=', '2')]")
    is_percentage = fields.Boolean()
    amount = fields.Float('Amount', compute='_compute_amount', store=True)
    percentage_or_value = fields.Float('Percentage Or Value')
    tax_id = fields.Many2one('account.tax', string='Tax')

    @api.onchange('deductions_id')
    def onchange_deductions_id(self):
        if self.deductions_id.type_deductions == '1':
            self.name = 'الخصم'
        elif self.deductions_id.type_deductions == '2':
            self.name = 'التامينات'
        elif self.deductions_id.type_deductions == '3':
            self.name = 'دفعة مقدمة'
        elif self.deductions_id.type_deductions == '4':
            self.name = 'ضمان اعمال'
        elif self.deductions_id.type_deductions == '5':
            self.name = 'ضمان نهائي'

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
    def create_journal_entry(self):
        self.env['account.move'].create({
            'type': 'entry',
            'journal_id': 1,
            'line_ids': [
                (0, 0, {
                    'name': '111',
                    'account_id': 1,
                    'debit': 100,
                }),
                (0, 0, {
                    'name': '222',
                    'account_id': 2,
                    'credit': 100,
                }),
            ],
        })

    @api.constrains('is_percentage', 'percentage_or_value')
    def _check_is_percentage(self):
        for record in self:
            if record.is_percentage:
                if record.percentage_or_value > 1:
                    raise ValidationError('You can not select percentage more than 100%')
                elif record.percentage_or_value < 0:
                    raise ValidationError('You can not select value less than 0')