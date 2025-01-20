# Report to know about Products which are about to come in Future.

from odoo import models, fields, api, _
import xlwt
from io import BytesIO
import base64
#from tabulate import tabulate


class StockForecast(models.TransientModel):
    _name = 'stock.forecast'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    body_html = fields.Html(render_engine='qweb',
                            sanitize_style=True, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = _('Stock Forecast Report')
            res.append((record.id, name))
        return res

    def generate_report_preview(self):
        # Retrieve stock moves within the specified date range
        stock_moves = self.env['stock.move'].search([
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])

        product_data = []
        for move in stock_moves:
            product = move.product_id
            quantity_forecast = move.product_qty
            product_data.append({
                'name': product.name,
                'quantity_forecast': quantity_forecast,
            })

        headers = ['Product', 'Quantity Forecast']
        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr>'
        for header in headers:
            html_table += f'<th style="border: 1px solid black; padding: 8px;">{header}</th>'
        html_table += '</tr>'

        for data in product_data:
            html_table += '<tr>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["name"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["quantity_forecast"]}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        self.body_html = html_table

    def generate_xls_report(self):
        stock_moves = self.env['stock.move'].search([
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Stock Forecast')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 1, 'Stock Forecast Report', header_style)
        worksheet.write(1, 0, 'Start Date:', header_style)
        worksheet.write(1, 1, str(self.start_date), header_style)
        worksheet.write(2, 0, 'End Date:', header_style)
        worksheet.write(2, 1, str(self.end_date), header_style)

        worksheet.write(4, 0, 'Product', header_style)
        worksheet.write(4, 1, 'Quantity Forecast', header_style)

        row = 5
        for move in stock_moves:
            product = move.product_id
            quantity_forecast = move.product_qty

            worksheet.write(row, 0, product.name, cell_style)
            worksheet.write(row, 1, quantity_forecast, cell_style)

            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Stock Forecast Report.xls'
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
        return self.env.ref('inventory_reports_adv_axis.stock_forecast_pdf_report').report_action(self, config=False)


    @api.model
    def stock_forecast_data_js(self,activeid):
        self = self.env['stock.forecast'].browse(int(activeid))
        filters = [('date', '>=', self.start_date), ('date', '<=', self.end_date)]
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        print("Ssssssssssssssssssssss", filters)
        stock_moves = self.env['stock.move'].search([
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])

        product_details = {}
        for move in stock_moves:
            product = move.product_id
            product_qty = move.product_qty

            # if product not in product_details:
            payroll_label.append(product.display_name)
            payroll_dataset.append(product_qty)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set


