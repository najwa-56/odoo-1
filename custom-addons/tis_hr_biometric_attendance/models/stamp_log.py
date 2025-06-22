from odoo import models, fields
from datetime import datetime

class StampLog(models.Model):
    _name = 'stamp.log'
    _description = 'Stamp Log'

    name = fields.Char(string='Stamp Name')
    log_date = fields.Datetime(string='Log Date',
                               default=lambda self: datetime.now())
    log_text = fields.Text("Log Text")
    device_id = fields.Many2one('biometric.config', string='Biometric Attendance Device', required=True,
                                ondelete='cascade')
    stamp = fields.Integer("Stamp")

