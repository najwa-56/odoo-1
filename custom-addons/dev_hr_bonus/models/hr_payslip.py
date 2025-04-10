# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, api, fields
from datetime import datetime

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        for payslip in self:
            payslip.input_line_ids.unlink()
            date_from = fields.Date.from_string(payslip.date_from)
            date_to = fields.Date.from_string(payslip.date_to)
            bonus_ids = self.env['hr.bonus'].search([
                ('state', '=', 'done'),
                ('applied_date', '>=', date_from),
                ('applied_date', '<=', date_to),
            ])
            print("bonus_ids================",bonus_ids)
            bonus_amount = 0.0
            bonus_percentage = 0.0
            employees = []
            if bonus_ids:
                for bonus in bonus_ids:
                    if bonus.employee_ids:
                        for employee in bonus.employee_ids:
                            employees.append(employee.employee_id.id)
                        if payslip.employee_id.id in employees:
                            if bonus.bonus_target == 'amount':
                                bonus_amount += bonus.amount
                            else:
                                bonus_percentage += bonus.percentage_amt
            if bonus_amount > 0:
                inputs = {
                    'name': 'Employee Bonus in Fixed Amount',
                    'code': 'BONUS_AMOUNT',
                }
                # type_id = self.env['hr.payslip.input.type'].create(inputs)
                vals = {
                    'name': 'Employee Bonus in %.2f %% of Salary' % (bonus_percentage,),
                    'payslip_id': payslip.id,
                    'code': 'BONUS_AMOUNT',
                    'amount': bonus_amount,
                    'contract_id': payslip.contract_id.id,
                    # 'input_type_id': type_id.id,
                }
                self.env['hr.payslip.input'].create(vals)
            if bonus_percentage > 0:
                inputs = {
                    'name': 'Employee Bonus in %.2f %% of Salary' % (bonus_percentage,),
                    'code': 'BONUS_AMOUNT',
                }
                # type_id = self.env['hr.payslip.input.type'].create(inputs)
                vals = {
                    'name': 'Employee Bonus in %.2f %% of Salary' % (bonus_percentage,),
                    'payslip_id': payslip.id,
                    'code': 'BONUS_PERCENTAGE',
                    'amount': bonus_percentage,
                    'contract_id': payslip.contract_id.id,
                    # 'input_type_id': type_id.id,
                }
                self.env['hr.payslip.input'].create(vals)

            # payslip default
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            # delete old payslip lines
            # payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or payslip.get_contract(
                payslip.employee_id, payslip.date_from, payslip.date_to
            )
            payslip.line_ids = False
            
            lines = [(0, 0, line) for line in payslip._get_payslip_lines(contract_ids,payslip.id)]
            payslip.write({
                'line_ids': lines,
                'number': number,
                'state': 'verify',
                # 'compute_date': fields.Date.today()
            })
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
