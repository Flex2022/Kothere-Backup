# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    probability_order_line_active = fields.Boolean(string='Probability based on Order lines', default=True,
                                                   related="company_id.probability_order_line_active",
                                                   readonly=False,
                                                   help="Compute the probability based on the order lines .")
