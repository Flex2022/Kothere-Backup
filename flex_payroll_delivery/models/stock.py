from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    distance_per_km = fields.Float(string='Distance per KM', default=0.0)
    is_apply_distance = fields.Boolean(
        string='Apply Distance Per KM',
        related='company_id.apply_distance',
        readonly=False,
        help="Enable to apply distance Per Km."
    )
    # date_done_without_time = fields.Date(
    #     string='Date Done Without Time',
    #     compute='_compute_date_done_without_time',
    #
    #     help="The date when the picking was done, without the time component."
    # )
    #
    # @api.depends('date_done')
    # def _compute_date_done_without_time(self):
    #     for record in self:
    #         if record.date_done:
    #             # Extract the date part from the datetime
    #             record.date_done_without_time = fields.Date.from_string(record.date_done).strftime('%Y-%m-%d')
    #         else:
    #             record.date_done_without_time = False