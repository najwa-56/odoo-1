# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class Roles(models.Model):
    _name = 'sanctions.roles'
    _description = 'sanctions.roles'
    
    def _default_head_branch(self):
         return self.env['hr.salary.rule'].search([('name', '=', 'Basic Salary')], limit=1).id
    
    model_id = fields.Many2one('sanctions.sanctions', string='Object', index=True, required=True, ondelete="cascade")
    num = fields.Char(string='التسلسل',required=True)
    times = fields.Selection([('first', 'أول مره'), ('second', 'ثاني مره'), ('third', 'ثالث مره'), ('fourth', 'رابع مره'), ('more', 'أكثر')],string='التكرار',required=True)
    type = fields.Selection([('non', 'لايوجد'), ('hours', 'ساعات'), ('percent', 'نسبة من اليوم'), ('days', 'أيام'), ('fixed', 'قيمة')],string='نوع الإجراء',required=True)
    amount = fields.Float(string='عامل الخصم',required=True)
    salary = fields.Many2one('hr.salary.rule',string='عناصر الراتب',required=True, default=_default_head_branch)

   