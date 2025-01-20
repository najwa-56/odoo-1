from odoo import fields, models, api
import xlwt
from io import BytesIO
import base64
#from tabulate import tabulate


class SerialLotNumberTrackingReport(models.TransientModel):
    _name = 'serial.lot.tracking'
    _description = 'Serial/Lot Number Tracking Report'

    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    body_html = fields.Html(render_engine='qweb', sanitize_style=True, readonly=True)

    def name_get(self):
        return [(rec.id, 'Serial/Lot Number Tracking Report') for rec in self]

    def generate_xls_report(self):
        products = self.env['product.product'].search([('tracking', 'in', ['serial', 'lot'])])

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Serial Lot Tracking')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 3, 'Serial/Lot Number Tracking Report', header_style)

        worksheet.write_merge(2, 2, 0, 1, 'Start Date:', header_style)
        worksheet.write_merge(2, 2, 2, 3, str(self.date_start), cell_style)
        worksheet.write_merge(3, 3, 0, 1, 'End Date:', header_style)
        worksheet.write_merge(3, 3, 2, 3, str(self.date_end), cell_style)

        worksheet.write(5, 0, 'Product', header_style)
        worksheet.write(5, 1, 'Serial/Lot Number', header_style)
        worksheet.write(5, 2, 'Expiration Date', header_style)
        worksheet.write(5, 3, 'Quantity', header_style)

        row = 6
        for product in products:
            if product.tracking == 'serial':
                serial_numbers = [
                    serial.name for serial in self.env['stock.lot'].search([
                        ('product_id', '=', product.id),
                        ('create_date', '>=', self.date_start),
                        ('create_date', '<=', self.date_end)
                    ])
                ]
                worksheet.write(row, 0, product.name, cell_style)
                worksheet.write(row, 1, ', '.join(serial_numbers), cell_style)
                worksheet.write(row, 2, '', cell_style)
                worksheet.write(row, 3, '', cell_style)
                row += 1
            elif product.tracking == 'lot':
                lot_tracking_data = [
                    [lot.name, lot.use_date, lot.product_qty] for lot in self.env['stock.lot'].search([
                        ('product_id', '=', product.id),
                        ('create_date', '>=', self.date_start),
                        ('create_date', '<=', self.date_end)
                    ])
                ]
                for data in lot_tracking_data:
                    worksheet.write(row, 0, product.name, cell_style)
                    worksheet.write(row, 1, data[0], cell_style)
                    worksheet.write(row, 2, data[1], cell_style)
                    worksheet.write(row, 3, data[2], cell_style)
                    row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Serial Lot Tracking Report.xls'
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
        return self.env.ref('inventory_reports_adv_axis.serial_lot_tracking_pdf_report').report_action(self, config=False)

    def generate_report_preview(self):
        products = self.env['product.product'].search([('tracking', 'in', ['serial', 'lot'])])

        product_data = []
        for product in products:
            if product.tracking == 'serial':
                serial_numbers = [
                    serial.name for serial in self.env['stock.lot'].search([
                        ('product_id', '=', product.id),
                        ('create_date', '>=', self.date_start),
                        ('create_date', '<=', self.date_end)
                    ])
                ]
                product_data.append([product.name, ', '.join(serial_numbers), '', ''])
            elif product.tracking == 'lot':
                lot_tracking_data = [
                    [lot.name, lot.use_date, lot.product_qty] for lot in self.env['stock.lot'].search([
                        ('product_id', '=', product.id),
                        ('create_date', '>=', self.date_start),
                        ('create_date', '<=', self.date_end)
                    ])
                ]
                product_data.extend([[product.name, data[0], data[1], data[2]] for data in lot_tracking_data])

        # Generate the HTML table
        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Product</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Serial/Lot Number</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Expiration Date</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Quantity</th>'
        html_table += '</tr>'

        for data in product_data:
            html_table += '<tr>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[0]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[1]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[2]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[3]}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        self.body_html = html_table

    def _get_report_data(self):
        products = self.env['product.product'].search([('tracking', 'in', ['serial', 'lot'])])

        report_data = []
        for product in products:
            if product.tracking == 'serial':
                serial_numbers = [
                    serial.name for serial in self.env['stock.lot'].search([
                        ('product_id', '=', product.id),
                        ('create_date', '>=', self.date_start),
                        ('create_date', '<=', self.date_end)
                    ])
                ]
                report_data.append([product.name, ', '.join(serial_numbers), '', ''])
            elif product.tracking == 'lot':
                lot_tracking_data = [
                    [lot.name, lot.use_date, lot.product_qty] for lot in self.env['stock.lot'].search([
                        ('product_id', '=', product.id),
                        ('create_date', '>=', self.date_start),
                        ('create_date', '<=', self.date_end)
                    ])
                ]
                report_data.extend([[product.name, data[0], data[1], data[2]] for data in lot_tracking_data])

        return report_data

    @api.model
    def lot_data_js(self, activeid):
        self = self.env['serial.lot.tracking'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        products = self.env['product.product'].search([('tracking', 'in', ['serial', 'lot'])])

        report_data = []
        lot_tracking_data = []
        for product in products:
            if product.tracking == 'serial':
                lot_tracking_data = [
                    serial.name for serial in self.env['stock.lot'].search([
                        ('product_id', '=', product.id),
                        ('create_date', '>=', self.date_start),
                        ('create_date', '<=', self.date_end)
                    ])
                ]
            elif product.tracking == 'lot':
                lot_tracking_data = [
                    [lot.name, lot.use_date, lot.product_qty] for lot in self.env['stock.lot'].search([
                        ('product_id', '=', product.id),
                        ('create_date', '>=', self.date_start),
                        ('create_date', '<=', self.date_end)
                    ])
                ]
            for lot_tracking_da in lot_tracking_data:
                payroll_label.append(lot_tracking_da[0])
                payroll_dataset.append(lot_tracking_da[2])
        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set
