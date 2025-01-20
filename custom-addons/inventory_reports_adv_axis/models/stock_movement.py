# Report to know which Products have been Transported to Which Location and How Much in Qty.

from odoo import models, fields, api, _
import xlwt
from io import BytesIO
import base64
#from tabulate import tabulate


class StockMovementReport(models.TransientModel):
    _name = 'stock.movement'
    _description = 'Stock Movement Report'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    dated_report = fields.Boolean(string='Dated Report')
    body_html = fields.Html(render_engine='qweb',
                            sanitize_style=True, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = _('Stock Movement Report')
            res.append((record.id, name))
        return res

    def generate_report_preview(self):
        filters = [('date', '>=', self.start_date), ('date', '<=', self.end_date)]
        stock_moves = self.env['stock.move'].search(filters)

        report_data = []
        if self.dated_report:
            report_data.append(['Date', 'Product', 'Source Location', 'Destination Location', 'Quantity'])
            date_groups = sorted(stock_moves.mapped('date'))
            for date in date_groups:
                moves = stock_moves.filtered(lambda m: m.date == date)
                for move in moves:
                    report_data.append(
                        [str(move.date), move.product_id.name, move.location_id.name, move.location_dest_id.name,
                         move.product_uom_qty])
        else:
            report_data.append(['Product', 'Source Location', 'Destination Location', 'Quantity'])
            for move in stock_moves:
                report_data.append(
                    [move.product_id.name, move.location_id.name, move.location_dest_id.name, move.product_uom_qty])

        # Generate an HTML table from the report_data list
        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        for data_row in report_data:
            html_table += '<tr>'
            for cell_data in data_row:
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{cell_data}</td>'
            html_table += '</tr>'
        html_table += '</table>'

        self.body_html = html_table

    def generate_xls_report(self):
        filters = [('date', '>=', self.start_date), ('date', '<=', self.end_date)]

        stock_moves = self.env['stock.move'].search(filters)

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Stock Movement')

        heading_style = xlwt.easyxf('font: bold on; align: horiz center;')
        worksheet.write_merge(0, 0, 0, 4, 'Stock Movement Report', heading_style)
        worksheet.write_merge(1, 1, 0, 1, 'Start Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.start_date))
        worksheet.write_merge(2, 2, 0, 1, 'End Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(2, 2, 2, 3, str(self.end_date))

        header_style = xlwt.easyxf('font: bold on;')

        row = 4
        if self.dated_report:
            worksheet.write(row, 0, 'Date', header_style)
            worksheet.write(row, 1, 'Product', header_style)
            worksheet.write(row, 2, 'Source Location', header_style)
            worksheet.write(row, 3, 'Destination Location', header_style)
            worksheet.write(row, 4, 'Quantity', header_style)
            row += 1

            date_groups = sorted(stock_moves.mapped('date'))
            for date in date_groups:
                moves = stock_moves.filtered(lambda m: m.date == date)
                row += 1
                for move in moves:
                    worksheet.write(row, 0, str(move.date))
                    worksheet.write(row, 1, move.product_id.name)
                    worksheet.write(row, 2, move.location_id.name)
                    worksheet.write(row, 3, move.location_dest_id.name)
                    worksheet.write(row, 4, move.product_uom_qty)
                    row += 1
        else:
            worksheet.write(row, 0, 'Product', header_style)
            worksheet.write(row, 1, 'Source Location', header_style)
            worksheet.write(row, 2, 'Destination Location', header_style)
            worksheet.write(row, 3, 'Quantity', header_style)
            row += 1

            for move in stock_moves:
                worksheet.write(row, 0, move.product_id.name)
                worksheet.write(row, 1, move.location_id.name)
                worksheet.write(row, 2, move.location_dest_id.name)
                worksheet.write(row, 3, move.product_uom_qty)
                row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Stock Movement Report.xls'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.encodebytes(report_file.read()),
            'res_model': self._name,
            'res_id': self.id
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % (attachment.id),
            'target': 'new',
        }

    def generate_pdf_report(self):
        return self.env.ref('inventory_reports_adv_axis.stock_movement_pdf_report').report_action(self, config=False)

    def _get_stock_moves(self):
        filters = [('date', '>=', self.start_date), ('date', '<=', self.end_date)]
        stock_moves = self.env['stock.move'].search(filters)
        return stock_moves


    @api.model
    def get_stock_moves_js(self,activeid):
        self = self.env['stock.movement'].browse(int(activeid))
        filters = [('date', '>=', self.start_date), ('date', '<=', self.end_date)]
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        print ("Ssssssssssssssssssssss",filters)
        inventory_moves = self.env['stock.move'].read_group(filters, fields=['product_id', 'product_uom_qty'], groupby=['product_id'], lazy=False)

        product_details = {}
        for move in inventory_moves:
            product = move['product_id'][0]
            quantity_sold = move['product_uom_qty']
            productobj = self.env['product.product'].browse(product)

            # if product not in product_details:
            payroll_label.append(productobj.display_name)
            payroll_dataset.append(quantity_sold)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set
