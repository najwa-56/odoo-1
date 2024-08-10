from odoo import fields, models


class Users(models.Model):
    _inherit = 'res.users'

    pos_security_pin = fields.Char(string="Manager Validation PIN", size=32)
