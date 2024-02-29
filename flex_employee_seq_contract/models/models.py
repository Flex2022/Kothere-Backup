from odoo import api, fields, models


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    sequence = fields.Char(string='Prefix', required=True, copy=False)
    next_seq = fields.Integer('Next Sequence', default=1)

    @api.model
    def create(self, vals):
        if not vals.get('sequence'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code('hr.department.sequence')
        return super(HrDepartment, self).create(vals)
