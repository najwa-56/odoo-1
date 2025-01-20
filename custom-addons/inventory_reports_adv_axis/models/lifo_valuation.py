# Report to know the LIFO Valuation of Products.
# LIFO is an inventory valuation method where the last items added to the inventory are assumed to be the first ones sold

from odoo import models, fields, api, _
import xlwt
from io import BytesIO
import base64
try:
    import tabulate
except:
    from pip._internal import main as pipmain

    pipmain(['install', 'tabulate'])


class LIFOValuationReport(models.TransientModel):
    _name = 'lifo.valuation'
    _description = 'LIFO Valuation Report'

    valuation_date = fields.Date(string='Valuation Date', required=True)
    body_html = fields.Html(render_engine='qweb', sanitize_style=True, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = _('LIFO Valuation Report')
            res.append((record.id, name))
        return res

    def generate_xls_report(self):
        products = self.env['product.product'].search([])
        sorted_products = sorted(products, key=lambda p: p.create_date, reverse=True)

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('LIFO Valuation')
        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 8, 'LIFO Valuation Report', header_style)
        worksheet.write_merge(1, 1, 0, 1, 'Report Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.valuation_date))

        worksheet.write(3, 0, 'Product', header_style)
        worksheet.write(3, 1, 'Type', header_style)
        worksheet.write(3, 2, 'Cost Price', header_style)
        worksheet.write(3, 3, 'Received Qty', header_style)
        worksheet.write(3, 4, 'Sales Qty', header_style)
        worksheet.write(3, 5, 'Internal Movements Qty', header_style)
        worksheet.write(3, 6, 'Adjustment Qty', header_style)
        worksheet.write(3, 7, 'Available Qty', header_style)
        worksheet.write(3, 8, 'Value', header_style)

        row = 4
        for product in sorted_products:
            received_qty = self._get_received_quantity(product)
            sales_qty = self._get_sales_quantity(product)
            internal_moves_qty = self._get_internal_moves_quantity(product)
            adjustment_qty = self._get_adjustment_quantity(product)
            available_qty = self._get_available_quantity(product)
            cost_price = product.standard_price
            value = available_qty * cost_price

            worksheet.write(row, 0, product.name)
            worksheet.write(row, 1, product.type)
            worksheet.write(row, 2, cost_price)
            worksheet.write(row, 3, received_qty)
            worksheet.write(row, 4, sales_qty)
            worksheet.write(row, 5, internal_moves_qty)
            worksheet.write(row, 6, adjustment_qty)
            worksheet.write(row, 7, available_qty)
            worksheet.write(row, 8, value)

            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'LIFO Valuation Report.xls'
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

    def generate_report_preview(self):
        products = self.env['product.product'].search([])
        sorted_products = sorted(products, key=lambda p: p.create_date, reverse=True)
        product_data = []

        for product in sorted_products:
            received_qty = self._get_received_quantity(product)
            sales_qty = self._get_sales_quantity(product)
            internal_moves_qty = self._get_internal_moves_quantity(product)
            adjustment_qty = self._get_adjustment_quantity(product)
            available_qty = self._get_available_quantity(product)
            cost_price = product.standard_price
            value = available_qty * cost_price

            product_data.append([
                product.name,
                product.type,
                cost_price,
                received_qty,
                sales_qty,
                internal_moves_qty,
                adjustment_qty,
                available_qty,
                value,
                '\n'
            ])

        headers = ['Product', 'Type', 'Cost Price', 'Received Qty', 'Sales Qty', 'Internal Movements Qty',
                   'Adjustment Qty', 'Available Qty', 'Value', '']
        self.body_html = tabulate(product_data, headers=headers, tablefmt='html')

    def generate_pdf_report(self):
        return self.env.ref('inventory_reports_adv_axis.lifo_valuation_pdf_report').report_action(self, config=False)

    def _get_received_quantity(self, product):
        stock_moves = self.env['stock.move'].search([
            ('product_id', '=', product.id),
            ('state', '=', 'done'),
            ('location_dest_id.usage', 'in', ['internal', 'transit']),
        ])

        return sum(move.product_uom_qty for move in stock_moves)

    def _get_sales_quantity(self, product):
        stock_moves = self.env['stock.move'].search([
            ('product_id', '=', product.id),
            ('state', '=', 'done'),
            ('location_dest_id.usage', '=', 'customer'),
        ])

        return sum(move.product_uom_qty for move in stock_moves)

    def _get_internal_moves_quantity(self, product):
        stock_moves = self.env['stock.move'].search([
            ('product_id', '=', product.id),
            ('state', '=', 'done'),
            ('location_dest_id.usage', '=', 'internal'),
        ])

        return sum(move.product_uom_qty for move in stock_moves)

    def _get_adjustment_quantity(self, product):
        stock_moves = self.env['stock.move'].search([
            ('product_id', '=', product.id),
            ('state', '=', 'done'),
            ('picking_id.picking_type_id.code', '=', 'internal'),
            ('location_dest_id.usage', 'in', ['internal', 'transit']),
        ])

        return sum(move.product_uom_qty for move in stock_moves)

    def _get_available_quantity(self, product):
        return product.qty_available

    @api.model
    def lifo_data_js(self,activeid):
        self = self.env['fifo.valuation'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        products = self.env['product.product'].search([])
        sorted_products = sorted(products, key=lambda p: p.create_date, reverse=True)
        product_data = []

        for product in sorted_products:
            received_qty = self._get_received_quantity(product)
            sales_qty = self._get_sales_quantity(product)
            internal_moves_qty = self._get_internal_moves_quantity(product)
            adjustment_qty = self._get_adjustment_quantity(product)
            available_qty = self._get_available_quantity(product)
            cost_price = product.standard_price
            value = available_qty * cost_price
            productname = product.display_name
            pvalue = value

            payroll_label.append(productname)
            payroll_dataset.append(pvalue)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set
