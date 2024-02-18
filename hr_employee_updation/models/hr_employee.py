# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import models, fields, _, api
# from dateutil.relativedelta import relativedelta
# from odoo.osv import expression
# from odoo.exceptions import UserError
from . import notification_and_email


# GENDER_SELECTION = [('male', 'Male'),
#                     ('female', 'Female'),
#                     ('other', 'Other')]


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # def mail_reminder(self):
    #     """Sending expiry date notification for ID and Passport"""
    #
    #     match = self.search([])
    #     hr_admin_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr_employee_updation.group_admin_notification').id)], limit=1, order="id desc")
    #
    #     for i in match:
    #         if i.id_expiry_date:
    #             exp_date = (i.id_expiry_date - fields.Date.today()).days
    #             if exp_date in (14, 7, 0):
    #                 mail_content = "  Hello  " + i.name + ",<br><br>Your ID " + i.identification_id + "is going to expire on " + \
    #                                str(i.id_expiry_date) + ".<br> Please renew it before expiry date"
    #                 author = self.env.user.partner_id.id
    #                 subject = _('ID-%s Expired On %s') % (i.identification_id, i.id_expiry_date),
    #                 email_to = i.work_email + ',' + hr_admin_id.email
    #                 warning = ""
    #                 notification_and_email.send_email(i, email_to, author, subject, mail_content, warning)
    #
    #     match1 = self.search([])
    #     for i in match1:
    #         if i.passport_expiry_date:
    #             exp_date = (i.passport_expiry_date - fields.Date.today()).days
    #             if exp_date in (30, 21, 14, 7, 0):
    #                 mail_content = "  Hello  " + i.name + ",<br><br>Your Passport " + i.passport_id + "is going to expire on " + \
    #                                str(i.passport_expiry_date) + ".<br> Please renew it before expiry date"
    #                 author = self.env.user.partner_id.id
    #                 subject = _('Passport-%s Expired On %s') % (i.passport_id, i.passport_expiry_date),
    #                 email_to = i.work_email + ',' + hr_admin_id.email
    #                 warning = ""
    #                 notification_and_email.send_email(i, email_to, author, subject, mail_content, warning)
    #
    # english_name = fields.Char('Arabic Name', tracking=True)
    # name_in_id = fields.Char('Name in ID', tracking=True)
    # name_in_id_english = fields.Char('Name in ID (English)', tracking=True)
    employee_number = fields.Char('Employee Number', tracking=True)

    # iban = fields.Char('IBAN Number', tracking=True)
    # personal_mobile = fields.Char(string='Mobile', related='address_home_id.mobile', store=True, help="Personal mobile number of the employee", tracking=True)
    # joining_date = fields.Date(string='Joining Date', help="Employee joining date computed from the contract start date", tracking=True)
    # id_expiry_date = fields.Date(string='ID Expiry Date', help='Expiry date of Identification ID', tracking=True)
    # passport_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Passport ID', tracking=True)
    # id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_rel', 'id_ref', 'attach_ref', string="Attachment", help='You can attach the copy of your Id', tracking=True)
    # passport_attachment_id = fields.Many2many('ir.attachment', 'passport_attachment_rel', 'passport_ref', 'attach_ref1', string="Attachment", help='You can attach the copy of Passport', tracking=True)
    # fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family', help='Family Information', tracking=True)
    # medical = fields.Selection([('no', 'No'), ('yes', 'Yes'), ('not', 'Not Yet')], 'Medical Status', tracking=True)
    # certificate = fields.Selection([('secondary', 'Secondary School'), ('high', 'High School'), ('diploma', 'Diploma'),
    #                                 ('bachelor', 'Bachelors Degree'), ('master', 'Masters Degree'), ('doctorate', 'Doctorates Degree'),
    #                                 ('other', 'Other')], 'Certificate Level', default='other', groups="hr.group_hr_user", tracking=True)
    # graduation_year = fields.Char('Graduation Year', tracking=True)
    # work_phone = fields.Char('Work Phone Ext', tracking=True)
    # work_mobile_ext = fields.Char('Work Mobile Ext', tracking=True)
    # is_manager = fields.Boolean('Is a Manager?', tracking=True)
    # office_id = fields.Many2one('hr.employee.office.location', 'Office Location', tracking=True)
    # religion = fields.Selection([('muslim', 'Muslim'), ('other', 'Other')], string='Religion', tracking=True)
    # calculate_leave = fields.Boolean('Calculate Leave', default=True, readonly=True, compute="_calculate_leave", store=True, tracking=True)
    # employee_status = fields.Selection([('period', 'Trial Period'), ('employee', 'Permanent Employee')], string='Status', compute='_employee_status', store=True, tracking=True)
    # contract_start_date = fields.Date('Contract Start Date', related='contract_id.date_start')
    # contract_end_date = fields.Date('Contract End Date', related='contract_id.date_end')
    # contract_total_salary = fields.Float('Total Salary', related='contract_id.total_salary', tracking=False)
    # user_check_tick = fields.Boolean('User Check', default=False)
    # employment_type = fields.Selection([('full', 'Full Time'), ('part', 'Part Time'), ('trainee', 'Trainee')], string='Employment Type', tracking=True)
    # employee_private_email = fields.Char('Private Email', tracking=True)
    # employee_private_phone = fields.Char('Private Phone', tracking=True)
    notice_period_flag = fields.Boolean('Under Notice Period', tracking=True)

    # residence_place_id = fields.Many2one('res.country.state', 'Residence Place', tracking=True)
    # specialization_id = fields.Many2many('hr.specialization', string='Specialization', tracking=True)
    # department_id = fields.Many2one('hr.department', 'Department', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=True)
    # job_id = fields.Many2one('hr.job', 'Job Position', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=True)
    # work_email = fields.Char('Work Email', tracking=True)
    # work_location = fields.Char('Work Location', tracking=True)
    # user_id = fields.Many2one('res.users', tracking=True)
    # resource_id = fields.Many2one('resource.resource', tracking=True)
    # resource_calendar_id = fields.Many2one('resource.calendar', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=True)
    # parent_id = fields.Many2one('hr.employee', 'Manager', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=True)
    # coach_id = fields.Many2one('hr.employee', 'Coach', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=True)
    #
    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = args or []
    #     domain = []
    #     if name:
    #         domain = ['|', ('name', operator, name), ('english_name', operator, name)]
    #     employee_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
    #     return models.lazy_name_get(self.browse(employee_ids).with_user(name_get_uid))
    #
    # def write(self, vals):
    #     if 'is_manager' in vals:
    #         group_id = self.sudo().env.ref('hr_employee_updation.group_hr_request_team_lead_approval')
    #         if vals['is_manager']:
    #             group_id.sudo().write({'users': [(4, self.user_id.id)]})
    #         else:
    #             group_id.sudo().write({'users': [(3, self.user_id.id)]})
    #     return super(HrEmployee, self).write(vals)
    #
    # def create_user(self):
    #     user_id = self.env['res.users'].create({'name': self.name, 'login': self.work_email})
    #     self.user_id = user_id.id
    #     self.address_home_id = user_id.partner_id.id
    #     self.address_home_id.email = self.work_email
    #     user_id.with_context(create_user=1).action_reset_password()
    #     self.user_check_tick = True
    #
    #     if not self.department_id.non_t2:
    #         group_id = self.sudo().env.ref('hr_employee_updation.group_hr_t2_employee')
    #         group_id.sudo().write({'users': [(4, user_id.id)]})
    #
    # @api.onchange('address_home_id')
    # def user_checking(self):
    #     if self.address_home_id:
    #         self.user_check_tick = True
    #     else:
    #         self.user_check_tick = False
    #
    # @api.onchange('parent_id')
    # def leave_manager(self):
    #     if self.parent_id:
    #         self.leave_manager_id = self.parent_id.user_id.id
    #
    # @api.onchange('department_id', 'job_id')
    # def department_job_contract(self):
    #     self.contract_id.department_id = self.department_id.id
    #     self.contract_id.job_id = self.job_id.id
    #
    # def _sync_user(self, user):
    #     vals = {}
    #     if user.tz:
    #         vals['tz'] = user.tz
    #     return vals
    #
    # @api.onchange('employment_type')
    # def onchange_employment(self):
    #     if self.employment_type == "full":
    #         self.joining_date = False
    #
    # @api.depends('employment_type')
    # def _calculate_leave(self):
    #     if self.employment_type == "full":
    #         self.calculate_leave = True
    #     else:
    #         self.calculate_leave = False
    #
    # @api.onchange('office_id')
    # def onchange_office_location(self):
    #     if self.office_id:
    #         self.tz = self.office_id.tz
    #         self.resource_calendar_id = self.office_id.resource_calendar_id
    #         category_id = self.env['hr.leave.rule'].search([('office_id', '=', self.office_id.id)], order='sequence asc', limit=1).category_id
    #         if category_id:
    #             self.category_ids = [(6, 0, [category_id.id])]
    #
    # def _check_employee_years(self):
    #     employees = self.env['hr.employee'].search([('office_id', '!=', False)])
    #     for rec in employees:
    #         current_year = fields.Date.today()
    #         join = rec.joining_date
    #         if join and rec.calculate_leave:
    #             category_id = False
    #             diff_date = relativedelta(current_year, join)
    #             months = diff_date.years * 12 + diff_date.months
    #             diff_years = int(months / 12)
    #             rule_ids = self.env['hr.leave.rule'].search([('office_id', '=', rec.office_id.id), ('leave_type_id.leave_type', '=', 'annual')])
    #             for rule in rule_ids:
    #                 if diff_years >= int(rule.from_year) and diff_years < int(rule.to_year):
    #                     category_id = rule.category_id
    #
    #             if category_id:
    #                 rec.category_ids = [(6, 0, [category_id.id])]
    #
    # @api.onchange('spouse_complete_name', 'spouse_birthdate')
    # def onchange_spouse(self):
    #     relation = self.env.ref('hr_employee_updation.employee_relationship')
    #     lines_info = []
    #     spouse_name = self.spouse_complete_name
    #     date = self.spouse_birthdate
    #     if spouse_name and date:
    #         lines_info.append((0, 0, {
    #             'member_name': spouse_name,
    #             'relation_id': relation.id,
    #             'birth_date': date,
    #         })
    #                           )
    #         self.fam_ids = [(6, 0, 0)] + lines_info

    @api.model
    def create(self, vals):
        vals['employee_number'] = self.env['ir.sequence'].next_by_code('hr.employee.number')
        res = super(HrEmployee, self).create(vals)
        # self.send_employee_details_for_manager(res)
        # self.send_employee_details_for_hr_user(res)
        # self.send_employee_details_for_product_manager(res)
        # if 'is_manager' in vals:
        #     group_id = self.sudo().env.ref('hr_employee_updation.group_hr_request_team_lead_approval')
        #     if vals['is_manager']:
        #         group_id.sudo().write({'users': [(4, self.user_id.id)]})
        return res


#     def send_employee_details_for_manager(self, res):
#         if res.parent_id.user_id:
#             mail_content = _("New Employee added."
#                              "<br> Name : %s"
#                              "<br> Starting Date: %s"
#                              "<br> Employment Type: %s"
#                              "<br><br> Best Regards,") % (res.name, res.joining_date, dict(self._fields['employment_type'].selection).get(res.employment_type))
#             author = res.parent_id.user_id.partner_id.id
#             subject = _('New Employee Added')
#             email_to = res.parent_id.work_email
#             warning = "send email warning"
#             notification_and_email.send_email(self, email_to, author, subject, mail_content, warning)
#
#     def send_employee_details_for_hr_user(self, res):
#         users = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr_employee_updation.group_notification_new_employee').id)], order="id desc")
#         for rec in users:
#             mail_content = _("New Employee added."
#                              "<br> Name : %s"
#                              "<br> Starting Date: %s"
#                              "<br> Employment Type: %s"
#                              "<br><br> Best Regards,") % (res.name, res.joining_date, dict(self._fields['employment_type'].selection).get(res.employment_type))
#             author = rec.partner_id.id
#             subject = _('New Employee Added')
#             email_to = rec.email
#             warning = "send email warning"
#             notification_and_email.send_email(self, email_to, author, subject, mail_content, warning)
#
#     def send_employee_details_for_product_manager(self, res):
#         users = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr_employee_updation.group_product_manager_notification').id)], order="id desc")
#         for rec in users:
#             mail_content = _("New Employee added."
#                              "<br> Name : %s"
#                              "<br> Starting Date: %s"
#                              "<br> Employment Type: %s"
#                              "<br><br> Best Regards,") % (res.name, res.joining_date,
#                                                           dict(self._fields['employment_type'].selection).get(
#                                                               res.employment_type))
#             author = rec.partner_id.id
#             subject = _('New Employee Added')
#             email_to = rec.email
#             warning = "send email warning"
#             notification_and_email.send_email(self, email_to, author, subject, mail_content, warning)
#
#     def delete_unused_leaves(self):
#         for rec in self.env['hr.employee'].search([]):
#             if rec.employee_id.remaining_leaves > rec.employee_id.office_id.allocation_per_year:
#                 holiday_status_id = self.env['hr.leave.type'].search([('leave_type', '=', 'annual')], limit=1)
#                 allocation = self.env['hr.leave.allocation'].create({
#                     'name': "Delete unused vacations",
#                     'holiday_status_id': holiday_status_id.id,
#                     'number_of_days': rec.office_id.allocation_per_year - rec.remaining_leaves,
#                     'holiday_type': 'employee',
#                     'employee_id': rec.id,
#                 })
#                 allocation.action_approve()
#                 allocation.action_validate()
#
#     def alert_employee_for_unused_leaves(self):
#         for rec in self.env['hr.employee'].search([]):
#             if rec.remaining_leaves > (rec.office_id.allocation_per_year / 2):
#                 mail_content = "Dear  " + rec.name + ",<br> <br> We would like to inform you that only %s days of " \
#                                                      "your annual leave balance will be transferred to the next " \
#                                                      "year, while the rest of the days will be deleted without any " \
#                                                      "compensation. <br><br>" \
#                                                      "We suggest that you schedule your leaves according to days " \
#                                                      "that suit with you and arrange with your direct manager. <br><br>" \
#                                                      "Thanks and good luck," % int(rec.office_id.allocation_per_year / 2)
#                 main_content = {
#                     'subject': _('REMINDER to Leave Balance'),
#                     'author_id': self.env.user.partner_id.id,
#                     'body_html': mail_content,
#                     'email_to': rec.work_email,
#                 }
#                 mail_id = self.env['mail.mail'].sudo().create(main_content)
#                 mail_id.mail_message_id.body = mail_content
#                 mail_id.send()
#
#     @api.depends('contract_id')
#     def _employee_status(self):
#         for rec in self.env['hr.employee'].search([('active', '=', True)]):
#             if rec.contract_id:
#                 if rec.contract_id.trial_date_end:
#                     if rec.contract_id.trial_date_end < fields.Date.today():
#                         rec.employee_status = 'employee'
#                     else:
#                         rec.employee_status = 'period'
#                 else:
#                     rec.employee_status = 'employee'
#
#
# class EmployeeRelationInfo(models.Model):
#     """Table for keep employee family information"""
#     _name = 'hr.employee.relation'
#
#     name = fields.Char(string="Relationship", help="Relationship with thw employee")
#
#
# class HrEmployeePublic(models.Model):
#     _inherit = 'hr.employee.public'
#
#     english_name = fields.Char('English Name', readonly=True)
#     employee_number = fields.Char('Employee Number', readonly=True)
#     iban = fields.Char('IBAN Number', readonly=True)
#     personal_mobile = fields.Char('Mobile', readonly=True)
#     joining_date = fields.Date('Joining Date', readonly=True)
#     id_expiry_date = fields.Date('Expiry Date', readonly=True)
#     passport_expiry_date = fields.Date('Expiry Date', readonly=True)
#     id_attachment_id = fields.Many2many('ir.attachment', 'idp_attachment_rel', 'id_ref', 'attach_ref', "Attachment", readonly=True)
#     passport_attachment_id = fields.Many2many('ir.attachment', 'ppassport_attachment_rel', 'passport_ref', 'attach_ref1', "Attachment", readonly=True)
#     fam_ids = fields.One2many('hr.employee.family', 'employee_id', 'Family', readonly=True)
#     medical = fields.Selection([('no', 'No'), ('yes', 'Yes'), ('not', 'Not Yet')], 'Medical Status', readonly=True)
#     graduation_year = fields.Char('Graduation Year', readonly=True)
#     work_mobile_ext = fields.Char('Work Mobile Ext', readonly=True)
#     is_manager = fields.Boolean('Is a Manager?', readonly=True)
#     office_id = fields.Many2one('hr.employee.office.location', 'Office Location', readonly=True)
#     religion = fields.Selection([('muslim', 'Muslim'), ('other', 'Other')], 'Religion', readonly=True)
#     calculate_leave = fields.Boolean('Calculate Leave', readonly=True)
#     employee_private_email = fields.Char('Private Email', readonly=True)
#     employee_private_phone = fields.Char('Private Phone', readonly=True)
#     residence_place_id = fields.Many2one('res.country.state', 'Residence Place', readonly=True)
#
#
class Department(models.Model):
    _name = 'hr.department'
    _inherit = ['hr.department', 'analytic.mixin']

    analytic_distribution = fields.Many2one('account.analytic.account', string='Analytic Account')
    non_t2 = fields.Boolean('Non-T2')
#
#
# class HrEmployeeFamilyInfo(models.Model):
#     """Table for keep employee family information"""
#
#     _name = 'hr.employee.family'
#     _description = 'HR Employee Family'
#
#     employee_id = fields.Many2one('hr.employee', string="Employee", help='Select corresponding Employee',
#                                   invisible=1)
#     relation_id = fields.Many2one('hr.employee.relation', string="Relation", help="Relationship with the employee")
#     member_name = fields.Char(string='Name')
#     member_contact = fields.Char(string='Contact No')
#     birth_date = fields.Date(string="DOB", tracking=True)
#
#
# class HrEmployeeBase(models.AbstractModel):
#     _inherit = "hr.employee.base"
#
#     def _compute_total_allocation_used(self):
#         for employee in self:
#             employee.allocation_used_count = float("%.2f" % round(employee.allocation_count, 2)) - float("%.2f" % round(employee.remaining_leaves, 2))
#             employee.allocation_used_display = "%.2f" % round(employee.allocation_used_count, 2)
#
#
# class MailActivity(models.Model):
#     _inherit = "mail.activity"
#
#     user_id = fields.Many2one('res.users', 'Assigned to', index=True, required=True, default=0)
#
#
# class Specialization(models.Model):
#     _name = 'hr.specialization'
#
#     name = fields.Char('Job Specialization')
