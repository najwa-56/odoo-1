# Report to know which product are making good profit and which product are not, in the term of profitability for a specific duration.
import xlwt
from io import BytesIO
import base64
from odoo import fields, models, api, _
#from tabulate import tabulate


class ProductProfitability(models.TransientModel):
    _name = 'product.profitability'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    body_html = fields.Html(render_engine='qweb',
                            sanitize_style=True, readonly=True)
    @api.model
    def product_profile_data_js(self,activeid):
        self = self.env['product.profitability'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        products = self.env['product.product'].search([])

        product_data = []
        for product in products:
            sale_orders = self.env['sale.order'].search([
                ('date_order', '>=', self.start_date),
                ('date_order', '<=', self.end_date),
                ('state', 'in', ['sale', 'done']),
                ('order_line.product_id', '=', product.id)
            ])

            total_revenue = sum(sale_orders.mapped('amount_total'))
            total_cost = product.standard_price * product.qty_available
            gross_profit = total_revenue - total_cost

            profit_percentage = round((gross_profit / total_revenue) * 100, 2) if total_revenue else 0

            payroll_label.append(product.display_name)
            payroll_dataset.append(profit_percentage)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set

    def name_get(self):
        res = []
        for record in self:
            name = _('Product Profitability Report')
            res.append((record.id, name))
        return res

    def generate_xls_report(self):
        products = self.env['product.product'].search([])

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Product Profitability')

        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 4, 'Product Profitability Report', header_style)
        worksheet.write_merge(1, 1, 0, 1, 'Start Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.start_date))
        worksheet.write_merge(2, 2, 0, 1, 'End Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(2, 2, 2, 3, str(self.end_date))
        worksheet.write(4, 0, 'Product', header_style)
        worksheet.write(4, 1, 'Total Revenue', header_style)
        worksheet.write(4, 2, 'Total Cost', header_style)
        worksheet.write(4, 3, 'Gross Profit', header_style)
        worksheet.write(4, 4, 'Profit Percentage', header_style)

        row = 6
        for product in products:
            sale_orders = self.env['sale.order'].search([
                ('date_order', '>=', self.start_date),
                ('date_order', '<=', self.end_date),
                ('state', 'in', ['sale', 'done']),
                ('order_line.product_id', '=', product.id)
            ])

            total_revenue = sum(sale_orders.mapped('amount_total'))
            total_cost = product.standard_price * product.qty_available
            gross_profit = total_revenue - total_cost

            profit_percentage = round((gross_profit / total_revenue) * 100, 2) if total_revenue else 0
            # profit_percentage = (gross_profit / total_revenue) * 100 if total_revenue else 0

            worksheet.write(row, 0, product.name)
            worksheet.write(row, 1, total_revenue, cell_style)
            worksheet.write(row, 2, total_cost, cell_style)
            worksheet.write(row, 3, gross_profit, cell_style)
            worksheet.write(row, 4, "{:.2f}".format(profit_percentage), cell_style)

            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Product Profitability Report.xls'
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
        return self.env.ref('inventory_reports_adv_axis.product_profitability_pdf_report').report_action(self, config=False)

    def generate_report_preview(self):
        products = self.env['product.product'].search([])

        product_data = []
        for product in products:
            sale_orders = self.env['sale.order'].search([
                ('date_order', '>=', self.start_date),
                ('date_order', '<=', self.end_date),
                ('state', 'in', ['sale', 'done']),
                ('order_line.product_id', '=', product.id)
            ])

            total_revenue = sum(sale_orders.mapped('amount_total'))
            total_cost = product.standard_price * product.qty_available
            gross_profit = total_revenue - total_cost

            profit_percentage = round((gross_profit / total_revenue) * 100, 2) if total_revenue else 0

            product_data.append([product.name, total_revenue, total_cost, gross_profit, profit_percentage])

        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Total Revenue</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Total Cost</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Gross Profit</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Profit Percentage</th>'
        html_table += '</tr>'

        for data in product_data:
            html_table += '<tr>'
            for value in data:
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{value}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        self.body_html = html_table

    def get_total_revenue(self, product):
        sale_orders = self.env['sale.order'].search([
            ('date_order', '>=', self.start_date),
            ('date_order', '<=', self.end_date),
            ('state', 'in', ['sale', 'done']),
            ('order_line.product_id', '=', product.id)
        ])
        return sum(sale_orders.mapped('amount_total'))

    def get_total_cost(self, product):
        return product.standard_price * product.qty_available

    def get_gross_profit(self, product):
        total_revenue = self.get_total_revenue(product)
        total_cost = self.get_total_cost(product)
        return total_revenue - total_cost

    def get_profit_percentage(self, product):
        total_revenue = self.get_total_revenue(product)
        gross_profit = self.get_gross_profit(product)
        return round((gross_profit / total_revenue) * 100, 2) if total_revenue else 0
