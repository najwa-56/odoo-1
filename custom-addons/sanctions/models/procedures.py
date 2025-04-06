# -*- coding: utf-8 -*-
from calendar import calendar
from datetime import datetime
from odoo import models, api, fields, _
from odoo.exceptions import UserError,ValidationError
import calendar
import logging
_logger = logging.getLogger(__name__)

class Employee(models.Model):
    _inherit = 'hr.employee'
    
    sanction = fields.One2many('sanctions.procedures','employee')

class Procedures(models.Model):
    _name = 'sanctions.procedures'
    _description = 'sanctions.procedures'

    dateof = fields.Date(string='تاريخ الخصم',required=True)
    employee = fields.Many2one('hr.employee',string='إسم الموظف',required=True)
    job = fields.Char(string='المنصب الوظيفي',readonly=True)
    admin = fields.Char(string='الإدارة',readonly=True)
    sanction = fields.Many2one('sanctions.sanctions',string='العقوبة / المخالفة',required=True)
    stime = fields.Char(string='تكرار العقوبة',readonly=True)
    stype = fields.Selection([('non', 'لايوجد'), ('hours', 'ساعات'), ('percent', 'نسبة من اليوم'), ('days', 'أيام'), ('fixed', 'قيمة')],string='نوع الخصم',readonly=True)
    samount = fields.Char(string='قيمة الخصم',readonly=True)
    date = fields.Date(string='التاريخ',readonly=True,default=datetime.today())
    desc = fields.Text(string='الوصف')
    expt = fields.Boolean(string='إستثناء موظف')
    editable = fields.Boolean(string='تعديل العقوبة')
    state = fields.Selection([
        ('draft', 'جديد'),
        ('manager_approve', 'المدير المباشر'),
        ('hr_approve', 'الموارد البشرية'),
        ('cancelled', 'ملغي'),
        ('confirm', 'مؤكد'),
    ], string='الحالة',  copy=False,
       tracking=True, help='Status of the sanctions', default='draft')
    work_location_id = fields.Many2one(related='employee.work_location_id', string='Work Location',store=True)
    @api.onchange('employee')
    def _onchange_employee(self):
        if self.employee:
            self.job = self.employee.job_id.name or ''
            self.admin = self.employee.department_id.name or ''
            self.sanction = None
            self.stime = None
            self.stype = None
            self.samount = None
            # self.stype = self.sanction.rols.search([('times','=','first')]).type
            # self.samount = self.env['sanctions.procedures'].search_count([('employee','=',self.employee.id)])

    @api.onchange('sanction')
    def _onchange_sanction(self):
        if self.sanction:
            sanction_employee = self.env['sanctions.procedures'].search_count([('employee','=',self.employee.id),('sanction','=',self.sanction.id)])
            if self.sanction.type == 'continuous':
                if sanction_employee == 0 and self.sanction.rols.filtered(lambda r: r.times == 'first'):
                    self.stime = "أول مرة"
                    self.stype = self.sanction.rols.filtered(lambda r: r.times == 'first').type
                    self.samount = self.sanction.rols.filtered(lambda r: r.times == 'first').amount
                elif sanction_employee == 1 and self.sanction.rols.filtered(lambda r: r.times == 'second'):
                    self.stime = "ثاني مرة"
                    self.stype = self.sanction.rols.filtered(lambda r: r.times == 'second').type
                    self.samount = self.sanction.rols.filtered(lambda r: r.times == 'second').amount
                elif sanction_employee == 2 and self.sanction.rols.filtered(lambda r: r.times == 'third'):
                    self.stime = "ثالث مرة"
                    self.stype = self.sanction.rols.filtered(lambda r: r.times == 'third').type
                    self.samount = self.sanction.rols.filtered(lambda r: r.times == 'third').amount
                elif sanction_employee == 3 and self.sanction.rols.filtered(lambda r: r.times == 'fourth'):
                    self.stime = "رابع مرة"
                    self.stype = self.sanction.rols.filtered(lambda r: r.times == 'fourth').type
                    self.samount = self.sanction.rols.filtered(lambda r: r.times == 'fourth').amount
                else:
                    self.stime = "أكثر من "+str(sanction_employee)+" مرات"
                    self.stype = self.sanction.rols.filtered(lambda r: r.times == 'more').type
                    self.samount = self.sanction.rols.filtered(lambda r: r.times == 'more').amount
            else:
                self.stime = "أول مرة"
                self.stype = self.sanction.rols.filtered(lambda r: r.times == 'first').type
                self.samount = self.sanction.rols.filtered(lambda r: r.times == 'first').amount

        else:
            self.stime = None
            self.stype = None
            self.samount = None

    def action_draft(self):
        return self.write({'state': 'manager_approve'})

    def action_sent(self):
        if self.employee.parent_id.user_id.id == self.env.uid or self.employee.parent_id.user_id.has_group('customs_hr.hr_manager_ftl'):
            return self.write({'state': 'hr_approve'})
        else:
            raise ValidationError(_('يجب الموافقه من خلال المدير المباشر !'))
            
    def action_hr_approve(self):
        self.state = 'hr_approve'
        return self.write({'state': 'confirm'})
    
    def set_to_draft(self):
        self.state = 'hr_approve'
        return self.write({'state': 'cancelled'})
    def is_after_contract(self,contract,date,msg):
        if type(date) == str:
            date= datetime.strptime(date,"%Y-%m-%d").date()
        
        if contract.date_start:
            if contract.date_start > date:
                raise UserError(_("يجب ان يكون تاريخ {} بعد تاريخ بدء العقد {}").format(msg,contract.date_start))
    def write(self, vals):
        if 'dateof' in vals:
            self.is_after_contract(self.employee.contract_id,vals['dateof'],"العقوبة")
        return super(Procedures, self).write(vals)
    @api.model
    def create(self, vals):
        if 'dateof' in vals:
            contract=self.env['hr.contract'].search([('employee_id','=',vals['employee'])],limit=1)
            self.is_after_contract(contract,vals['dateof'],"العقوبة")
        return super(Procedures, self).create(vals)
            
