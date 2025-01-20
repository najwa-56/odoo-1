# Report to know the Turnover Ratio of Inventory on basis of total goods sold.

from odoo import fields, models, api, _
import xlwt
from io import BytesIO
import base64
#from tabulate import tabulate


class InventoryTurnoverReport(models.TransientModel):
    _name = 'stock.inventory.turnover'
    _description = 'Inventory Turnover Report'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    body_html = fields.Html(render_engine='qweb',
                            sanitize_style=True, readonly=True)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')
    product_ids = fields.Many2many('product.product', string='Products')
    filter_report_by = fields.Selection([
        ('none', 'None'),
        # ('warehouse', 'Warehouse'),
        ('product', 'Product')
    ], string='Filter Report By :', required=True, default='none')

    @api.onchange('filter_report_by')
    def _onchange_filter_report_by(self):
        if self.filter_report_by == 'none':
            self.warehouse_ids = False
            self.product_ids = False
        elif self.filter_report_by == 'product':
            self.warehouse_ids = False
        elif self.filter_report_by == 'warehouse':
            self.product_ids = False

    def name_get(self):
        res = []
        for record in self:
            name = _('Inventory Turnover Report')
            res.append((record.id, name))
        return res

    def generate_xls_report(self):
        filters = [('state', '=', 'done')]
        if self.start_date:
            filters.append(('date', '>=', self.start_date))
        if self.end_date:
            filters.append(('date', '<=', self.end_date))
        if self.warehouse_ids:
            filters.append(('warehouse_id', 'in', self.warehouse_ids.ids))
        if self.product_ids:
            filters.append(('product_id', 'in', self.product_ids.ids))

        inventory_moves = self.env['stock.move'].search(filters)

        product_details = {}
        for move in inventory_moves:
            product = move.product_id
            quantity_sold = move.product_uom_qty
            cogs = product.standard_price * quantity_sold
            average_inventory = product.standard_price

            if average_inventory:
                turnover_ratio = cogs / average_inventory
            else:
                turnover_ratio = 0.0

            if product not in product_details:
                product_details[product] = {
                    'name': product.name,
                    'quantity_sold': quantity_sold,
                    'cogs': cogs,
                    'average_inventory': average_inventory,
                    'turnover_ratio': turnover_ratio,
                }
            else:
                product_details[product]['quantity_sold'] += quantity_sold
                product_details[product]['cogs'] += cogs

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Inventory Turnover Ratios')

        heading_style = xlwt.easyxf('font: bold on; align: horiz center;')
        worksheet.write_merge(0, 0, 0, 5, 'Inventory Turnover Ratio Report', heading_style)
        worksheet.write_merge(1, 1, 0, 1, 'Start Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.start_date))
        worksheet.write_merge(2, 2, 0, 1, 'End Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(2, 2, 2, 3, str(self.end_date))
        if self.product_ids:
            worksheet.write_merge(4, 4, 0, 1, 'Products:', xlwt.easyxf('font: bold on;'))
            worksheet.write_merge(4, 4, 2, 5, ', '.join(self.product_ids.mapped('name')))
        if self.warehouse_ids:
            worksheet.write_merge(6, 6, 0, 1, 'Warehouses:', xlwt.easyxf('font: bold on;'))
            worksheet.write_merge(6, 6, 2, 5, ', '.join(self.warehouse_ids.mapped('name')))
        worksheet.write_merge(5, 5, 0, 1, 'Report Filter By :', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(5, 5, 2, 3, dict(self._fields['filter_report_by'].selection).get(self.filter_report_by))

        header_style = xlwt.easyxf('font: bold on;')

        row = 8
        if self.filter_report_by == 'none':
            worksheet.write(7, 0, 'Products', header_style)
            worksheet.write(7, 1, 'Quantity Sold', header_style)
            worksheet.write(7, 2, 'COGS', header_style)
            worksheet.write(7, 3, 'Average Inventory', header_style)
            worksheet.write(7, 4, 'Turnover Ratio', header_style)
            row = 8
            for details in product_details.values():
                worksheet.write(row, 0, details['name'])
                worksheet.write(row, 1, details['quantity_sold'])
                worksheet.write(row, 2, details['cogs'])
                worksheet.write(row, 3, details['average_inventory'])
                worksheet.write(row, 4, details['turnover_ratio'])
                row += 1

        elif self.filter_report_by == 'product':
            for details in product_details.values():
                worksheet.write(row, 0, 'Product:', header_style)
                worksheet.write(row, 1, details['name'])
                worksheet.write(row + 1, 0, 'Quantity Sold', header_style)
                worksheet.write(row + 1, 1, 'COGS', header_style)
                worksheet.write(row + 1, 2, 'Average Inventory', header_style)
                worksheet.write(row + 1, 3, 'Turnover Ratio', header_style)
                worksheet.write(row + 2, 0, details['quantity_sold'])
                worksheet.write(row + 2, 1, details['cogs'])
                worksheet.write(row + 2, 2, details['average_inventory'])
                worksheet.write(row + 2, 3, details['turnover_ratio'])
                row += 5
        elif self.filter_report_by == 'warehouse':
            warehouse_product_details = {}
            for move in inventory_moves:
                product = move.product_id
                warehouse = move.warehouse_id

                if warehouse not in warehouse_product_details:
                    warehouse_product_details[warehouse] = {}

                if product not in warehouse_product_details[warehouse]:
                    warehouse_product_details[warehouse][product] = {
                        'name': product.name,
                        'quantity_sold': quantity_sold,
                        'cogs': cogs,
                        'average_inventory': average_inventory,
                        'turnover_ratio': turnover_ratio,
                    }
                else:
                    warehouse_product_details[warehouse][product]['quantity_sold'] += quantity_sold
                    warehouse_product_details[warehouse][product]['cogs'] += cogs

            row = 7
            for warehouse, products in warehouse_product_details.items():
                worksheet.write(row, 0, 'Warehouse:', header_style)
                worksheet.write(row, 1, warehouse.name)
                row += 2

                worksheet.write(row, 0, 'Product', header_style)
                worksheet.write(row, 1, 'Quantity Sold', header_style)
                worksheet.write(row, 2, 'COGS', header_style)
                worksheet.write(row, 3, 'Average Inventory', header_style)
                worksheet.write(row, 4, 'Turnover Ratio', header_style)
                row += 1

                for details in products.values():
                    worksheet.write(row, 0, details['name'])
                    worksheet.write(row, 1, details['quantity_sold'])
                    worksheet.write(row, 2, details['cogs'])
                    worksheet.write(row, 3, details['average_inventory'])
                    worksheet.write(row, 4, details['turnover_ratio'])
                    row += 1

                row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'Inventory Turnover Ratio Report.xls'
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
        if self.filter_report_by:
            return self.env.ref('inventory_reports_adv_axis.inv_turnover_pdf_report').report_action(self)
        else:
            return self.env.ref('inventory_reports_adv_axis.inv_turnover_pdf_report').report_action(self)

    def generate_report_preview(self):
        filters = [('state', '=', 'done')]
        if self.start_date:
            filters.append(('date', '>=', self.start_date))
        if self.end_date:
            filters.append(('date', '<=', self.end_date))
        if self.warehouse_ids:
            filters.append(('warehouse_id', 'in', self.warehouse_ids.ids))
        if self.product_ids:
            filters.append(('product_id', 'in', self.product_ids.ids))

        inventory_moves = self.env['stock.move'].search(filters)

        product_details = {}
        for move in inventory_moves:
            product = move.product_id
            quantity_sold = move.product_uom_qty
            cogs = product.standard_price * quantity_sold
            average_inventory = product.standard_price

            if average_inventory:
                turnover_ratio = cogs / average_inventory
            else:
                turnover_ratio = 0.0

            if product not in product_details:
                product_details[product] = {
                    'name': product.name,
                    'quantity_sold': quantity_sold,
                    'cogs': cogs,
                    'average_inventory': average_inventory,
                    'turnover_ratio': turnover_ratio,
                }
            else:
                product_details[product]['quantity_sold'] += quantity_sold
                product_details[product]['cogs'] += cogs

        if self.filter_report_by == 'none':
            html_table = '<table style="border-collapse: collapse; width: 100%;">'
            html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Quantity Sold</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">COGS</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Average Inventory</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Turnover Ratio</th></tr>'

            for details in product_details.values():
                html_table += '<tr>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["name"]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["quantity_sold"]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["cogs"]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["average_inventory"]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["turnover_ratio"]}</td>'
                html_table += '</tr>'

            html_table += '</table>'
            self.body_html = html_table

        elif self.filter_report_by == 'product':
            html_table = '<table style="border-collapse: collapse; width: 100%;">'
            html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Quantity Sold</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">COGS</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Average Inventory</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;">Turnover Ratio</th>'
            html_table += '</tr>'

            for details in product_details.values():
                html_table += '<tr>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["name"]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["quantity_sold"]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["cogs"]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["average_inventory"]}</td>'
                html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["turnover_ratio"]}</td>'
                html_table += '</tr>'

            html_table += '</table>'
            self.body_html = html_table

        elif self.filter_report_by == 'warehouse':
            warehouse_product_details = {}
            for move in inventory_moves:
                product = move.product_id
                warehouse = move.warehouse_id

                if warehouse not in warehouse_product_details:
                    warehouse_product_details[warehouse] = {}

                if product not in warehouse_product_details[warehouse]:
                    warehouse_product_details[warehouse][product] = {
                        'name': product.name,
                        'quantity_sold': quantity_sold,
                        'cogs': cogs,
                        'average_inventory': average_inventory,
                        'turnover_ratio': turnover_ratio,
                    }
                else:
                    warehouse_product_details[warehouse][product]['quantity_sold'] += quantity_sold
                    warehouse_product_details[warehouse][product]['cogs'] += cogs

            html_table = '<table style="border-collapse: collapse; width: 100%;">'
            for warehouse, products in warehouse_product_details.items():
                html_table += f'<tr><th colspan="5" style="border: 1px solid black; padding: 8px;">Warehouse: {warehouse.name}</th></tr>'
                html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product</th>'
                html_table += '<th style="border: 1px solid black; padding: 8px;">Quantity Sold</th>'
                html_table += '<th style="border: 1px solid black; padding: 8px;">COGS</th>'
                html_table += '<th style="border: 1px solid black; padding: 8px;">Average Inventory</th>'
                html_table += '<th style="border: 1px solid black; padding: 8px;">Turnover Ratio</th></tr>'

                for details in products.values():
                    html_table += '<tr>'
                    html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["name"]}</td>'
                    html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["quantity_sold"]}</td>'
                    html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["cogs"]}</td>'
                    html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["average_inventory"]}</td>'
                    html_table += f'<td style="border: 1px solid black; padding: 8px;">{details["turnover_ratio"]}</td>'
                    html_table += '</tr>'
            html_table += '</table>'
            self.body_html = html_table

    def get_product_details(self):
        filters = [('state', '=', 'done')]
        if self.start_date:
            filters.append(('date', '>=', self.start_date))
        if self.end_date:
            filters.append(('date', '<=', self.end_date))
        if self.warehouse_ids:
            filters.append(('warehouse_id', 'in', self.warehouse_ids.ids))
        if self.product_ids:
            filters.append(('product_id', 'in', self.product_ids.ids))

        inventory_moves = self.env['stock.move'].search(filters)

        product_details = {}
        for move in inventory_moves:
            product = move.product_id
            quantity_sold = move.product_uom_qty
            cogs = product.standard_price * quantity_sold
            average_inventory = product.standard_price

            if average_inventory:
                turnover_ratio = cogs / average_inventory
            else:
                turnover_ratio = 0.0

            if product not in product_details:
                product_details[product] = {
                    'name': product.name,
                    'quantity_sold': quantity_sold,
                    'cogs': cogs,
                    'average_inventory': average_inventory,
                    'turnover_ratio': turnover_ratio,
                }
            else:
                product_details[product]['quantity_sold'] += quantity_sold
                product_details[product]['cogs'] += cogs

        return product_details

    @api.model
    def get_product_details_js(self):
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        filters = [('state', '=', 'done')]
        if self.start_date:
            filters.append(('date', '>=', self.start_date))
        if self.end_date:
            filters.append(('date', '<=', self.end_date))
        if self.warehouse_ids:
            filters.append(('warehouse_id', 'in', self.warehouse_ids.ids))
        if self.product_ids:
            filters.append(('product_id', 'in', self.product_ids.ids))

        inventory_moves = self.env['stock.move'].read_group(filters, fields=['product_id', 'product_uom_qty'], groupby=['product_id'], lazy=False)

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
