from odoo import api, fields, models, _
import datetime as date


class ClearanceReport(models.Model):
    _inherit = 'hr.contract'

    # Get Employee Data

    national_id = fields.Char(string='National ID', related='employee_id.country_id.name')
    manager_for_employee = fields.Many2one('hr.employee', string='Manager', related='employee_id.parent_id')
    employee_number = fields.Char(string='Employee Number', related='employee_id.employee_number')

    # Get Management Data

    vacation = fields.Boolean(string='Vacation')
    exit = fields.Boolean(string='Exit')

    @api.depends('vacation', 'exit')
    @api.onchange('exit', 'vacation')
    def onchange_vacation_exit(self):
        if self.vacation:
            self.exit = False
        elif self.exit:
            self.vacation = False

    # related management
    Date_of_clearance = fields.Datetime(string='Date of Clearance', compute='_compute_date_of_clearance')
    clear = fields.Boolean(string='Clear')
    not_clear = fields.Boolean(string='Not Clear')
    reason = fields.Char(string='Reason')
    replacement = fields.Many2one('hr.employee', string='Replacement')

    # IT Data
    Name_of_it_person = fields.Many2one('hr.employee', string='Name of IT Person')
    email = fields.Boolean(string='Email')
    Device = fields.Boolean(string='Device')
    other = fields.Boolean(string='Other')
    other_reason = fields.Char(string='Other Reason')
    clear_it = fields.Boolean(string='Clear')
    not_clear_it = fields.Boolean(string='Not Clear')
    reason_it = fields.Char(string='Reason')

    # HR Data
    Name_of_hr_person = fields.Char(string='Name of HR Person', related='employee_id.user_id.name', editable=True)
    housing = fields.Boolean(string='Housing')
    transportation = fields.Boolean(string='Transportation')
    telecom = fields.Boolean(string='Telecom')
    medical_card = fields.Boolean(string='Medical Card')
    emp_card = fields.Boolean(string='Emp Card')
    loans = fields.Boolean(string='Loans')
    business_card = fields.Boolean(string='Business Card')
    gosi = fields.Boolean(string='GOSI')
    custody = fields.Boolean(string='Custody')
    clear_hr = fields.Boolean(string='Clear')
    not_clear_hr = fields.Boolean(string='Not Clear')
    reason_hr = fields.Char(string='Reason')

    #  Accounting Data
    Name_of_acc_person = fields.Many2one('hr.employee', string='Name of Accounting Person')
    clear_acc = fields.Boolean(string='Clear')
    not_clear_acc = fields.Boolean(string='Not Clear')
    reason_acc = fields.Char(string='Reason')

    # شؤون الموظفين
    clear_s = fields.Boolean(string='Clear')
    not_clear_s = fields.Boolean(string='Not Clear')
    reason_s = fields.Char(string='Reason')

    def print_clearance_letter(self):
        return self.env.ref('flex_report_clearance_letter.action_clearance_letter').report_action(self)
    def _compute_date_of_clearance(self):
        for rec in self:
            rec.Date_of_clearance = date.datetime.now().date()
            print(rec.Date_of_clearance)



