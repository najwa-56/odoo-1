from odoo import models, fields

class RepeatDay(models.Model):
    _name = 'repeat.day'
    _description = 'Repeat Day Option'
    _order = 'sequence'

    name = fields.Char(string='Day', required=True)
    code = fields.Char(string='Code', required=True)  # e.g. 'mon', 'tue'
    sequence = fields.Integer(string='Order', default=10)
