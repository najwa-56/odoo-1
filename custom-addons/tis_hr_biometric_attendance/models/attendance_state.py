from odoo import models, fields

class AttendanceState(models.Model):
    _name = 'attendance.state'
    _description = 'Attendance State'

    name = fields.Char(string='State Name', required=True)
    code = fields.Char(string='Code', required=True)
    device_id = fields.Many2one('biometric.config', "Device", ondelete='cascade')
    description = fields.Text(string='Description')
    activity_type = fields.Selection([('check_in', 'Check-In'),
                              ('check_out', 'Check-Out')], string="Activity Type")
