# Report to know Qty. on Hand & Upcoming Forecasted Qty. & By When will the Qty. be fulfilled.

from odoo import fields, models, api
import xlwt
from io import BytesIO
import base64
#from tabulate import tabulate


class InventoryCoverage(models.TransientModel):
    _name = 'inventory.coverage'

    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    body_html = fields.Html(render_engine='qweb',
                            sanitize_style=True, readonly=True)

    def name_get(self):
        return [(record.id, 'Inventory Coverage Report') for record in self]

    def generate_xls_report(self):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Inventory Coverage')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 3, 'Inventory Coverage Report', header_style)

        worksheet.write_merge(2, 2, 0, 1, 'Start Date:', header_style)
        worksheet.write_merge(2, 2, 2, 3, str(self.date_start), cell_style)
        worksheet.write_merge(3, 3, 0, 1, 'End Date:', header_style)
        worksheet.write_merge(3, 3, 2, 3, str(self.date_end), cell_style)

        worksheet.write(5, 0, 'Product', header_style)
        worksheet.write(5, 1, 'On Hand Quantity', header_style)
        worksheet.write(5, 2, 'Forecasted Quantity', header_style)
        worksheet.write(5, 3, 'Coverage (Days)', header_style)

        products = self.env['product.product'].search([])

        row = 6
        for product in products:
            on_hand_qty = product.qty_available
            forecasted_qty = product.virtual_available

            coverage = 0.0
            if forecasted_qty:
                coverage = on_hand_qty / forecasted_qty

            worksheet.write(row, 0, product.name, cell_style)
            worksheet.write(row, 1, on_hand_qty, cell_style)
            worksheet.write(row, 2, forecasted_qty, cell_style)
            worksheet.write(row, 3, int(coverage), cell_style)

            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Inventory Coverage Report.xls'
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
        return self.env.ref('inventory_reports_adv_axis.inventory_coverage_pdf_report').report_action(self, config=False)

    def generate_report_preview(self):
        products = self.env['product.product'].search([])

        product_data = []
        for product in products:
            on_hand_qty = product.qty_available
            forecasted_qty = product.virtual_available

            coverage = 0.0
            if forecasted_qty:
                coverage = on_hand_qty / forecasted_qty

            product_data.append([product.name, on_hand_qty, forecasted_qty, int(coverage)])

        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">On Hand Quantity</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Forecasted Quantity</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Coverage (Days)</th></tr>'

        for data in product_data:
            html_table += '<tr>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[0]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[1]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[2]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[3]}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        self.body_html = html_table

    @api.model
    def inventory_coverage_data_js(self,activeid):
        self = self.env['inventory.coverage'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        products = self.env['product.product'].search([])

        report_data = []
        for product in products:
            payroll_label.append(product.display_name)
            payroll_dataset.append(product.virtual_available)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set

