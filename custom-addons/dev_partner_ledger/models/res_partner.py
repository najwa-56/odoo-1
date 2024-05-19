# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields, api, _

    
class res_partner(models.Model):
    _inherit = 'res.partner'
    
    
    def fetch_all(self):
        list_move_ids = []
        for each_self in self:
            each_self.journal_item_ids = False
            if each_self.id:
                rec_account_id = each_self.with_context(force_company=self.env.company.id).property_account_receivable_id.id
                pay_account_id = each_self.with_context(force_company=self.env.company.id).property_account_payable_id.id
                acc_id = [rec_account_id,pay_account_id]
                account_ids = str(tuple(acc_id))
                if account_ids and rec_account_id and pay_account_id:
                    each_self._cr.execute(
                    "SELECT l.id " \
                    "FROM account_move_line l " \
                    "LEFT JOIN account_journal j " \
                        "ON (l.journal_id = j.id) " \
                    "LEFT JOIN account_account acc " \
                        "ON (l.account_id = acc.id) " \
                    "LEFT JOIN res_currency c ON (l.currency_id=c.id)" \
                    "LEFT JOIN account_move m ON (l.move_id =m.id)" \
                    "WHERE l.partner_id = " +(str(each_self.id))+ \
                        " AND l.account_id IN %s"%(account_ids) + "ORDER BY l.date")
                    res = each_self._cr.fetchall()
                    for each in res:
                        list_move_ids.append(each[0])
                    if list_move_ids:
                        each_self.journal_item_ids = list_move_ids
                else:
                    each_self.journal_item_ids = False
    
    def compute_total(self):
        for each in self:
            each.balance = 0
            if each.credit or each.debit:
                each.balance = each.credit - each.debit
    
    balance = fields.Float("Balance",compute='compute_total',inverse='compute_total')
    journal_item_ids = fields.One2many('account.move.line','partner_id',string="Journal Entries", compute='fetch_all')
    
        
    
    

            
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
