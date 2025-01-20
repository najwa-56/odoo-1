from odoo import models, fields, api, _
import xlwt
from io import BytesIO
import base64


class StockReturnReport(models.TransientModel):
    _name = 'stock.return'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    body_html = fields.Html(render_engine='qweb', sanitize_style=True, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = _('Stock Return Report')
            res.append((record.id, name))
        return res

    def generate_report_preview(self):
        returns = self._get_stock_returns()

        report_data = []
        for return_line in returns:
            product = return_line.product_id
            return_qty = return_line.product_qty
            unit_price = return_line.price_unit
            total_return = return_qty * unit_price

            report_data.append({
                'product': product.name,
                'return_qty': return_qty,
                'unit_price': unit_price,
                'total_return': total_return,
            })

        self.body_html = self._generate_html_table(report_data)

    def _generate_html_table(self, report_data):
        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Return Quantity</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Unit Price</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Total Return</th>'
        html_table += '</tr>'

        for data in report_data:
            html_table += '<tr>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["product"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["return_qty"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["unit_price"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["total_return"]}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        return html_table

    def _get_stock_returns(self):
        domain = [
            ('state', '=', 'done'),  # To get only completed stock moves (returned items)
            ('picking_id.picking_type_id.code', '=', 'outgoing'),  # Outgoing moves indicate returns
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]
        return self.env['stock.move'].search(domain)

    def generate_xls_report(self):
        returns = self._get_stock_returns()

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Stock Return Report')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 3, 'Stock Return Report', header_style)
        worksheet.write_merge(1, 1, 0, 1, 'Start Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.start_date))
        worksheet.write_merge(2, 2, 0, 1, 'End Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(2, 2, 2, 3, str(self.end_date))

        worksheet.write(4, 0, 'Product', header_style)
        worksheet.write(4, 1, 'Return Quantity', header_style)
        worksheet.write(4, 2, 'Unit Price', header_style)
        worksheet.write(4, 3, 'Total Return', header_style)

        row = 5
        for return_line in returns:
            product = return_line.product_id
            return_qty = return_line.product_qty
            unit_price = return_line.price_unit
            total_return = return_qty * unit_price

            worksheet.write(row, 0, product.name, cell_style)
            worksheet.write(row, 1, return_qty, cell_style)
            worksheet.write(row, 2, unit_price, cell_style)
            worksheet.write(row, 3, total_return, cell_style)

            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Stock Return Report.xls'
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
        return self.env.ref('inventory_reports_adv_axis.stock_return_pdf_report').report_action(self, config=False)

    def _get_stock_return_data(self):
        domain = [
            ('state', '=', 'done'),
            ('picking_id.picking_type_id.code', '=', 'outgoing'),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]
        return self.env['stock.move'].search(domain)



    @api.model
    def st_return_data_js(self,activeid):
        self = self.env['stock.return'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        returns = self._get_stock_returns()
        for return_line in returns:
            product = return_line.product_id
            return_qty = return_line.product_qty
            unit_price = return_line.price_unit
            total_return = return_qty * unit_price

            payroll_label.append(product.display_name)
            payroll_dataset.append(total_return)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set
