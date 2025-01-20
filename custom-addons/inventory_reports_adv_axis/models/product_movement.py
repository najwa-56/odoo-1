# Report to differentiate Products as per criteria of Fast, Slow & Non-Moving.

import xlwt
import base64

#from tabulate import tabulate

from odoo import models, fields, _
from io import BytesIO


class ProductMovementReport(models.TransientModel):
    _name = 'product.movement'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    slow_moving_qty = fields.Float(string='Qty. for Slow Moving')
    fast_moving_qty = fields.Float(string='Qty. for Fast Moving')
    warehouse_ids = fields.Many2many('stock.warehouse', string="Warehouse")
    body_html = fields.Html(render_engine='qweb',
                            sanitize_style=True, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = _('Product Movement Report')
            res.append((record.id, name))
        return res

    def generate_xls_report(self):
        products = self.env['product.product'].search([])

        fast_moving_products = []
        slow_moving_products = []
        not_moving_products = []

        for product in products:
            total_quantity = sum(product.stock_move_ids.filtered(lambda move: move.state == 'done').mapped('product_uom_qty'))

            if total_quantity >= self.fast_moving_qty:
                fast_moving_products.append(product)
            elif total_quantity <= self.slow_moving_qty:
                not_moving_products.append(product)
            else:
                slow_moving_products.append(product)

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Product Movement Report')

        heading_style = xlwt.easyxf('font: bold on; align: horiz center;')
        worksheet.write_merge(0, 0, 0, 10, 'Product Movement Report', heading_style)

        filter_style = xlwt.easyxf('font: bold on;')
        worksheet.write_merge(2, 2, 0, 1, 'Start Date:', filter_style)
        worksheet.write_merge(2, 2, 2, 3, str(self.start_date))
        worksheet.write_merge(2, 2, 4, 5, 'End Date:', filter_style)
        worksheet.write_merge(2, 2, 6, 7, str(self.end_date))
        # worksheet.write_merge(2, 2, 8, 9, 'Warehouses:', filter_style)
        # worksheet.write_merge(2, 2, 10, 11, ", ".join(self.warehouse_ids.mapped('name')))

        worksheet.write_merge(4, 4, 0, 2, 'Fast Moving Products', heading_style)
        worksheet.write(5, 0, 'Product Name', heading_style)
        worksheet.write(5, 1, 'Category', heading_style)
        worksheet.write(5, 2, 'Total Quantity', heading_style)
        row = 6
        for product in fast_moving_products:
            worksheet.write(row, 0, product.name)
            worksheet.write(row, 1, product.categ_id.name)
            worksheet.write(row, 2, sum(product.stock_move_ids.filtered(lambda move: move.state == 'done').mapped(
                'product_uom_qty')))
            row += 1

        worksheet.write_merge(4, 4, 4, 6, 'Slow Moving Products', heading_style)
        worksheet.write(5, 4, 'Product Name', heading_style)
        worksheet.write(5, 5, 'Category', heading_style)
        worksheet.write(5, 6, 'Total Quantity', heading_style)
        row = 6
        for product in slow_moving_products:
            worksheet.write(row, 4, product.name)
            worksheet.write(row, 5, product.categ_id.name)
            worksheet.write(row, 6, sum(product.stock_move_ids.filtered(lambda move: move.state == 'done').mapped(
                'product_uom_qty')))
            row += 1

        worksheet.write_merge(4, 4, 8, 10, 'Non Moving Products', heading_style)
        worksheet.write(5, 8, 'Product Name', heading_style)
        worksheet.write(5, 9, 'Category', heading_style)
        worksheet.write(5, 10, 'Total Quantity', heading_style)
        row = 6
        for product in not_moving_products:
            worksheet.write(row, 8, product.name)
            worksheet.write(row, 9, product.categ_id.name)
            worksheet.write(row, 10, sum(product.stock_move_ids.filtered(lambda move: move.state == 'done').mapped(
                'product_uom_qty')))
            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Product Movement Report.xls'
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
        return self.env.ref('inventory_reports_adv_axis.fsn_moving_pdf_report').report_action(self, config=False)

    def generate_report_preview(self):
        fast_moving_products, slow_moving_products, not_moving_products = self._get_product_movements()

        product_data = []

        # Add merged header for Fast Moving Products
        product_data.append(['Fast Moving Products', '', ''])
        product_data.append(['Product', 'Category', 'Total Quantity'])
        for product in fast_moving_products:
            total_quantity = sum(
                product.stock_move_ids.filtered(lambda move: move.state == 'done').mapped('product_uom_qty'))
            product_data.append([product.name, product.categ_id.name, total_quantity])

        # Add merged header for Slow Moving Products
        product_data.append(['Slow Moving Products', '', ''])
        product_data.append(['Product', 'Category', 'Total Quantity'])
        for product in slow_moving_products:
            total_quantity = sum(
                product.stock_move_ids.filtered(lambda move: move.state == 'done').mapped('product_uom_qty'))
            product_data.append([product.name, product.categ_id.name, total_quantity])

        # Add merged header for Non Moving Products
        product_data.append(['Non Moving Products', '', ''])
        product_data.append(['Product', 'Category', 'Total Quantity'])
        for product in not_moving_products:
            total_quantity = sum(
                product.stock_move_ids.filtered(lambda move: move.state == 'done').mapped('product_uom_qty'))
            product_data.append([product.name, product.categ_id.name, total_quantity])

        # Convert the product_data list into an HTML table
        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        for data in product_data:
            html_table += '<tr>'
            for cell in data:
                # Use colspan=3 for merged headers
                html_table += f'<td style="border: 1px solid black; padding: 8px;" colspan="3">{cell}</td>'
            html_table += '</tr>'
        html_table += '</table>'

        self.body_html = html_table

    def _get_product_movements(self):
        products = self.env['product.product'].search([])
        fast_moving_products = []
        slow_moving_products = []
        not_moving_products = []

        for product in products:
            total_quantity = sum(
                product.stock_move_ids.filtered(lambda move: move.state == 'done').mapped('product_uom_qty'))

            if total_quantity >= self.fast_moving_qty:
                fast_moving_products.append(product)
            elif total_quantity <= self.slow_moving_qty:
                not_moving_products.append(product)
            else:
                slow_moving_products.append(product)

        return fast_moving_products, slow_moving_products, not_moving_products

    def generate_graph_report(self):
        if self.warehouse_ids.ids:
            domain = [('categ_id', 'in', self.warehouse_ids.ids)]
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

    def generate_graph_view(self):
        fast_moving_products, slow_moving_products, not_moving_products = self._get_product_movements()

        graph_data = [
                         {
                             'name': _('Fast Moving'),
                             'x': _('Fast Moving'),
                             'y': sum(product.stock_move_ids.filtered(lambda move: move.state == 'done').mapped(
                                 'product_uom_qty')),
                         }
                         for product in fast_moving_products
                     ] + [
                         {
                             'name': _('Slow Moving'),
                             'x': _('Slow Moving'),
                             'y': sum(product.stock_move_ids.filtered(lambda move: move.state == 'done').mapped(
                                 'product_uom_qty')),
                         }
                         for product in slow_moving_products
                     ] + [
                         {
                             'name': _('Non-Moving'),
                             'x': _('Non-Moving'),
                             'y': sum(product.stock_move_ids.filtered(lambda move: move.state == 'done').mapped(
                                 'product_uom_qty')),
                         }
                         for product in not_moving_products
                     ]

        # Open the graph view
        return {
            'type': 'ir.actions.client',
            'tag': 'object',
            'params': {
                'model': 'ir.ui.view',
                'method': 'load_graph',
                'args': [self.env.ref('inventory_reports_adv_axis.view_product_movement_graph').id, graph_data],
            },
        }
