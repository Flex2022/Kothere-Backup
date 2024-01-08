# -*- coding: utf-8 -*-

from odoo import fields, models, _


class PayrollAdjustRequest(models.TransientModel):
    _name = 'payroll.adjust.request'
    _description = 'Payroll Adjust Request'

    note = fields.Text('Adjust Request')

    def payroll_adjust_request(self):
        record_id = self.env['hr.payslip.run'].browse(self._context.get('active_ids'))
        record_id.adjust_request = record_id.adjust_request + ' / ' + self.note if record_id.adjust_request else self.note
        user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('account.group_account_manager').id)], limit=1, order="id desc")

        note = '<p>Dear %s, </p>'\
               '<p>Please check adjust not for payroll # %s.' % (user_id.name, record_id.name)
        warning = _('Please set manager for employee or check manger user.')
        record_id.send_notification(user_id, note, warning)
        record_id.state = 'accounting'


class AdjustVariableIncrease(models.TransientModel):
    _name = 'adjust.variable.increase'
    _description = 'Payroll Adjust Variable Increase'

    note = fields.Text('Adjust Request')

    def variable_adjust_request(self):
        record_id = self.env['hr.variable.increase'].browse(self._context.get('active_ids'))
        record_id.adjust_request = record_id.adjust_request + ' / ' + self.note if record_id.adjust_request else self.note
        user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('account.group_account_manager').id)], limit=1, order="id desc")

        note = '<p>Dear %s, </p>'\
               '<p>Please check adjust not for variable increase ( %s ).' % (user_id.name, record_id.name)
        warning = _('Please set manager for employee or check manger user.')
        record_id.send_notification(user_id, note, warning)
        record_id.state = 'accounting'
