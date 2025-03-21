# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo import tools, _


class Allowance(models.Model):
    _name = 'hr.allowance'
    _rec_name = 'name'
    _description = 'Allowance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Allowance Name", required=True)
    active = fields.Boolean(string="Active", default=True)

    def unlink(self):
        for record in self:
            contract_lines = self.env['hr.contract.allowance.line'].search_count([('contract_id', '=', record.id)])
            if contract_lines != 0:
                raise exceptions.ValidationError(
                    _('You can not delete that allowance is it used in employee contracts'))
        res = super(Allowance, self).unlink()
        return res


class ContractAllowanceLine(models.Model):
    _name = 'hr.contract.allowance.line'
    _rec_name = 'allowance_id'
    _description = 'Contract Allowance Line'

    allowance_id = fields.Many2one(comodel_name="hr.allowance", string="Allowance")
    contract_id = fields.Many2one(comodel_name="hr.contract", string="Contract")
    amount = fields.Float(string="Amount")


class Contract(models.Model):
    _name = "hr.contract"
    _inherit = 'hr.contract'

    @api.constrains('state')
    def _check_state(self):
        for record in self:
            if record.state == 'open':
                contract_ids = self.env['hr.contract'].search(
                    [('employee_id', '=', record.employee_id.id), ('state', '=', 'open')])
                if len(contract_ids) > 1:
                    raise exceptions.ValidationError(_('Employee Must Have Only One Running Contract'))

    allowances_ids = fields.One2many(comodel_name="hr.contract.allowance.line", inverse_name="contract_id")

    def get_all_allowances(self):
        return sum(self.allowances_ids.mapped('amount'))
