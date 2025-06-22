from odoo import api, fields, models

class AttendanceDataLogDevice(models.Model):
    _name = 'attendance.data.log.device'

    device_id = fields.Many2one('biometric.config',
                                "Device", ondelete='cascade')
    log_code = fields.Char('Log Code')
    description = fields.Selection([('-1', 'N/A'),
        ('0', 'Power On'),
        ('1', 'Power Off'),
        ('2', 'Authentication Failure'),
        ('3', 'Alarm'),
        ('4', 'Enter Menu'),
        ('5', 'Change Settings'),
        ('6', 'Enroll Fingerprint'),
        ('7', 'Enroll Password'),
        ('8', 'Enroll HID Card'),
        ('9', 'Delete User'),
        ('10', 'Delete Fingerprint'),
        ('11', 'Delete Password'),
        ('12', 'Delete RF Card'),
        ('13', 'Clear Data'),
        ('14', 'Create MF Card'),
        ('15', 'Enroll MF Card'),
        ('16', 'Register MF Card'),
        ('17', 'Delete MF Card Registration'),
        ('18', 'Clear MF Card Content'),
        ('19', 'Move Enrollment Data to Card'),
        ('20', 'Copy Data from Card to Machine'),
        ('21', 'Set Time'),
        ('22', 'Factory Reset'),
        ('23', 'Delete Entry/Exit Records'),
        ('24', 'Clear Administrator Permissions'),
        ('25', 'Modify Access Group Settings'),
        ('26', 'Modify User Access Settings'),
        ('27', 'Modify Access Time Zones'),
        ('28', 'Modify Unlocking Combination Settings'),
        ('29', 'Unlock'),
        ('30', 'Enroll New User'),
        ('31', 'Change Fingerprint Properties'),
        ('32', 'Forced Alarm'),
        ('33', 'Doorbell Call'),
        ('34', 'Anti-submarine'),
        ('35', 'Delete Attendance Photo'),
        ('36', 'Modify User Other Information'),
        ('37', 'Holiday'),
        ('38', 'Restore Data')], 'Description Log Code')
    operator = fields.Char('Operator')
    op_time = fields.Datetime('Created On')
    value_1 = fields.Char('Value 1')
    value_2 = fields.Char('Value 2')
    value_3 = fields.Char('Value 3')
    reserved = fields.Char('Reserved')
    opStamp = fields.Integer('OpStamp')
