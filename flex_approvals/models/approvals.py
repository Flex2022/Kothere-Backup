from odoo import api, fields, models, _

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')]


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    has_appointment_type = fields.Selection(CATEGORY_SELECTION, string="Has type of appointment", default="no",
                                            required=True)
    create_job_position = fields.Boolean(string='Create Job Position')


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'
    has_appointment_type = fields.Selection(related="category_id.has_appointment_type")

    appointment_type = fields.Selection([
        ('external', 'External'),
        ('internal', 'Internal'), ], string="Appointment Type", )
    create_job_position = fields.Boolean(related="category_id.create_job_position")
    hr_job_ids = fields.One2many('hr.job', 'approval_job_id')
    hr_job_position_count = fields.Integer(compute="compute_hr_job_position_count")
    job_position = fields.Char('Job position title')

    def action_approve(self, approver=None):
        res = super(ApprovalRequest, self).action_approve(approver)
        for approval in self:
            self.env['hr.job'].sudo().create({
                'name': approval.job_position,
                'description': approval.reason,
                'no_of_recruitment': approval.quantity,
                'approval_job_id': approval.id,
            })
        return res

    def compute_hr_job_position_count(self):
        for approval in self:
            approval.hr_job_position_count = 0
            if approval.hr_job_ids:
                approval.hr_job_position_count = len(approval.hr_job_ids)

    def create_new_job_position(self):
        self.ensure_one()
        return {
            'name': _('Create Job Position'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.job',
            'view_mode': 'form',
            'view_id': self.env.ref('hr.view_hr_job_form').id,
            'target': 'new',
            'context': dict(self._context, **{
                'default_name': '',
                'default_description': self.reason,
                'default_approval_job_id': self.id,
            })
        }

    def action_view_hr_jobs(self):
        """
        This function opens a list view of HR job positions related to the current approval request.
        """
        action = self.env.ref('hr.action_hr_job')
        result = action.read()[0]

        hr_job_ids = self.mapped('hr_job_ids')
        if len(hr_job_ids) > 1:
            result['domain'] = [('id', 'in', hr_job_ids.ids)]
        elif hr_job_ids:
            form_view = [(self.env.ref('hr.view_hr_job_form').id, 'form')]
            result['domain'] = [('id', 'in', hr_job_ids.ids)]
            result['views'] = form_view
            result['res_id'] = hr_job_ids.id
        return result
