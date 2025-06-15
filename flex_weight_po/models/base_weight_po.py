from odoo import api, fields, models


class BaseWeightPO(models.Model):
    _name = "base.weight.po"
    _description = "Base Weight Purchase Order"

    weight = fields.Float(string="Weight",
                          required=True,
                          help="Weight of the product in kg"
                          )

    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Indicates whether the record is active or not.",
    )



    def create(self, vals):
        """
        Override create method to ensure weight is positive.
        """
        print(vals)
        return super(BaseWeightPO, self).create(vals)
