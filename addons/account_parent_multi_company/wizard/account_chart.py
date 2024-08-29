##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2020 - Today O4ODOO (Omal Bastin)
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################

from odoo import models, fields, api, exceptions, _


class OpenAccountChartMultiCompany(models.TransientModel):
    """
    For Chart of Accounts
    """
    _inherit = "account.open.chart"
    
    view_consolidation = fields.Boolean('View Consolidation') #Not using anymore
    consolidated_coa = fields.Boolean('Show Consolidated CoA', default=False)
    target_currency_id = fields.Many2one(
        'res.currency', 'Target Currency')
    company_ids = fields.Many2many(
        'res.company', 'res_company_coachart_rel',
        'coa_id', 'cid', string='Companies')
    
    @api.onchange('consolidated_coa')
    def onchange_consolidated_coa(self):
        companies = self.env.user.company_ids
        allowed_company_ids = self.env.context.get('allowed_company_ids', [])
        self.report_type = 'account_type'
        if self.consolidated_coa:
            if len(allowed_company_ids) <= 1:
                raise exceptions.UserError(
                    _("Please Allow multiple companies in the multi company "
                      "options(top right corner)"))
            self.company_ids = [(6, 0, allowed_company_ids)]
            self.target_currency_id = self.env.company.currency_id.id
        
    def _build_contexts(self):
        res = super()._build_contexts()
        self.ensure_one()
        if self.consolidated_coa:
            res['company_ids'] = self.company_ids.ids
            res['allowed_company_ids'] = self.company_ids.ids
            res['consolidated_coa'] = self.consolidated_coa
            res['target_currency_id'] = self.target_currency_id.id
            del res['company_id']
        return res

    @api.model
    def get_accounts(self, line_id, context):
        return self.env['account.account'].sudo().with_context(context).search([
            ('company_id', '=', context.get('company_id', False)),
            ('parent_id', '=', line_id)])

    @api.model
    def get_accounts(self, line_id, context):
        if not context.get('consolidated_coa', False):
            return super().get_accounts(line_id=line_id, context=context)
        
        account = self.env['account.account'].sudo().with_context(context)
        account_domain = [('company_id', 'in', context.get('company_ids', []))]
        
        if line_id:
            parent_account = account.browse(line_id)
            account_domain += [('parent_id.code', '=', parent_account.code)]
        else:
            account_domain += [('parent_id', '=', False)]
        return account.sudo().with_context(context).search(account_domain)

    @api.model
    def get_at_accounts(self, at_data, context):
        if not context.get('consolidated_coa', False):
            return super().get_at_accounts(at_data=at_data, context=context)

        account_domain = [('company_id', 'in', context.get('company_ids', []))]
        if not at_data['atype']:
            account_domain += [('internal_group', 'in', at_data['internal_group'])]
        else:
            account_domain += [('account_type', 'in', at_data['account_type'])]
        return self.env['account.account'].sudo().with_context(context).search(
            account_domain)

    def get_heading(self, context):
        if not context.get('consolidated_coa', False):
            return super().get_heading(context=context)
        companies = self.env['res.company'].browse(context.get('company_ids'))
        res = "Consolidated Chart of Account: %s" % ', '.join(
            companies.mapped('display_name'))
        return res
    
    @api.model
    def _amount_to_str(self, value, currency):
        context = self.env.context
        if not context.get('consolidated_coa', False):
            return super()._amount_to_str(value=value, currency=currency)
        target_currency_id = context.get('target_currency_id')
        return self.format_amount_to_str(
            value, self.env['res.currency'].browse(target_currency_id))
        # field_options = {'display_currency': self.env['res.currency'].browse(target_currency_id),
        #                  # 'from_currency': currency
        #                  }
        # return self.env['ir.qweb.field.monetary'].value_to_html(value, field_options)
    
    @api.model
    def _lines(self, wiz_id=None, line_id=None, level=1, obj_ids=[]):
        context = self.env.context.copy()
        if not context.get('consolidated_coa', False):
            return super()._lines(wiz_id=wiz_id, line_id=line_id, level=level,
                                  obj_ids=obj_ids)

        final_vals = []
        account_code_dict = {}
        account_code_movement_dict = {}
        display_account = context.get('display_account', 'all')
        for account in obj_ids:
            if account.code not in account_code_movement_dict:
                account_code_movement_dict[account.code] = False
            if account.debit or account.credit:
                account_code_movement_dict[account.code] = True
            company_id = False
            if account.account_type != 'view':
                company_id = account.company_id.id
            if (account.code, company_id) not in account_code_dict:
                account_code_dict[(account.code, company_id)] = self.line_data(
                    level, wiz_id=wiz_id,parent_id=line_id, account=account)
                if company_id:
                    account_code_dict[
                        (account.code, company_id)]['name'] = "%s (%s)" % (
                        account.name, account.company_id.name)
            else:
                account_code_dict[(account.code, company_id)]['db'] += account.debit
                account_code_dict[(account.code, company_id)]['cr'] += account.credit
                account_code_dict[(account.code, company_id)]['bal'] += account.balance
                account_code_dict[
                    (account.code, company_id)]['ini_bal'] += account.initial_balance
                account_code_dict[(account.code, company_id)]['end_bal'] += (
                        account.balance + account.initial_balance)
                
        for acd in account_code_dict:
            company = account_code_dict[acd]['company_obj']
            account_code_dict[acd]['debit'] = self.float_html_formatting(
                account_code_dict[acd]['db'], company)
            account_code_dict[acd]['credit'] = self.float_html_formatting(
                account_code_dict[acd]['cr'], company)
            account_code_dict[acd]['balance'] = self.float_html_formatting(
                account_code_dict[acd]['bal'], company)
            account_code_dict[acd]['initial_balance'] = self.float_html_formatting(
                account_code_dict[acd]['ini_bal'], company)
            account_code_dict[acd]['ending_balance'] = self.float_html_formatting(
                account_code_dict[acd]['end_bal'], company)
            
        if display_account == 'movement':
            for each in account_code_dict.values():
                if account_code_movement_dict[each['code']]:
                    final_vals += [each]
        else:
            final_vals += list(account_code_dict.values())
        return final_vals
    

