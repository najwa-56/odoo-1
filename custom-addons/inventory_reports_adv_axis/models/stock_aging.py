# Report To Know Which Product Is Since Long In The Inventory.

from odoo import models, fields, api, _
import xlwt
from io import BytesIO
import base64
#from tabulate import tabulate


class StockAging(models.TransientModel):
    _name = 'stock.aging'
    _description = 'Stock Aging Report'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    body_html = fields.Html(render_engine='qweb', sanitize_style=True, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = 'Stock Aging Report'
            res.append((record.id, name))
        return res

    def generate_xls_report(self):
        filters = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]

        stock_moves = self.env['stock.move'].search(filters)
        today = fields.Date.from_string(fields.Date.today())

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Stock Aging Report')

        heading_style = xlwt.easyxf('font: bold on; align: horiz center;')
        worksheet.write_merge(0, 0, 0, 3, 'Stock Aging Report', heading_style)
        worksheet.write_merge(1, 1, 0, 1, 'Start Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.start_date))
        worksheet.write_merge(2, 2, 0, 1, 'End Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(2, 2, 2, 3, str(self.end_date))

        header_style = xlwt.easyxf('font: bold on;')

        worksheet.write(4, 0, 'Product', header_style)
        worksheet.write(4, 1, 'Quantity', header_style)
        worksheet.write(4, 2, 'Date Received', header_style)
        worksheet.write(4, 3, 'Days in Stock', header_style)

        row = 5
        for move in stock_moves:
            product = move.product_id
            date_received = fields.Date.from_string(move.date)
            days_in_stock = (today - date_received).days

            worksheet.write(row, 0, product.name)
            worksheet.write(row, 1, move.product_uom_qty)
            worksheet.write(row, 2, str(date_received))
            worksheet.write(row, 3, days_in_stock)
            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Stock Aging Report.xls'
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

    def generate_pdf_report(self):
        return self.env.ref('inventory_reports_adv_axis.stock_aging_pdf_report').report_action(self, config=False)

    def generate_report_preview(self):
        filters = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]

        stock_moves = self.env['stock.move'].search(filters)
        today = fields.Date.from_string(fields.Date.today())

        report_data = []
        for move in stock_moves:
            product = move.product_id
            date_received = fields.Date.from_string(move.date)
            days_in_stock = (today - date_received).days

            report_data.append([product.name, move.product_uom_qty, str(date_received), days_in_stock])

        headers = ['Product', 'Quantity', 'Date Received', 'Days in Stock']

        # Generating the tabulated HTML table
        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr>'
        for header in headers:
            html_table += f'<th style="border: 1px solid black; padding: 8px;">{header}</th>'
        html_table += '</tr>'

        for data in report_data:
            html_table += '<tr>'
            for value in data:
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{value}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        self.body_html = html_table

    @api.model
    def stock_aging_data_js(self, activeid):
        self = self.env['sales.analysis'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        filters = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]

        stock_moves = self.env['stock.move'].search(filters)
        today = fields.Date.from_string(fields.Date.today())

        report_data = []
        for move in stock_moves:
            product = move.product_id
            date_received = fields.Date.from_string(move.date)
            days_in_stock = (today - date_received).days

            payroll_label.append(product.display_name)
            payroll_dataset.append(days_in_stock)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set
