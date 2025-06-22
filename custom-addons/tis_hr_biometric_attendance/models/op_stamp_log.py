from odoo import models, fields
from datetime import datetime

class OpStampLog(models.Model):
    _name = 'op.stamp.log'
    _description = 'Operation Stamp Log'

    name = fields.Char(string='Log Name')
    log_date = fields.Datetime(string='Log Date',
                               default=lambda self: datetime.now())
    log_text = fields.Text("Log Text")
    device_id = fields.Many2one('biometric.config', string='Biometric Attendance Device', required=True,
                                ondelete='cascade')
    opStamp = fields.Integer("OpStamp")
