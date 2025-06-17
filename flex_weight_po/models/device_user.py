from odoo import api, fields, models


class FlexDeviceUser(models.Model):
    _name = 'flex.device.user'
    _description = 'Flex Device User'
    _rec_name = 'user_id'

    user_id = fields.Many2one('res.users', string='User', required=True)
    device_id = fields.Char(string='Device ID')