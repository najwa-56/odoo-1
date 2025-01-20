# Report to know about the Balance of all Accounts in terms of Assets & Liabilities.

from odoo import models, fields, api, _
from io import BytesIO
import base64
import xlwt
from datetime import date, datetime, time


class InventoryBalanceSheet(models.TransientModel):
    _name = 'inventory.balance.sheet'

    year = fields.Selection([(str(num), str(num)) for num in range(2000, (datetime.now().year)+1)][::-1], 'Year',required=True)
    #
    # year = fields.Selection([
    #     ('2023', '2023'),
    #     ('2022', '2022'),
    #     ('2021', '2021'),
    #     ('2020', '2020'),
    #     ('2019', '2019'),
    #     ('2018', '2018'),
    #     ('2017', '2017'),
    #     ('2016', '2016'),
    #     ('2015', '2015'),
    #     ('2014', '2014'),
    #     ('2013', '2013'),
    #     ('2012', '2012'),
    #     ('2011', '2011'),
    #     ('2010', '2010'),
    # ], string='Year :', required=True)
    report_data = fields.Text(string='Report Data')
    body_html = fields.Html(render_engine='qweb',
                            sanitize_style=True, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = _('Balance Sheet Report')
            res.append((record.id, name))
        return res

    def generate_report_preview(self):
        accounts = self.env['account.account'].search([])
        balance_data = self._get_account_balances(accounts)

        # Create the report content as a tabular HTML
        html_table = '<h2>Balance Sheet Report</h2>'
        html_table += f'<h4><strong>Year:</strong> {self.year}</h4>'
        html_table += '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr><th style="border: 1px solid black; padding: 8px;"><h2>Account</h2></th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;"><h2>Balance</h2></th></tr>'

        for account in accounts:
            balance = balance_data.get(account.id, 0.0)
            html_table += '<tr>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{account.name}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{balance}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        self.body_html = html_table

    def generate_xls_report(self):
        return self._generate_balance_sheet()

    def _generate_balance_sheet(self):
        # Get the accounts and their balances for the selected year
        accounts = self.env['account.account'].search([])
        balance_data = self._get_account_balances(accounts)

        # Create the Excel workbook and worksheet
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Balance Sheet')

        # Write the report title
        title_style = xlwt.easyxf('font: bold on; align: horiz center;')
        worksheet.write_merge(0, 0, 0, 2, 'Balance Sheet Report', title_style)
        worksheet.write_merge(1, 1, 0, 1, 'Year:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 2, self.year)

        # Write the headers for the account data
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        worksheet.write(3, 0, 'Account', header_style)
        worksheet.write(3, 1, 'Balance', header_style)

        # Write the account data
        row = 4
        for account in accounts:
            balance = balance_data.get(account.id, 0.0)
            worksheet.write(row, 0, account.name)
            worksheet.write(row, 1, balance)
            row += 1

        # Save the report file
        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Balance Sheet Report.xls'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.encodebytes(report_file.read()),
            'res_model': self._name,
            'res_id': self.id
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }

    def _get_account_balances(self, accounts):
        # Calculate the balance for each account for the selected year
        balance_data = {}
        for account in accounts:
            balance = self._calculate_account_balance(account)
            balance_data[account.id] = balance
        return balance_data

    def _calculate_account_balance(self, account):
        move_lines = self.env['account.move.line'].search([
            ('account_id', '=', account.id),
            ('date', '>=', f'{self.year}-01-01'),
            ('date', '<=', f'{self.year}-12-31'),
        ])

        balance = sum(move_lines.mapped('debit')) - sum(move_lines.mapped('credit'))
        return balance

    def generate_pdf_report(self):
        return self.env.ref('inventory_reports_adv_axis.balance_sheet_pdf_report').report_action(self, config=False)

    @api.model
    def inventory_balance_sheet_data_js(self,activeid):
        self = self.env['inventory.balance.sheet'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        accounts = self.env['account.account'].search([])
        for account in accounts:
            move_lines = self.env['account.move.line'].search([
                ('account_id', '=', account.id),
                ('date', '>=', f'{self.year}-01-01'),
                ('date', '<=', f'{self.year}-12-31'),
            ])

            report_data = []
            balance = sum(move_lines.mapped('debit')) - sum(move_lines.mapped('credit'))
            for move in move_lines:

                payroll_label.append(move.account_id.name)
                payroll_dataset.append(balance)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set
