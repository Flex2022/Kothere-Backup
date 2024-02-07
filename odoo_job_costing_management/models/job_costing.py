# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pandas as pd
import base64
import io


class JobCosting(models.Model):
    _name = 'job.costing'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Job Costing"
    _rec_name = 'number'

    @api.model
    def create(self, vals):
        number = self.env['ir.sequence'].next_by_code('job.costing')
        vals.update({
            'number': number,
        })
        return super(JobCosting, self).create(vals)

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise UserError(_('You can not delete Job Cost Sheet which is not draft or cancelled.'))
        return super(JobCosting, self).unlink()

    @api.depends(
        'job_cost_line_ids',
        'job_cost_line_ids.product_qty',
        'job_cost_line_ids.cost_price',
    )
    def _compute_material_total(self):
        for rec in self:
            rec.material_total = sum([(p.product_qty * p.cost_price) for p in rec.job_cost_line_ids])

    @api.depends(
        'job_labour_line_ids',
        'job_labour_line_ids.hours',
        'job_labour_line_ids.cost_price'
    )
    def _compute_labor_total(self):
        for rec in self:
            rec.labor_total = sum([(p.hours * p.cost_price) for p in rec.job_labour_line_ids])

    @api.depends(
        'job_overhead_line_ids',
        'job_overhead_line_ids.product_qty',
        'job_overhead_line_ids.cost_price'
    )
    def _compute_overhead_total(self):
        for rec in self:
            rec.overhead_total = sum([(p.product_qty * p.cost_price) for p in rec.job_overhead_line_ids])

    @api.depends(
        'material_total',
        'labor_total',
        'overhead_total'
    )
    def _compute_jobcost_total(self):
        for rec in self:
            rec.jobcost_total = rec.material_total + rec.labor_total + rec.overhead_total

    def _purchase_order_line_count(self):
        purchase_order_lines_obj = self.env['purchase.order.line']
        for order_line in self:
            order_line.purchase_order_line_count = purchase_order_lines_obj.search_count(
                [('job_cost_id', '=', order_line.id)])

    def _job_costsheet_line_count(self):
        job_costsheet_lines_obj = self.env['job.cost.line']
        for jobcost_sheet_line in self:
            jobcost_sheet_line.job_costsheet_line_count = job_costsheet_lines_obj.search_count(
                [('direct_id', '=', jobcost_sheet_line.id)])

    def _timesheet_line_count(self):
        hr_timesheet_obj = self.env['account.analytic.line']
        for timesheet_line in self:
            timesheet_line.timesheet_line_count = hr_timesheet_obj.search_count(
                [('job_cost_id', '=', timesheet_line.id)])

    def _account_invoice_line_count(self):
        #        account_invoice_lines_obj = self.env['account.invoice.line']
        account_invoice_lines_obj = self.env['account.move.line']
        for invoice_line in self:
            invoice_line.account_invoice_line_count = account_invoice_lines_obj.search_count(
                [('job_cost_id', '=', invoice_line.id)])

    @api.onchange('project_id')
    def _onchange_project_id(self):
        for rec in self:
            rec.analytic_id = rec.project_id.analytic_account_id.id

    number = fields.Char(
        readonly=True,
        default='New',
        copy=False,
    )
    name = fields.Char(
        required=True,
        copy=True,
        default='New',
        string='Name',
    )
    notes_job = fields.Text(
        required=False,
        copy=True,
        string='Job Cost Details'
    )
    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        string='Created By',
        readonly=True
    )
    description = fields.Char(
        string='Description',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.user.company_id.currency_id,
        readonly=True
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        string='Company',
        readonly=True
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
    )
    analytic_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
    )
    contract_date = fields.Date(
        string='Contract Date',
    )
    start_date = fields.Date(
        string='Create Date',
        readonly=True,
        default=fields.Date.today(),
    )
    complete_date = fields.Date(
        string='Closed Date',
        readonly=True,
    )
    material_total = fields.Float(
        string='Total Material Cost',
        compute='_compute_material_total',
        store=True,
    )
    labor_total = fields.Float(
        string='Total Labour Cost',
        compute='_compute_labor_total',
        store=True,
    )
    overhead_total = fields.Float(
        string='Total Overhead Cost',
        compute='_compute_overhead_total',
        store=True,
    )
    jobcost_total = fields.Float(
        string='Total Cost',
        compute='_compute_jobcost_total',
        store=True,
    )
    job_cost_line_ids = fields.One2many(
        'job.cost.line',
        'direct_id',
        string='Direct Materials',
        copy=False,
        domain=[('job_type', '=', 'material')],
    )
    job_labour_line_ids = fields.One2many(
        'job.cost.line',
        'direct_id',
        string='Direct Labours',
        copy=False,
        domain=[('job_type', '=', 'labour')],
    )
    job_overhead_line_ids = fields.One2many(
        'job.cost.line',
        'direct_id',
        string='Direct Overheads',
        copy=False,
        domain=[('job_type', '=', 'overhead')],
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        #        domain=[('customer','=', True)],
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('approve', 'Approved'),
            ('done', 'Done'),
            ('cancel', 'Canceled'),
        ],
        string='State',
        tracking=True,
        default='draft',
    )
    task_id = fields.Many2one(
        'project.task',
        string='Job Order',
    )
    so_number = fields.Char(
        string='Sale Reference'
    )

    purchase_order_line_count = fields.Integer(
        compute='_purchase_order_line_count'
    )

    job_costsheet_line_count = fields.Integer(
        compute='_job_costsheet_line_count'
    )

    purchase_order_line_ids = fields.One2many(
        "purchase.order.line",
        'job_cost_id',
    )

    timesheet_line_count = fields.Integer(
        compute='_timesheet_line_count'
    )

    timesheet_line_ids = fields.One2many(
        'account.analytic.line',
        'job_cost_id',
    )

    account_invoice_line_count = fields.Integer(
        compute='_account_invoice_line_count'
    )

    account_invoice_line_ids = fields.One2many(
        #        "account.invoice.line",
        'account.move.line',
        'job_cost_id',
    )

    # Add a file field to the wizard
    data_file = fields.Binary(string="Excel File", required=False)
    file_name = fields.Char(string="File Name")

    @api.onchange('data_file')
    def import_lines(self):
        if not self.data_file:
            return

        excel_data = self._read_excel_data()
        if not self._check_if_the_excel_is_depended_on_my_template(excel_data):
            raise UserError('Please use the right template')

        job_cost_line_ids = []
        job_labour_line_ids = []
        job_overhead_line_ids = []
        for _, row_data in excel_data.iterrows():
            job_cost_line_id = self._process_excel_row(row_data)
            if job_cost_line_id:
                if job_cost_line_id.job_type == 'material':
                    job_cost_line_ids.append(job_cost_line_id.id)
                elif job_cost_line_id.job_type == 'labour':
                    job_labour_line_ids.append(job_cost_line_id.id)
                elif job_cost_line_id.job_type == 'overhead':
                    job_overhead_line_ids.append(job_cost_line_id.id)
        # Update lines
        self.job_cost_line_ids = [(6, 0, job_cost_line_ids)]
        self.job_labour_line_ids = [(6, 0, job_labour_line_ids)]
        self.job_overhead_line_ids = [(6, 0, job_overhead_line_ids)]

        # Remove the file
        self.data_file = False

    def _read_excel_data(self):
        file = io.BytesIO(base64.b64decode(self.data_file))
        return pd.read_excel(file, engine='openpyxl')

    def _process_excel_row(self, row):
        job_type_str = str(row['Type']).lower()
        if job_type_str not in ['material', 'labour', 'overhead']:
            return

        job_type_id = self.env['job.type'].search([('name', '=', row['Job Type'])], limit=1)
        if not job_type_id:
            return

        job_cost_line_id = self._create_other_lines(row, job_type_id)
        return job_cost_line_id

    def _create_other_lines(self, row, job_type_id):
        product_name = row['Product']
        product_id = self.env['product.product'].search([('name', '=', product_name)], limit=1) or self.env[
            'product.product'].create({
            'name': product_name,
            'type': 'product',
        })

        try:
            product_qty = int(row['Qty'])
        except ValueError:
            product_qty = 1

        try:
            cost_price = float(row['Cost'])
        except ValueError:
            cost_price = product_id.standard_price

        job_cost_line_id = self.env['job.cost.line'].create({
            'job_type': str(row['Type']).lower(),
            'job_type_id': job_type_id.id,
            'product_id': product_id.id,
            'description': row['Description'],
            'product_qty': product_qty,
            'reference': row['Reference'],
            'date': row['Date'],
            'cost_price': cost_price,
            'basis': row['Basis'],
            'hours': float(row['Hours']) if row['Hours'] else 0.0,
        })
        return job_cost_line_id

    def _check_if_the_excel_is_depended_on_my_template(self, df):
        return df.columns.tolist() == ['Type', 'Job Type', 'Product', 'Description', 'Qty', 'Reference', 'Cost', 'Date',
                                       'Basis', 'Hours']

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def action_approve(self):
        for rec in self:
            rec.state = 'approve'

    def action_done(self):
        for rec in self:
            rec.state = 'done'
            rec.complete_date = fields.date.today()

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_view_purchase_order_line(self):
        self.ensure_one()
        purchase_order_lines_obj = self.env['purchase.order.line']
        cost_ids = purchase_order_lines_obj.search([('job_cost_id', '=', self.id)]).ids
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order Line',
            'res_model': 'purchase.order.line',
            'res_id': self.id,
            'domain': "[('id','in',[" + ','.join(map(str, cost_ids)) + "])]",
            'view_type': 'form',
            'view_mode': 'tree,form',
            # 'target' : self.id,
        }
        return action

    def action_view_hr_timesheet_line(self):
        self.ensure_one()
        hr_timesheet = self.env['account.analytic.line']
        cost_ids = hr_timesheet.search([('job_cost_id', '=', self.id)]).ids
        action = self.env["ir.actions.actions"]._for_xml_id("hr_timesheet.act_hr_timesheet_line")
        action['domain'] = [('id', 'in', cost_ids)]
        return action

    def action_view_jobcost_sheet_lines(self):
        self.ensure_one()
        jobcost_line = self.env['job.cost.line']
        cost_ids = jobcost_line.search([('direct_id', '=', self.id)]).ids
        action = self.env["ir.actions.actions"]._for_xml_id("odoo_job_costing_management.action_job_cost_line_custom")
        action['domain'] = [('id', 'in', cost_ids)]
        ctx = 'context' in action and action['context'] and eval(action['context']).copy() or {}
        ctx.update(create=False)
        ctx.update(edit=False)
        ctx.update(delete=False)
        action['context'] = ctx
        return action

    def action_view_vendor_bill_line(self):
        self.ensure_one()
        account_invoice_lines_obj = self.env['account.move.line']
        cost_ids = account_invoice_lines_obj.search([('job_cost_id', '=', self.id)]).ids
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Account Invoice Line',
            'res_model': 'account.move.line',
            'res_id': self.id,
            'domain': "[('id','in',[" + ','.join(map(str, cost_ids)) + "])]",
            'view_type': 'form',
            'view_mode': 'tree,form',
        }
        action['context'] = {
            'create': False,
            'edit': False,
        }
        return action
