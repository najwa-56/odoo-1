# Report to know Total Sold Products having detail about Quantity, Unit Price and Total Sales .

from odoo import models, fields, api, _
import xlwt
from io import BytesIO
import base64


class SalesAnalysis(models.TransientModel):
    _name = 'sales.analysis'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    filtered_report = fields.Boolean(string='Filter Report')
    category_ids = fields.Many2many('product.category', string='Product Categories')
    body_html = fields.Html(render_engine='qweb',
                            sanitize_style=True, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = _('Sales Analysis Report')
            res.append((record.id, name))
        return res

    @api.onchange('filtered_report')
    def _onchange_filtered_report(self):
        if not self.filtered_report:
            self.category_ids = False

    def generate_report_preview(self):
        if self.filtered_report:
            sales = self._get_filtered_sales()
        else:
            sales = self.env['sale.order.line'].search([
                ('order_id.date_order', '>=', self.start_date),
                ('order_id.date_order', '<=', self.end_date)
            ])

        report_data = []
        for sale in sales:
            product = sale.product_id
            quantity_sold = sale.product_uom_qty
            unit_price = sale.price_unit
            total_sales = quantity_sold * unit_price

            if self.filtered_report and self.category_ids:
                category = product.categ_id.name
            else:
                category = ''

            report_data.append({
                'product': product.name,
                'quantity_sold': quantity_sold,
                'unit_price': unit_price,
                'total_sales': total_sales,
                'category': category,
            })

        self.body_html = self._generate_html_table(report_data)

    def _generate_html_table(self, report_data):
        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Quantity Sold</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Unit Price</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Total Sales</th>'
        if self.filtered_report and self.category_ids:
            html_table += '<th style="border: 1px solid black; padding: 8px;">Category</th>'
        html_table += '</tr>'

        for data in report_data:
            html_table += '<tr>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["product"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["quantity_sold"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["unit_price"]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["total_sales"]}</td>'
            if self.filtered_report and self.category_ids:
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["category"]}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        return html_table

    def _get_filtered_sales(self):
        domain = [
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date),
        ]
        if self.category_ids:
            domain.append(('product_id.categ_id', 'in', self.category_ids.ids))

        return self.env['sale.order.line'].search(domain)

    def generate_xls_report(self):
        if self.filtered_report:
            return self._generate_filtered_report()
        else:
            return self._generate_full_report()

    def generate_pdf_report(self):
        if self.filtered_report:
            return self.env.ref('inventory_reports_adv_axis.sales_analysis_pdf_report').report_action(self, config=False)
        else:
            return self.env.ref('inventory_reports_adv_axis.sales_analysis_pdf_report').report_action(self, config=False)

    def _generate_full_report(self):
        sales = self.env['sale.order.line'].search([
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date)
        ])

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sales Analysis')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 4, 'Sales Analysis Report', header_style)
        worksheet.write_merge(1, 1, 0, 1, 'Start Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.start_date))
        worksheet.write_merge(2, 2, 0, 1, 'End Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(2, 2, 2, 3, str(self.end_date))

        worksheet.write(4, 0, 'Product', header_style)
        worksheet.write(4, 1, 'Quantity Sold', header_style)
        worksheet.write(4, 2, 'Unit Price', header_style)
        worksheet.write(4, 3, 'Total Sales', header_style)

        row = 5
        for sale in sales:
            product = sale.product_id
            quantity_sold = sale.product_uom_qty
            unit_price = sale.price_unit
            total_sales = quantity_sold * unit_price

            worksheet.write(row, 0, product.name, cell_style)
            worksheet.write(row, 1, quantity_sold, cell_style)
            worksheet.write(row, 2, unit_price, cell_style)
            worksheet.write(row, 3, total_sales, cell_style)

            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Sales Analysis Report.xls'
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

    def _generate_filtered_report(self):
        sales = self.env['sale.order.line'].search([
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date),
            ('product_id.categ_id', 'in', self.category_ids.ids)
        ])

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sales Analysis')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 4, 'Sales Analysis Report', header_style)
        worksheet.write_merge(1, 1, 0, 1, 'Start Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 4, str(self.start_date))
        worksheet.write_merge(2, 2, 0, 1, 'End Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(2, 2, 2, 4, str(self.end_date))

        worksheet.write(4, 0, 'Product', header_style)
        worksheet.write(4, 1, 'Quantity Sold', header_style)
        worksheet.write(4, 2, 'Unit Price', header_style)
        worksheet.write(4, 3, 'Total Sales', header_style)

        if self.category_ids:
            worksheet.write(4, 4, 'Category', header_style)

        row = 5
        for sale in sales:
            product = sale.product_id
            quantity_sold = sale.product_uom_qty
            unit_price = sale.price_unit
            total_sales = quantity_sold * unit_price

            worksheet.write(row, 0, product.name, cell_style)
            worksheet.write(row, 1, quantity_sold, cell_style)
            worksheet.write(row, 2, unit_price, cell_style)
            worksheet.write(row, 3, total_sales, cell_style)
            if self.category_ids:
                worksheet.write(row, 4, product.categ_id.name)

            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Sales Analysis Report.xls'
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


    @api.model
    def sale_anaysis_report_data_js(self,activeid):
        self = self.env['sales.analysis'].browse(int(activeid))
        filters = [
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date),
        ]
        if self.category_ids:
            filters = [
                ('order_id.date_order', '>=', self.start_date),
                ('order_id.date_order', '<=', self.end_date),
                ('product_id.categ_id', 'in', self.category_ids.ids)
            ]
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        print ("Ssssssssssssssssssssss",filters)
        inventory_moves = self.env['sale.order.line'].read_group(filters, fields=['product_id', 'product_uom_qty'], groupby=['product_id'], lazy=False)

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
