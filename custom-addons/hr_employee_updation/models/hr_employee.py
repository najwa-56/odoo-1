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
from odoo import api, fields, models, _
import dateutil.relativedelta
from datetime import datetime, timedelta, date



GENDER_SELECTION = [('male', 'Male'),
                    ('female', 'Female'),
                    ('other', 'Other')]


class HrEmployee(models.Model):
    """Extended model for HR employees with additional features."""
    _inherit = 'hr.employee'

    personal_mobile = fields.Char(string='Mobile', related='private_phone',
                                  help="Personal mobile number of the "
                                       "employee", store=True, )
    joining_date = fields.Date(compute='_compute_joining_date',
                               string='Joining Date', store=True,
                               help="Employee joining date computed from the"
                                    " contract start date")
    id_expiry_date = fields.Date(help='Expiry date of Identification document',
                                 string='Expiry Date',)
    passport_expiry_date = fields.Date(help='Expiry date of Passport ID',
                                       string='Expiry Date')
    identification_attachment_ids = fields.Many2many(
        'ir.attachment', 'id_attachment_rel',
        'id_ref', 'attach_ref', string="Attachment",
        help='Attach the copy of Identification document')
    passport_attachment_ids = fields.Many2many(
        'ir.attachment',
        'passport_attachment_rel',
        'passport_ref', 'attach_ref1', string="Attachment",
        help='Attach the copy of Passport')
    family_info_ids = fields.One2many('hr.employee.family', 'employee_id',
                                      string='Family',
                                      help='Family Information')


    state = fields.Selection(string="Employee State",
                             selection=[('draft','Draft'),('experiment', 'In Experiment'),
                                 ('service', 'In Service'),
                                 ],
                             default='draft', required=False, track_visibility='onchange')

    start_date = fields.Date('Start Date',)
    end_date = fields.Date('End Date')
    trial_period = fields.Selection([('3_m','3 Months'),('6_m','6 Months')],required=True)
    trial_date = fields.Date('Trial End Date')

    service_days = fields.Integer(string='Service Days', compute="compute_service_years")
    service_months = fields.Integer(string='Service Months', compute="compute_service_years")
    service_years = fields.Integer(string='Service Years', compute="compute_service_years")
    date_of_direct_action = fields.Date()
    arabic_name = fields.Char('Arabic Name',required=True)
    emp_code = fields.Char('Employee Code' , readonly=False , required=True)
    attachment_ids = fields.One2many('hr.employee.attachment', 'employee_id', string="Attachments")
   

    def approve(self):
        current_contract = self.contract_id or self.contract_ids
        current_contract.write({'state':'experiment'})
        self.write({'state': 'experiment', 'emp_code': not self.emp_code and self.env['ir.sequence'].next_by_code('employee.code') or self.emp_code})

    def service(self):
        current_contract = self.contract_id or self.contract_ids
        current_contract.write({'state': 'open'})
        self.write({'state':'service'})

    def return_to_work(self):
        current_contract = self.contract_id or self.contract_ids
        current_contract.write({'state': 'open'})
        self.write({'state':'service','end_date':False})

    @api.depends('start_date')
    def compute_service_years(self):
        for request in self:
            if request.start_date:
                start_date=fields.Datetime.from_string(request.start_date)
                end_date=fields.Datetime.from_string(request.end_date and request.end_date or fields.Datetime.now())

                start_y, start_m, start_d, start_h, min, sec, wd, yd, i = start_date.timetuple()
                end_y, end_m, end_d, end_h, min, sec, wd, yd, i = end_date.timetuple()
                request.service_years = end_y - start_y
                request.service_months = (end_m - start_m)
                request.service_days = (end_d - start_d)

                if (end_m - start_m) < 0 and (end_d - start_d) < 0 :
                    request.service_months = abs(12 - (start_m - end_m))
                    request.service_years = request.service_years -1
                    request.service_days = abs(30 - (start_d - end_d) )
                    request.service_months = request.service_months -1
                elif (end_d - start_d) < 0 and (end_m - start_m) >= 0:
                    request.service_days = abs(30 - (start_d - end_d) )
                    request.service_months = request.service_months -1
                    if request.service_months < 0 :
                        request.service_months = abs(12 + (request.service_months))
                        request.service_years = request.service_years -1
                elif (end_m - start_m) < 0 and (end_d - start_d) >= 0 :
                    request.service_months = abs(12 - (start_m - end_m))
                    request.service_years = request.service_years -1
                else :
                    request.service_years = end_y - start_y
                    request.service_months = (end_m - start_m)
                    request.service_days = (end_d - start_d)
            else:
                request.service_years = 0
                request.service_months = 0
                request.service_days = 0

                


    @api.onchange('trial_period','start_date')
    def onchange_trial_end(self):
        if self.start_date and self.trial_period:
            start_date = fields.Datetime.from_string(self.start_date).date()
            months = 3 if self.trial_period == '3_m' else 6
            end_trial_date = start_date + dateutil.relativedelta.relativedelta(months=months)
            self.trial_date = end_trial_date
        else:
            self.trial_date = False


    @api.depends('contract_id')
    def _compute_joining_date(self):
        """Compute the joining date of the employee based on their contract
         information."""
        for employee in self:
            employee.joining_date = min(
                employee.contract_id.mapped('date_start')) \
                if employee.contract_id else False

    @api.onchange('spouse_complete_name', 'spouse_birthdate')
    def _onchange_spouse_complete_name(self):
        """Populates the family_info_ids field with the spouse's information,
         creating a family member record associated with the employee when
         spouse's complete name or birthdate changed."""
        relation = self.env.ref('hr_employee_updation.employee_relationship')
        if self.spouse_complete_name and self.spouse_birthdate:
            self.family_info_ids = [(0, 0, {
                'member_name': self.spouse_complete_name,
                'relation_id': relation.id,
                'birth_date': self.spouse_birthdate,
            })]

    def expiry_mail_reminder(self):
        """Sending  ID and Passport expiry notification."""
        current_date = fields.Date.context_today(self) + timedelta(days=1)
        employee_ids = self.search(['|', ('id_expiry_date', '!=', False),
                                    ('passport_expiry_date', '!=', False)])
        for employee in employee_ids:
            if employee.id_expiry_date:
                exp_date = fields.Date.from_string(
                    employee.id_expiry_date) - timedelta(days=14)
                if current_date >= exp_date:
                    mail_content = ("Hello  " + employee.name + ",<br>Your ID "
                                    + employee.identification_id +
                                    " is going to expire on " +
                                    str(employee.id_expiry_date)
                                    + ". Please renew it before expiry date")
                    main_content = {
                        'subject': _('ID-%s Expired On %s') % (
                            employee.identification_id,
                            employee.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': employee.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
            if employee.passport_expiry_date:
                exp_date = fields.Date.from_string(
                    employee.passport_expiry_date) - timedelta(days=180)
                if current_date >= exp_date:
                    mail_content = ("  Hello  " + employee.name +
                                    ",<br>Your Passport " + employee.passport_id
                                    +" is going to expire on " +
                                    str(employee.passport_expiry_date) +
                                    ". Please renew it before expire")
                    main_content = {
                        'subject': _('Passport-%s Expired On %s') % (
                            employee.passport_id,
                            employee.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': employee.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()


class HrEmployeeFamily(models.Model):
    """Table for keep employee family information"""
    _name = 'hr.employee.family'
    _description = 'HR Employee Family Info'
    _rec_name = 'member_name'

    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  help='Select corresponding Employee',
                                  invisible=1)
    relation_id = fields.Many2one('hr.employee.relation', string="Relation",
                                  help="Relationship with the employee")
    member_name = fields.Char(string='Name', help='Name of the family member')
    member_contact = fields.Char(string='Contact No',
                                 help='Contact No of the family member')
    birth_date = fields.Date(string="DOB", tracking=True,
                             help='Birth date of the family member')






class EmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    joining_date = fields.Date(related='employee_id.joining_date', string="Join Date", readonly=False)
    id_expiry_date = fields.Date(related='employee_id.id_expiry_date', readonly=False)
    passport_expiry_date = fields.Date(related='employee_id.passport_expiry_date', readonly=False)
    state = fields.Selection(related='employee_id.state', readonly=False)
    start_date = fields.Date(related='employee_id.start_date', readonly=False)
    end_date = fields.Date(related='employee_id.end_date', readonly=False)
    trial_period = fields.Selection(related='employee_id.trial_period', readonly=False)
    trial_date = fields.Date(related='employee_id.trial_date', readonly=False)
    date_of_direct_action = fields.Date(related='employee_id.date_of_direct_action', readonly=False)
    arabic_name = fields.Char(related='employee_id.arabic_name', readonly=False)
    emp_code = fields.Char(related='employee_id.arabic_name', readonly=False)


class User(models.Model):
    _inherit = ['res.users']
    joining_date = fields.Date(related='employee_id.joining_date', string="Join Date", readonly=False, related_sudo=False)
    id_expiry_date = fields.Date(related='employee_id.id_expiry_date', readonly=False, related_sudo=False)
    passport_expiry_date = fields.Date(related='employee_id.passport_expiry_date', readonly=False, related_sudo=False)
    state = fields.Selection(related='employee_id.state', readonly=False, related_sudo=False)
    start_date = fields.Date(related='employee_id.start_date', readonly=False, related_sudo=False)
    end_date = fields.Date(related='employee_id.end_date', readonly=False, related_sudo=False)
    trial_period = fields.Selection(related='employee_id.trial_period', readonly=False, related_sudo=False)
    trial_date = fields.Date(related='employee_id.trial_date', readonly=False, related_sudo=False)
    date_of_direct_action = fields.Date(related='employee_id.date_of_direct_action', readonly=False, related_sudo=False)
    arabic_name = fields.Char(related='employee_id.arabic_name', readonly=False, related_sudo=False)
    emp_code = fields.Char(related='employee_id.arabic_name', readonly=False, related_sudo=False)

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + [
            'joining_date', 'id_expiry_date', 'passport_expiry_date', 'state',
            'start_date', 'end_date', 'trial_period', 'trial_date', 'date_of_direct_action',
            'arabic_name', 'emp_code'
        ]




   

class HrEmployeeAttachment(models.Model):
    _name = 'hr.employee.attachment'
    _description = 'Employee Attachment'

    name = fields.Char(string="Attachment Name", required=True)
    file = fields.Binary(string="File", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", ondelete="cascade")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    notify_before_days = fields.Integer(string="Notify Before (days)")
    notified = fields.Boolean(string="Already Notified", default=False)

     



    @api.model
    def notify_expiring_attachments(self):
        today = date.today()
        records = self.search([
            ('end_date', '!=', False),
            ('notify_before_days', '!=', False),
            ('notified', '=', False)
        ])

        for record in records:
            notify_date = record.end_date - timedelta(days=record.notify_before_days)
            if today >= notify_date:
                hr_group = self.env.ref('hr.group_hr_manager')
                recipients = hr_group.sudo().users.mapped('partner_id.email')

                if recipients:
                    mail_values = {
                        'subject': f"Attachment Expiry Notification: {record.name}",
                        'body_html': f"""
                            <p><strong>Employee:</strong> {record.employee_id.name}</p>
                            <p><strong>Attachment:</strong> {record.name}</p>
                            <p><strong>Expires on:</strong> {record.end_date}</p>
                        """,
                        'email_to': ','.join(recipients),
                    }
                    self.env['mail.mail'].sudo().create(mail_values).send()
                    record.notified = True

