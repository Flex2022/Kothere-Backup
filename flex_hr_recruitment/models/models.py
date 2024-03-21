from odoo import api, fields, models, _

AVAILABLE_PRIORITIES = [
    ('0', 'Normal'),
    ('1', 'Good'),
    ('2', 'Very Good'),
    ('3', 'Excellent')
]


class EvaluationRate(models.Model):
    _name = 'evaluation.rate'
    _description = 'Evaluation'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Evaluation', default='0')


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    evaluation_rate = fields.One2many('evaluation.applicant', 'hr_application', string='Evaluation Rate')
    name = fields.Char("Subject / Application", help="Email subject for applications sent via email", index='trigram',
                       copy=False, readonly=True, default=lambda self: _('New'))
    partner_name_ar = fields.Char(string='Partner Name Arabic')
    residency_number = fields.Char(string='Residency Number')
    passport_number = fields.Char(string='Passport Number')
    # nationality = fields.Many2one("res.country", string='nationality')
    marital_status = fields.Selection([
        ('single', _('Single')),
        ('married', _('Married')),
        ('divorced', _('Divorced')),
        ('widower', _('Widower')),
    ], string='Marital Status', default='single')
    marital_status_ar = fields.Selection([
        ('single1', 'أعزب'),
        ('married2', 'متزوج'),
        ('divorced3', 'مطلق'),
        ('widower4', 'أرمل'),
    ], string='Marital Status Arabic', default='single1')
    contract_duration = fields.Char(string='Contract Duration', translate=True)
    housing_allowance1 = fields.Float(string='Housing Allowance')
    transportation_allowance1 = fields.Float(string='Transportation Allowance')
    annual_leave = fields.Many2one('annual.leave', string='Annual Leave')
    yearly_ticket = fields.Char(string='Yearly Ticket', translate=True)
    sign_city = fields.Many2one('res.country.state', string='Sign City')
    work_place = fields.Char(string='Work Place', translate=True)
    accept = fields.Boolean(string='Accepted')
    not_accept = fields.Boolean(string='Not Accepted')
    create_date1 = fields.Datetime(string='Create Date', readonly=False)
    start_work_date = fields.Datetime(string='Start Work Date')
    stage_id_char = fields.Char(string='Stage')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_number = fields.Char(string='Employee Number', related='employee_id.employee_number')
    exag = fields.Boolean(string='Exaggeration')
    reas = fields.Boolean(string='Reasonable')
    not_clear = fields.Boolean(string='Not Clear')
    interview_date = fields.Datetime(string='Interview Date')

    long_career = fields.Boolean(string='Long Career')
    not_long_career = fields.Boolean(string='Short Career')

    rec_yes = fields.Boolean(string='Yes')
    rec_no = fields.Boolean(string='No')

    note = fields.Text(string='Note')

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        for rec in self:
            rec.stage_id_char = rec.stage_id.name

    @api.onchange('accept')
    def _onchange_accept(self):
        for rec in self:
            if rec.accept:
                rec.not_accept = False

    @api.onchange('not_accept')
    def _onchange_not_accept(self):
        for rec in self:
            if rec.not_accept:
                rec.accept = False

    @api.onchange('marital_status')
    def _onchange_marital_status(self):
        for rec in self:
            if rec.marital_status == 'single':
                rec.marital_status_ar = 'single1'
            elif rec.marital_status == 'married':
                rec.marital_status_ar = 'married2'
            elif rec.marital_status == 'divorced':
                rec.marital_status_ar = 'divorced3'
            elif rec.marital_status == 'widower':
                rec.marital_status_ar = 'widower4'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.recruitment')
        return super(HrApplicant, self).create(vals_list)

    def action_offer_send(self):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        self.ensure_one()

        lang = self.env.context.get('lang')
        mail_template = self._find_mail_template()
        if mail_template and mail_template.lang:
            lang = mail_template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'hr.applicant',
            'default_res_ids': self.ids,
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            # 'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang)
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def _find_mail_template(self):
        """ Get the appropriate mail template for the current sales order based on its state.

        If the SO is confirmed, we return the mail template for the sale confirmation.
        Otherwise, we return the quotation email template.

        :return: The correct mail template based on the current status
        :rtype: record of `mail.template` or `None` if not found
        """
        self.ensure_one()

        return self.env.ref('flex_hr_recruitment.email_template_edi_offer', raise_if_not_found=False)

        # self.write({'state': 'sent'})

    # def create_employee(self):
    #     self.env['hr.employee'].create({
    #         'name': self.partner_name,
    #         'department_id': self.department_id.id,
    #     })
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Employees',
    #         'res_model': 'hr.employee',
    #         'view_mode': 'tree,form',
    #         'domain': [('name', '=', self.partner_name)],
    #         'context': "{'create': False}"
    #     }

    # if partner_name doesn't exist in hr.employee, create it
    def create_employee(self):
        employee = self.env['hr.employee'].search([('name', '=', self.partner_name)])
        if not employee:
            employee = self.env['hr.employee'].create({
                'name': self.partner_name,
                'department_id': self.department_id.id,
                'private_email': self.email_from,
                'private_phone': self.partner_phone,
                'marital_status': self.marital_status,
                'iqama_id': self.residency_number,
                'passport_id': self.passport_number,
                'country_id': self.nationality.id,
            })
            self.env['hr.contract'].create({
                'name': self.employee_number,
                'employee_id': employee.id,
                'department_id': self.department_id.id,
                'job_id': self.job_id.id,
                # 'job_id': self.job_id.id,
                # 'wage': self.expected_salary,
                # 'date_start': self.contract_start_date,
                # 'date_end': self.contract_end_date,
                'hr_responsible_id': self.user_id.id,
                'wage': self.salary_expected,
                'l10n_sa_housing_allowance': self.housing_allowance1,
                'l10n_sa_transportation_allowance': self.transportation_allowance1,
            })
            for rec in self:
                rec.employee_id = employee.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Employees',
            'res_model': 'hr.employee',
            'view_mode': 'tree,form',
            'res_id': employee.id,
            'domain': [('name', '=', self.partner_name)],
            'context': "{'create': False}"
        }


class EvaluationApplicant(models.Model):
    _name = 'evaluation.applicant'
    _description = 'Evaluation Applicant'
    _rec_name = 'evaluation_rate'

    evaluation_rate = fields.Many2one('evaluation.rate', string='Evaluation Name', required=True)
    hr_application = fields.Many2one('hr.applicant', string='HR Application')
    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Evaluation', related='evaluation_rate.priority',
                                readonly=False, store=True)
    poor = fields.Boolean(string='Poor')
    good = fields.Boolean(string='Good')
    medium = fields.Boolean(string='Medium')
    excellent = fields.Boolean(string='Excellent')


class AnnualLeave(models.Model):
    _name = 'annual.leave'
    _description = 'Annual Leave'

    name = fields.Char(string='Name', translate=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    name_ar = fields.Char(string='Name Arabic')


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    name = fields.Char(string='State Name', required=True,
                       help='Administrative divisions of a country. E.g. Fed. State, Departement, Canton',
                       translate=True)


class GenerateSimulationLink(models.TransientModel):
    _inherit = 'generate.simulation.link'

    employee_new = fields.Char(string='Employee')

    def _get_url_triggers(self):
        return ['applicant_id', 'final_yearly_costs', 'employee_contract_id', 'job_title', 'employee_job_id',
                'department_id', 'contract_start_date', 'contract_end_date', 'employee_new']

    @api.onchange('applicant_id')
    def _onchange_job_selection(self):
        self.employee_new = self.applicant_id.partner_name
        self.department_id = self.applicant_id.department_id
        self.employee_job_id = self.applicant_id.job_id
        # need to bring the contarct_id that similer number to the employee number
        # self.contract_id = self.env['hr.contract'].search([('employee_id', '=', self.applicant_id.employee_id.id)]).id

    # @api.onchange('employee_id','applicant_id')
    # # add domain to contract_id to show only the contract that related to the employee
    # def _onchange_contract_id(self):
    #     for rec in self:
    #         if self.employee_id:
    #             self.contract_id = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)]).id
    #         elif self.applicant_id:
    #             self.contract_id = self.env['hr.contract'].search(
    #                 [('employee_id', '=', self.applicant_id.employee_id.id)]).id

    # like above but limit 1 and order desc
    @api.onchange('employee_id', 'applicant_id')
    def _onchange_contract_id(self):
        for rec in self:
            if self.employee_id:
                self.contract_id = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)], limit=1,
                                                                  order='id desc').id
            elif self.applicant_id:
                self.contract_id = self.env['hr.contract'].search(
                    [('employee_id', '=', self.applicant_id.employee_id.id)], limit=1, order='id desc').id

    def _onchange_employee_id(self):
        # self.employee_new = self.employee_id.name
        self.contract_id = self.env['hr.contract'].search([('name', '=', self.employee_id.employee_number)]).id
        # self.department_id = self.employee_id.department_id

    # create employee


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    marital_status = fields.Selection([
        ('single', _('Single')),
        ('married', _('Married')),
        ('divorced', _('Divorced')),
        ('widower', _('Widower')),
    ], string='Marital Status', default='single')


class HrContract(models.Model):
    _inherit = 'hr.contract'

    contract_duration_ar_month = fields.Selection([
        ('31', '3 أشهر'),
        ('61', '6 أشهر'),
        ('91', '9 أشهر'),
        ('121', '12 أشهر'),
        ('151', '15 أشهر'),
        ('181', '18 أشهر'),
        ('211', '21 أشهر'),
        ('241', '24 أشهر'),

    ], string='Contract Duration Arabic', default=False)

    @api.onchange('contract_type_duration')
    def _onchange_contract_type_duration(self):
        for rec in self:
            if rec.contract_type_duration == '3':
                rec.contract_duration_ar_month = '31'
            elif rec.contract_type_duration == '6':
                rec.contract_duration_ar_month = '61'
            elif rec.contract_type_duration == '9':
                rec.contract_duration_ar_month = '91'
            elif rec.contract_type_duration == '12':
                rec.contract_duration_ar_month = '121'
            elif rec.contract_type_duration == '15':
                rec.contract_duration_ar_month = '151'
            elif rec.contract_type_duration == '18':
                rec.contract_duration_ar_month = '181'
            elif rec.contract_type_duration == '21':
                rec.contract_duration_ar_month = '211'
            elif rec.contract_type_duration == '24':
                rec.contract_duration_ar_month = '241'
