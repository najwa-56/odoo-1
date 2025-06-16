from odoo import models, fields

class RepeatMonthDay(models.Model):
    _name = 'repeat.month.day'
    _description = 'Monthly Repeat Day'
    _rec_name = 'day_number'
    _order = 'day_number'

    day_number = fields.Integer(string="Day of Month", required=True)

    def name_get(self):
        return [(rec.id, str(rec.day_number)) for rec in self]
