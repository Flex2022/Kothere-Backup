from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_number = fields.Char(string='Employee Number', compute="compute_employee_number", store=True,
                                  readonly=True)

    @api.depends('department_id')
    def compute_employee_number(self):
        for employee in self:
            if employee.id:
                if employee.department_id:
                    employee.employee_number = "{}{}".format(employee.department_id.sequence,
                                                             employee.department_id.next_seq)
                    employee.department_id.next_seq += 1


class HrContract(models.Model):
    _inherit = 'hr.contract'

    name = fields.Char('Contract Reference', required=True, related='employee_id.employee_number',
                       readonly=True)
