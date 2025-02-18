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
from datetime import datetime

from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta


from odoo import models, fields, api

class HrContract(models.Model):
    """This class extends the 'hr.contract' model to add a custom 'notice_days'
     field. The 'notice_days' field is used to store the notice period for HR
     contracts."""
    _inherit = 'hr.contract'

    def _default_notice_days(self):
        """Get the default notice period from the  configuration.
            :return: The default notice period in days.
            :rtype: int """
        return self.env['ir.config_parameter'].get_param(
            'hr_employee_updation.no_of_days') if self.env[
            'ir.config_parameter'].get_param(
            'hr_employee_updation.notice_period') else 0

    notice_days = fields.Integer(string="Notice Period",
                                 default=_default_notice_days,
                                 help="Number of days required for notice"
                                      " before termination.")

    date_start = fields.Date('Start Date',  related='employee_id.start_date',help="Start date of the contract.",store=True)
    date_end = fields.Date('End Date',related='employee_id.end_date',help="End date of the contract (if it's a fixed-term contract).",store=True)
    trial_date_end = fields.Date('End of Trial Period',related='employee_id.trial_date', help="End date of the trial period (if there is one).",store=True)
    state = fields.Selection(selection_add=[('experiment', 'In Experiment'),('open',)])



    @api.depends('employee_id.state')
    def _compute_contract_status(self):
        for rec in self:
            if rec.employee_id.state in ('draft','experiment','service'):
               rec.state = rec.employee_id.state
            else:rec.state = 'end_service'


    def _get_expire_contract(self):
        contract_expiration_remainder =self.env['ir.config_parameter'].sudo().get_param('hr_employee_updation.contract_expiration_remainder')
        today = fields.Date.today()
        body=""
        # date_end = today + relativedelta(days=str(contract_expiration_remainder))
        date_end = today + timedelta(days=int(contract_expiration_remainder))


        contract_ids = self.env['hr.contract'].sudo().search([('state', '=', 'open'),('date_end', '!=', False),('date_end','=',date_end)])

        users = self.env['res.users'].search([])
        employee_name=[]


        for contract in contract_ids:
            # employee_name.append(contract.employee_id.name)
            body = ("The  Contract %s must be expired on %s ")%(contract.name,contract.date_end)
            message = self.env['mail.message'].create({
                'subject': 'contracts expiration',
                'body': body,
                'model': 'hr.contract',
                'message_type': 'notification',
            })
            for user in users:
                if user.has_group('hr_employee_updation.group_hr_reminder'):
                    contract.message_post(body=body,partner_ids=[user.id], notify_by_email=True, message_type='notification', )
                    notif_create_values = [{
                        'mail_message_id': message.id,
                        'res_partner_id': user.partner_id.id,
                        'notification_type': 'inbox',

                    }]
                    if notif_create_values:
                        self.env['mail.notification'].sudo().create(notif_create_values)

            new_end_date = contract.date_end + relativedelta(years=1)
            contract.employee_id.write({'end_date': new_end_date})