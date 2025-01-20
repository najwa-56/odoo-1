# stock_velocity_reports/models/stock_velocity_analysis.py

from odoo import models, fields, api, _
import xlwt
from io import BytesIO
import base64


class StockVelocityAnalysis(models.TransientModel):
    _name = 'stock.velocity.analysis'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    body_html = fields.Html(render_engine='qweb', sanitize_style=True, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = _('Stock Velocity Report')
            res.append((record.id, name))
        return res

    def generate_report_preview(self):
        stock_moves = self._get_stock_moves()

        report_data = []
        for move in stock_moves:
            product = move.product_id
            quantity_moved = move.product_uom_qty
            date_moved = move.date
            velocity = self._calculate_velocity(product, quantity_moved, date_moved)

            report_data.append({
                'product': product.name,
                'quantity_moved': quantity_moved,
                'date_moved': date_moved,
                'velocity': velocity,
            })

        self.body_html = self._generate_html_table(report_data)

    def _generate_html_table(self, report_data):
        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Quantity Moved</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Date Moved</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Velocity</th>'
        html_table += '</tr>'

        for data in report_data:
            html_table += '<tr>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["product"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["quantity_moved"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["date_moved"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["velocity"]}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        return html_table

    def _get_stock_moves(self):
        return self.env['stock.move'].search([
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ])

    def _calculate_velocity(self, product, quantity_moved, date_moved):
        # Implement your velocity calculation logic here.
        # Velocity could be the average quantity moved per day for a product.
        # For simplicity, let's assume velocity = quantity_moved / number_of_days.
        number_of_days = (self.end_date - self.start_date).days + 1
        return round(quantity_moved / number_of_days, 2)

    def generate_xls_report(self):
        stock_moves = self._get_stock_moves()

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Stock Velocity Report')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 3, 'Stock Velocity Report', header_style)
        worksheet.write_merge(1, 1, 0, 1, 'Start Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.start_date))
        worksheet.write_merge(2, 2, 0, 1, 'End Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(2, 2, 2, 3, str(self.end_date))

        worksheet.write(4, 0, 'Product', header_style)
        worksheet.write(4, 1, 'Quantity Moved', header_style)
        worksheet.write(4, 2, 'Date Moved', header_style)
        worksheet.write(4, 3, 'Velocity', header_style)

        row = 5
        for move in stock_moves:
            product = move.product_id
            quantity_moved = move.product_uom_qty
            date_moved = move.date
            velocity = self._calculate_velocity(product, quantity_moved, date_moved)

            worksheet.write(row, 0, product.name, cell_style)
            worksheet.write(row, 1, quantity_moved, cell_style)
            worksheet.write(row, 2, str(date_moved), cell_style)
            worksheet.write(row, 3, velocity, cell_style)

            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Stock Velocity Report.xls'
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
        return self.env.ref('inventory_reports_adv_axis.stock_velocity_pdf_report').report_action(self, config=False)

    @api.model
    def velocity_data_js(self,activeid):
        self = self.env['stock.velocity.analysis'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        stock_moves = self._get_stock_moves()

        for move in stock_moves:
            product = move.product_id
            quantity_moved = move.product_uom_qty
            date_moved = move.date
            velocity = self._calculate_velocity(product, quantity_moved, date_moved)

            payroll_label.append(product.display_name)
            payroll_dataset.append(velocity)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set
