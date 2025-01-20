import random
from odoo import models, fields, _,api
import xlwt
from io import BytesIO
import base64
#from tabulate import tabulate


class XYZAnalysis(models.TransientModel):
    _name = 'xyz.analysis'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    body_html = fields.Html(render_engine='qweb',
                            sanitize_style=True, readonly=True)

    @api.model
    def xyz_data_js(self, activeid):
        self = self.env['xyz.analysis'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []

        products = self.env['product.product'].search([])

        report_data = []
        for product in products:

            payroll_label.append(product.display_name)
            payroll_dataset.append(product.standard_price * product.qty_available)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set

    def name_get(self):
        res = []
        for record in self:
            name = _('XYZ Analysis Report')
            res.append((record.id, name))
        return res

    def generate_report_preview(self):
        products = self.env['product.product'].search([])

        report_data = self._prepare_report_data(products)
        product_data = self._prepare_product_data(report_data)

        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr><th style="border: 1px solid black; padding: 8px;">Product Name</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Category</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Current Stock</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Stock Value</th>'
        html_table += '<th style="border: 1px solid black; padding: 8px;">Class</th>'
        html_table += '</tr>'

        for data in product_data:
            html_table += '<tr>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[0]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[1]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[2]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[3]}</td>'
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[4]}</td>'
            html_table += '</tr>'

        html_table += '</table>'
        self.body_html = html_table

    def generate_xls_report(self):
        # products = self.env['stock.move.line'].search([])
        start_date = fields.Date.to_date(self.start_date)
        end_date = fields.Date.to_date(self.end_date)
        products = self.env['stock.move.line'].search(
            [('date', '>=', start_date), ('date', '<=', end_date), ('state', '=', 'done')]).mapped('product_id')

        report_data = self._prepare_report_data(products)
        return self._generate_excel_report(report_data)

    def generate_pdf_report(self):
        return self.env.ref('inventory_reports_adv_axis.inventory_xyz_analysis_pdf_report').report_action(self, config=False)

    def _prepare_report_data(self, products):
        total_value = sum(product.standard_price * product.qty_available for product in products)

        class_x_threshold = total_value * 0.7
        class_y_threshold = class_x_threshold + total_value * 0.2
        class_z_threshold = class_y_threshold + total_value * 0.1

        class_x_products = []
        class_y_products = []
        class_z_products = []

        for product in products:
            product_value = product.standard_price * product.qty_available

            if product_value <= class_x_threshold:
                class_x_products.append(product)
            elif product_value <= class_y_threshold:
                class_y_products.append(product)
            else:
                class_z_products.append(product)

        report_data = {
            'class_x_products': class_x_products,
            'class_y_products': class_y_products,
            'class_z_products': class_z_products,
        }

        return report_data

    def _prepare_product_data(self, report_data):
        product_data = []
        all_products = report_data['class_x_products'] + report_data['class_y_products'] + report_data[
            'class_z_products']
        random.shuffle(all_products)

        for product in all_products:
            product_value = product.standard_price * product.qty_available

            product_data.append([product.name, product.categ_id.name, str(product.qty_available),
                                 str(product_value), self._get_product_class(product)])

        return product_data

    def _get_product_class(self, product):
        total_value = product.standard_price * product.qty_available

        class_x_threshold = total_value * 0.7
        class_y_threshold = class_x_threshold + total_value * 0.2
        class_z_threshold = class_y_threshold + total_value * 0.1

        if total_value <= class_x_threshold:
            return 'X'
        elif total_value <= class_y_threshold:
            return 'Y'
        else:
            return 'Z'

    def _generate_excel_report(self, report_data):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('XYZ Analysis')

        header_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')

        worksheet.write_merge(0, 0, 0, 4, 'XYZ Analysis Report', header_style)
        worksheet.write(2, 0, 'Product Name', header_style)
        worksheet.write(2, 1, 'Category', header_style)
        worksheet.write(2, 2, 'Current Stock', header_style)
        worksheet.write(2, 3, 'Stock Value', header_style)
        worksheet.write(2, 4, 'Class', header_style)

        row = 3
        all_products = report_data['class_x_products'] + report_data['class_y_products'] + report_data[
            'class_z_products']
        random.shuffle(all_products)

        for product in all_products:
            product_value = product.standard_price * product.qty_available

            worksheet.write(row, 0, product.name, cell_style)
            worksheet.write(row, 1, product.categ_id.name, cell_style)
            worksheet.write(row, 2, product.qty_available, cell_style)
            worksheet.write(row, 3, product_value, cell_style)

            if product in report_data['class_x_products']:
                worksheet.write(row, 4, 'X', cell_style)
            elif product in report_data['class_y_products']:
                worksheet.write(row, 4, 'Y', cell_style)
            elif product in report_data['class_z_products']:
                worksheet.write(row, 4, 'Z', cell_style)

            row += 1

        worksheet.col(0).width = 5000
        worksheet.col(1).width = 5000
        worksheet.col(2).width = 5000
        worksheet.col(3).width = 5000
        worksheet.col(4).width = 5000

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'XYZ Analysis Report.xls'
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
