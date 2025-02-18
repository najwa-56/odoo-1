# -*- coding: utf-8 -*-
#############################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models,api


class ResConfigSettings(models.TransientModel):
    """Inherited the res_config_settings to add notice_period
    configurations."""
    _inherit = 'res.config.settings'

    notice_period = fields.Boolean(string='Notice Period',
                                   help='Enable to configure a notice period'
                                        ' for an employee.',
                                   config_parameter='hr_employee_updation.notice_period')
    no_of_days = fields.Integer(string='Notice Period Days',
                                help='Set the number of days for the notice'
                                     ' period.',
                                config_parameter='hr_employee_updation.no_of_days')

    contract_expiration_remainder = fields.Integer(string='Contract Expiration Remainder',
                                                   config_parameter='hr_employee_updation.contract_expiration_remainder')



    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #     param_setting = self.env['ir.config_parameter'].sudo()
    #     param_setting.set_param('hr_employee_updation.employee_id_option', self.employee_id_option)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_setting = self.env['ir.config_parameter'].sudo()
        contract_expiration_remainder = param_setting.get_param('hr_employee_updation.contract_expiration_remainder')
        res.update(contract_expiration_remainder=contract_expiration_remainder)
        return res