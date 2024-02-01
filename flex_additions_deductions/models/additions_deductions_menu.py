from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Additions_deductions(models.Model):
    _name = 'additions.deductions'
    _description = 'AdditionsDeductions'
    _rec_name = 'name'

    # Main Fields
    name = fields.Char()
    type = fields.Selection([('1', 'Additions'),
                             ('2', 'Deductions')], string='Type')
    account_id = fields.Many2one('account.account', string='Account')
    type_deductions = fields.Selection([('1', 'الخصم'),
                                        ('2', 'التامينات'),
                                        ('3', 'دفعة مقدمة'),
                                        ('4', 'ضمان اعمال')], string='Deductions')


    def open_additions_deductions_menu(self):
        return {
            'name': 'Additions & Deductions',
            'view_mode': 'tree,form',
            'res_model': 'additions.deductions',
            'type': 'ir.actions.act_window',
            'domain': [('type', '=', '1')],
        }

    def open_additions_deductions_menu_deductions(self):
        return {
            'name': 'Additions & Deductions',
            'view_mode': 'tree,form',
            'res_model': 'additions.deductions',
            'type': 'ir.actions.act_window',
            'domain': [('type', '=', '2')],
        }

    @api.constrains('type', 'type_deductions')
    def _check_type(self):
        for record in self:
            if record.type == '1' and record.type_deductions:
                raise ValidationError('You can not select type deductions with type additions')
            elif record.type == '2' and not record.type_deductions:
                raise ValidationError('You must select type deductions with type deductions')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)