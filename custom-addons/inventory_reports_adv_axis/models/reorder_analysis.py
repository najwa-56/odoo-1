# Report to know which Product has to be Reordered, When to be Reordered and How much to be Reordered.


from datetime import datetime
from odoo import fields, models, api, _
import xlwt
from io import BytesIO
import base64
#from tabulate import tabulate


class ReorderAnalysisReport(models.TransientModel):
    _name = 'stock.reorder.analysis'
    _description = 'Reorder Analysis Report'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    body_html = fields.Html(render_engine='qweb',
                            sanitize_style=True, readonly=True)
    # product_ids = fields.Many2many('product.product', string='Products')
    # warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouses')

    def name_get(self):
        res = []
        for record in self:
            name = 'Reorder Analysis Report'
            res.append((record.id, name))
        return res

    @api.onchange('start_date', 'end_date')
    def _onchange_date_range(self):
        self.body_html = ''

    def generate_report_preview(self):
        products = self.env['product.product'].search([])

        product_data = []
        for product in products:
            quantity_on_hand = product.qty_available
            reorder_point = product.reordering_min_qty
            to_order = max(0, reorder_point - quantity_on_hand)

            product_data.append({
                'name': product.name,
                'qty_on_hand': quantity_on_hand,
                'reorder_point': reorder_point,
                'to_order': to_order,
            })

        headers = ['Product', 'Quantity On Hand', 'Reorder Point', 'To Order']
        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr>'
        for header in headers:
            html_table += f'<th style="border: 1px solid black; padding: 8px;">{header}</th>'
        html_table += '</tr>'

        for data in product_data:
            html_table += '<tr>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["name"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["qty_on_hand"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["reorder_point"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["to_order"]}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        self.body_html = html_table

    def generate_xls_report(self):
        filters = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]

        products = self.env['product.product'].search([])

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Reorder Analysis Report')

        heading_style = xlwt.easyxf('font: bold on; align: horiz center;')
        worksheet.write_merge(0, 0, 0, 3, 'Reorder Analysis Report', heading_style)
        worksheet.write_merge(1, 1, 0, 1, 'Start Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.start_date))
        worksheet.write_merge(2, 2, 0, 1, 'End Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(2, 2, 2, 3, str(self.end_date))

        header_style = xlwt.easyxf('font: bold on;')

        worksheet.write(4, 0, 'Product', header_style)
        worksheet.write(4, 1, 'Quantity On Hand', header_style)
        worksheet.write(4, 2, 'Reorder Point', header_style)
        worksheet.write(4, 3, 'To Order', header_style)

        row = 5
        for product in products:
            quantity_on_hand = product.qty_available
            reorder_point = product.reordering_min_qty
            to_order = max(0, reorder_point - quantity_on_hand)

            worksheet.write(row, 0, product.name)
            worksheet.write(row, 1, quantity_on_hand)
            worksheet.write(row, 2, reorder_point)
            worksheet.write(row, 3, to_order)
            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Reorder Analysis Report.xls'
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
        return self.env.ref('inventory_reports_adv_axis.reorder_analysis_pdf_report').report_action(self, config=False)


    @api.model
    def stock_reorder_analysis_data_js(self,activeid):
        self = self.env['stock.reorder.analysis'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        filters = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]

        products = self.env['product.product'].search([])
        for product in products:
            productname = product.display_name
            reodeing_qty = product.reordering_min_qty

            payroll_label.append(productname)
            payroll_dataset.append(reodeing_qty)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set
