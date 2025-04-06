# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class Sanctions(models.Model):
    _name = 'sanctions.sanctions'
    _description = 'sanctions.sanctions'
    procedures = fields.One2many('sanctions.procedures','sanction')
    name = fields.Char(string='إسم العقوبات', help="إسم العقوبات",required=True)
    # jobs = fields.Many2many('hr.job',string='تطبق على الوظائف',required=True)
    rols = fields.One2many('sanctions.roles','model_id',string='القواعد',required=True)
    reference_no = fields.Char(string='الكود', readonly=True, default=lambda self: _('New'))

    type = fields.Selection([
        ('continuous', 'Continuous'),
        ('frequently', 'Frequently'),
      
        

    ], string='Type',  copy=False,
       tracking=True, help='Type of the sanctions', default='continuous')


    @api.model
    def create(self, vals):
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
            'sanctions.sanctions') or _('New')
        res = super(Sanctions, self).create(vals)
        return res
   