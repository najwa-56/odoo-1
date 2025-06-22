from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class FingerTemplate(models.Model):
    """Model to store fingerprint templates for employees."""
    _name = 'finger.template'
    _description = 'Finger Template'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  related='device_user_id.employee_id',
                                  store=True)
    device_id = fields.Many2one('biometric.config',
                                string='Device', ondelete='cascade')
    device_user_id = fields.Many2one('biometric.attendance.devices',
                                     string='Device User Id')
    template_data = fields.Binary(string='Template Data', required=True)

