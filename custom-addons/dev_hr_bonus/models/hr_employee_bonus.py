# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Devintelle Software Solutions (<http://devintellecs.com>).
#
##############################################################################
from odoo import api, fields, models, _
from datetime import date


class HrBonus(models.Model):
    _name = 'hr.bonus'
    _description = 'HR Bonus'

    @api.onchange('target', 'country_ids', 'state_ids', 'company_ids',
                  'department_ids', 'job_ids')
    def onchange_target(self):
        bonus_employees = []
        if self.target:
            self.employee_ids = False
            domain = []
            if self.target == 'country':
                domain = [('address_id.country_id', 'in', self.country_ids.ids)]
            elif self.target == 'state':
                domain = [('address_id.state_id', 'in', self.state_ids.ids)]
            elif self.target == 'company':
                domain = [('company_id', 'in', self.company_ids.ids)]
            elif self.target == 'department':
                domain = [('department_id', 'in', self.department_ids.ids)]
            elif self.target == 'job':
                domain = [('job_id', 'in', self.job_ids.ids)]
            
            employee_ids = self.env['hr.employee'].search(domain)
            for emp in employee_ids:
                bonus_employees.append((0, 0, {'employee_id': emp.id, 'email': emp.work_email}))
            self.employee_ids = bonus_employees

    name = fields.Char(string='Bonus Summary', required=True)
    date = fields.Date('Declaration Date', required=True)
    applied_date = fields.Date('Applied Date')
    description = fields.Text('Bonus Description')
    amount = fields.Float(string="Bonus Amount", digits=(5, 2))
    percentage_amt = fields.Float(string="Salary Percentage", digits=(3, 2))
    bonus_target = fields.Selection(
        [('amount', 'Amount'), ('per', 'Percentage')], string="Bonus By")
    state = fields.Selection([
        ('tentative', 'Draft'),
        ('cancelled', 'Cancelled'),
        ('confirmed', 'Confirmed'),
        ('mail_sent', 'Mails Sent'),
        ('done', 'Done'),
    ], 'Status', default='tentative')
    employee_ids = fields.One2many('hr.bonus.employee', 'bonus_id', string='Employees')
    target = fields.Selection(
        [('country', 'Country Wise'), ('state', 'State Wise'),
         ('company', 'Company Wise'),
         ('department', 'Department Wise'), ('job', 'Job Profile Wise')],
        string="Target Group")
    country_ids = fields.Many2many('res.country', 'country_bonus_rel', 'bonus_id', 'country_id', string="Countries")
    state_ids = fields.Many2many('res.country.state', 'state_bonus_rel', 'bonus_id', 'state_id', string="States")
    company_ids = fields.Many2many('res.company', 'company_bonus_rel', 'bonus_id', 'company_id', string="Companies")
    department_ids = fields.Many2many('hr.department', 'department_bonus_rel', 'bonus_id', 'department_id', string="Departments")
    job_ids = fields.Many2many('hr.job', 'job_bonus_rel', 'bonus_id', 'job_id', string="JOB Profiles")

    def mail_send(self):
        for bonus in self:
            for emp in bonus.employee_ids:
                if not emp.email or emp.mail_sent:
                    continue
                emp.action_bonus_mail_sent()
                emp.mail_sent = True
            if not bonus.applied_date:
                bonus.applied_date = date.today()
        self.state = 'mail_sent'

    def do_confirm(self):
        self.state = 'confirmed'

    def do_tentative(self):
        self.state = 'tentative'

    def do_done(self):
        self.state = 'done'

    def do_cancel(self):
        self.state = 'cancelled'

    def set_to_draft(self):
        self.state = 'tentative'


class HrBonusEmployee(models.Model):
    _name = "hr.bonus.employee"
    _description = 'HR Bonus Employee'

    bonus_id = fields.Many2one('hr.bonus', 'Bonus')
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    mail_sent = fields.Boolean('Mail Sent', default=False)
    email = fields.Char('Email', size=124, help="Email of Invited Person")
    company_id = fields.Many2one(related='employee_id.company_id')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.email = self.employee_id.work_email or self.employee_id.user_id.email or ''

    def action_bonus_mail_sent(self):
        '''
        This function opens a window to compose an email, with the edi holiday template message loaded by default
        '''
        template_id = self.env.ref('dev_hr_bonus.email_template_edi_employee_bonus').id
        if template_id:
            template = self.env['mail.template'].browse(template_id)
            template.send_mail(self.id, force_send=True)
        self.mail_sent = True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
