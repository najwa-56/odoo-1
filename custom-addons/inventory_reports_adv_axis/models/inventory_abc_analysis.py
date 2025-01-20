from odoo import models, fields, api, _
import base64
from io import BytesIO
import xlwt
#import calendar
#from tabulate import tabulate


class InventoryABCAnalysis(models.TransientModel):
    _name = 'inventory.abc.analysis'
    _description = 'Inventory ABC Analysis Report'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    body_html = fields.Html(render_engine='qweb', sanitize_style=True, readonly=True)

    @api.model
    def abc_data_js(self, activeid):
        self = self.env['inventory.abc.analysis'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []

        products = self.env['product.product'].search([])

        product_movements = {}
        for product in products:
            product_movements[product.id] = self._calculate_total_movements(product)

            sorted_products = sorted(product_movements.items(), key=lambda x: x[1], reverse=True)
            cumulative_movements = sum(movements for _, movements in sorted_products)

            payroll_label.append(product.display_name)
            payroll_dataset.append(cumulative_movements)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set


    def name_get(self):
        res = []
        for record in self:
            name = _('Inventory ABC Analysis Report')
            res.append((record.id, name))
        return res

    def generate_xls_report(self):
        products = self.env['product.product'].search([])

        product_movements = {}
        for product in products:
            product_movements[product.id] = self._calculate_total_movements(product)

        sorted_products = sorted(product_movements.items(), key=lambda x: x[1], reverse=True)
        cumulative_movements = sum(movements for _, movements in sorted_products)

        abc_analysis = []
        cumulative_percentage = 0.0
        for product, movements in sorted_products:
            if cumulative_movements != 0:
                percentage = (movements / cumulative_movements) * 100
            else:
                percentage = 0.0
            percentage = round(percentage, 2)
            cumulative_percentage += percentage

            if cumulative_percentage <= 80:
                category = 'A'
            elif cumulative_percentage <= 95:
                category = 'B'
            else:
                category = 'C'

            abc_analysis.append({
                'product': self.env['product.product'].browse(product),
                'movements': movements,
                'percentage': percentage,
                'category': category,
            })

        # Create the report
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('ABC Analysis')

        heading_style = xlwt.easyxf('font: bold on; align: horiz center;')
        worksheet.write_merge(0, 0, 0, 4, 'Inventory ABC Analysis Report', heading_style)
        worksheet.write_merge(1, 1, 0, 1, 'Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.start_date)+'-->'+ str(self.end_date))

        header_style = xlwt.easyxf('font: bold on;')

        row = 3
        worksheet.write(row, 0, 'Product', header_style)
        worksheet.write(row, 1, 'Movements', header_style)
        worksheet.write(row, 2, 'Percentage', header_style)
        worksheet.write(row, 3, 'Category', header_style)
        row += 1

        for analysis in abc_analysis:
            worksheet.write(row, 0, analysis['product'].name)
            worksheet.write(row, 1, analysis['movements'])
            worksheet.write(row, 2, analysis['percentage'])
            worksheet.write(row, 3, analysis['category'])
            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'inventory_abc_analysis_report.xls'
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
        return self.env.ref('inventory_reports_adv_axis.inv_valuation_abc_analysis_pdf_report').report_action(self, config=False)

    def generate_report_preview(self):
        abc_analysis = self._calculate_abc_analysis()

        # Generate the HTML table for the report
        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Product</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Movements</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Percentage</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Category</th>'
        html_table += '</tr>'

        for analysis in abc_analysis:
            html_table += '<tr>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{analysis["product"].name}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{analysis["movements"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{analysis["percentage"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{analysis["category"]}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        self.body_html = html_table

    def _calculate_total_movements(self, product):
        # Calculate total movements for the given product
        movements = 0.0
        start_date = fields.Date.to_date(self.start_date)
        end_date = fields.Date.to_date(self.end_date)
        stock_moves = self.env['stock.move'].search([('date', '>=', start_date), ('date', '<=', end_date)])
        for move in stock_moves:
            if move.product_id == product:
                movements += move.product_uom_qty
        return movements

    def _calculate_abc_analysis(self):
        products = self.env['product.product'].search([])

        product_movements = {}
        for product in products:
            product_movements[product.id] = self._calculate_total_movements(product)

        sorted_products = sorted(product_movements.items(), key=lambda x: x[1], reverse=True)
        cumulative_movements = sum(movements for _, movements in sorted_products)

        abc_analysis = []
        cumulative_percentage = 0.0
        for product, movements in sorted_products:
            if cumulative_movements != 0:
                percentage = (movements / cumulative_movements) * 100
            else:
                percentage = 0.0
            percentage = round(percentage, 2)
            cumulative_percentage += percentage

            if cumulative_percentage <= 80:
                category = 'A'
            elif cumulative_percentage <= 95:
                category = 'B'
            else:
                category = 'C'

            abc_analysis.append({
                'product': self.env['product.product'].browse(product),
                'movements': movements,
                'percentage': percentage,
                'category': category,
            })

        return abc_analysis
