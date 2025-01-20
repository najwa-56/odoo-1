# Report to know which Products are in Extra Qty. so we can adjust our Purchases Accordingly.
from odoo import models, fields, api, _
from io import BytesIO
import base64
import xlwt


class InventoryOverstock(models.TransientModel):
    _name = 'inventory.overstock'

    threshold = fields.Float(string='Threshold Quantity', required=True)
    body_html = fields.Html(render_engine='qweb', sanitize_style=True, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = _('Inventory Overstock Report')
            res.append((record.id, name))
        return res

    def generate_report(self):
        products = self.env['product.product'].search([
            ('qty_available', '>', self.threshold)
        ])

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Inventory Overstock')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 2, 'Inventory Overstock Report', header_style)
        worksheet.write_merge(1, 1, 0, 0, 'Threshold:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 1, 2, str(self.threshold))

        worksheet.write(3, 0, 'Product', header_style)
        worksheet.write(3, 1, 'Quantity Available', header_style)
        worksheet.write(3, 2, 'Threshold', header_style)

        row = 4
        for product in products:
            quantity_available = product.qty_available

            worksheet.write(row, 0, product.name, cell_style)
            worksheet.write(row, 1, quantity_available, cell_style)
            worksheet.write(row, 2, self.threshold, cell_style)

            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Inventory Overstock Report.xls'
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
        return self.env.ref('inventory_reports_adv_axis.inventory_overstock_pdf_report').report_action(self, config=False)

    def generate_report_preview(self):
        products = self.env['product.product'].search([
            ('qty_available', '>', self.threshold)
        ])

        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Quantity Available</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Threshold</th></tr>'

        for product in products:
            html_table += '<tr>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{product.name}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{product.qty_available}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{self.threshold}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        self.body_html = html_table

    @api.model
    def inventory_overstock_data_js(self,activeid):
        self = self.env['inventory.overstock'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        products = self.env['product.product'].search([
            ('qty_available', '>', self.threshold)
        ])

        report_data = []
        for product in products:

            payroll_label.append(product.display_name)
            payroll_dataset.append(product.qty_available)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set



