# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
import base64
import os
from datetime import datetime,date
from datetime import *
from io import BytesIO
import xlsxwriter
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from xlsxwriter.utility import xl_col_to_name
from pytz import timezone
from odoo.tools import config
import string
import random
from num2words import num2words
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import xlwt
import pytz


class PosExcel(models.TransientModel):
    _inherit = "pos.details.wizard"

    file = fields.Binary()


    def print_excel_report(self):
        file_name = _('Product.xlsx')
        fp = BytesIO()
        workbook = xlwt.Workbook()
        workbook = xlsxwriter.Workbook(os.path.join(config['data_dir'], 'Product.xlsx'))
        worksheet = workbook.add_worksheet('Product')
        worksheet_payment = workbook.add_worksheet('Payment')
        worksheet_tax = workbook.add_worksheet('Tax')
        worksheet_total = workbook.add_worksheet('Final Totals')
        session_total_formate = workbook.add_format({'align': 'center',
                                        'bold': True,
                                        'valign': 'vcenter',
                                        'size': 10,
                                        'bg_color':'gray',
                                        'text_wrap': True,
                                        })
        session_total_formate.set_border()
        session_total_formate1 = workbook.add_format({'align': 'center'})
        session_total_formate2 = workbook.add_format({'align': 'center',
                                        'bold': True,
                                        'valign': 'vcenter',
                                        'size': 10,
                                        'color':'green',
                                        'text_wrap': True,
                                        })
        worksheet.merge_range('A1:G5', '%s\nSales Details\n%s - %s'%(self.env.user.company_id.name,self.start_date,self.end_date), session_total_formate2)
        worksheet_payment.merge_range('A1:C3', 'Payment', session_total_formate2)
        worksheet_tax.merge_range('A1:D3', 'Tax', session_total_formate2)
        worksheet_total.merge_range('A1:D3', 'Total Amounts', session_total_formate2)
        row = 5
        worksheet.write(row, 0, 'No',session_total_formate)
        worksheet.set_column('A:A', 10)
        worksheet.set_row(5,30)
        worksheet.write(row, 1, 'Product',session_total_formate)
        worksheet.set_column('B:B', 30)
        worksheet.write(row, 2, 'Qty',session_total_formate)
        worksheet.set_column('C:C', 10)
        worksheet.write(row, 3, 'Unit Price',session_total_formate)
        worksheet.set_column('D:D', 10)
        worksheet.write(row, 4, 'Discounts',session_total_formate)
        worksheet.set_column('E:E', 10)
        worksheet.write(row, 5, 'Unit of Mesaure',session_total_formate)
        worksheet.set_column('F:F', 20)
        worksheet.write(row, 6, 'Subtotal(Discounts Deducted)',session_total_formate)
        worksheet.write(row, 7, 'Name Field',session_total_formate)
        worksheet.set_column('G:G', 20)
        configs = self.pos_config_ids
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
        today = today.astimezone(pytz.timezone('UTC'))
        if self.start_date:
            date_start = fields.Datetime.from_string(self.start_date)
        else:
            date_start = today
        if self.end_date:
            date_stop = fields.Datetime.from_string(self.end_date)
        else:
            date_stop = today + timedelta(days=1, seconds=-1)
        date_stop = max(date_stop, date_start)
        date_start = fields.Datetime.to_string(date_start)
        date_stop = fields.Datetime.to_string(date_stop)
        orders = self.env['pos.order'].search([
            ('date_order', '>=', date_start),
            ('date_order', '<=', date_stop),
            ('state', 'in', ['paid','invoiced','done']),
            ('config_id', 'in', configs.ids)])
        user_currency = self.env.user.company_id.currency_id
        total = 0.0
        products_sold = {}
        taxes = {}
        for order in orders:
            if user_currency != order.pricelist_id.currency_id:
                total += order.pricelist_id.currency_id._convert(
                    order.amount_total, user_currency, order.company_id, order.date_order or fields.Date.today())
            else:
                total += order.amount_total
            currency = order.session_id.currency_id
            for line in order.lines:
                key = (line.product_id, line.price_unit, line.discount , line.name_field ,line.product_uom_id)
                products_sold.setdefault(key, 0.0)
                products_sold[key] += line.qty
                if line.tax_ids_after_fiscal_position:
                    line_taxes = line.tax_ids_after_fiscal_position.compute_all(line.price_unit * (1-(line.discount or 0.0)/100.0), currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
                    for tax in line_taxes['taxes']:
                        taxes.setdefault(tax['id'], {'name': tax['name'], 'tax_amount':0.0, 'base_amount':0.0})
                        taxes[tax['id']]['tax_amount'] += tax['amount']
                        taxes[tax['id']]['base_amount'] += tax['base']
                else:
                    taxes.setdefault(0, {'name': _('No Taxes'), 'tax_amount':0.0, 'base_amount':0.0})
                    taxes[0]['base_amount'] += line.price_subtotal_incl
        payment_ids = self.env["pos.payment"].search([('pos_order_id', 'in', orders.ids)]).ids
        if payment_ids:
            self.env.cr.execute("""
                SELECT COALESCE(method.name->>%s, method.name->>'en_US') p_name, sum(amount) total
                FROM pos_payment AS payment,
                     pos_payment_method AS method
                WHERE payment.payment_method_id = method.id
                    AND payment.id IN %s
                GROUP BY method.name
            """, (self.env.lang,tuple(payment_ids),))
            payments = self.env.cr.dictfetchall()
        else:
            payments = []
        products = sorted([{
                'product_id': product.id,
                'product_name': product.name,
                'code': product.default_code,
                'quantity': qty,
                'price_unit': price_unit,
                'discount': discount,
                'uom': product.uom_id.name,
                'product_uom_id': product_uom_id.name,
                'name_field':name_field
            } for (product, price_unit, discount , name_field , product_uom_id), qty in products_sold.items()], key=lambda l: l['product_name'])    
        row = 6
        totals = 0.0
        for product_id in products:
            sub_total_disc_deducted = (product_id.get('quantity') * product_id.get('price_unit')) * (product_id.get('discount')/100)
            sub_total_disc_deducted = (product_id.get('quantity') * product_id.get('price_unit')) - sub_total_disc_deducted
            worksheet.write(row, 0,row-5,session_total_formate1)
            worksheet.write(row,1,product_id.get('product_name'),session_total_formate1)
            worksheet.write(row,2,product_id.get('quantity'),session_total_formate1)
            worksheet.write(row,3,product_id.get('price_unit'),session_total_formate1)
            worksheet.write(row,4,product_id.get('discount'),session_total_formate1)
            worksheet.write(row,5,product_id.get('product_uom_id'),session_total_formate1)
            worksheet.write(row,6,sub_total_disc_deducted)
            worksheet.write(row,7,product_id.get('name_field'),session_total_formate1)
            totals += sub_total_disc_deducted
            row +=1
        worksheet.write(row+2,5,'Total without taxes',session_total_formate1)                
        worksheet.write(row+2,6, totals)    
        row = 3
        worksheet_payment.write(row, 0, 'No',session_total_formate)
        worksheet_payment.set_column('A:A', 10)
        worksheet_payment.set_row(3,30)
        worksheet_payment.write(row, 1, 'Name',session_total_formate)
        worksheet_payment.set_column('B:B', 30)
        worksheet_payment.write(row, 2, 'Total Amounts',session_total_formate)
        worksheet.set_column('C:C', 30)
        row = 4 
        for payment in payments:
            worksheet_payment.write(row, 0,row-3,session_total_formate1)
            worksheet_payment.write(row,1,payment.get('p_name'),session_total_formate1)
            worksheet_payment.write(row,2,payment.get('total'),session_total_formate1)
            row += 1
        row = 3
        worksheet_tax.write(row, 0, 'No',session_total_formate)
        worksheet_tax.set_column('A:A', 10)
        worksheet_tax.set_row(3,30)
        worksheet_tax.write(row, 1, 'Name',session_total_formate)
        worksheet_tax.set_column('B:B', 30)
        worksheet_tax.write(row, 2, 'Tax Amount',session_total_formate)
        worksheet_tax.set_column('C:C', 30)
        worksheet_tax.write(row, 3, 'Base Amount',session_total_formate)
        worksheet_tax.set_column('D:D', 30) 
        row = 4
        for tax in taxes.values():
            worksheet_tax.write(row, 0,row-3,session_total_formate1)
            worksheet_tax.write(row,1,tax.get('name'),session_total_formate1)
            worksheet_tax.write(row,2,tax.get('tax_amount'),session_total_formate1)
            worksheet_tax.write(row,3,tax.get('base_amount'),session_total_formate1)
            row += 1
        row = 3
        worksheet_total.merge_range('A4:D6', total,session_total_formate)       
        workbook.close()
        file_download = base64.b64encode(fp.getvalue())
        fp.close()
        data_file = open(config['data_dir'] + "/Product.xlsx", "rb")
        out = data_file.read()
        data_file.close()
        self.file = base64.b64encode(out)
        return {
            'name': 'Product',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%d/file/%s?download=false' % (self._name, self.id, 'Sales Details.xlsx'),
            }