# Report to know the Total Available Qty of Product.

from odoo import fields, models, api, _
import xlwt
from io import BytesIO
import base64
#from tabulate import tabulate


class StockAvailabilityReport(models.TransientModel):
    _name = 'stock.availability'

    stock_at_date = fields.Date(string='Stock At Date', required=True)
    # location_ids = fields.Many2many('stock.location', string='Location')
    category_ids = fields.Many2many('product.category', string='Category')
    filtered_report = fields.Boolean(string='Filter Report')
    body_html = fields.Html(render_engine='qweb',
                            sanitize_style=True, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = _('Stock Availability Report')
            res.append((record.id, name))
        return res

    @api.onchange('filtered_report')
    def _onchange_filtered_report(self):
        if not self.filtered_report:
            # self.location_ids = False
            self.category_ids = False

    def generate_report_preview(self):
        if self.filtered_report:
            products = self._get_filtered_products()
            product_data = []
            for product in products:
                product_data.append([product.name, str(product.qty_available), product.uom_id.name])
            html_table = '<table style="border-collapse: collapse; width: 100%;">'
            html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Available Qty</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Unit</th>'
            html_table += '</tr>'

            for data in product_data:
                html_table += '<tr>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[0]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[1]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[2]}</td>'
                html_table += '</tr>'
            html_table += '</table>'
            self.body_html = html_table
        else:
            products = self.env['product.product'].search([])
            product_data = []
            for product in products:
                product_data.append([product.name, str(product.qty_available), product.uom_id.name])
            html_table = '<table style="border-collapse: collapse; width: 100%;">'
            html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Available Qty</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Unit</th>'
            html_table += '</tr>'

            for data in product_data:
                html_table += '<tr>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[0]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[1]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[2]}</td>'
                html_table += '</tr>'
            html_table += '</table>'
            self.body_html = html_table

    def generate_xls_report(self):
        if self.filtered_report:
            return self._generate_filtered_report()
        else:
            return self._generate_simple_report()

    def generate_pdf_report(self):
        if self.filtered_report:
            return self.env.ref('inventory_reports_adv_axis.stock_availability_pdf_report').report_action(self, config=False)
        else:
            return self.env.ref('inventory_reports_adv_axis.stock_availability_pdf_report').report_action(self, config=False)

    def _generate_simple_report(self):
        products = self.env['product.product'].search([])

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Stock Availability')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 3, 'Stock Availability Report', header_style)
        worksheet.write_merge(1, 1, 0, 1, 'Report Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.stock_at_date))

        worksheet.write(3, 0, 'Product', header_style)
        worksheet.write(3, 1, 'Available Quantity', header_style)
        worksheet.write(3, 2, 'Unit', header_style)

        row = 4
        for product in products:
            available_quantity = product.qty_available

            worksheet.write(row, 0, product.name)
            worksheet.write(row, 1, available_quantity)
            worksheet.write(row, 2, product.uom_id.name)

            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Stock Availability Report.xls'
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
        products = self._get_filtered_products()

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Stock Availability')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 3, 'Stock Availability Report', header_style)
        worksheet.write_merge(1, 1, 0, 1, 'Report Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.stock_at_date))

        worksheet.write(3, 0, 'Product', header_style)
        worksheet.write(3, 1, 'Available Quantity', header_style)
        worksheet.write(3, 2, 'Unit', header_style)

        if self.category_ids:
            worksheet.write(3, 3, 'Category', header_style)
        # if self.location_ids:
        #     worksheet.write(3, 4, 'Warehouse', header_style)

        row = 4
        for product in products:
            available_quantity = product.qty_available

            worksheet.write(row, 0, product.name)
            worksheet.write(row, 1, available_quantity)
            worksheet.write(row, 2, product.uom_id.name)

            if self.category_ids:
                worksheet.write(row, 3, product.categ_id.name)
            # if self.location_ids:
            #     worksheet.write(row, 4, product.location_id.name)

            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Stock Availability Report.xls'
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

    def _get_filtered_products(self):
        domain = []
        if self.category_ids:
            domain.append(('categ_id', 'in', self.category_ids.ids))
        # if self.location_ids:
        #     domain.append(('location_id', 'in', self.location_ids.ids))

        return self.env['product.product'].search(domain)


    @api.model
    def get_filtered_products_js(self):
        domain = []
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        if self.category_ids:
            domain.append(('categ_id', 'in', self.category_ids.ids))
        # inventory_moves = self.env['product.product'].read_group(domain, fields=['id','display_name', 'qty_available'],
        #                                                     groupby=['name'], lazy=True)

        product_details = {}
        inventory_moves = self.env['product.product'].search(domain)
        print ("OOOOOOOOOOOOOO",inventory_moves)
        for move in inventory_moves:
            product = move.display_name
            quantity_sold = move.qty_available
            # productobj = self.env['product.product'].browse(product)

            # if product not in product_details:
            payroll_label.append(product)
            payroll_dataset.append(quantity_sold)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set
