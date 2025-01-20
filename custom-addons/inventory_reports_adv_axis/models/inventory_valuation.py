# Report to know the Available Quantity of the Products.

from odoo import models, fields, api, _
import xlwt
from io import BytesIO
import base64
#from tabulate import tabulate


class InventoryValuationReport(models.TransientModel):
    _name = 'inventory.valuation'
    _description = 'Inventory Valuation Report'

    valuation_date = fields.Date(string='Valuation Date', required=True)
    filtered_report = fields.Boolean(string='Filtered Report')
    body_html = fields.Html(render_engine='qweb',
                            sanitize_style=True, readonly=True)
    product_category_ids = fields.Many2many('product.category', string='Product Categories')
    # warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouses')

    def name_get(self):
        res = []
        for record in self:
            name = _('Inventory Valuation Report')
            res.append((record.id, name))
        return res

    @api.onchange('filtered_report')
    def _onchange_filtered_report(self):
        if not self.filtered_report:
            # self.warehouse_ids = False
            self.product_category_ids = False

    def generate_xls_report(self):
        if self.filtered_report:
            return self._generate_filtered_report()
        else:
            return self._generate_simple_report()

    def generate_graph_report(self):
        if self.product_category_ids.ids:
            domain = [('categ_id', 'in', self.product_category_ids.ids)]
        else:
            domain = []
        return {
            'name': 'Data for Graph',
            'view_mode': 'graph,tree,form',
            'target': 'current',
            'domain': domain,
            'res_model': 'report.merge.object',
            'type': 'ir.actions.act_window',
        }

    def generate_report_preview(self):
        if self.filtered_report:
            products = self._get_filtered_products()
            product_data = []
            for product in products:
                product_data.append({
                    'name': product.name,
                    'qty_available': product.qty_available,
                    'uom_name': product.uom_id.name,
                    'category_name': product.categ_id.name if self.product_category_ids else '',
                })
            html_table = '<table style="border-collapse: collapse; width: 100%;">'
            html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Available Qty</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Unit</th>'
            if self.product_category_ids:
                html_table += '<th style="border: 1px solid black; padding: 8px;">Category</th>'
            html_table += '</tr>'

            for data in product_data:
                html_table += '<tr>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["name"]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["qty_available"]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["uom_name"]}</td>'
                if self.product_category_ids:
                    html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["category_name"]}</td>'
                html_table += '</tr>'

            html_table += '</table>'
            self.body_html = html_table
        else:
            products = self.env['product.product'].search([])
            product_data = []
            for product in products:
                product_data.append({
                    'name': product.name,
                    'qty_available': product.qty_available,
                    'uom_name': product.uom_id.name,
                })

            html_table = '<table style="border-collapse: collapse; width: 100%;">'
            html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Available Qty</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Unit</th>'
            html_table += '</tr>'

            for data in product_data:
                html_table += '<tr>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["name"]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["qty_available"]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["uom_name"]}</td>'
                html_table += '</tr>'

            html_table += '</table>'
            self.body_html = html_table

    def generate_pdf_report(self):
        if self.filtered_report:
                return self.env.ref('inventory_reports_adv_axis.inv_valuation_pdf_report').report_action(self, config=False)
        else:
            return self.env.ref('inventory_reports_adv_axis.inv_valuation_pdf_report').report_action(self, config=False)

    def _generate_simple_report(self):
        products = self.env['product.product'].search([])

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Inventory Valuation')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 3, 'Inventory Valuation Report', header_style)
        worksheet.write_merge(1, 1, 0, 1, 'Report Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.valuation_date))

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

        filename = 'Inventory Valuation Report.xls'
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
        worksheet = workbook.add_sheet('Inventory Valuation')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 3, 'Inventory Valuation Report', header_style)
        worksheet.write_merge(1, 1, 0, 1, 'Report Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.valuation_date))

        worksheet.write(3, 0, 'Product', header_style)
        worksheet.write(3, 1, 'Available Quantity', header_style)
        worksheet.write(3, 2, 'Unit', header_style)

        if self.product_category_ids:
            worksheet.write(3, 3, 'Category', header_style)
        # if self.location_ids:
        #     worksheet.write(3, 4, 'Warehouse', header_style)

        row = 4
        for product in products:
            available_quantity = product.qty_available

            worksheet.write(row, 0, product.name)
            worksheet.write(row, 1, available_quantity)
            worksheet.write(row, 2, product.uom_id.name)

            if self.product_category_ids:
                worksheet.write(row, 3, product.categ_id.name)
            # if self.location_ids:
            #     worksheet.write(row, 4, product.location_id.name)

            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Inventory Valuation Report.xls'
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
        if self.product_category_ids:
            domain.append(('categ_id', 'in', self.product_category_ids.ids))

        return self.env['product.product'].search(domain)


    @api.model
    def get_product_data_dict(self):
        data_set = {}
        payroll_label =[]
        payroll_dataset =[]
        products = self.env['product.product'].search([])
        for data in products:
            payroll_label.append(data.display_name)
            payroll_dataset.append(data.qty_available)
        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set
