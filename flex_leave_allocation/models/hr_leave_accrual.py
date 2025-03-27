from odoo import api, fields, models
from dateutil.relativedelta import relativedelta



class AccrualPlanLevel(models.Model):
    _inherit = "hr.leave.accrual.level"


    def _get_level_transition_date(self, allocation_start):
        if self.start_type == 'day':
            return allocation_start + relativedelta(days=self.start_count)
        if self.start_type == 'month':
            return allocation_start + relativedelta(months=self.start_count)
        if self.start_type == 'year':
            return allocation_start + relativedelta(years=self.start_count)