# Report to know which products have expired or are about to expire.

from odoo import models, fields, api, _
import xlwt
from io import BytesIO
from datetime import datetime, time
import base64
try:
    import tabulate
except:
    from pip._internal import main as pipmain

    pipmain(['install', 'tabulate'])


class StockExpiry(models.TransientModel):
    _name = 'stock.expiry'
    _description = 'Stock Expiry/Expired Report'

    report_type = fields.Selection([
        ('expiry', 'Stock Expiry'),
        ('expired', 'Stock Expired')
    ], string='Report Type', default='expiry')
    start_date = fields.Date(string='Start Date', required=True, default=fields.Date.today())
    end_date = fields.Date(string='End Date', required=True, default=fields.Date.today())
    body_html = fields.Html(render_engine='qweb', sanitize_style=True, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = _('Stock Expiry/Expired Report')
            res.append((record.id, name))
        return res

    def _get_filtered_products(self):
        number_of_days = (self.end_date - self.start_date).days
        domain = [('expiration_time', '<=', number_of_days)]
        if self.report_type == 'expiry':
            domain.append(('expiration_time', '>=', number_of_days))
        else:
            domain.append(('expiration_time', '<', number_of_days))
        return self.env['product.product'].search(domain)

    def generate_report_preview(self):
        filtered_products = self._get_filtered_products()

        report_name = 'Stock Expiry Report' if self.report_type == 'expiry' else 'Stock Expired Report'

        product_data = []
        for product in filtered_products:
            product_data.append([product.name, datetime.fromtimestamp(product.expiration_time).strftime('%Y-%m-%d')])

        self.body_html = tabulate(product_data, headers=['Product', 'Expiry Date'], tablefmt='html')

    def generate_xls_report(self):
        filtered_products = self._get_filtered_products()

        report_name = 'Stock Expiry Report' if self.report_type == 'expiry' else 'Stock Expired Report'

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(report_name)

        heading_style = xlwt.easyxf('font: bold on; align: horiz center;')
        worksheet.write_merge(0, 0, 0, 1, report_name, heading_style)

        header_style = xlwt.easyxf('font: bold on;')

        worksheet.write(2, 0, 'Product', header_style)
        worksheet.write(2, 1, 'Expiry Date', header_style)

        row = 3
        for product in filtered_products:
            worksheet.write(row, 0, product.name)
            worksheet.write(row, 1, datetime.fromtimestamp(product.expiration_time).strftime('%Y-%m-%d'))
            row += 1

        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = f"{report_name}.xls"
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
        if self.report_type == 'expiry':
            report_ref = 'inventory_reports_adv_axis.stock_expiry_pdf_report'
        else:
            report_ref = 'inventory_reports_adv_axis.stock_expired_pdf_report'

        return self.env.ref(report_ref).report_action(self)

    @api.model
    def stock_expire_data_js(self,activeid):
        self = self.env['stock.expiry'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        number_of_days = (self.end_date - self.start_date).days
        domain = [('expiration_time', '<=', number_of_days)]
        if self.report_type == 'expiry':
            domain.append(('expiration_time', '>=', number_of_days))
        else:
            domain.append(('expiration_time', '<', number_of_days))
        products = self.env['product.product'].search(domain)
        for product in products:
            productname = product.display_name
            expiration_time = product.expiration_time

            payroll_label.append(productname)
            payroll_dataset.append(expiration_time)

        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set
