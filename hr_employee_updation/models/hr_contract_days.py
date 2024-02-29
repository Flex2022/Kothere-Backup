# -*- coding: utf-8 -*-
# from addons.base_gengo.models.res_company import res_company
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from . import notification_and_email


class ReasonForEndOfService(models.Model):
    _name = 'reason.for.end.of.service'
    _rec_name = 'name'
    _description = 'Reason For End Of Service'

    name = fields.Char('Reason For End Of Service', required=True)
    name_arabic = fields.Char('Reason For End Of Service In Arabic', required=True)

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, '%s %s' % (record.name, record.name_arabic)))
        return res


class HrEmployeeContract(models.Model):
    _inherit = 'hr.contract'

    @api.depends('wage', 'housing_allowance_type', 'housing_allowance_value', 'mobile_allowance_type',
                 'other_allowance_type',
                 'mobile_allowance_value', 'transportation_allowance_type', 'transportation_allowance_value',
                 'other_allowance_value',
                 'variable_increase')
    def _compute_total_salary(self):
        for contract in self:
            housing_amount = transportation_amount = mobile_amount = other_amount = 0.0

            if contract.housing_allowance_type == 'amount':
                housing_amount = contract.housing_allowance_value
            elif contract.housing_allowance_type == 'percentage':
                housing_amount = contract.housing_allowance_value * contract.wage / 100

            if contract.transportation_allowance_type == 'amount':
                transportation_amount = contract.transportation_allowance_value
            elif contract.transportation_allowance_type == 'percentage':
                transportation_amount = contract.transportation_allowance_value * contract.wage / 100

            if contract.mobile_allowance_type == 'amount':
                mobile_amount = contract.mobile_allowance_value
            elif contract.mobile_allowance_type == 'percentage':
                mobile_amount = contract.mobile_allowance_value * contract.wage / 100

            if contract.other_allowance_type == 'amount':
                other_amount = contract.other_allowance_value
            elif contract.other_allowance_type == 'percentage':
                other_amount = contract.other_allowance_value * contract.wage / 100

            contract.total_salary = contract.wage + housing_amount + transportation_amount + mobile_amount + other_amount
            contract.total_with_variable_increase = contract.total_salary + contract.variable_increase
            currency_id_arabic = self.env['res.currency'].browse(153)
            currency_id_english = self.env['res.currency'].browse(2)
            contract.tafqit_arabic = str(currency_id_arabic.amount_to_text(contract.total_salary))
            contract.tafqit_english = str(currency_id_english.amount_to_text(contract.total_salary))

    def _get_default_notice_days(self):
        if self.env['ir.config_parameter'].get_param('hr_resignation.notice_period'):
            return self.env['ir.config_parameter'].get_param('hr_resignation.no_of_days')
        else:
            return 0

    def _compute_service_year(self):
        for rec in self:
            if rec.employee_id.joining_date:
                now = fields.Date.today()
                diff = relativedelta(now, rec.employee_id.joining_date)
                rec.service_year = diff.years
                rec.service_month = diff.months
                rec.service_day = diff.days

    def _get_default_hr_user(self):
        try:
            return self.env['res.users'].search(
                [('groups_id', 'in', self.env.user.has_group('hr_employee_updation.group_hr_notification').id)],
                limit=1,
                order="id desc")
        except:
            return False

    hr_leave_id = fields.Many2one('hr.leave.allocation', string='Leave Request', compute='_compute_hr_leave_id')
    notice_days = fields.Integer(string="Notice Period", default=_get_default_notice_days)
    transportation_allowance_type = fields.Selection([('amount', 'Amount'), ('percentage', 'Percentage')],
                                                     tracking=True, string='Transportation', default='amount')
    transportation_allowance_value = fields.Float('Transportation Value', tracking=True, )
    housing_allowance_type = fields.Selection([('amount', 'Amount'), ('percentage', 'Percentage')], tracking=True,
                                              string='Housing', default='amount')
    housing_allowance_value = fields.Float('Housing Value', tracking=True)
    mobile_allowance_type = fields.Selection([('amount', 'Amount'), ('percentage', 'Percentage')], string='Mobile',
                                             tracking=True, default='amount')
    other_allowance_type = fields.Selection([('amount', 'Amount'), ('percentage', 'Percentage')], string='Other',
                                            tracking=True, default='amount')
    mobile_allowance_value = fields.Float('Mobile Value', tracking=True)
    other_allowance_value = fields.Float('Other Value', tracking=True)
    total_salary = fields.Float('Total Salary', compute='_compute_total_salary', store=True, tracking=True)
    with_gosi = fields.Boolean('With GOSI/SS', tracking=True)
    variable_increase = fields.Float('Variable Increase', tracking=True)
    increase_schedule = fields.Selection([('1', 'Monthly'), ('3', 'Quarterly'), ('6', 'Half Yearly')], tracking=True,
                                         string='Increase Schedule', default='3')
    increase_start_date = fields.Date('Increase Start Date')
    contract_period_type = fields.Selection([('limited', 'Limited'), ('unlimited', 'Unlimited')], string='Period Type',
                                            default='limited')
    hr_user_id = fields.Many2one('res.users', 'HR User', default=_get_default_hr_user)
    service_year = fields.Integer('Year', compute='_compute_service_year')
    service_month = fields.Integer('Month', compute='_compute_service_year')
    service_day = fields.Integer('Day', compute='_compute_service_year')
    leave_provision = fields.Float('Leave Provision')
    eos_provision = fields.Float('EOS Provision')
    currency_id = fields.Many2one("res.currency", related=False, readonly=False, required=True,
                                  default=lambda self: self.env.user.company_id.currency_id,
                                  track_visibility='always')
    contract_template = fields.Html('Contract Template')
    attached = fields.Binary(string='UPLOAD YOUR FILE', track_visibility='always', readonly=True,
                             states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    stop_daily_notification = fields.Boolean('Stop Notification')
    total_with_variable_increase = fields.Float('Total with Variable Increase', compute='_compute_total_salary',
                                                store=True, tracking=True)
    tafqit_arabic = fields.Char('Tafqit Arabic')
    tafqit_english = fields.Char('Tafqit English')
    payroll_days = fields.Float('Payroll Due Days ')
    days_of_the_month = fields.Float('Days of the Month', default=30, store=False)
    number_od_days_off = fields.Float('Number of Days Off', compute='_compute_number_of_days_off', store=False)
    reason_end_service = fields.Many2one('reason.for.end.of.service', string='Reason for End of Service')
    name_arabic = fields.Many2one('reason.for.end.of.service', string='Reason for End of Service')

    salary_if_any = fields.Float('Salary if any', digits=(12, 2), compute='_compute_salary_if_any', store=True)
    overtime = fields.Char('Overtime', digits=(12, 2))
    vacation_benefits = fields.Float('Vacation', digits=(12, 2), compute='_compute_vacation')
    end_of_service = fields.Float('End of Service', digits=(12, 2), related='bonus_amount')
    other_benefits = fields.Float('Other ', digits=(12, 2))
    total_amount_due = fields.Float('Total Amount Due', digits=(12, 2), compute='_compute_total_amount_due', store=True)
    his_predecessor_is_due = fields.Float('His Predecessor is Due', digits=(12, 2))
    covenant_deductions = fields.Float('Covenant', digits=(12, 2))
    vacations_paid_deductions = fields.Float('Vacations Paid', digits=(12, 2))
    loan_deductions = fields.Float('Loan', digits=(12, 2))
    other_deductions = fields.Float('Other', digits=(12, 2))
    total_amount_deductions = fields.Float('Total Amount Deduction', digits=(12, 2),
                                           compute='_compute_total_amount_deductions', store=True)
    net_receivables = fields.Float('Net Receivables', digits=(12, 2), compute='_compute_net_receivables', store=True)
    service_duration_days = fields.Integer(compute="_compute_service_duration")
    service_duration_months = fields.Integer(compute="_compute_service_duration")
    service_duration_years = fields.Integer(compute="_compute_service_duration")

    contract_type_sel = fields.Selection(
        [('saudi', 'Saudi'), ('non_saudi', 'Non Saudi'), ('remote_work', 'Remote Work'), ('part_time', 'Part Time')],
        string='Contract Type', default='saudi')

    types_of_end_services = fields.Selection(
        [('end_of_the_contract',
          'فسخ العقد من قبل العامل أو ترك العامل العمل لغير الحالات الواردة في المادة (81)'),
         ('employees_resignation', 'استقاله العامل (قبل انتهاء العمل)'),
         ('separation_of_the_work', 'فسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)')],
        string='Types Of End Services')

    bonus_amount = fields.Float(string='Bonus Amount', compute='_compute_bonus_amount')

    days_spent_in_current_month = fields.Float(string='Days Spent in Current Month',
                                               compute='_compute_days_spent_in_current_month')

    @api.depends('employee_id')
    def _compute_hr_leave_id(self):
        for rec in self:
            rec.hr_leave_id = self.env['hr.leave.allocation'].search(
                [('employee_id', '=', rec.employee_id.id)], limit=1)

    @api.depends('hr_leave_id')
    def _compute_number_of_days_off(self):

        for rec in self:
            hr_leave_report = rec.env['hr.leave.report'].search(
                [('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate')])
            if rec.hr_leave_id:
                rec.number_od_days_off = sum(hr_leave_report.mapped('number_of_days'))
            else:
                rec.number_od_days_off = 0.0

    @api.onchange('state')
    def onchange_payroll_days(self):
        for rec in self:
            if rec.state == 'close':
                rec.payroll_days = rec.days_spent_in_current_month
            else:
                rec.payroll_days = 0.0

    @api.depends('days_spent_in_current_month')
    def _compute_days_spent_in_current_month(self):
        for record in self:
            today = fields.Date.today()
            first_day_of_month = today.replace(day=1)
            days_spent = (today - first_day_of_month).days + 1
            record.days_spent_in_current_month = days_spent

    @api.onchange('bonus_amount')
    def onchange_end_of_service(self):
        for rec in self:
            if rec.bonus_amount:
                rec.end_of_service = rec.bonus_amount
            else:
                rec.end_of_service = 0.0

    @api.depends('types_of_end_services')
    def _compute_bonus_amount(self):
        for rec in self:
            employee_contracts_ids = self.env['hr.contract'].search(
                [('state', 'in', ['open', 'close']), ('employee_id', '=', rec.employee_id.id)])
            working_years = 0
            for record in employee_contracts_ids:
                if record.state == 'open':
                    working_years += (((fields.Date.today() - record.date_start).days + 1) / 365)
                else:
                    working_years += (((record.date_end - record.date_start).days + 1) / 365)

            # compute bonus amount
            if rec.types_of_end_services == 'end_of_the_contract':
                rec.bonus_amount = self.compute_bonus_end_of_the_contract(working_years)
            elif rec.types_of_end_services == 'employees_resignation':
                rec.bonus_amount = self.compute_bonus_employee_resignation(working_years)
            else:
                rec.bonus_amount = 0

    def compute_bonus_end_of_the_contract(self, working_years):
        for rec in self:
            bonus_amount = 0
            # if working years more than 5 years then bonus amount += total_salary
            if working_years > 5:
                bonus_amount += rec.total_salary * (working_years - 5) + (self.total_salary * 2.5)
            else:
                bonus_amount += (rec.total_salary * working_years) / 2
            return bonus_amount

    def compute_bonus_employee_resignation(self, working_years):
        bonus_amount = 0
        if working_years > 10:
            bonus_amount += self.total_salary * (working_years - 10) + (self.total_salary * 5 * 2 / 3) + (
                    ((self.total_salary / 2) * 5) / 3)
        elif working_years > 5:
            bonus_amount += self.total_salary * (2 / 3) * (working_years - 5) + (((self.total_salary / 2) * 5) / 3)
        elif working_years > 2:
            bonus_amount += ((self.total_salary / 2) * working_years) / 3

        return bonus_amount

    @api.depends('date_start', 'date_end')
    def _compute_service_duration(self):
        for contract in self:
            if contract.date_start and contract.date_end:
                delta = contract.date_end - contract.date_start
                years = (delta.days + 1) // 365
                remaining_days = (delta.days + 1) % 365
                months = remaining_days // 30
                days = remaining_days % 30

                contract.service_duration_years = years
                contract.service_duration_months = months
                contract.service_duration_days = days
            else:
                contract.service_duration_years = 0
                contract.service_duration_months = 0
                contract.service_duration_days = 0

    @api.depends('salary_if_any', 'overtime', 'vacation_benefits', 'end_of_service', 'other_benefits')
    def _compute_total_amount_due(self):
        for record in self:
            record.total_amount_due = (
                    float(record.salary_if_any) + float(record.overtime) + float(record.vacation_benefits) + float(
                record.end_of_service) + float(record.other_benefits))

    @api.depends('total_amount_due', 'total_amount_deductions')
    def _compute_net_receivables(self):
        for record in self:
            record.net_receivables = abs((
                    float(record.total_amount_deductions) - float(record.total_amount_due)))

    @api.depends('his_predecessor_is_due', 'covenant_deductions', 'vacations_paid_deductions', 'loan_deductions',
                 'other_deductions')
    def _compute_total_amount_deductions(self):
        for record in self:
            record.total_amount_deductions = (
                    float(record.his_predecessor_is_due) + float(record.covenant_deductions) + float(
                record.vacations_paid_deductions) + float(
                record.loan_deductions) + float(record.other_deductions))

    @api.depends('total_salary', 'payroll_days', 'days_of_the_month')
    def _compute_salary_if_any(self):
        for record in self:
            if record.days_of_the_month and record.payroll_days:
                record.salary_if_any = (float(record.total_salary) / float(
                    record.days_of_the_month)) * float(record.payroll_days)

            else:
                record.salary_if_any = 0
        pass

    @api.depends('total_salary', 'number_od_days_off')
    def _compute_vacation(self):
        for record in self:
            if record.number_od_days_off:
                record.vacation_benefits = (float(record.total_salary) / 30) * float(record.number_od_days_off)
            else:
                record.vacation_benefits = 0

    @api.onchange('contract_type_sel')
    def onchange_type_id(self):
        if self.contract_type_sel == 'saudi':
            template = ''' <div style="with: 100%; clear: both;">
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;font-size: 20px;text-align: center;width:50%">
								<strong>EMPLOYMENT CONTRACT</strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;font-size: 20px;text-align: center;width:50%">
								<strong>عقد عمـل</strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p style="text-align: left;">This employment contract no. ({0}) is entered into on {1} between: </p>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<p> حُرر هذا العقد رقم ({2}) بتاريخ {3}بين كل من:</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p> 1) Business Research and Development Company,  a limited liability  company incorporated in Saudi Arabia under   Commercial Registration No. 1010421211 and headquartered at Riyadh - .Alyasmin District – Riyadh 13326-2871, Kingdom of Saudi Arabia  (the "Employer"); and</p>
							</div>
							<div class="col-sm-6" style="padding: 10px;text-align: right;width:50%"><p>١) شركةأبحاث وتطوير الأعمال التجارية ، شركة ذات مسؤولية محدودة مسجلة في المملكة العربية السعودية بموجب سجل تجاري رقم ١٠١٠٤٢١٢١١ وعنوان مقرها الرئيس الرياض - حي الياسمين - الرياض 13326-2871 المملكة العربية السعودية (ويشار إليها فيما يلي في هذا العقد بـ "صاحب العمل") ، و</p></div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p style="text-align: left;">2) [{4}], a [{5}] national {30}, with I.D/Passport No. [{6}], whose address is located at [{7}] (the "Employee").</p>
							</div>
							<div class="col-sm-6" style=" padding: 10px;direction: rtl;text-align: right;width:50%">
								<p>    ٢ )  [{8}]، [{9}] الجنسية، إقامة رقم{30} ، وجواز رقم [{10}]، وعنوانه [{11}]. (ويشار إليه فيما يلي بـ "الموظف")
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p style="text-align: left;">(together, the "Parties").<br></br>
									Whereas both Parties have acknowledged their legal competence to conclude this contract; the Parties hereby agree as follows: </p>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<p>(ويشار اليهما معاً بـ "الطرفين أو الطرفان"). <br></br>
									وبعد أن أقر الطرفان بأهليتهما المعتبرة شرعاً ونظاماً لإبرام هذا العقد، فقد اتفق الطرفان على الشروط والأحكام التالية:</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 1. Gregorian Calendar </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> ١. التاريخ الميلادي </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p style="text-align: left;">All periods and dates in this Contract will be in accordance with the Gregorian Calendar. </p>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<p>تكون جميع المدد والتواريخ في هذا العقد وفق التاريخ الميلادي.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 2. Appointment </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> ٢. التعيين </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p style="text-align: left;">a. The Parties agree that the Employee shall work under the management and supervision of the Employer as
									[{12}]. The Employee shall perform the duties assigned to such role in a way commensurate to the Employee's practical and technical capabilities and expertise, and in accordance with the operational requirements in a manner that does not violate Articles 58, 59 and 60 of the Labour Law.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;width:50%">
								<p>i. اتفق الطرفان على أن يعمل الموظف تحت إدارة وإشراف صاحب العمل بوظيفة [{13}] ومباشرة الأعمال التي يكلف بها بما يتناسب مع خبراته وقدراته العملية والعلمية والفنية، وفقاً لاحتياجات العمل وبما لا يتعارض مع الضوابط المنصوص عليها في المواد (الثامنة والخمسين والتاسعة والخمسين والستين) من نظام العمل.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p style="text-align: left;">b.  Employment hereunder is conditional on the Employee's reporting to work not later than the date specified in paragraph (a.) of Article (5.) below.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;width:50%">
								<p>ii . يشترط لتعيين الموظف بموجب هذا العقد مباشرته لعمله في موعد لا يتجاوز التاريخ المحدد في المادة (5.) الفقرة (1.) أدناه.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p style="text-align: left;">c.  This Contract shall be subject to and conditional upon the relevant Saudi Arabian government authorities granting any necessary permissions,including any regulatory consents, residency and/or work permits (in each case, as applicable).</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;width:50%">
								<p>iii . يخضع هذا العقد ويتوقف نفاذه على ضرورة الحصول على موافقة السلطات المعنية في المملكة العربية السعودية بما في ذلك أي رخص أو تصاريح مطلوبة نظاماً و/أو الحصول على الاقامة ورخص العمل اللازمة حسب ما يقتضي الأمر.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 3. Basic Monthly Salary and Other Benefits </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> ٣ . الأجر الأساسي الشهري والمزايا الأخرى </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p style="text-align: left;"> a. <strong>Total Salary: </strong>({14}) SR /moth (Gregorian) Prior Cutting Gosi Cost.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
								<p style="text-align: right;"> i. <strong>الراتب الإجمالي</strong> :({15}) ريال في الشهر الميلادي قبل اشتراك التأمينات الاجتماعية. </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p style="text-align: left;"> b. <strong> Basic Salary:</strong> ({16}) SR /moth (Gregorian).</p>
							</div>
							<div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
								<p style="text-align: right;"> ii. <strong>الراتب الأساسي</strong>:({17})ريال في الشهر (الميلادي). </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p style="text-align: left;"> c. <strong>Housing:</strong> ({18}) SR (25% of the Basic Salary).</p>
							</div>
							<div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
								<p style="text-align: right;">iii .<strong>بدل السكن</strong>:({19})   ريال (25% من الراتب الأساسي). </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p style="text-align: left;"> d. <strong>Transportation:</strong> ({20}) SR (10% of the Basic Salary).</p>
							</div>
							<div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
								<p style="text-align: right;">iv .<strong>بدل النقل</strong>:({21})   ريال (10% من الراتب الأساسي). </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p style="text-align: left;">e. <strong>Medical Insurance:</strong> Employee, wife and his Children (as per company policy).</p>
							</div>
							<div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
								<p style="text-align: right;">v .<strong>التأمين الطبي:</strong> للموظف والزوجة وأطفاله (حسب الأنظمة الداخلية للشركة). </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p style="text-align: left;"> f. 9.75% of the wage (basic salary + housing
									allowance) is deducted for the General Organization for Social Insurance (GOSI) on a monthly basis.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
								<p style="text-align: right;">vi .ًيتم استقطاع ٩.٧٥% من الأجور الخاضعة للتأمينات ( الراتب الأساسي + بدل السكن ) لمصلحة التأمينات الاجتماعية شهرياً. </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 4. Work Location </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">٤. موقع العمل </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p style="text-align: left;">The Employee will be employed in Riyadh, Saudi Arabia. However, the Employer reserves the right to change the Employee's job location as per the Employer's operational requirements. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;width:50%">
								<p>   يكون موقع عمل الموظف في منطقة الرياض بالمملكة العربية السعودية، علماً بأنه يحق لصاحب العمل أن يغير موقع عمل الموظف تبعاً لحاجة العمل.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 5. Term of Employment </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">٥. مدة العقد </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a. The duration of this Contract is a year, beginning on the commencement date of the Employee's employment on [{24}] and ending on [{25}].</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>
									١ . مدة هذا العقد سنة كاملة. تبدأ من تاريخ الموظف للعمل في [{26}] وتنتهي في [{27}].</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 6. Probation Period </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">٦. فترة التجربة </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> The Employee shall be on probation for ninety (90) days beginning on the first day of employment. The Parties may by written agreement extend the probation period for not more than ninety (90) days. During the probation period, the Employer may terminate this Contract without notice and without the payment of any compensation or end of service award. This probation period is exclusive of Eid Al Fitr, Eid Al Adha holidays, and sick le­­ave.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>يخضع الموظف لفترة تجربة تستمر لمدة تسعين (90) يوماً تبدأ من تاريخ مباشرته للعمل، ولا يدخل في حسابها إجازة عيدي الفطر والأضحى والإجازة المرضية. ويجوز باتفاق مكتوب بين الطرفين تمديد فترة التجربة لمدة تسعين (90) يوماً أخرى، ويحق لصاحب العمل خلال فترة التجربة إنهاء هذا العقد بدون إشعار، وبدون تعويض أو مكافأة نهاية الخدمة.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 7. Compliance with Laws and Instructions </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">٧ .القوانين والتعليمات </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> The Employee undertakes to comply with good conduct during the employment and at all times, and with all policies and procedures, directives and instructions issued by the Employer and acknowledges that the laws, regulations and customs of Saudi Arabia shall govern this Contract. The Employee shall bear all penalties incurred by the Employee with respect to such laws, regulations and customs.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>يلتزم الموظف بحسن السلوك والأخلاق أثناء العمل في جميع الأوقات ويلتزم بالأنظمة والأعراف والعادات والآداب المرعية في المملكة العربية السعودية وكذلك الالتزام بكل السياسات والإجراءات والقواعد واللوائح والتعليمات المعمول بها لدى صاحب العمل ويتحمل كافة الغرامات المالية الناتجة عن مخالفته لتلك الأنظمة.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 8. Other Employment </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">٨ .العمل لدى الغير </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a. In accepting employment hereunder, the Employee undertakes that he will not engage in any other business or employment (with or without remuneration). </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>١. بقبوله العمل بموجب هذا العقد، يتعهد الموظف بأن لا يمارس أي عمل أو وظيفة أخرى سواء بمقابل أو بدون مقابل.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> b. The Employee shall not without the Employer’s prior written permission be entitled to directly or indirectly, temporarily or permanently be engaged by or do any business solely, with individual(s) or companies other than the Employer.  </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p> ٢. يلتزم الموظف بأن لا يرتبط بأداء أي عمل بشكل مباشر أو غير مباشر سواء بشكل مؤقت أو دائم مع أي شخص أو أشخاص سواء كانوا أفراداً أو شركات بخلاف صاحب العمل، دون موافقة مسبقة من صاحب العمل. </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> c. The Employee shall devote their time and attention during working hours to the best interests and the business of the Employer and shall faithfully serve the Employer and shall use their utmost best endeavours to promote the Employer’s business. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>  ٣ . يلتزم الموظف بأن يكرس وقته وعنايته خلال ساعات العمل لمصالح وأعمال صاحب العمل، وأن يعمل لصاحب العمل بإخلاص وأن يبذل أقصى ما يمكنه لتنمية أعمال  صاحب العمل. </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 9. Confidentiality / Intellectual Property </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">٩ .السريـة/ الملكية الفكرية </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a. The Employee shall commit to confidentiality and  don't, under any circumstances, at any time during his employment with the Employer or thereafter, disclose any information regarding the business or affairs of the Employer (or any associated company), their trade practices, trade and industrial and professional secrets or customers to any person, firm or company except under the direction and with the prior written consent of the Employer. Upon termination of the Employee's employment with the Employer, the Employee shall not remove or retain figures, calculations, letters, reports, or other data or documents containing such information. This Article shall survive the termination or expiry of this Contract for a period of 25 years applicable anywhere in the world. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>١. على الموظف طوال مدة خدمته لدى صاحب العمل وبعد انتهائها، بأن يلتزم بالسرية وألا يفصح بأي حال من الأحوال، أو في أي وقت من الأوقات، عن أية معلومات تتعلق بنشاط صاحب العمل أو شؤونه (أو بعمل أو شؤون أي من الشركات التابعة له) أو بممارساتها أو أسرارها التجارية والصناعية والمهنية أو عملائها، إلى أي شخص أو مؤسسة أو شركة، إلا بتوجيه من صاحب العمل وموافقة كتابية مسبقة منه. ولا يجوز للموظف عند إنهاء خدمته أن يزيل أو يحتفظ بأية أرقام أو حسابات أو خطابات أو تقارير أو بيانات أو مستندات أخرى تحتوي على مثل تلك المعلومات. وستبقى هذه المادة سارية المفعول حتى بعد إنهاء أو انتهاء هذا العقد ولمدة 25 سنة في أي مكان في العالم.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> b. The Employee acknowledges that all intellectual property rights subsisting or attaching to the Employer's confidential information or other materials of whatsoever nature made, originated or developed by the Employee at any time during his employment with the Employer whether before or after the date of this Contract shall belong to and vest in the Employer to the fullest extent permitted by law.  To such end the Employee also undertakes, at the request of the Employer, to execute such documents and give all such assistance as in the opinion of the Employer may be necessary or desirable to vest any intellectual property rights therein in the Employer absolutely and the Employee hereby assigns all present and future rights for works produced or originated by him during his employment. The Employee shall not have any claim to any right, title or interest therein.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p> ٢. يقر الموظف بأن جميع حقوق الملكية الفكرية الناشئة عن أو المرتبطة بالمعلومات السرية الخاصة بصاحب العمل أو المواد الأخرى أياً كانت طبيعتها والتي يتم إنشاؤها أو تطويرها من قبل الموظف في أي وقت خلال عمله لدى صاحب العمل، سواءً كان ذلك قبل تاريخ هذا العقد أو بعده، ستكون ملكاً لصاحب العمل إلى أقصى حد مسموح به قانوناً. ولهذا الغرض، يتعهد الموظف أيضاً، حال طلب صاحب العمل منه ذلك، بتحرير الوثائق وتقديم كافة أشكال المساعدة التي يراها صاحب العمل ضرورية أو مستحسنة لتسجيل حقوق الملكية الفكرية باسم صاحب العمل حصرياً. ويتنازل الموظف بموجبه عن كل الحقوق الحالية والمستقبلية الخاصة بالأعمال التي ينتجها أو يطورها أثناء عمله لدى صاحب العمل، ولا يحق للموظف المطالبة بأي تعويض عن هذه الحقوق أو حقوق الملكية أو المصالح. </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> c. The Employee agrees that the Employer has the right to hold and process information about the Employee for legal, personnel, administrative and management purposes and in particular to the processing of any sensitive personal data. The Employee consents to the Employer making such information available to any of its affiliates and regulatory authorities.  </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p> ٣  . يوافق الموظف على أن لصاحب العمل الحق في الاحتفاظ ومعالجة المعلومات المتعلقة بالموظف لأغراض قانونية أو تتعلق بالإدارة وشؤون الموظفين وخصوصاً ما يتعلق بالاحتفاظ ومعالجة أي بيانات شخصية مهمة. كما يوافق الموظف على قيام صاحب العمل بإتاحة تلك المعلومات لأي من الشركات التابعة له أو السلطات التنظيمية. </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 10. Business Restraint </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١٠ .قيود العمل </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p>The Employee agrees that during the term of this Contract, and for the period of twelve (12) months immediately following the expiration or termination of this Contract, the Employee shall not solicit or entice away or in any manner endeavour to solicit or entice away from the Employer any person who is employed by the Employer. This Article shall survive the termination or expiry of this Contract.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>يوافق الموظف على عدم القيام، خلال مدة هذا العقد ولمدة اثني عشر (12) شهراً من تاريخ إنهائه أو انتهائه، بتقديم عرض أو محاولة إقناع أي شخص يعمل لدى صاحب العمل بأي وسيلة كانت لترك العمل لدى صاحب العمل.  وستبقى هذه المادة سارية المفعول حتى بعد إنهاء أو انتهاء هذا العقد.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 11. Working Hours </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١١. ساعات العمل  </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a. The normal number of working days are (6) six days per week, and the Employee shall work for forty eight (48) hours per week.   </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>١.تحدد أيام العمل ب(٦) ستة أيام بالأسبوع أو (٤٨)  ثمانية وأربعون ساعة في الأسبوع.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> b.  he Employer will determine the Employee's weekly day(s) of rest. It is agreed that pay for the day(s) of rest is included in the Employee's regular wage. Any payment to the Employee for overtime worked will be subject to the Employee obtaining prior approval for the overtime from the Employee's line manager. If the Employee does not obtain prior written approval from the Employer to work overtime, the Employee will not be entitled to any overtime payment. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p> ٢. يحدد صاحب العمل أيام العطلة الأسبوعية التي يحصل عليها الموظف كأيام راحة. ومن المعلوم أن أجر أيام العطلة الأسبوعية مشمول ضمن الأجر الذي يتقاضاه الموظف بصفة منتظمة. ويشترط لحصول الموظف على مقابل لساعات العمل الاضافية التي عملها أن يحصل على موافقة مسبقة من مديره المباشر. وإذا لم يحصل الموظف على موافقة مسبقة من صاحب العمل على ساعات العمل الإضافية، فلن يستحق الموظف أي مقابل عنها.
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> c. During the month of Ramadan, work hours will be (36) thirty six hours per week in accordance with the Saudi Labor Law. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p> ٣  .خلال شهر رمضان المبارك تكون ساعات العمل الأسبوعية (36) ستة وثلاثون ساعة أسبوعياً وفقاً لنظام العمل السعودي.
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> d. The Employer will manage working hours and respite during the day for the employee, and the periods designated for rest, prayers, and meals shall not be included in the actual working hours, during such periods, the worker shall not be under the employer's authority.   </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>٤  .ينظم صاحب العمل ساعات العمل وفترات الراحة خلال اليوم للموظف ولا تدخل الفترات المخصصة للراحة والصلاة والطعام ضمن ساعات العمل الفعلية، ولا يكون الموظف خلال هذه الفترة تحت سلطة صاحب العمل.
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 12. National Holidays, Maternity Leave and Other Leave </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١٢ . العطلات الرسمية وإجازة الوضع والإجازات الأخرى  </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a. The Employee will be entitled to days off for public holidays in accordance with the Saudi Labour Law.  If the Employee is required to work on a holiday, the Employee shall be entitled to payment for every hour actually worked on such holiday in accordance with the Saudi Labour Law. The Employee must first obtain prior written approval from the Employer to work on a public holiday. Failure to obtain this approval will result in the Employee not being entitled to payment in accordance with this provision. 
								</p>
								</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>١.يحق للموظف خلال السنة الحصول على العطلات الرسمية المعتمدة وفقاً لنظام العمل السعودي. وإذا طُلب منه العمل خلال أيام العطلات الرسمية، فإنه يستحق تعويضاً عن كل ساعة عمل فعلية خلال هذه العطلة وفقاً لنظام العمل السعودي. ويشترط لحصول الموظف على مقابل لساعات العمل الإضافية التي عملها أن يحصل على موافقة مسبقة من مديره المباشر للعمل خلال العطلات الرسمية. وإذا لم يحصل الموظف على موافقة مسبقة من صاحب العمل على العمل لساعات إضافية فلن يستحق الموظف أي مقابل عنها حسب ما أشير إليه في هذه المادة. </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> b. The Employee will be eligible for maternity leave with full pay for a period of ten (10) weeks to be used as the Employee deems appropriate, provided that the same shall commence at least four (4) weeks prior to the expected due date, which shall be determined by the Employer's physician or based on a certified medical certificate. (this Article is applicable if the Employee is a female). </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p> ٢. تستحق الموظفة إجازة وضع بأجر كامل لمدة عشرة (10) أسابيع، توزعها كيف تشاء، تبدأ بحد أقصى بأربعة (4) أسابيع قبل التاريخ المرجح للوضع، ويحدد التاريخ المرجح للوضع بواسطة طبيب المنشأة، أو بناءً على شهادة طبية مصدقة من جهة صحية. (تنطبق هذه المادة على الموظفات فقط)
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> c. The Employee shall be entitled to paid time off for feeding their child up to 2 years after the birth of the child, provided that the same shall not exceed one (1) hour per day in the aggregate. (this Article is applicable if the Employee is a female).</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p> ٣  .يحق للموظفة عندما تعود إلى مزاولة عملها بعد إجازة الوضع، أن تأخذ بقصد إرضاع مولودها لمدة عامين بعد ولادة الطفل فترة أو فترات للاستراحة لا تزيد في مجموعها على الساعة (1) في اليوم الواحد وتحسب هذه الفترة أو الفترات من ساعات العمل الفعلية.  (تنطبق هذه المادة على الموظفات فقط)
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> d. The Employee shall be entitled to four (4) months and ten (10) days paid leave following the death of the Employee's husband and shall be entitled to extend such leave without pay if the Employee is pregnant during the said period until the due date. In all cases, such leave shall end following the birth of the Employee's child and the Employee will not be entitled to use the remaining period thereof. (this Article is applicable if the Employee is a Muslim female).  </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>٤  .يحق للموظفة في حالة وفاة زوجها إجازة عدة بأجر كامل لمدة لا تقل عن أربعة (4) أشهر وعشرة (10) أيام من تاريخ الوفاة، ولها الحق في تمديد هذه الإجازة دون أجر إن كانت حاملاً –خلال هذه الفترة- حتى تضع حملها، ولا يجوز لها الاستفادة من باقي إجازة العدة الممنوحة لها بعد وضع حملها.  (تنطبق هذه المادة على الموظفات المسلمات فقط)
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 13. Annual Vacation </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١٣ .الاجـازة السنوية </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p>  The Employee will be eligible for a vacation consisting of thirty (30) days per year.  Vacation days shall be scheduled by the Employer in accordance with its operational requirements, provided that the vacation salary shall be paid in advance. The Employer reserves the right to transfer the vacation to the following year for a period not exceeding ninety (90) days, and may, with the written consent of the Employee, transfer the vacation to the end of the following year should operational circumstances so require.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>يستحق الموظف عن كل عام، إجازة سنوية مدتها (30)ثلاثين  يوم مدفوعة الأجر، ويحدد صاحب العمل تاريخ الإجازة خلال سنة الاستحقاق وفقاً لظروف العمل، على أن يتم دفع أجر الإجازة مقدماً عند استحقاقها، ولصاحب العمل تأجيل الإجازة بعد نهاية سنة استحقاقها لمدة لا تزيد عن (90) يوماً، كما له بموافقة الموظف كتابة تأجيلها إلى نهاية السنة التالية لسنة الاستحقاق وذلك حسب مقتضيات ظروف العمل.</p>
							</div>
						</div>
						<div class="row">
						<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 14. Medical Insurance </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١٤ .التأمين الطبي </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> The Employer will provide the Employee with medical insurance coverage in accordance with the Cooperative Health Insurance Law and the company rules.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>يلتزم صاحب العمل بتوفير الرعاية الطبية للموظف بالتامين الصحي وفقاً لأحكام نظام الضمان الصحي التعاوني وأنظمة الشركة.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 15. Medical Examination </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١٥ .الفحص الطبي </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> The Employee shall be required to undergo a medical examination prior to employment or at any other time to determine the Employee's fitness for employment or continued employment.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>يلتزم الموظف بأن يخضع وفقاً لطلب صاحب العمل للفحوص الطبية التي يرغب في إجرائها عليه قبل الالتحاق بالعمل، أو أثناءه للتحقق من خلوه من الأمراض المهنية أو السارية.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 16. Registration with GOSI </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١٦ .اشتراك المؤسسة العامة للتأمينات الاجتماعية</strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p>  The Employer will register the Employee with the General Organization for Social Insurance and shall pay the subscription fee thereof in accordance with its regulations. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl">
								<p>يلتزم صاحب العمل بتسجيل الموظف لدى المؤسسة العامة للتأمينات الاجتماعية وسداد الاشتراكات حسب أنظمتها.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 17. Additional Employee Obligations </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١٧. التزامات إضافية للموظف  </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a. The Employee will perform his duties in accordance with the best practices of the occupation and in accordance with the Employer's instructions if the same does not violate the Contract, applicable law or customs, and does not endanger the Employee.  </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
								<p>١.يلتزم الموظف بأن ينجز العمل الموكل إليه، وفقاً لأصول المهنة، ووفق تعليمات صاحب العمل، إذا لم يكن في هذه التعليمات ما يخالف العقد أو النظام أو الآداب العامة ولم يكن في تنفيذها ما يعرضه للخطر.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> b. The employee is obliged to maintain the employer's money , property and the tasks assigned to him\her because of his\her job such as  tools, devices and equipment. The employee is also responsible for any damage to the employer or the property and if he or she is excessively encroachment. The employee shall return all the employer's property, including his confidential information and documents, whether printed or electronic, before leaving in vacation or at the end of the contract</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
								<p> ٢. يلتزم الموظف بالمحافظة على أموال وممتلكات صاحب العمل والمهمات المسندة إليه وما قد يسلم إليه بسبب وظيفته من أدوات وأجهزة ومعدات ويكون مسؤولًا عن أية أضرار يلحقها بصاحب العمل أو ممتلكاته متعدياً مفرطاً، ويلتزم الموظف بإعادة كل ممتلكات صاحب العمل ويشمل ذلك معلوماته ووثائقه السرية (سواء أكانت بشكل مطبوع أو إلكتروني) قبل مغادرته للإجازة أو عند انقضاء العقد.
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> c. The Employee must provide any help necessary without extra compensation in the event of circumstances endangering the safety of the work premises or the persons engaged therein.   </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
								<p> ٣  .  يلتزم الموظف بأن يقدم كل عون ومساعدة دون أن يشترط لذلك أجراً إضافياً في حالات الأخطار الي تهدد سلامة مكان العمل أو الأشخاص العاملين فيه..
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 18. Termination </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١٨. إنهاء العقد  </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a. Except where Article 6. of this Contract applies, this Contract shall terminate upon the expiry of its term where prior written notice has been given in accordance with Article 5. (b.) of this contract or by the mutual agreement between the Parties evidenced by the written consent of the Employee. (this Article is applicable if the contract is for a fixed term only)  </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
								<p>١.ينتهي هذا العقد بانتهاء مدته في العقد محدد المدة إذا تم إشعار أحد الطرفين من قبل الآخر خطياً بعدم رغبته في التجديد بناء على المادة (5.- 2.) من هذا العقد ، أو باتفاق الطرفين على إنهائه، بشرط موافقة الموظف كتابة مع الأخذ في الاعتبار ما ورد في المادة (6.) من هذا العقد.  (تنطبق هذه المادة على عقود العمل محددة المدة فقط)  </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> b. The Employer may terminate this Contract for cause and without notice, compensation or end of service benefits in accordance with Article 80 of the Labour Law, or in case the Employee is found in breach of Article (39) of the Labour Law, or in breach of any of his/her obligation in this contract, provided that the Employee shall be entitled to submit his objections to the termination.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
								<p> ٢. يحق لصاحب العمل فسخ العقد وذلك طبقاً للحالات الواردة في المادة (الثمانون) من نظام العمل، أو في حالة مخالفة الموظف للمادة (٣٩) من نظام العمل، أو إخلاله بأي من التزاماته في هذا العقد، وذلك دون مكافأة أو إشعار للموظف أو تعويضه شريطة إتاحة الفرصة للموظف في إبداء أسباب معارضته للفسخ.
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> c. The Employee will be entitled to leave work and terminate the Contract for cause and without notice in accordance with Article 81 of the Labour Law, provided that the Employee shall be entitled to receive all of his entitlements.   </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
								<p> ٣  . يحق للموظف ترك العمل وإنهاء العقد دون إشعار صاحب العمل وذلك طبقاً للحالات الواردة في المادة (الحادية والثمانون) من نظام العمل، مع احتفاظه بحقه في الحصول على كافة مستحقاته.
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> d. In the event that this Contract is terminated without cause prior to the expiry of its term by one of the parties, the other party is entitled to two (2) months’ salary as compensation. It is understood between the parties, that if the employee submits his resignation prior the termination of the contract without a legitimate reason to terminate this contract, then the compensation in this paragraph shall apply. However, if the Employer accept such resignation, then such termination shall be considered to have been made with mutual consent. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
								<p>٤  .في حال إنهاء العقد من قبل أحد الطرفين قبل انقضاء مدته دون سبب مشروع فيحق للطرف الآخر مقابل هذا الإنهاء تعويضاً قدره أجر شهرين، ومن المتفق عليه بين الطرفين إذا تقدم الموظف باستقالة قبل تمام مدة العقد يعد سبباً غير مشروع لإنهاء العقد، ويطبق عليه التعويض المنصوص عليه في هذه الفقرة ما لم يوافق صاحب العمل على تلك الاستقالة، فيعتبر انهاء العقد قد تم بموافقة الطرفين.
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> e. Where the term of this contract has become indefinite, in the event that this Contract is terminated without cause by one of the Parties, the other Party is entitled to two (2) months' salary as compensation. (this Article is applicable if the contract is for an indefinite term only) </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
								<p>٥  .في حال إنهاء العقد بعد تحوله إلى عقد غير محدد المدة من قبل أحد الطرفين دون سبب مشروع فيحق للطرف الآخر مقابل هذا الإنهاء تعويضاً قدره أجر شهرين. (تنطبق هذه المادة على العقد غير محدد المدة فقط)
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> f. The Employer also has the right to terminate this Contract for the following valid reasons upon giving the Employee two (2) months' notice in writing, or upon payment in lieu of such notice, in the following cases: </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
								<p>٦  .يحق لصاحب العمل أن ينهي هذا العقد للأسباب المشروعة التالية بموجب منح الموظف  إشعار مكتوب مدته (2) شهرين أو بدل عنه وفقاً لما يقتضيه نظام العمل السعودي:
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p> i. force majeure; or </p>
							</div>
							<div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%;direction: rtl;">
								<p>١. في حالة القوة القاهرة. </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p> ii.permanent closure of the Employer; or </p>
							</div>
								<div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%;direction: rtl;">
									<p> ٢.  إغلاق المنشأة نهائياً.</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
									<p> iii. the cessation of the activity in which the Employee works; or  </p>
								</div>
								<div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%;direction: rtl;">
									<p> ٣  . إنهاء النشاط الذي يعمل فيه العامل.
									</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
									<p> iv. the Employee's physical or mental disability rendering him unable to perform his work as established by a medical certificate; or </p>
								</div>
								<div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%;direction: rtl;">
									<p>٤  .في حال عجز الموظف جسدياً أو عقلياً عن أداء عمله بموجب شهادة طبية.
									</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
									<p> v. the Employee ceases to hold any licences, certificates, permits or approvals necessary to perform his job. </p>
								</div>
								<div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%;direction: rtl;">
									<p>٥  .إذا لم يعد الموظف حائزاً على أية تراخيص أو شهادات أو تصاريح أو موافقات لازمة له لأداء عمله.
									</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> g.Except where this Contract is terminated under Articles (18-b), (18.-c), or Article (6.) and Article (5), the Party who terminates this Contract must provide the other with prior written notice of at least sixty (60) days prior to the termination date. </p>
								</div>
								<div class="col-sm-6" style="padding-left: 20px;text-align: right;width:50%;direction: rtl;">
									<p>٧  .يلتزم أي من الطرفين عند إنهائه للعقد إشعار الطرف الآخر كتابة قبل الإنهاء بمدة لا تقل عن ستين (60) يوماً مع الأخذ بعين الإعتبار ما ورد في المادة (18-ب) و (19-ج) والمادة (6) والمادة (5) من هذا العقد
									</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> h.Upon the termination of the of the employment contract the Employer shall have the right to pay the Employee an amount in lieu of vacation days accrued but not taken. On the other hand, in the event the Employee has taken more holiday time than that accrued at the termination date, he or she shall pay the Employer the corresponding sum. </p>
								</div>
								<div class="col-sm-6" style="padding-left: 20px;text-align: right;width:50%;direction: rtl;">
									<p>٨  .يحق لصاحب العمل عند انتهاء عقد العمل ان يدفع للموظف مقابل نقدي عن أيام الاجازات المستحقة التي لم يتمتع بها الموظف، ويحق لصاحب العمل أن يطلب من الموظف سداد مقابل نقدي عن أيام الاجازات التي تمتع بها الموظف وتزيد عن أيام الاجازة المستحقة له
									</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> i.Upon the termination of this Contract, the Employee is required to return all property belonging to the Employer which is in the Employee's possession. Upon the termination of this Contract and the settlement of all outstanding matters, the Employee will execute a release of all claims against the Employer, and the Employer will issue a Service Certificate to the Employee. </p>
								</div>
								<div class="col-sm-6" style="ppadding-left: 20px;text-align: right;width:50%;direction: rtl;">
									<p>٩  .عند إنهاء هذا العقد يتعين على الموظف أن يعيد كل ما بحوزته من ممتلكات تعود لصاحب العمل. وعند إنهاء هذا العقد وتسوية جميع الأمور العالقة يبرم الموظف وصاحب العمل مخالصة وبراءة ذمة يخلي بموجبها كل طرف ذمة الطرف الآخر من جميع المطالبات ويصدر صاحب العمل شهادة خدمة للموظف
									</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left;text-decoration: underline;"> 19. End of Service Award </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;text-decoration: underline;">١٩ . مكافأة نهاية الخدمة  </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> a. Unless this Contract is terminated based on any of the orescriped reasons in Article (18-b) of this Contract, the Employee will receive an end of service award as per Saudi Labor Law. </p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
									<p>١.ما لم يكن إنهاء العلاقة التعاقدية مبني على أي من الحالات المذكورة في المادة (١٨-ب) من هذا العقد، فيستحق الموظف، مكافأة نهاية خدمة وفقاً لنظام العمل. </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> b. Commissions, bonuses, and similar payments which by their nature are subject to increase and decrease shall not be considered part of the Employee's wage for purposes of calculating the end of service award.</p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
									<p> ٢.لأغراض احتساب مكافأة نهاية الخدمة، فإن العمولات والمدفوعات المشابهة التي يحصل عليها الموظف والتي تعتبر بطبيعتها قابلة للزيادة والنقصان، لا تعتبر جزءاً من أجره عند احتساب مكافأة نهاية الخدمة.
									</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left;text-decoration: underline;"> 20. Waiver / Severability </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;text-decoration: underline;">٢٠ .التنازل وإمكانية الفصل بين بنود الاتفاق </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> The failure of either Party (a) to enforce at any time any of the provisions of this Contract or (b) to require at any time performance by the other Party of any of the provisions hereof, shall in no way be construed to be a waiver of the provisions or to affect the validity of this Contract or the right of either Party thereafter to enforce each and every provision in accordance with the terms of this Contract.  Invalidation of any provision of this Contract, or a portion thereof, shall not invalidate any other provision or the remainder of the relevant provision and the rest of this Contract shall in all such cases remain in full force.</p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
									<p>إذا تعذر على أي من الطرفين في أي وقت إنفاذ أي شرط من شروط هذا العقد أو مطالبة الطرف الآخر في أي وقت بإنفاذ أي من أحكامه، فإن ذلك لا يجب أن يفسر بأي حال من الأحوال على أنه تنازل عن تلك الأحكام أو على أنه يؤثر على صلاحية هذا العقد أو على حق أي من الطرفين في إنفاذ كل حكم من أحكام العقد وفقا لشروطه وأحكامه. وإذا أصبح أي شرط من شروط هذا العقد أو جزء منه باطلاً، فإن ذلك لا يبطل أي شرط آخر أو الجزء المتبقي من الشرط المعني وبقية أجزاء هذه الاتفاقية. وتظل بقية شروط وأحكام هذا العقد في جميع هذه الحالات نافذة بكامل القوة والأثر.</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left;text-decoration: underline;"> 21. Governing Law / Disputes </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;text-decoration: underline;">٢١ .القانون الحاكم/ المنازعات </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p>This Contract shall be governed by and construed in accordance with the laws and regulations of the Kingdom of Saudi Arabia, including without limitation the Labour Law issued under Royal Decree No. M/51 dated 23/08/1426H (as amended from time to time).  The Parties will make every effort to settle disputes amicably, but if the Parties are unable to reach an amicable settlement, the dispute will be referred to and decided by the relevant local labour committee in Riyadh or other appropriate Saudi Arabian administrative or judicial body in Riyadh.</p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
									<p>يخضع هذا العقد لأنظمة وقوانين المملكة العربية السعودية ويفسر وفقاً لها، بما في ذلك على سبيل المثال لا الحصر نظام العمل الصادر بموجب المرسوم الملكي رقم م/51، بتاريخ 23/8/1426هـ. وتعديلاته وعلى الطرفين أن يبذلا كل جهد ممكن لتسوية أية نزاعات تنشأ بينهما على خلفية هذا العقد بالطرق الودية. وإذا تعذر على الطرفين التوصل إلى تسوية ودية، يحال النزاع إلى اللجنة العمالية المعنية في مدينة الرياض، أو إلى السلطات القضائية السعودية المعنية في مدينة الرياض حيث تعتبر هي جهة الاختصاص والفصل في هذا العقد. </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left;text-decoration: underline;"> 22. Entire Agreement </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;text-decoration: underline;">٢٢ .مجمل الاتفاق </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> This Contract constitutes the entire agreement between the Parties with respect to the Employee's employment by the Employer in the Kingdom of Saudi Arabia and supersedes and renders null and void all prior or contemporaneous agreements or understandings, whether oral or written.
This Contract may only be amended, or supplemented, by the written agreement of the Employee and the Employer.</p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
									<p>يشكل هذا العقد مجمل الاتفاق بين الطرفين فيما يتعلق بتعيين الموظف من قبل صاحب العمل في المملكة العربية السعودية. ويلغي هذا العقد ويحل محل جميع الاتفاقيات أو التفاهمات السابقة أو المتزامنة مع هذا العقد، خطية كانت أم شفهية، ولا يجوز تعديل هذا العقد أو الاضافة إليه إلا بموجب اتفاق خطي بين صاحب العمل والموظف. </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left;text-decoration: underline;"> 23. Notices </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;text-decoration: underline;">٢٣ .الاشعارات </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> All notices between the Parties shall be in writing and sent to the addresses indicated in this contract, by registered mail, express mail, or email to both Parties. Each party undertakes to notify the other in writing in case of changing the address or changing the email, otherwise the address & email indicated in this contract will remain the official communication channels.</p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
									<p>تتم جميع الإشعارات بين الطرفين كتابة على العناوين الموضحة في هذا العقد عن طريق البريد المسجل أو البريد الممتاز أو البريد الإلكتروني لكلٍ من الطرفين، ويلتزم كل طرف بإشعار الآخر خطياً في حال تغييره للعنوان الخاص به، أو تغيير البريد الإلكتروني، وإلا اعتبر العنوان أو البريد الإلكتروني المدونان في هذا العقد، هما المعمول بهما نظاماً.</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left;text-decoration: underline;"> 24.Employee's Endorsement of the Validity of the Information : </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;text-decoration: underline;">٢٤ .إقرار الموظف بصحة المعلومات: </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> The employee acknowledges that all the information he\she provides to the employer is correct. If otherwise proven, the employer has the right to take the action he\she deems appropriate.</p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
									<p>يقر الموظف بأن جميع البيانات التي قدمها لصاحب العمل صحيحة، وفي حال ثبوت خلاف ذلك يحق لصاحب العمل اتخاذ الإجراء الذي يراه مناسباً.</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left;text-decoration: underline;"> 25.Counterparts: </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;text-decoration: underline;">٢٥   .نسخ العقد </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> This Contract has been executed in two (2) originals in Arabic and English out of (25) articles, in the event of a conflict between the same article in both language, the Arabic article shall it considered approved for interpretation of this contract and each party has received a copy thereof.</p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
									<p>حرر هذا العقد من نسختين أصليتين باللغتين العربية والإنجليزية من خمسة وعشرون مادة، وفي حال وجد اختلاف بين النص الواحد في كلا اللغتين يعتبر النص العربي هو المعتمد لتفسير هذا العقد، وقد أستلم كل طرف نسخة منها للعمل بموجبها.</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left"> The Employer </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;">صاحب العمل </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>On Behalf of Business Research and Development Co. </p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>بالنيابة عن شركة أبحاث وتطوير الأعمال التجارية </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>Name : ............................ </p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>الاسم:............................ </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>Date : ..../../..</p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>التاريخ: ..../../.. </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>Signature: ............................</p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>التوقيع: ............................ </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left"> The Employee </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;">الموظف </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>Name : {28}</p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>الاسم:{29} </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>Date : ..../../..</p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>التاريخ: ..../../.. </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>Signature: ............................</p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>التوقيع: ............................ </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p></p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>  الإيميل الشخصي: ............................ </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p></p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>  رقم الجوال الشخصي: ............................ </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p></p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p> رقم شخص آخر في حال الطوارئ: ............................ </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p style="text-align: left"></p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p> العنوان الوطني: ............................ </p>
								</div>
							</div>

					</div>
            '''.format(self.id, self.date_start, self.id, self.date_start, self.employee_id.name,
                       self.employee_id.country_id.name, \
                       self.employee_id.passport_id, self.employee_id.residence_place_id.name,
                       self.employee_id.name_in_id, self.employee_id.country_id.name, \
                       self.employee_id.passport_id, self.employee_id.residence_place_id.name, \
                       self.job_id.name, self.job_id.name, self.total_salary, self.total_salary,
                       self.wage, self.wage, self.housing_allowance_value,
                       self.housing_allowance_value, \
                       self.transportation_allowance_value, self.transportation_allowance_value,
                       self.employee_id.office_id.name, self.employee_id.office_id.name, \
                       self.date_start, self.date_end, self.date_start, self.date_end, self.employee_id.name,
                       self.employee_id.name_in_id, self.employee_id.identification_id)

        if self.contract_type_sel == 'non_saudi':
            template = ''' <div style="with: 100%; clear: both;">
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;font-size: 20px;text-align: center;width:50%"><strong>EMPLOYMENT CONTRACT</strong></div>
                                <div class="col-sm-6" style="padding: 10px;font-size: 20px;text-align: center;width:50%"><strong>عقد عمـل</strong></div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <p style="text-align: left;">This employment contract no. ({0}) is entered into on {1} between: </p>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <p> حُرر هذا العقد رقم ({2}) بتاريخ {3}بين كل من:</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <p> 1) Business Research and Development Company,  a limited liability  company incorporated in Saudi Arabia under   Commercial Registration No. 1010421211 and headquartered at Riyadh - .Alyasmin District – Riyadh 13326-2871, Kingdom of Saudi Arabia  (the "Employer"); and</p>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;text-align: right;width:50%"><p>١) شركةأبحاث وتطوير الأعمال التجارية ، شركة ذات مسؤولية محدودة مسجلة في المملكة العربية السعودية بموجب سجل تجاري رقم ١٠١٠٤٢١٢١١ وعنوان مقرها الرئيس الرياض - حي الياسمين - الرياض 13326-2871 المملكة العربية السعودية (ويشار إليها فيما يلي في هذا العقد بـ "صاحب العمل") ، و</p></div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <p style="text-align: left;">2) [{4}], a [{5}] {30} national, with I.D/Passport No. [{6}], whose address is located at [{7}] (the "Employee").</p>
                                </div>
                                <div class="col-sm-6" style=" padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <p>    ٢ )  [{8}]، [{9}] الجنسية، إقامة رقم{30} ، وجواز رقم [{10}]، وعنوانه [{11}]. (ويشار إليه فيما يلي بـ "الموظف")
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <p style="text-align: left;">(together, the "Parties").<br></br>
                                        Whereas both Parties have acknowledged their legal competence to conclude this contract; the Parties hereby agree as follows: </p>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <p>(ويشار اليهما معاً بـ "الطرفين أو الطرفان"). <br></br>
                                        وبعد أن أقر الطرفان بأهليتهما المعتبرة شرعاً ونظاماً لإبرام هذا العقد، فقد اتفق الطرفان على الشروط والأحكام التالية:</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 1. Gregorian Calendar </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> ١. التاريخ الميلادي </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <p style="text-align: left;">All periods and dates in this Contract will be in accordance with the Gregorian Calendar. </p>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <p>تكون جميع المدد والتواريخ في هذا العقد وفق التاريخ الميلادي.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 2. Appointment </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> ٢. التعيين </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p style="text-align: left;">a. The Parties agree that the Employee shall work under the management and supervision of the Employer as
                                        [{12}]. The Employee shall perform the duties assigned to such role in a way commensurate to the Employee's practical and technical capabilities and expertise, and in accordance with the operational requirements in a manner that does not violate Articles 58, 59 and 60 of the Labour Law.</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;width:50%">
                                    <p>i. اتفق الطرفان على أن يعمل الموظف تحت إدارة وإشراف صاحب العمل بوظيفة [{13}] ومباشرة الأعمال التي يكلف بها بما يتناسب مع خبراته وقدراته العملية والعلمية والفنية، وفقاً لاحتياجات العمل وبما لا يتعارض مع الضوابط المنصوص عليها في المواد (الثامنة والخمسين والتاسعة والخمسين والستين) من نظام العمل.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p style="text-align: left;">b.  Employment hereunder is conditional on the Employee's reporting to work not later than the date specified in paragraph (a.) of Article (5.) below.</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;width:50%">
                                    <p>ii . يشترط لتعيين الموظف بموجب هذا العقد مباشرته لعمله في موعد لا يتجاوز التاريخ المحدد في المادة (5.) الفقرة (1.) أدناه.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p style="text-align: left;">c.  This Contract shall be subject to and conditional upon the relevant Saudi Arabian government authorities granting any necessary permissions,including any regulatory consents, residency and/or work permits (in each case, as applicable).</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;width:50%">
                                    <p>iii . يخضع هذا العقد ويتوقف نفاذه على ضرورة الحصول على موافقة السلطات المعنية في المملكة العربية السعودية بما في ذلك أي رخص أو تصاريح مطلوبة نظاماً و/أو الحصول على الاقامة ورخص العمل اللازمة حسب ما يقتضي الأمر.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;;text-align: left;width:50%">
                                    <p style="text-align: left;">d.  The Employer shall bear the cost of the Employee's work visa fees, transfer of services fees (if it is from another employer in Saudi Arabia), residency card, and work permit fees, the cost of renewal thereof including any penalties imposed for any failure to renew the same, fees related to a change of occupation and exit and return fees. On termination of the contract the Employer shall also bear the fees of the return ticket to the Employee's home country in the same manner as the Employee arrived in Saudi Arabia (if applicable), provided that the Employee has obtained a final exit visa and the Employee's services have not been transferred to a different Employer inside Saudi Arabia. (this Article is applicable if the Employee is a Non-Saudi).</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;width:50%">
                                    <p>iiii . يتحمل صاحب العمل رسوم (استقدام الموظف/نقل خدماته إليه) ورسوم الإقامة ورخصة العمل وتجديدهما وما يترتب على تأخير ذلك من غرامات ورسوم تغيير المهنة والخروج والعودة وتذكرة عودة الطرف الثاني إلى موطنه بالوسيلة التي قدم بها بعد انتهاء العلاقة بين الطرفين إذا تم منحه تأشيرة خروج نهائي ولم تنقل خدماته الى صاحب عمل آخر داخل المملكة العربية السعودية. (تنطبق هذه المادة في حال كان الموظف غير سعودي).</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 3. Basic Monthly Salary and Other Benefits </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> ٣ . الأجر الأساسي الشهري والمزايا الأخرى </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
                                    <p style="text-align: left;"> a. <strong>Total Salary: </strong>({14}) SR /moth (Gregorian) Prior Cutting Gosi Cost.</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
                                    <p style="text-align: right;"> i. <strong>الراتب الإجمالي</strong> :({15}) ريال في الشهر الميلادي قبل خصم مستحقات اشتراك التأمينات الاجتماعية.. </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
                                    <p style="text-align: left;"> b. <strong> Basic Salary:</strong> ({16}) SR /moth (Gregorian).</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
                                    <p style="text-align: right;"> ii. <strong>الراتب الأساسي</strong>:({17})ريال في الشهر (الميلادي). </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
                                    <p style="text-align: left;"> c. <strong>Housing:</strong> ({18}) SR (25% of the Basic Salary).</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
                                    <p style="text-align: right;">iii .<strong>بدل السكن</strong>:({19})   ريال (25% من الراتب الأساسي). </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
                                    <p style="text-align: left;"> d. <strong>Transportation:</strong> ({20}) SR (10% of the Basic Salary).</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
                                    <p style="text-align: right;">iv .<strong>بدل النقل</strong>:({21})   ريال (10% من الراتب الأساسي). </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
                                    <p style="text-align: left;"> e.<strong> Annual Ticket:</strong> Once a year, the Employee alone is entitled to an Economy Class flight ticket from the area of employment to the country of origin. The employee may never be entitled to ask to exchange the ticket with cash, if the ticket is not used in a year.</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
                                    <p style="text-align: right;">v .<strong>تذكرة سنوية:</strong> يحق للموظف وحده - مرة واحد سنوياً – تذكرة طيران على الفئة الاقتصادية. ولا يحق بأي حال من الأحوال طلب استرداد قيمة التذكرة في حال عدم الانتفاع بها في سنتها.  </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
                                    <p style="text-align: left;">f. <strong>Medical Insurance:</strong> Employee, wife and his Children (as per company policy).</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
                                    <p style="text-align: right;">vi .<strong>التأمين الطبي:</strong> للموظف والزوجة وأطفاله (حسب الأنظمة الداخلية للشركة). </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
                                    <p style="text-align: left;"> g. 2% of the wage (basic salary + housing
                                        allowance) is deducted for the General Organization for Social Insurance (GOSI) on a monthly basis.</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
                                    <p style="text-align: right;">vii .يتم استقطاع ٢% من الأجور الخاضعة للتأمينات (الراتب الأساسي + بدل السكن ) لمصلحة التأمينات الاجتماعية شهرياً. </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 4. Work Location </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">٤. موقع العمل </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p style="text-align: left;">The Employee will be employed [{22}]. However, the Employer reserves the right to change the Employee's job location as per the Employer's operational requirements. </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;width:50%">
                                    <p>   يكون موقع العمل الموظف [{23}]. علماً بأنه يحق لصاحب العمل أن يغير موقع عمل الموظف تبعاً لحاجة العمل.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 5. Term of Employment </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">٥. مدة العقد </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> a. The duration of this Contract is a year, beginning on the commencement date of the Employee's employment on [{24}] and ending on [{25}].</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>
                                        ١ . مدة هذا العقد سنة كاملة. تبدأ من تاريخ الموظف للعمل في [{26}] وتنتهي في [{27}].</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 6. Probation Period </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">٦. فترة التجربة </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> The Employee shall be on probation for ninety (90) days beginning on the first day of employment. The Parties may by written agreement extend the probation period for not more than ninety (90) days. During the probation period, the Employer may terminate this Contract without notice and without the payment of any compensation or end of service award. This probation period is exclusive of Eid Al Fitr, Eid Al Adha holidays, and sick leave.</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>يخضع الموظف لفترة تجربة تستمر لمدة تسعين (90) يوماً تبدأ من تاريخ مباشرته للعمل، ولا يدخل في حسابها إجازة عيدي الفطر والأضحى والإجازة المرضية. ويجوز باتفاق مكتوب بين الطرفين تمديد فترة التجربة لمدة تسعين (90) يوماً أخرى، ويحق لصاحب العمل خلال فترة التجربة إنهاء هذا العقد بدون إشعار، وبدون تعويض أو مكافأة نهاية الخدمة.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 7. Compliance with Laws and Instructions </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">٧ .القوانين والتعليمات </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p>The Employee undertakes to comply with good conduct during the employment and at all times, and with all policies and procedures, directives and instructions issued by the Employer and acknowledges that the laws, regulations and customs of Saudi Arabia shall govern this Contract. The Employee shall bear all penalties incurred by the Employee with respect to such laws, regulations and customs.</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>يلتزم الموظف بحسن السلوك والأخلاق أثناء العمل في جميع الأوقات ويلتزم بالأنظمة والأعراف والعادات والآداب المرعية في المملكة العربية السعودية وكذلك الالتزام بكل السياسات والإجراءات والقواعد واللوائح والتعليمات المعمول بها لدى صاحب العمل ويتحمل كافة الغرامات المالية الناتجة عن مخالفته لتلك الأنظمة.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 8. Other Employment </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">٨ .العمل لدى الغير </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> a. In accepting employment hereunder, the Employee undertakes that he will not engage in any other business or employment (with or without remuneration). </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>١. بقبوله العمل بموجب هذا العقد، يتعهد الموظف بأن لا يمارس أي عمل أو وظيفة أخرى سواء بمقابل أو بدون مقابل.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> b. The Employee shall not without the Employer’s prior written permission be entitled to directly or indirectly, temporarily or permanently be engaged by or do any business solely, with individual(s) or companies other than the Employer.  </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p> ٢. يلتزم الموظف بأن لا يرتبط بأداء أي عمل بشكل مباشر أو غير مباشر سواء بشكل مؤقت أو دائم مع أي شخص أو أشخاص سواء كانوا أفراداً أو شركات بخلاف صاحب العمل، دون موافقة مسبقة من صاحب العمل. </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> c. The Employee shall devote their time and attention during working hours to the best interests and the business of the Employer and shall faithfully serve the Employer and shall use their utmost best endeavours to promote the Employer’s business. </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>  ٣ . يلتزم الموظف بأن يكرس وقته وعنايته خلال ساعات العمل لمصالح وأعمال صاحب العمل، وأن يعمل لصاحب العمل بإخلاص وأن يبذل أقصى ما يمكنه لتنمية أعمال  صاحب العمل. </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 9. Confidentiality / Intellectual Property </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">٩ .السريـة/ الملكية الفكرية </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> a. The Employee shall commit to confidentiality and  don't, under any circumstances, at any time during his employment with the Employer or thereafter, disclose any information regarding the business or affairs of the Employer (or any associated company), their trade practices, trade and industrial and professional secrets or customers to any person, firm or company except under the direction and with the prior written consent of the Employer. Upon termination of the Employee's employment with the Employer, the Employee shall not remove or retain figures, calculations, letters, reports, or other data or documents containing such information. This Article shall survive the termination or expiry of this Contract for a period of 25 years applicable anywhere in the world. </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>١. على الموظف طوال مدة خدمته لدى صاحب العمل وبعد انتهائها، بأن يلتزم بالسرية وألا يفصح بأي حال من الأحوال، أو في أي وقت من الأوقات، عن أية معلومات تتعلق بنشاط صاحب العمل أو شؤونه (أو بعمل أو شؤون أي من الشركات التابعة له) أو بممارساتها أو أسرارها التجارية والصناعية والمهنية أو عملائها، إلى أي شخص أو مؤسسة أو شركة، إلا بتوجيه من صاحب العمل وموافقة كتابية مسبقة منه. ولا يجوز للموظف عند إنهاء خدمته أن يزيل أو يحتفظ بأية أرقام أو حسابات أو خطابات أو تقارير أو بيانات أو مستندات أخرى تحتوي على مثل تلك المعلومات. وستبقى هذه المادة سارية المفعول حتى بعد إنهاء أو انتهاء هذا العقد ولمدة 25 سنة في أي مكان في العالم.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> b. The Employee acknowledges that all intellectual property rights subsisting or attaching to the Employer's confidential information or other materials of whatsoever nature made, originated or developed by the Employee at any time during his employment with the Employer whether before or after the date of this Contract shall belong to and vest in the Employer to the fullest extent permitted by law.  To such end the Employee also undertakes, at the request of the Employer, to execute such documents and give all such assistance as in the opinion of the Employer may be necessary or desirable to vest any intellectual property rights therein in the Employer absolutely and the Employee hereby assigns all present and future rights for works produced or originated by him during his employment. The Employee shall not have any claim to any right, title or interest therein. </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p> ٢. يقر الموظف بأن جميع حقوق الملكية الفكرية الناشئة عن أو المرتبطة بالمعلومات السرية الخاصة بصاحب العمل أو المواد الأخرى أياً كانت طبيعتها والتي يتم إنشاؤها أو تطويرها من قبل الموظف في أي وقت خلال عمله لدى صاحب العمل، سواءً كان ذلك قبل تاريخ هذا العقد أو بعده، ستكون ملكاً لصاحب العمل إلى أقصى حد مسموح به قانوناً. ولهذا الغرض، يتعهد الموظف أيضاً، حال طلب صاحب العمل منه ذلك، بتحرير الوثائق وتقديم كافة أشكال المساعدة التي يراها صاحب العمل ضرورية أو مستحسنة لتسجيل حقوق الملكية الفكرية باسم صاحب العمل حصرياً. ويتنازل الموظف بموجبه عن كل الحقوق الحالية والمستقبلية الخاصة بالأعمال التي ينتجها أو يطورها أثناء عمله لدى صاحب العمل، ولا يحق للموظف المطالبة بأي تعويض عن هذه الحقوق أو حقوق الملكية أو المصالح.
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> c. The Employee agrees that the Employer has the right to hold and process information about the Employee for legal, personnel, administrative and management purposes and in particular to the processing of any sensitive personal data. The Employee consents to the Employer making such information available to any of its affiliates and regulatory authorities. </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p> ٣  . يوافق الموظف على أن لصاحب العمل الحق في الاحتفاظ ومعالجة المعلومات المتعلقة بالموظف لأغراض قانونية أو تتعلق بالإدارة وشؤون الموظفين وخصوصاً ما يتعلق بالاحتفاظ ومعالجة أي بيانات شخصية مهمة. كما يوافق الموظف على قيام صاحب العمل بإتاحة تلك المعلومات لأي من الشركات التابعة له أو السلطات التنظيمية.
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 10. Business Restraint </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">١٠ .قيود العمل </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p>The Employee agrees that during the term of this Contract, and for the period of twelve (12) months immediately following the expiration or termination of this Contract, the Employee shall not solicit or entice away or in any manner endeavour to solicit or entice away from the Employer any person who is employed by the Employer. This Article shall survive the termination or expiry of this Contract.</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>يوافق الموظف على عدم القيام، خلال مدة هذا العقد ولمدة اثني عشر (12) شهراً من تاريخ إنهائه أو انتهائه، بتقديم عرض أو محاولة إقناع أي شخص يعمل لدى صاحب العمل بأي وسيلة كانت لترك العمل لدى صاحب العمل.  وستبقى هذه المادة سارية المفعول حتى بعد إنهاء أو انتهاء هذا العقد.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 11. Working Hours </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right; width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">١١. ساعات العمل  </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> a. The normal number of working days are (6) six days per week, and the Employee shall work for forty eight (48) hours per week.  </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>١.تحدد أيام العمل ب(٦) ستة أيام بالأسبوع أو (٤٨)  ثمانية وأربعون ساعة في الأسبوع.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%;direction: rtl;">
                                    <p> b. The Employer will determine the Employee's weekly day(s) of rest. It is agreed that pay for the day(s) of rest is included in the Employee's regular wage. Any payment to the Employee for overtime worked will be subject to the Employee obtaining prior approval for the overtime from the Employee's line manager. If the Employee does not obtain prior written approval from the Employer to work overtime, the Employee will not be entitled to any overtime payment. </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
                                    <p> ٢. يحدد صاحب العمل أيام العطلة الأسبوعية التي يحصل عليها الموظف كأيام راحة. ومن المعلوم أن أجر أيام العطلة الأسبوعية مشمول ضمن الأجر الذي يتقاضاه الموظف بصفة منتظمة. ويشترط لحصول الموظف على مقابل لساعات العمل الاضافية التي عملها أن يحصل على موافقة مسبقة من مديره المباشر. وإذا لم يحصل الموظف على موافقة مسبقة من صاحب العمل على ساعات العمل الإضافية، فلن يستحق الموظف أي مقابل عنها
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> c. During the month of Ramadan, Muslim employees’s work hours will be (36) thirty six hours per week in accordance with the Saudi Labor Law. </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p> ٣  .خلال شهر رمضان المبارك تكون ساعات العمل الأسبوعية (36) ستة وثلاثون ساعة أسبوعياً للموظفين المسلمين وفقاً لنظام العمل السعودي.
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> d. The Employer will manage working hours and respite during the day for the employee, and the periods designated for rest, prayers, and meals shall not be included in the actual working hours, during such periods, the worker shall not be under the employer's authority.  </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>٤  .ينظم صاحب العمل ساعات العمل وفترات الراحة خلال اليوم للموظف ولا تدخل الفترات المخصصة للراحة والصلاة والطعام ضمن ساعات العمل الفعلية، ولا يكون الموظف خلال هذه الفترة تحت سلطة صاحب العمل.
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 12. National Holidays, Maternity Leave and Other Leave </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%;direction: rtl;">
                                    <strong style="text-align: left;text-decoration: underline;">١٢ . العطلات الرسمية وإجازة الوضع والإجازات الأخرى  </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> a. An Employee will be entitled to days off for public holidays in accordance with the Saudi Labour Law.  If the Employee is required to work on a holiday, the Employee shall be entitled to payment for every hour actually worked on such holiday in accordance with the Saudi Labour Law. The Employee must first obtain prior written approval from the Employer to work on a public holiday. Failure to obtain this approval will result in the Employee not being entitled to payment in accordance with this provision. </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>١.يحق للموظف خلال السنة الحصول على العطلات الرسمية المعتمدة وفقاً لنظام العمل السعودي. وإذا طُلب منه العمل خلال أيام العطلات الرسمية، فإنه يستحق تعويضاً عن كل ساعة عمل فعلية خلال هذه العطلة وفقاً لنظام العمل السعودي. ويشترط لحصول الموظف على مقابل لساعات العمل الإضافية التي عملها أن يحصل على موافقة مسبقة من مديره المباشر للعمل خلال العطلات الرسمية. وإذا لم يحصل الموظف على موافقة مسبقة من صاحب العمل على العمل لساعات إضافية فلن يستحق الموظف أي مقابل عنها حسب ما أشير إليه في هذه المادة.  </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> b. A female Employee will be eligible for maternity leave with full pay for a period of ten (10) weeks to be used as the Employee deems appropriate, provided that the same shall commence at least four (4) weeks prior to the expected due date, which shall be determined by the Employer's physician or based on a certified medical certificate. (this Article is applicable if the Employee is a female). </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p> ٢. تستحق الموظفة إجازة وضع بأجر كامل لمدة عشرة (10) أسابيع، توزعها كيف تشاء، تبدأ بحد أقصى بأربعة (4) أسابيع قبل التاريخ المرجح للوضع، ويحدد التاريخ المرجح للوضع بواسطة طبيب المنشأة، أو بناءً على شهادة طبية مصدقة من جهة صحية. (تنطبق هذه المادة على الموظفات فقط)
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> c. A female Employee shall be entitled to paid time off for feeding their child up to 2 years after the birth of the child, provided that the same shall not exceed one (1) hour per day in the aggregate. (this Article is applicable if the Employee is a female).</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p> ٣  .يحق للموظفة عندما تعود إلى مزاولة عملها بعد إجازة الوضع، أن تأخذ بقصد إرضاع مولودها لمدة عامين بعد ولادة الطفل فترة أو فترات للاستراحة لا تزيد في مجموعها على الساعة (1) في اليوم الواحد وتحسب هذه الفترة أو الفترات من ساعات العمل الفعلية.  (تنطبق هذه المادة على الموظفات فقط)
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> d. A Muslim Female Employee shall be entitled to four (4) months and ten (10) days paid leave following the demise of her husband and shall be entitled to extend such leave without pay if the Employee is pregnant during the said period until the due date. In all cases, such leave shall end following the birth of the Employee's child and the Employee will not be entitled to use the remaining period thereof. (this Article is applicable if the Employee is a Muslim female).  </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>٤  .يحق للموظفة المسلمة في حالة وفاة زوجها إجازة عدة بأجر كامل لمدة لا تقل عن أربعة (4) أشهر وعشرة (10) أيام من تاريخ الوفاة، ولها الحق في تمديد هذه الإجازة دون أجر إن كانت حاملاً –خلال هذه الفترة- حتى تضع حملها، ولا يجوز لها الاستفادة من باقي إجازة العدة الممنوحة لها بعد وضع حملها.  (تنطبق هذه المادة على الموظفات المسلمات فقط)
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> e. A None-Muslim female Employee shall be entitled to fifteen (15) days paid leave following the demise of her husband in accordance with Article 160/2 of the Saudi Labour Law. (this Article is applicable if the Employee is a Non-Muslim female).  </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>٥  .يحق للموظفة في حالة وفاة زوجها، إجازة بأجر كامل لمدة خمسة عشر (15) يوماً وفق ما نصت عليه الفقرة (2) من المادة (الستين بعد المائة) من نظام العمل. (تنطبق هذه المادة على الموظفات غير المسلمات فقط)
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 13. Annual Vacation </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">١٣ .الاجـازة السنوية </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> The Employee will be eligible for a vacation consisting of (30) days per year.  Vacation days shall be scheduled by the Employer in accordance with its operational requirements, provided that the vacation salary shall be paid in advance. The Employer reserves the right to transfer the vacation to the following year for a period not exceeding ninety (90) days, and may, with the written consent of the Employee, transfer the vacation to the end of the following year should operational circumstances so require.</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%";direction: rtl;>
                                    <p>يستحق الموظف عن كل عام، إجازة سنوية مدتها (30) ثلاثين  يوماً مدفوعة الأجر، ويحدد صاحب العمل تاريخ الإجازة خلال سنة الاستحقاق وفقاً لظروف العمل، على أن يتم دفع أجر الإجازة مقدماً عند استحقاقها، ولصاحب العمل تأجيل الإجازة بعد نهاية سنة استحقاقها لمدة لا تزيد عن (90) يوماً، كما له بموافقة الموظف كتابة تأجيلها إلى نهاية السنة التالية لسنة الاستحقاق وذلك حسب مقتضيات ظروف العمل.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 14. Medical Insurance </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">١٤ .التأمين الطبي </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> The Employer will provide the Employee with medical insurance coverage in accordance with the Cooperative Health Insurance Law and the company rules.</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>يلتزم صاحب العمل بتوفير الرعاية الطبية للموظف بالتامين الصحي وفقاً لأحكام نظام الضمان الصحي التعاوني وأنظمة الشركة.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 15. Medical Examination </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">١٥ .الفحص الطبي </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> The Employee shall be required to undergo a medical examination prior to employment or at any other time to determine the Employee's fitness for employment or continued employment..</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>يلتزم الموظف بأن يخضع وفقاً لطلب صاحب العمل للفحوص الطبية التي يرغب في إجرائها عليه قبل الالتحاق بالعمل، أو أثناءه للتحقق من خلوه من الأمراض المهنية أو السارية.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 16. Registration with GOSI </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">١٦ .اشتراك المؤسسة العامة للتأمينات الاجتماعية</strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> The Employer will register the Employee with the General Organization for Social Insurance and shall pay the subscription fee thereof in accordance with its regulations. </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>يلتزم صاحب العمل بتسجيل الموظف لدى المؤسسة العامة للتأمينات الاجتماعية وسداد الاشتراكات حسب أنظمتها.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 17. Additional Employee Obligations </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">١٧. التزامات إضافية للموظف  </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> a. The Employee will perform his duties in accordance with the best practices of the occupation and in accordance with the Employer's instructions if the same does not violate the Contract, applicable law or customs, and does not endanger the Employee.  </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>١.يلتزم الموظف بأن ينجز العمل الموكل إليه، وفقاً لأصول المهنة، ووفق تعليمات صاحب العمل، إذا لم يكن في هذه التعليمات ما يخالف العقد أو النظام أو الآداب العامة ولم يكن في تنفيذها ما يعرضه للخطر.</p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> b. The employee is obliged to maintain the employer's money , property and the tasks assigned to him\her because of his\her job such as  tools, devices and equipment. The employee is also responsible for any damage to the employer or the property and if he or she is excessively encroachment. The employee shall return all the employer's property, including his confidential information and documents, whether printed or electronic, before leaving in vacation or at the end of the contract</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p> ٢. يلتزم الموظف بالمحافظة على أموال وممتلكات صاحب العمل والمهمات المسندة إليه وما قد يسلم إليه بسبب وظيفته من أدوات وأجهزة ومعدات ويكون مسؤولًا عن أية أضرار يلحقها بصاحب العمل أو ممتلكاته متعدياً مفرطاً، ويلتزم الموظف بإعادة كل ممتلكات صاحب العمل ويشمل ذلك معلوماته ووثائقه السرية (سواء أكانت بشكل مطبوع أو إلكتروني) قبل مغادرته للإجازة أو عند انقضاء العقد.
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> c. The Employee must provide any help necessary without extra compensation in the event of circumstances endangering the safety of the work premises or the persons engaged therein.  </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p> ٣  . يلتزم الموظف بأن يقدم كل عون ومساعدة دون أن يشترط لذلك أجراً إضافياً في حالات الأخطار الي تهدد سلامة مكان العمل أو الأشخاص العاملين فيه.
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;"> 18. Termination </strong>
                                </div>
                                <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                    <strong style="text-align: left;text-decoration: underline;">١٨. إنهاء العقد  </strong>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> a. Except where Article 6. of this Contract applies, this Contract shall terminate upon the expiry of its term where prior written notice has been given in accordance with Article 5. (b.) of this contract or by the mutual agreement between the Parties evidenced by the written consent of the Employee.  </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>١.ينتهي هذا العقد بانتهاء مدته في العقد محدد المدة إذا تم إشعار أحد الطرفين من قبل الآخر خطياً بعدم رغبته في التجديد بناء على المادة (5.- 2.) من هذا العقد، أو باتفاق الطرفين على إنهائه، بشرط موافقة الموظف كتابة مع الأخذ في الاعتبار ما ورد في المادة (6.) من هذا العقد.  </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> b. The Employer may terminate this Contract for cause and without notice, compensation or end of service benefits in accordance with Article 80 of the Labour Law, or in case the Employee is found in breach of Article (39) of the Labour Law, or in breach of any of his/her obligation in this contract, provided that the Employee shall be entitled to submit his objections to the termination.</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p> ٢. يحق لصاحب العمل فسخ العقد وذلك طبقاً للحالات الواردة في المادة (الثمانون) من نظام العمل، أو في حالة مخالفة الموظف للمادة (٣٩) من نظام العمل، أو إخلاله بأي من التزاماته في هذا العقد، وذلك دون مكافأة أو إشعار للموظف أو تعويضه شريطة إتاحة الفرصة للموظف في إبداء أسباب معارضته للفسخ.
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> c. The Employee will be entitled to leave work and terminate the Contract for cause and without notice in accordance with Article 81 of the Labour Law, provided that the Employee shall be entitled to receive all of his entitlements. </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p> ٣  . يحق للموظف ترك العمل وإنهاء العقد دون إشعار صاحب العمل وذلك طبقاً للحالات الواردة في المادة (الحادية والثمانون) من نظام العمل، مع احتفاظه بحقه في الحصول على كافة مستحقاته.
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> d. In the event that this Contract is terminated without cause prior to the expiry of its term by one of the parties, the other party is entitled to two (2) months’ salary as compensation. It is understood between the parties, that if the employee submits his resignation prior the termination of the contract without a legitimate reason to terminate this contract, then the compensation in this paragraph shall apply. However, if the Employer accept such resignation, then such termination shall be considered to have been made with mutual consent.</p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>٤  .في حال إنهاء العقد من قبل أحد الطرفين قبل انقضاء مدته دون سبب مشروع فيحق للطرف الآخر مقابل هذا الإنهاء تعويضاً قدره أجر شهرين، ومن المتفق عليه بين الطرفين إذا تقدم الموظف باستقالة قبل تمام مدة العقد يعد سبباً غير مشروع لإنهاء العقد، ويطبق عليه التعويض المنصوص عليه في هذه الفقرة ما لم يوافق صاحب العمل على تلك الاستقالة، فيعتبر انهاء العقد قد تم بموافقة الطرفين.
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> e. Where the term of this contract has become indefinite, in the event that this Contract is terminated without cause by one of the Parties, the other Party is entitled to two (2) months' salary as compensation. (this Article is applicable if the contract is for an indefinite term only) </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>٥.في حال إنهاء العقد بعد تحوله إلى عقد غير محدد المدة من قبل أحد الطرفين دون سبب مشروع فيحق للطرف الآخر مقابل هذا الإنهاء تعويضاً قدره أجر شهرين. (تنطبق هذه المادة على العقد غير محدد المدة فقط)
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                    <p> f. The Employer also has the right to terminate this Contract for the following valid reasons upon giving the Employee two (2) months' notice in writing, or upon payment in lieu of such notice, in the following cases: </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                    <p>٦  .يحق لصاحب العمل أن ينهي هذا العقد للأسباب المشروعة التالية بموجب منح الموظف  إشعار مكتوب مدته (2) شهرين أو بدل عنه وفقاً لما يقتضيه نظام العمل السعودي:
                                    </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
                                    <p> i. force majeure; or </p>
                                </div>
                                <div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%;direction: rtl;">
                                    <p>١. في حالة القوة القاهرة </p>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
                                    <p> ii.permanent closure of the Employer; or </p>
                                </div>
                                    <div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%;direction: rtl;">
                                        <p> ٢.  إغلاق المنشأة نهائياً</p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
                                        <p> iii. the cessation of the activity in which the Employee works; or  </p>
                                    </div>
                                    <div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%;direction: rtl;">
                                        <p> ٣.  إنهاء النشاط الذي يعمل فيه العامل.
                                        </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
                                        <p> iv. the Employee's physical or mental disability rendering him unable to perform his work as established by a medical certificate; or </p>
                                    </div>
                                    <div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%;direction: rtl;">
                                        <p>٤.في حال عجز الموظف جسدياً أو عقلياً عن أداء عمله بموجب شهادة طبية.
                                        </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
                                        <p> v. the Employee ceases to hold any licences, certificates, permits or approvals necessary to perform his job. </p>
                                    </div>
                                    <div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%;direction: rtl;">
                                        <p>٥.إذا لم يعد الموظف حائزاً على أية تراخيص أو شهادات أو تصاريح أو موافقات لازمة له لأداء عمله.
                                        </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                        <p> g.Except where this Contract is terminated under Articles (18-b), (18.-c), or Article (6.) and Article (5), the Party who terminates this Contract must provide the other with prior written notice of at least sixty (60) days prior to the termination date. </p>
                                    </div>
                                    <div class="col-sm-6" style="padding-left: 20px;text-align: right;width:50%;direction: rtl;">
                                        <p>٧  .يلتزم أي من الطرفين عند إنهائه للعقد إشعار الطرف الآخر كتابة قبل الإنهاء بمدة لا تقل عن ستين (60) يوماً مع الأخذ بعين الإعتبار ما ورد في المادة (18-ب) و (19-ج) والمادة (6) والمادة (5) من هذا العقد
                                        </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                        <p> h.Upon the termination of the of the employment contract the Employer shall have the right to pay the Employee an amount in lieu of vacation days accrued but not taken. On the other hand, in the event the Employee has taken more holiday time than that accrued at the termination date, he or she shall pay the Employer the corresponding sum. </p>
                                    </div>
                                    <div class="col-sm-6" style="padding-left: 20px;text-align: right;width:50%;direction: rtl;">
                                        <p>٨  .يحق لصاحب العمل عند انتهاء عقد العمل ان يدفع للموظف مقابل نقدي عن أيام الاجازات المستحقة التي لم يتمتع بها الموظف، ويحق لصاحب العمل أن يطلب من الموظف سداد مقابل نقدي عن أيام الاجازات التي تمتع بها الموظف وتزيد عن أيام الاجازة المستحقة له
                                        </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                        <p> i.Upon the termination of this Contract, the Employee is required to return all property belonging to the Employer which is in the Employee's possession. Upon the termination of this Contract and the settlement of all outstanding matters, the Employee will execute a release of all claims against the Employer, and the Employer will issue a Service Certificate to the Employee. </p>
                                    </div>
                                    <div class="col-sm-6" style="padding-left: 20px;text-align: right;width:50%;direction: rtl;">
                                        <p>٩  .عند إنهاء هذا العقد يتعين على الموظف أن يعيد كل ما بحوزته من ممتلكات تعود لصاحب العمل. وعند إنهاء هذا العقد وتسوية جميع الأمور العالقة يبرم الموظف وصاحب العمل مخالصة وبراءة ذمة يخلي بموجبها كل طرف ذمة الطرف الآخر من جميع المطالبات ويصدر صاحب العمل شهادة خدمة للموظف
                                        </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <strong style="text-align: left;text-decoration: underline;"> 19. End of Service Award </strong>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <strong style="text-align: left;text-decoration: underline;">١٩ . مكافأة نهاية الخدمة  </strong>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                        <p> a. Unless this Contract is terminated based on any of the orescriped reasons in Article (18-b) of this Contract, the Employee will receive an end of service award as per Saudi Labor Law.  </p>
                                    </div>
                                    <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                        <p>١.ما لم يكن إنهاء العلاقة التعاقدية مبني على أي من الحالات المذكورة في المادة (١٨-ب) من هذا العقد، فيستحق الموظف، مكافأة نهاية خدمة وفقاً لنظام العمل.  </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                        <p> b.Commissions, bonuses, and similar payments which by their nature are subject to increase and decrease shall not be considered part of the Employee's wage for purposes of calculating the end of service award.</p>
                                    </div>
                                    <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                        <p> ٢. لأغراض احتساب مكافأة نهاية الخدمة، فإن العمولات والمدفوعات المشابهة التي يحصل عليها الموظف والتي تعتبر بطبيعتها قابلة للزيادة والنقصان، لا تعتبر جزءاً من أجره عند احتساب مكافأة نهاية الخدمة.
                                        </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <strong style="text-align: left;text-decoration: underline;"> 20. Waiver / Severability </strong>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right; width:50%">
                                        <strong style="text-align: left;text-decoration: underline;">٢٠ .التنازل وإمكانية الفصل بين بنود الاتفاق </strong>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <p>The failure of either Party (a) to enforce at any time any of the provisions of this Contract or (b) to require at any time performance by the other Party of any of the provisions hereof, shall in no way be construed to be a waiver of the provisions or to affect the validity of this Contract or the right of either Party thereafter to enforce each and every provision in accordance with the terms of this Contract.  Invalidation of any provision of this Contract, or a portion thereof, shall not invalidate any other provision or the remainder of the relevant provision and the rest of this Contract shall in all such cases remain in full force.</p>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right; width:50%">
                                        <p>إذا تعذر على أي من الطرفين في أي وقت إنفاذ أي شرط من شروط هذا العقد أو مطالبة الطرف الآخر في أي وقت بإنفاذ أي من أحكامه، فإن ذلك لا يجب أن يفسر بأي حال من الأحوال على أنه تنازل عن تلك الأحكام أو على أنه يؤثر على صلاحية هذا العقد أو على حق أي من الطرفين في إنفاذ كل حكم من أحكام العقد وفقا لشروطه وأحكامه. وإذا أصبح أي شرط من شروط هذا العقد أو جزء منه باطلاً، فإن ذلك لا يبطل أي شرط آخر أو الجزء المتبقي من الشرط المعني وبقية أجزاء هذه الاتفاقية. وتظل بقية شروط وأحكام هذا العقد في جميع هذه الحالات نافذة بكامل القوة والأثر. </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <strong style="text-align: left;text-decoration: underline;"> 21. Governing Law / Disputes </strong>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <strong style="text-align: left;text-decoration: underline;">٢١ .القانون الحاكم/ المنازعات </strong>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                        <p>This Contract shall be governed by and construed in accordance with the laws and regulations of the Kingdom of Saudi Arabia, including without limitation the Labour Law issued under Royal Decree No. M/51 dated 23/08/1426H (as amended from time to time).  The Parties will make every effort to settle disputes amicably, but if the Parties are unable to reach an amicable settlement, the dispute will be referred to and decided by the relevant local labour committee in Riyadh or other appropriate Saudi Arabian administrative or judicial body in Riyadh.</p>
                                    </div>
                                    <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                        <p>يخضع هذا العقد لأنظمة وقوانين المملكة العربية السعودية ويفسر وفقاً لها، بما في ذلك على سبيل المثال لا الحصر نظام العمل الصادر بموجب المرسوم الملكي رقم م/51، بتاريخ 23/8/1426هـ. وتعديلاته وعلى الطرفين أن يبذلا كل جهد ممكن لتسوية أية نزاعات تنشأ بينهما على خلفية هذا العقد بالطرق الودية. وإذا تعذر على الطرفين التوصل إلى تسوية ودية، يحال النزاع إلى اللجنة العمالية المعنية في مدينة الرياض، أو إلى السلطات القضائية السعودية المعنية في مدينة الرياض حيث تعتبر هي جهة الاختصاص والفصل في هذا العقد. </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <strong style="text-align: left;text-decoration: underline;"> 22. Entire Agreement </strong>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <strong style="text-align: left;text-decoration: underline;">٢٢ .مجمل الاتفاق </strong>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                        <p> This Contract constitutes the entire agreement between the Parties with respect to the Employee's employment by the Employer in the Kingdom of Saudi Arabia and supersedes and renders null and void all prior or contemporaneous agreements or understandings, whether oral or written.
                                            This Contract may only be amended, or supplemented, by the written agreement of the Employee and the Employer.</p>
                                    </div>
                                    <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                        <p>يشكل هذا العقد مجمل الاتفاق بين الطرفين فيما يتعلق بتعيين الموظف من قبل صاحب العمل في المملكة العربية السعودية. ويلغي هذا العقد ويحل محل جميع الاتفاقيات أو التفاهمات السابقة أو المتزامنة مع هذا العقد، خطية كانت أم شفهية، ولا يجوز تعديل هذا العقد أو الاضافة إليه إلا بموجب اتفاق خطي بين صاحب العمل والموظف. </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <strong style="text-align: left;text-decoration: underline;"> 23. Notices </strong>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <strong style="text-align: left;text-decoration: underline;">٢٣ .الاشعارات </strong>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                        <p> All notices between the Parties shall be in writing and sent to the addresses indicated in this contract, by registered mail, express mail, or email to both Parties. Each party undertakes to notify the other in writing in case of changing the address or changing the email, otherwise the address and email indicated in this contract will remain the official communication channels.</p>
                                    </div>
                                    <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                        <p>تتم جميع الإشعارات بين الطرفين كتابة على العناوين الموضحة في هذا العقد عن طريق البريد المسجل أو البريد الممتاز أو البريد الإلكتروني لكلٍ من الطرفين، ويلتزم كل طرف بإشعار الآخر خطياً في حال تغييره للعنوان الخاص به، أو تغيير البريد الإلكتروني، وإلا اعتبر العنوان أو البريد الإلكتروني المدونان في هذا العقد، هما المعمول بهما نظاماً.</p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <strong style="text-align: left;text-decoration: underline;"> 24.Employee's Endorsement of the Validity of the Information : </strong>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <strong style="text-align: left;text-decoration: underline;">٢٤ .إقرار الموظف بصحة المعلومات: </strong>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                        <p> The employee acknowledges that all the information he\she provides to the employer is correct. If otherwise proven, the employer has the right to take the action he\she deems appropriate.</p>
                                    </div>
                                    <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                        <p>يقر الموظف بأن جميع البيانات التي قدمها لصاحب العمل صحيحة، وفي حال ثبوت خلاف ذلك يحق لصاحب العمل اتخاذ الإجراء الذي يراه مناسباً.</p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <strong style="text-align: left;text-decoration: underline;"> 25.Counterparts: </strong>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <strong style="text-align: left;text-decoration: underline;">٢٥   .نسخ العقد </strong>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
                                        <p> This Contract has been executed in two (2) originals in Arabic and English out of (25) articles, in the event of a conflict between the same article in both language, the Arabic article shall it considered approved for interpretation of this contract and each party has received a copy thereof.</p>
                                    </div>
                                    <div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%;direction: rtl;">
                                        <p>حرر هذا العقد من نسختين أصليتين باللغتين العربية والإنجليزية من خمسة وعشرون مادة، وفي حال وجد اختلاف بين النص الواحد في كلا اللغتين يعتبر النص العربي هو المعتمد لتفسير هذا العقد، وقد أستلم كل طرف نسخة منها للعمل بموجبها.</p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <strong style="text-align: left"> The Employer </strong>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <strong style="text-align: left;">صاحب العمل </strong>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <p>On Behalf of Business Research and Development Co. </p>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <p>بالنيابة عن شركة أبحاث وتطوير الأعمال التجارية </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <p>Name : ............................ </p>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <p>الاسم:............................ </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <p>Date : ..../../..</p>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <p>التاريخ: ..../../.. </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <p>Signature: ............................</p>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <p>التوقيع: ............................ </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <strong style="text-align: left"> The Employee </strong>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <strong style="text-align: left;">الموظف </strong>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <p>Name : {28} </p>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <p>الاسم:{29} </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <p>Date : ..../../..</p>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <p>التاريخ: ..../../.. </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <p>Signature: ............................</p>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <p>التوقيع: ............................ </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <p></p>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <p>  الإيميل الشخصي: ............................ </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <p></p>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <p>  رقم الجوال الشخصي: ............................ </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <p></p>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <p> رقم شخص آخر في حال الطوارئ: ............................ </p>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
                                        <p style="text-align: left"></p>
                                    </div>
                                    <div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
                                        <p> العنوان الوطني: ............................ </p>
                                    </div>
                                </div>
    
                        </div>'''.format(self.id, self.date_start, self.id, self.date_start, self.employee_id.name,
                                         self.employee_id.country_id.name, \
                                         self.employee_id.passport_id, self.employee_id.residence_place_id.name,
                                         self.employee_id.name_in_id, self.employee_id.country_id.name, \
                                         self.employee_id.passport_id, self.employee_id.residence_place_id.name, \
                                         self.job_id.name, self.job_id.name, self.total_salary, self.total_salary,
                                         self.wage, self.wage, self.housing_allowance_value,
                                         self.housing_allowance_value, \
                                         self.transportation_allowance_value, self.transportation_allowance_value,
                                         self.employee_id.office_id.name, self.employee_id.office_id.name, \
                                         self.date_start, self.date_end, self.date_start, self.date_end,
                                         self.employee_id.name, self.employee_id.name_in_id,
                                         self.employee_id.identification_id)

        if self.contract_type_sel == 'remote_work':
            template = '''<div style="with: 100%; clear: both;">
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;font-size: 20px;text-align: center;width:50%">
								<strong>EMPLOYMENT CONTRACT</strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;font-size: 20px;text-align: center;width:50%">
								<strong>عقد عمـل عن بعد</strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p style="text-align: left;">This employment contract no. ({0}) is entered into on {1} between: </p>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<p> حُرر هذا العقد ({2}) بتاريخ {3}بين كل من:</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p> 1) Business Research and Development Company,  a limited liability  company incorporated in Saudi Arabia under   Commercial Registration No. 1010421211 and headquartered at Riyadh - .Alyasmin District – Riyadh 13326-2871, Kingdom of Saudi Arabia  (the "Employer"); and</p>
							</div>
							<div class="col-sm-6" style="padding: 10px;text-align: right;width:50%"><p>١) شركةأبحاث وتطوير الأعمال التجارية ، شركة ذات مسؤولية محدودة مسجلة في المملكة العربية السعودية بموجب سجل تجاري رقم ١٠١٠٤٢١٢١١ وعنوان مقرها الرئيس الرياض - حي الياسمين - الرياض 13326-2871 المملكة العربية السعودية (ويشار إليها فيما يلي في هذا العقد بـ "صاحب العمل") ، و</p></div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p style="text-align: left;">2) [{4}], a [{5}] national, with I.D/Passport No. [{6}], whose address is located at [{7}] (the "Employee").</p>
							</div>
							<div class="col-sm-6" style=" padding: 10px;direction: rtl;text-align: right;width:50%">
								<p>    ٢ )  [{8}]، [{9}] الجنسية، إقامة رقم{22} ، وجواز رقم [{10}]، وعنوانه [{11}]. (ويشار إليه فيما يلي بـ "الموظف")
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p style="text-align: left;">(together, the "Parties").<br></br>
									Whereas both Parties have acknowledged their legal competence to conclude this contract; the Parties hereby agree as follows: </p>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<p>(ويشار اليهما معاً بـ "الطرفين أو الطرفان"). <br></br>
									وبعد أن أقر الطرفان بأهليتهما المعتبرة شرعاً ونظاماً لإبرام هذا العقد، فقد اتفق الطرفان على الشروط والأحكام التالية:</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 1. Gregorian Calendar </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> ١. التاريخ الميلادي </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p style="text-align: left;">All periods and dates in this Contract will be in accordance with the Gregorian Calendar. </p>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<p>تكون جميع المدد والتواريخ في هذا العقد وفق التاريخ الميلادي.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 2. Appointment </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> ٢. التعيين </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p style="text-align: left;">a. The Parties agree that the Employee shall work under the management and supervision of the Employer as
									[{12}]. The Employee shall perform the duties assigned to such role in a way commensurate to the Employee's practical and technical capabilities and expertise, and in accordance with the operational requirements in a manner that does not violate Articles 58, 59 and 60 of the Labour Law.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;width:50%">
								<p>i. اتفق الطرفان على أن يعمل الموظف تحت إدارة وإشراف صاحب العمل بوظيفة [{13}] ومباشرة الأعمال التي يكلف بها بما يتناسب مع خبراته وقدراته العملية والعلمية والفنية، وفقاً لاحتياجات العمل وبما لا يتعارض مع الضوابط المنصوص عليها في المواد (الثامنة والخمسين والتاسعة والخمسين والستين) من نظام العمل.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p style="text-align: left;">b.  Employment hereunder is conditional on the Employee's reporting to work not later than the date specified in paragraph (a.) of Article (5.) below.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;">
								<p>ii . يشترط لتعيين الموظف بموجب هذا العقد مباشرته لعمله في موعد لا يتجاوز التاريخ المحدد في المادة (5.) الفقرة (1.) أدناه.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p style="text-align: left;">c.  This Contract shall be subject to and conditional upon the relevant Saudi Arabian government authorities granting any necessary permissions,including any regulatory consents, residency and/or work permits (in each case, as applicable).</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;width:50%">
								<p>iii . يخضع هذا العقد ويتوقف نفاذه على ضرورة الحصول على موافقة السلطات المعنية في المملكة العربية السعودية بما في ذلك أي رخص أو تصاريح مطلوبة نظاماً و/أو الحصول على الاقامة ورخص العمل اللازمة حسب ما يقتضي الأمر.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;;text-align: left;width:50%">
								<p style="text-align: left;">d.The employee shall bear the financial costs related to the fees of the Saudi Zakat, Tax and Customs Authority at the rate of 15%. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;">
								<p>iiii . يتحمل الموظف التكاليف المالية الخاصة برسوم هيئة الزكاة والضريبة والجمارك السعودية بمقدار 15%. </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 3. Basic Monthly Salary and Other Benefits </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> ٣ . الأجر الأساسي الشهري والمزايا الأخرى </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p style="text-align: left;"> 1. <strong>Total Salary: </strong>({14}) riyals / month (Gregorian) inclusive of customs duties and government taxes.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
								<p style="text-align: right;"> ١. <strong>الراتب الإجمالي</strong> :({15})  ريال في الشهر الميلادي قبل خصم الضرائب الخ </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p style="text-align: left;"> 2. value is deducted referred to in paragraph (e) as agreed government fees.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: left;width:50%">
								<p style="text-align: right;"> ٢. يتم استقطاع النسبة المشار إليها في فقرة (د) كرسوم حكومية متفق عليها. </p>
							</div>
						</div>

						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 4. Work Location </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">٤. موقع العمل </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p style="text-align: left;">The Employee will be employed remotely.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;direction: rtl;text-align: right;width:50%">
								<p> يكون موقع العمل الموظف عن بعد.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 5. Term of Employment </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">٥. مدة العقد </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a. The duration of this Contract is a year, beginning on the commencement date of the Employee's employment on [{16}] and ending on [{17}].</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p>
									١ . مدة هذا العقد سنة كاملة. تبدأ من تاريخ الموظف للعمل في [{18}] وتنتهي في [{19}].</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> b. The term of this Contract will renew automatically for a similar duration, unless one Party provides the other with prior written notice of its intention not to renew no later than sixty (60) days prior to the expiry of the then current term specified in paragraph (a.) of Article (5.) of this contract .</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p>
									٢ . تتجدد مدة العقد لمدة أو لمدد مماثلة ما لم يشعر أحد الطرفين الآخر خطياً بعدم رغبته في التجديد قبل ستين  (60) يوماً من تاريخ انتهاء مدة العقد المحددة في المادة (5.) الفقرة (1.) من هذا العقد، أو المدة المجددة.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 6. Probation Period </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">٦. فترة التجربة </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> The Employee shall be on probation for ninety (90) days beginning on the first day of employment. The Parties may by written agreement extend the probation period for not more than ninety (90) days. During the probation period, the Employer may terminate this Contract without notice and without the payment of any compensation or end of service award. This probation period is exclusive of Eid Al Fitr, Eid Al Adha holidays, and sick le­­ave.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p>يخضع الموظف لفترة تجربة تستمر لمدة تسعين (90) يوماً تبدأ من تاريخ مباشرته للعمل، ولا يدخل في حسابها إجازة عيدي الفطر والأضحى والإجازة المرضية. ويجوز باتفاق مكتوب بين الطرفين تمديد فترة التجربة لمدة تسعين (90) يوماً أخرى، ويحق لصاحب العمل خلال فترة التجربة إنهاء هذا العقد بدون إشعار، وبدون تعويض أو مكافأة نهاية الخدمة.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 7. Compliance with Laws and Instructions </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">٧ .القوانين والتعليمات </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> The Employee undertakes to comply with good conduct during the employment and at all times, and with all policies and procedures, directives and instructions issued by the Employer and acknowledges that the laws, regulations and customs of Saudi Arabia shall govern this Contract. The Employee shall bear all penalties incurred by the Employee with respect to such laws, regulations and customs.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p>يلتزم الموظف بحسن السلوك والأخلاق أثناء العمل في جميع الأوقات ويلتزم بالأنظمة والأعراف والعادات والآداب المرعية في المملكة العربية السعودية وكذلك الالتزام بكل السياسات والإجراءات والقواعد واللوائح والتعليمات المعمول بها لدى صاحب العمل ويتحمل كافة الغرامات المالية الناتجة عن مخالفته لتلك الأنظمة.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 8. Other Employment </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">٨ .العمل لدى الغير </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a. In accepting employment hereunder, the Employee undertakes that he will not engage in any other business or employment (with or without remuneration). </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p>١. بقبوله العمل بموجب هذا العقد، يتعهد الموظف بأن لا يمارس أي عمل أو وظيفة أخرى سواء بمقابل أو بدون مقابل.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> b. The Employee shall not without the Employer’s prior written permission be entitled to directly or indirectly, temporarily or permanently be engaged by or do any business solely, with individual(s) or companies other than the Employer.  </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p> ٢. يلتزم الموظف بأن لا يرتبط بأداء أي عمل بشكل مباشر أو غير مباشر سواء بشكل مؤقت أو دائم مع أي شخص أو أشخاص سواء كانوا أفراداً أو شركات بخلاف صاحب العمل، دون موافقة مسبقة من صاحب العمل. </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> c. The Employee shall devote their time and attention during working hours to the best interests and the business of the Employer and shall faithfully serve the Employer and shall use their utmost best endeavours to promote the Employer’s business. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p>  ٣ . يلتزم الموظف بأن يكرس وقته وعنايته خلال ساعات العمل لمصالح وأعمال صاحب العمل، وأن يعمل لصاحب العمل بإخلاص وأن يبذل أقصى ما يمكنه لتنمية أعمال  صاحب العمل. </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 9. Confidentiality / Intellectual Property </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">٩ .السريـة/ الملكية الفكرية </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a. The Employee shall commit to confidentiality and  don't, under any circumstances, at any time during his employment with the Employer or thereafter, disclose any information regarding the business or affairs of the Employer (or any associated company), their trade practices, trade and industrial and professional secrets or customers to any person, firm or company except under the direction and with the prior written consent of the Employer. Upon termination of the Employee's employment with the Employer, the Employee shall not remove or retain figures, calculations, letters, reports, or other data or documents containing such information. This Article shall survive the termination or expiry of this Contract for a period of 25 years applicable anywhere in the world. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p>١. على الموظف طوال مدة خدمته لدى صاحب العمل وبعد انتهائها، بأن يلتزم بالسرية وألا يفصح بأي حال من الأحوال، أو في أي وقت من الأوقات، عن أية معلومات تتعلق بنشاط صاحب العمل أو شؤونه (أو بعمل أو شؤون أي من الشركات التابعة له) أو بممارساتها أو أسرارها التجارية والصناعية والمهنية أو عملائها، إلى أي شخص أو مؤسسة أو شركة، إلا بتوجيه من صاحب العمل وموافقة كتابية مسبقة منه. ولا يجوز للموظف عند إنهاء خدمته أن يزيل أو يحتفظ بأية أرقام أو حسابات أو خطابات أو تقارير أو بيانات أو مستندات أخرى تحتوي على مثل تلك المعلومات. وستبقى هذه المادة سارية المفعول حتى بعد إنهاء أو انتهاء هذا العقد ولمدة 25 سنة في أي مكان في العالم.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> b. The Employee acknowledges that all intellectual property rights subsisting or attaching to the Employer's confidential information or other materials of whatsoever nature made, originated or developed by the Employee at any time during his employment with the Employer whether before or after the date of this Contract shall belong to and vest in the Employer to the fullest extent permitted by law.  To such end the Employee also undertakes, at the request of the Employer, to execute such documents and give all such assistance as in the opinion of the Employer may be necessary or desirable to vest any intellectual property rights therein in the Employer absolutely and the Employee hereby assigns all present and future rights for works produced or originated by him during his employment. The Employee shall not have any claim to any right, title or interest therein. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p> ٢. يقر الموظف بأن جميع حقوق الملكية الفكرية الناشئة عن أو المرتبطة بالمعلومات السرية الخاصة بصاحب العمل أو المواد الأخرى أياً كانت طبيعتها والتي يتم إنشاؤها أو تطويرها من قبل الموظف في أي وقت خلال عمله لدى صاحب العمل، سواءً كان ذلك قبل تاريخ هذا العقد أو بعده، ستكون ملكاً لصاحب العمل إلى أقصى حد مسموح به قانوناً. ولهذا الغرض، يتعهد الموظف أيضاً، حال طلب صاحب العمل منه ذلك، بتحرير الوثائق وتقديم كافة أشكال المساعدة التي يراها صاحب العمل ضرورية أو مستحسنة لتسجيل حقوق الملكية الفكرية باسم صاحب العمل حصرياً. ويتنازل الموظف بموجبه عن كل الحقوق الحالية والمستقبلية الخاصة بالأعمال التي ينتجها أو يطورها أثناء عمله لدى صاحب العمل، ولا يحق للموظف المطالبة بأي تعويض عن هذه الحقوق أو حقوق الملكية أو المصالح.
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> c. The Employee agrees that the Employer has the right to hold and process information about the Employee for legal, personnel, administrative and management purposes and in particular to the processing of any sensitive personal data. The Employee consents to the Employer making such information available to any of its affiliates and regulatory authorities. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p> ٣  . يوافق الموظف على أن لصاحب العمل الحق في الاحتفاظ ومعالجة المعلومات المتعلقة بالموظف لأغراض قانونية أو تتعلق بالإدارة وشؤون الموظفين وخصوصاً ما يتعلق بالاحتفاظ ومعالجة أي بيانات شخصية مهمة. كما يوافق الموظف على قيام صاحب العمل بإتاحة تلك المعلومات لأي من الشركات التابعة له أو السلطات التنظيمية.
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 10. Business Restraint </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١٠ .قيود العمل </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p>The Employee agrees that during the term of this Contract, and for the period of twelve (12) months immediately following the expiration or termination of this Contract, the Employee shall not solicit or entice away or in any manner endeavour to solicit or entice away from the Employer any person who is employed by the Employer. This Article shall survive the termination or expiry of this Contract.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p>يوافق الموظف على عدم القيام، خلال مدة هذا العقد ولمدة اثني عشر (12) شهراً من تاريخ إنهائه أو انتهائه، بتقديم عرض أو محاولة إقناع أي شخص يعمل لدى صاحب العمل بأي وسيلة كانت لترك العمل لدى صاحب العمل.  وستبقى هذه المادة سارية المفعول حتى بعد إنهاء أو انتهاء هذا العقد.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 11. Working Hours </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١١. ساعات العمل  </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a. The normal number of working days are (5) five days per week, and the Employee shall work for forty hours (40) hours per week.  </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p>١.تتحدد أيام العمل ب)5(خمس أيام بالأسبوع أو (40) أربعون ساعة في الأسبوع،.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> b. The Employer will determine the Employee's weekly day(s) of rest. It is agreed that pay for the day(s) of rest is included in the Employee's regular wage. Any payment to the Employee for overtime worked will be subject to the Employee obtaining prior approval for the overtime from the Employee's line manager. If the Employee does not obtain prior written approval from the Employer to work overtime, the Employee will not be entitled to any overtime payment. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;">
								<p> ٢. يحدد صاحب العمل أيام العطلة الأسبوعية التي يحصل عليها الموظف كأيام راحة. ومن المعلوم أن أجر أيام العطلة الأسبوعية مشمول ضمن الأجر الذي يتقاضاه الموظف بصفة منتظمة. ويشترط لحصول الموظف على مقابل لساعات العمل الاضافية التي عملها أن يحصل على موافقة مسبقة من مديره المباشر. وإذا لم يحصل الموظف على موافقة مسبقة من صاحب العمل على ساعات العمل الإضافية، فلن يستحق الموظف أي مقابل عنها
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> c. During the month of Ramadan, Muslim employees’s work hours will be (36) thirty six hours per week in accordance with the Saudi Labor Law. </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;">
								<p> ٣  .خلال شهر رمضان المبارك تكون ساعات العمل الأسبوعية (36) ستة وثلاثون ساعة أسبوعياً للموظفين المسلمين وفقاً لنظام العمل السعودي.
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> d. The Employer will manage working hours and respite during the day for the employee, and the periods designated for rest, prayers, and meals shall not be included in the actual working hours, during such periods, the worker shall not be under the employer's authority.  </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;">
								<p>٤  .ينظم صاحب العمل ساعات العمل وفترات الراحة خلال اليوم للموظف ولا تدخل الفترات المخصصة للراحة والصلاة والطعام ضمن ساعات العمل الفعلية، ولا يكون الموظف خلال هذه الفترة تحت سلطة صاحب العمل.
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 12. National Holidays, Maternity Leave and Other Leave </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١٢ . العطلات الرسمية   </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a.An Employee will be entitled to days off for public holidays in accordance with the Saudi Labour Law.  </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;">
								<p>١.يحق للموظف خلال السنة الحصول على العطلات الرسمية المعتمدة وفقاً لنظام العمل السعودي ونظام العمل في دولة الإقامة للموظف.  </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 13. Annual Vacation </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١٣ .الاجـازة السنوية </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> The Employee will be eligible for a vacation consisting of (21) days per year.  Vacation days shall be scheduled by the Employer in accordance with its operational requirements, provided that the vacation salary shall be paid in advance. The Employer reserves the right to transfer the vacation to the following year for a period not exceeding ninety (90) days, and may, with the written consent of the Employee, transfer the vacation to the end of the following year should operational circumstances so require.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p>يستحق الموظف عن كل عام، إجازة سنوية مدتها (21)واحد وعشرون  يوماً مدفوعة الأجر، ويحدد صاحب العمل تاريخ الإجازة خلال سنة الاستحقاق وفقاً لظروف العمل، على أن يتم دفع أجر الإجازة مقدماً عند استحقاقها، ولصاحب العمل تأجيل الإجازة بعد نهاية سنة استحقاقها لمدة لا تزيد عن (90) يوماً، كما له بموافقة الموظف كتابة تأجيلها إلى نهاية السنة التالية لسنة الاستحقاق وذلك حسب مقتضيات ظروف العمل.</p>
							</div>
						</div>

						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 14. Additional Employee Obligations </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١٤. التزامات إضافية للموظف  </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a. The Employee will perform his duties in accordance with the best practices of the occupation and in accordance with the Employer's instructions if the same does not violate the Contract, applicable law or customs, and does not endanger the Employee.  </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p>١.يلتزم الموظف بأن ينجز العمل الموكل إليه، وفقاً لأصول المهنة، ووفق تعليمات صاحب العمل، إذا لم يكن في هذه التعليمات ما يخالف العقد أو النظام أو الآداب العامة ولم يكن في تنفيذها ما يعرضه للخطر.</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> b. The employee is obliged to maintain the employer's money , property and the tasks assigned to him\her because of his\her job such as  tools, devices and equipment. The employee is also responsible for any damage to the employer or the property and if he or she is excessively encroachment. The employee shall return all the employer's property, including his confidential information and documents, whether printed or electronic, before leaving in vacation or at the end of the contract</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p> ٢. يلتزم الموظف بالمحافظة على أموال وممتلكات صاحب العمل والمهمات المسندة إليه وما قد يسلم إليه بسبب وظيفته من أدوات وأجهزة ومعدات ويكون مسؤولًا عن أية أضرار يلحقها بصاحب العمل أو ممتلكاته متعدياً مفرطاً، ويلتزم الموظف بإعادة كل ممتلكات صاحب العمل ويشمل ذلك معلوماته ووثائقه السرية (سواء أكانت بشكل مطبوع أو إلكتروني) قبل مغادرته للإجازة أو عند انقضاء العقد.
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> c. The Employee must provide any help necessary without extra compensation in the event of circumstances endangering the safety of the work premises or the persons engaged therein.   </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p> ٣  . يلتزم الموظف بأن يقدم كل عون ومساعدة دون أن يشترط لذلك أجراً إضافياً في حالات الأخطار الي تهدد سلامة مكان العمل أو الأشخاص العاملين فيه.

								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> 15. Termination </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">١٥. إنهاء العقد  </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> a. Except where Article 6. of this Contract applies, this Contract shall terminate upon the expiry of its term where prior written notice has been given in accordance with Article 5. (b.) of this contract or by the mutual agreement between the Parties evidenced by the written consent of the Employee.  </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p>١.ينتهي هذا العقد بانتهاء مدته في العقد محدد المدة إذا تم إشعار أحد الطرفين من قبل الآخر خطياً بعدم رغبته في التجديد بناء على المادة (5.- 2.) من هذا العقد، أو باتفاق الطرفين على إنهائه، بشرط موافقة الموظف كتابة مع الأخذ في الاعتبار ما ورد في المادة (6.) من هذا العقد.  </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> b. The Employer may terminate this Contract for cause and without notice, compensation or end of service benefits in accordance with Article 80 of the Labour Law, or in case the Employee is found in breach of Article (39) of the Labour Law, or in breach of any of his/her obligation in this contract, provided that the Employee shall be entitled to submit his objections to the termination.</p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p> ٢. يحق لصاحب العمل فسخ العقد وذلك طبقاً للحالات الواردة في المادة (الثمانون) من نظام العمل، أو في حالة مخالفة الموظف للمادة (٣٩) من نظام العمل، أو إخلاله بأي من التزاماته في هذا العقد، وذلك دون مكافأة أو إشعار للموظف أو تعويضه شريطة إتاحة الفرصة للموظف في إبداء أسباب معارضته للفسخ.
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
								<p> c. The Employer also has the right to terminate this Contract for the following valid reasons upon giving the Employee two (2) months' notice in writing, or upon payment in lieu of such notice, in the following cases: </p>
							</div>
							<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
								<p> ٣  . يحق لصاحب العمل أن ينهي هذا العقد للأسباب المشروعة التالية بموجب منح الموظف إشعار مكتوب مدته (2) شهرين أو بدل عنه وفقاً لما يقتضيه نظام العمل السعودي:
								</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p> i. force majeure; or </p>
							</div>
							<div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%">
								<p>١. في حالة القوة القاهرة. </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p> ii.permanent closure of the Employer; or </p>
							</div>
								<div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%">
									<p> ٢.  إغلاق المنشأة نهائياً.</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
									<p> iii. the cessation of the activity in which the Employee works; or  </p>
								</div>
								<div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%">
									<p> ٣  . إنهاء النشاط الذي يعمل فيه العامل.
									</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
									<p> iv. the Employee's physical or mental disability rendering him unable to perform his work as established by a medical certificate; or </p>
								</div>
								<div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%">
									<p>٤  .في حال عجز الموظف جسدياً أو عقلياً عن أداء عمله بموجب شهادة طبية.
									</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
									<p> v. the Employee ceases to hold any licences, certificates, permits or approvals necessary to perform his job. </p>
								</div>
								<div class="col-sm-6" style="padding-right: 30px;text-align: right;width:50%">
									<p>٥  .إذا لم يعد الموظف حائزاً على أية تراخيص أو شهادات أو تصاريح أو موافقات لازمة له لأداء عمله.
									</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> g.Except where this Contract is terminated under Articles (18-b), (18.-c), or Article (6.) and Article (5), the Party who terminates this Contract must provide the other with prior written notice of at least sixty (60) days prior to the termination date. </p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
									<p>٧  .يلتزم أي من الطرفين عند إنهائه للعقد إشعار الطرف الآخر كتابة قبل الإنهاء بمدة لا تقل عن ستين (60) يوماً مع الأخذ بعين الإعتبار ما ورد في المادة (18-ب) و (19-ج) والمادة (6) والمادة (5) من هذا العقد
									</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> h.Upon the termination of the of the employment contract the Employer shall have the right to pay the Employee an amount in lieu of vacation days accrued but not taken. On the other hand, in the event the Employee has taken more holiday time than that accrued at the termination date, he or she shall pay the Employer the corresponding sum. </p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
									<p>٨  .يحق لصاحب العمل عند انتهاء عقد العمل ان يدفع للموظف مقابل نقدي عن أيام الاجازات المستحقة التي لم يتمتع بها الموظف، ويحق لصاحب العمل أن يطلب من الموظف سداد مقابل نقدي عن أيام الاجازات التي تمتع بها الموظف وتزيد عن أيام الاجازة المستحقة له
									</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> i.Upon the termination of this Contract, the Employee is required to return all property belonging to the Employer which is in the Employee's possession. Upon the termination of this Contract and the settlement of all outstanding matters, the Employee will execute a release of all claims against the Employer, and the Employer will issue a Service Certificate to the Employee. </p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
									<p>٩  .عند إنهاء هذا العقد يتعين على الموظف أن يعيد كل ما بحوزته من ممتلكات تعود لصاحب العمل. وعند إنهاء هذا العقد وتسوية جميع الأمور العالقة يبرم الموظف وصاحب العمل مخالصة وبراءة ذمة يخلي بموجبها كل طرف ذمة الطرف الآخر من جميع المطالبات ويصدر صاحب العمل شهادة خدمة للموظف
									</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left;text-decoration: underline;"> 16. Waiver / Severability </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;text-decoration: underline;">١٦ .التنازل وإمكانية الفصل بين بنود الاتفاق </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p>The failure of either Party (a) to enforce at any time any of the provisions of this Contract or (b) to require at any time performance by the other Party of any of the provisions hereof, shall in no way be construed to be a waiver of the provisions or to affect the validity of this Contract or the right of either Party thereafter to enforce each and every provision in accordance with the terms of this Contract.  Invalidation of any provision of this Contract, or a portion thereof, shall not invalidate any other provision or the remainder of the relevant provision and the rest of this Contract shall in all such cases remain in full force.</p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
									<p>إذا تعذر على أي من الطرفين في أي وقت إنفاذ أي شرط من شروط هذا العقد أو مطالبة الطرف الآخر في أي وقت بإنفاذ أي من أحكامه، فإن ذلك لا يجب أن يفسر بأي حال من الأحوال على أنه تنازل عن تلك الأحكام أو على أنه يؤثر على صلاحية هذا العقد أو على حق أي من الطرفين في إنفاذ كل حكم من أحكام العقد وفقا لشروطه وأحكامه. وإذا أصبح أي شرط من شروط هذا العقد أو جزء منه باطلاً، فإن ذلك لا يبطل أي شرط آخر أو الجزء المتبقي من الشرط المعني وبقية أجزاء هذه الاتفاقية. وتظل بقية شروط وأحكام هذا العقد في جميع هذه الحالات نافذة بكامل القوة والأثر. </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left;text-decoration: underline;"> 17. Governing Law / Disputes </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;text-decoration: underline;">١٧ .القانون الحاكم/ المنازعات </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p>This Contract shall be governed by and construed in accordance with the laws and regulations of the Kingdom of Saudi Arabia, including without limitation the Labour Law issued under Royal Decree No. M/51 dated 23/08/1426H (as amended from time to time).  The Parties will make every effort to settle disputes amicably, but if the Parties are unable to reach an amicable settlement, the dispute will be referred to and decided by the relevant local labour committee in Riyadh or other appropriate Saudi Arabian administrative or judicial body in Riyadh.</p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
									<p>يخضع هذا العقد لأنظمة وقوانين المملكة العربية السعودية ويفسر وفقاً لها، بما في ذلك على سبيل المثال لا الحصر نظام العمل الصادر بموجب المرسوم الملكي رقم م/51، بتاريخ 23/8/1426هـ. وتعديلاته وعلى الطرفين أن يبذلا كل جهد ممكن لتسوية أية نزاعات تنشأ بينهما على خلفية هذا العقد بالطرق الودية. وإذا تعذر على الطرفين التوصل إلى تسوية ودية، يحال النزاع إلى اللجنة العمالية المعنية في مدينة الرياض، أو إلى السلطات القضائية السعودية المعنية في مدينة الرياض حيث تعتبر هي جهة الاختصاص والفصل في هذا العقد. </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left;text-decoration: underline;"> 18. Entire Agreement </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;text-decoration: underline;">١٨ .مجمل الاتفاق </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> This Contract constitutes the entire agreement between the Parties with respect to the Employee's employment by the Employer in the Kingdom of Saudi Arabia and supersedes and renders null and void all prior or contemporaneous agreements or understandings, whether oral or written.
										This Contract may only be amended, or supplemented, by the written agreement of the Employee and the Employer.</p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
									<p>يشكل هذا العقد مجمل الاتفاق بين الطرفين فيما يتعلق بتعيين الموظف من قبل صاحب العمل في المملكة العربية السعودية. ويلغي هذا العقد ويحل محل جميع الاتفاقيات أو التفاهمات السابقة أو المتزامنة مع هذا العقد، خطية كانت أم شفهية، ولا يجوز تعديل هذا العقد أو الاضافة إليه إلا بموجب اتفاق خطي بين صاحب العمل والموظف. </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left;text-decoration: underline;"> 19. Notices </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;text-decoration: underline;">١٩ .الاشعارات </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> All notices between the Parties shall be in writing and sent to the addresses indicated in this contract, by registered mail, express mail, or email to both Parties. Each party undertakes to notify the other in writing in case of changing the address or changing the email, otherwise the address and email indicated in this contract will remain the official communication channels.</p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
									<p>تتم جميع الإشعارات بين الطرفين كتابة على العناوين الموضحة في هذا العقد عن طريق البريد المسجل أو البريد الممتاز أو البريد الإلكتروني لكلٍ من الطرفين، ويلتزم كل طرف بإشعار الآخر خطياً في حال تغييره للعنوان الخاص به، أو تغيير البريد الإلكتروني، وإلا اعتبر العنوان أو البريد الإلكتروني المدونان في هذا العقد، هما المعمول بهما نظاماً.</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left;text-decoration: underline;"> 20.Employee's Endorsement of the Validity of the Information : </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;text-decoration: underline;">٢٠ .إقرار الموظف بصحة المعلومات: </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> The employee acknowledges that all the information he\she provides to the employer is correct. If otherwise proven, the employer has the right to take the action he\she deems appropriate.</p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
									<p>يقر الموظف بأن جميع البيانات التي قدمها لصاحب العمل صحيحة، وفي حال ثبوت خلاف ذلك يحق لصاحب العمل اتخاذ الإجراء الذي يراه مناسباً.</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left;text-decoration: underline;"> 21.Counterparts: </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;text-decoration: underline;">٢١   .نسخ العقد </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding-left: 20px;text-align: left;width:50%">
									<p> This Contract has been executed in two (2) originals in Arabic and English out of (21) articles, in the event of a conflict between the same article in both language, the Arabic article shall it considered approved for interpretation of this contract and each party has received a copy thereof.</p>
								</div>
								<div class="col-sm-6" style="padding-right: 20px;text-align: right;width:50%">
									<p>حرر هذا العقد من نسختين أصليتين باللغتين العربية والإنجليزية من واحد وعشرون مادة، وفي حال وجد اختلاف بين النص الواحد في كلا اللغتين يعتبر النص العربي هو المعتمد لتفسير هذا العقد، وقد أستلم كل طرف نسخة منها للعمل بموجبها.</p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left"> The Employer </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;">صاحب العمل </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>On Behalf of Business Research and Development Co. </p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>بالنيابة عن شركة أبحاث وتطوير الأعمال التجارية </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>Name : ............................ </p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>الاسم:............................ </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>Date : ..../../..</p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>التاريخ: ..../../.. </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>Signature: ............................</p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>التوقيع: ............................ </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<strong style="text-align: left"> The Employee </strong>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<strong style="text-align: left;">الموظف </strong>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>Name : {20} </p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>الاسم:{21} </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>Date : ..../../..</p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>التاريخ: ..../../.. </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p>Signature: ............................</p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>التوقيع: ............................ </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p></p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>  الإيميل الشخصي: ............................ </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p></p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p>  رقم الجوال الشخصي: ............................ </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p></p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p> رقم شخص آخر في حال الطوارئ: ............................ </p>
								</div>
							</div>
							<div class="row">
								<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
									<p style="text-align: left"></p>
								</div>
								<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
									<p> العنوان الوطني: ............................ </p>
								</div>
							</div>
				</div> '''.format(self.id, self.date_start, self.id, self.date_start, self.employee_id.name_in_id,
                                  self.employee_id.country_id.name, \
                                  self.employee_id.passport_id, self.employee_id.residence_place_id.name,
                                  self.employee_id.name_in_id, self.employee_id.country_id.name, \
                                  self.employee_id.passport_id, self.employee_id.residence_place_id.name, \
                                  self.job_id.name, self.job_id.name, self.total_salary, self.total_salary,
                                  self.date_start, self.date_end, self.date_start, self.date_end,
                                  self.employee_id.name_in_id, self.employee_id.english_name,
                                  self.employee_id.identification_id)
        if self.contract_type_sel == 'part_time':
            template = '''<div style="with: 100%; clear: both;">
						<div  style='text-align: center;'><strong>Employment contract – Part time</strong></div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%;">
								<p  style="text-align: left;">Date:  {0}  </p>
							</div>
							<div class="col-sm-6" style="padding: 10px ;direction: rtl;text-align: right;width:50%;">
								<p>التاريخ: {1} </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p style="text-align: left;">Dear:  {2} </p>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<p>السيده: {3}</p>
							</div>
						</div>
						<br></br>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p style="text-align: left;">
									T2 is pleased to offer you an employment opportunity, as the following:  </p>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<p>يسر شركة أبحاث وتطوير الأعمال أن تعرض عليك الوظيفة التالية :</p>
							</div>
						</div>
						<br></br>
						<div class="text-center" style="  style='text-align: center;' border: 1px solid #e1dedd;" > Part Time: {4}</div>
						<br></br>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left;text-decoration: underline;"> Terms and Conditions: </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<strong style="text-align: left;text-decoration: underline;">الراتب والمميزات: </strong>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p style="text-align: left;"> 1. <strong>Total Salary: </strong>({5}) TND/month(Gregorian).</p>
							</div>
							<div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: right;width:50%">
								<p> ١. <strong>الراتب الإجمالي</strong> :({6}) دينار تونسي في الشهر (الميلادي). </p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding-left: 30px;text-align: left;width:50%">
								<p style="text-align: left;"> 2. <strong> Working Hours:</strong> 20  hours per week</p>
							</div>
							<div class="col-sm-6" style="padding-right: 30px;direction: rtl;text-align: right;width:50%">
								<p > ٢. <strong>ساعات العمل:</strong>20 ساعة في الأسبوع </p>
							</div>
						</div>
						<br></br>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<strong style="text-align: left"> I hereby accept this offer </strong>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">

							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p> Name: {7}</p>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<p>الاسم: {8}</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p>Expected Date of Joining:</p>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<p>التاريخ المتوقع لمباشرة العمل:</p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6" style="padding: 10px;text-align: left;width:50%">
								<p>Signature and Date: </p>
							</div>
							<div class="col-sm-6" style="padding: 10px;direction: rtl;text-align: right;width:50%">
								<p>التوقيع والتاريخ:</p>
						</div>'''.format(self.date_start, self.date_start, self.employee_id.name_in_id,
                                         self.employee_id.name_in_id,
                                         self.job_id.name, self.total_salary, self.total_salary,
                                         self.employee_id.name_in_id, self.employee_id.english_name)
        self.contract_template = template

    @api.model
    def update_state(self):
        super(HrEmployeeContract, self).update_state()
        for contract in self.search([]):
            date_now = fields.Date.today()
            contract_end_date = contract.date_end
            trial_end_date = contract.trial_date_end
            if contract_end_date:
                diff_days = (contract_end_date - date_now).days
                notify_before = contract.employee_id.office_id.contract_notification_before
                if diff_days <= notify_before and not self.stop_daily_notification:
                    template = self.env.ref('hr_employee_updation.contract_email_notification_template')
                    self.env['mail.template'].browse(template.id).send_mail(contract.id)

            if trial_end_date and not self.stop_daily_notification:
                diff_days = (trial_end_date - date_now).days
                if diff_days in [14, 7]:
                    template = self.env.ref('hr_employee_updation.trial_contract_email_notification_template')
                    self.env['mail.template'].browse(template.id).send_mail(contract.id)

    def salary_change_alert(self, vals):
        for rec in self:
            body = ''
            if 'wage' in vals:
                body = 'Wage: From %s To %s \n' % (rec.wage, vals['wage'])

            if 'transportation_allowance_type' in vals:
                body += 'Transportation Type : From %s To %s \n' % (
                    rec.transportation_allowance_type, vals['transportation_allowance_type'])

            if 'transportation_allowance_value' in vals:
                body += 'Transportation Value : From %s To %s \n' % (
                    rec.transportation_allowance_value, vals['transportation_allowance_value'])

            if 'housing_allowance_type' in vals:
                body += 'Housing Type : From %s To %s \n' % (rec.housing_allowance_type, vals['housing_allowance_type'])

            if 'housing_allowance_value' in vals:
                body += 'Housing Type : From %s To %s \n' % (
                    rec.housing_allowance_value, vals['housing_allowance_value'])

            if 'total_salary' in vals:
                body += 'Total Salary : From %s To %s \n' % (rec.total_salary, vals['total_salary'])

            if 'variable_increase' in vals:
                body += 'Variable Increase : From %s To %s \n' % (rec.variable_increase, vals['variable_increase'])

            if body:
                user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)],
                                                       limit=1, order="id desc")
                note = _(
                    '<p>Dear %s <br><br> We would like to inform you that the contract of the employee %s has been amended as follows:  <br><br> %s <br><br> Best Regards,</p>') % (
                           user_id.name, rec.employee_id.name, body)
                warning = _('Please set HR manager.')
                date = fields.Date.today()
                activity_type = 'mail.mail_activity_data_todo'
                model = 'hr.contract'
                notification_and_email.notification(rec, user_id, date, activity_type, model, note, warning)

    def write(self, vals):
        self.salary_change_alert(vals)
        return super(HrEmployeeContract, self).write(vals)
