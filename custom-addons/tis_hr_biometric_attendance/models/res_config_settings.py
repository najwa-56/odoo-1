# -*- encoding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    minimal_attendance = fields.Boolean(string='Minimal Attendance',
                                        config_parameter='tis_hr_biometric_attendance.minimal_attendance')


