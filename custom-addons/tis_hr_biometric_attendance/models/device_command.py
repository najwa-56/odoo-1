from odoo import models, fields

class DeviceCommand(models.Model):
    _name = 'device.command'
    _description = 'Device Command'

    name = fields.Char(string='Command Name', required=True)
    device_id = fields.Many2one('biometric.config', string='Device', required=True,
                                ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', "Employee")
    status = fields.Selection([
        ('pending', 'Pending'),
        ('executed', 'Executed'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Status', default='pending')
    pin = fields.Char('PIN')
    execution_log = fields.Text(string='Execution Log')

