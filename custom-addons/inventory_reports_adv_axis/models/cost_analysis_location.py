# Report for Cost Analysis By Location.

from odoo import models, fields, api, _
import xlwt
from io import BytesIO
import base64
import datetime
import time


class CostAnalysisByLocationReport(models.TransientModel):
    _name = 'cost.analysis.location'
    _description = 'Cost Analysis By Location Report'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    location_ids = fields.Many2many('stock.location', string='Locations')
    body_html = fields.Html(render_engine='qweb', sanitize_style=True, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = _('Cost Analysis by Location Report')
            res.append((record.id, name))
        return res

    @api.onchange('location_ids')
    def _onchange_location_ids(self):
        if not self.location_ids:
            self.location_ids = False

    def generate_report_preview(self):
        moves = self._get_filtered_stock_moves()

        report_data = []
        for move in moves:
            product = move.product_id
            location = move.location_dest_id
            quantity = move.product_qty
            unit_cost = move.price_unit
            total_cost = quantity * unit_cost

            report_data.append({
                'product': product.name,
                'location': location.name,
                'quantity': quantity,
                'unit_cost': unit_cost,
                'total_cost': total_cost,
            })

        self.body_html = self._generate_html_table(report_data)

    def _generate_html_table(self, report_data):
        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Location</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Quantity</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Unit Cost</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Total Cost</th>'
        html_table += '</tr>'

        for data in report_data:
            html_table += '<tr>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["product"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["location"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["quantity"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["unit_cost"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["total_cost"]}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        return html_table

    def _get_filtered_stock_moves(self):
        domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]
        if self.location_ids:
            domain.append(('location_dest_id', 'in', self.location_ids.ids))

        return self.env['stock.move'].search(domain)

    def generate_xls_report(self):
        moves = self._get_filtered_stock_moves()

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Cost Analysis by Location')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 4, 'Cost Analysis by Location Report', header_style)
        worksheet.write_merge(1, 1, 0, 1, 'Start Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.start_date))
        worksheet.write_merge(2, 2, 0, 1, 'End Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(2, 2, 2, 3, str(self.end_date))

        worksheet.write(4, 0, 'Product', header_style)
        worksheet.write(4, 1, 'Location', header_style)
        worksheet.write(4, 2, 'Quantity', header_style)
        worksheet.write(4, 3, 'Unit Cost', header_style)
        worksheet.write(4, 4, 'Total Cost', header_style)

        row = 5
        for move in moves:
            product = move.product_id
            location = move.location_dest_id
            quantity = move.product_qty
            unit_cost = move.price_unit
            total_cost = quantity * unit_cost

            worksheet.write(row, 0, product.name, cell_style)
            worksheet.write(row, 1, location.name, cell_style)
            worksheet.write(row, 2, quantity, cell_style)
            worksheet.write(row, 3, unit_cost, cell_style)
            worksheet.write(row, 4, total_cost, cell_style)

            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Cost Analysis by Location Report.xls'
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
        return self.env.ref('inventory_reports_adv_axis.sales_analysis_pdf_report').report_action(self)

    @api.model
    def cost_data_js(self,activeid):
        self = self.env['cost.analysis.location'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        moves = self._get_filtered_stock_moves()
        for move in moves:
            product = move.product_id
            location = move.location_dest_id
            quantity = move.product_qty
            unit_cost = move.price_unit
            total_cost = quantity * unit_cost

            payroll_label.append(product.display_name)
            payroll_dataset.append(total_cost)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set
