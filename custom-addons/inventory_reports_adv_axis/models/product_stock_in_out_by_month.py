import xlwt
from io import BytesIO
import base64
import calendar
try:
    import pandas
except:
    from pip._internal import main as pipmain

    pipmain(['install', 'pandas'])
from odoo import fields, models, api, _
from pandas.tseries.offsets import MonthEnd
from datetime import datetime, timedelta
import pandas as pd
from odoo.tools import config, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat

class ProductInOutStock(models.TransientModel):
    _name = 'product.in.out.stock'
    _rec_name ='start_date'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    body_html = fields.Html(render_engine='qweb', sanitize_style=True, readonly=True)

    def get_pdf_data(self):
        start_date = fields.Date.to_date(self.start_date).replace(day=1)
        end_date = fields.Date.to_date(self.end_date).replace(
            day=calendar.monthrange(self.end_date.year, self.end_date.month)[1])
        prev_last = fields.Date.to_date(self.start_date) - timedelta(days=1)
        prev_first = prev_last.replace(day=1)
        product_data_list = []
        product_avegare_list = []
        product_avg_dict = {}
        stockmoveline = self.env['stock.move.line']
        count = 0
        for beg in pd.date_range(start_date, end_date, freq='MS'):
            product_data_list_monthwise = []
            count = count + 1
            print(beg.strftime(DEFAULT_SERVER_DATE_FORMAT), (beg + MonthEnd(1)).strftime(DEFAULT_SERVER_DATE_FORMAT))
            start_date_m = beg.strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date_m = (beg + MonthEnd(1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            res_out = stockmoveline.read_group(
                [('date', '>=', start_date_m), ('date', '<=', end_date_m), ('state', '=', 'done'),
                 ('picking_type_id.code', '=', 'outgoing')], ['product_id', 'qty_done', 'date'],
                groupby=['product_id', 'date:month'], orderby='id DESC')

            for res1 in res_out:
                molprod = res1['product_id'][0]
                product_object = self.env['product.product'].sudo().browse(molprod)
                res_in = stockmoveline.read_group(
                    [('date', '>=', start_date_m), ('date', '<=', end_date_m), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'incoming'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_res_in = stockmoveline.read_group(
                    [('date', '>=', prev_first), ('date', '<=', prev_last), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'incoming'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_res_out = stockmoveline.read_group(
                    [('date', '>=', prev_first), ('date', '<=', prev_last), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'outgoing'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_stock = prev_res_in[0].get('qty_done') if prev_res_in else 0 - prev_res_out[0].get(
                    'qty_done') if prev_res_out else 0
                avail_stock = res_in[0].get('qty_done') if res_in else 0 - res1.get('qty_done') if res1 else 0
                if fields.Date.to_date(start_date_m) - timedelta(days=1) == prev_last:
                    intial_stock = prev_stock
                else:
                    intial_stock = avail_stock
                product_data_dict = {
                    'start_date': fields.Date.to_date(start_date_m).strftime('%B') + ' - ' + fields.Date.to_date(
                        start_date_m).strftime('%Y'), 'product_id': product_object.display_name,
                    'category': product_object.categ_id.display_name, 'intial_stock': intial_stock,
                    'in_qty': res_in[0].get('qty_done') if res_in else 0,
                    'out_qty': res1.get('qty_done') if res1 else 0, 'total_stock': intial_stock,
                    'in_qty': intial_stock + res_in[0].get('qty_done') if res_in else 0 - res1.get(
                        'qty_done') if res1 else 0}
                if product_object not in product_avg_dict:
                    product_avg_dict[product_object] = res1.get('qty_done') if res1 else 0
                else:
                    product_avg_dict[product_object] += res1.get('qty_done') if res1 else 0
                    if count > 1:
                        product_avg_dict[product_object] = product_avg_dict[product_object] / count

                product_data_list_monthwise.append(product_data_dict)
            product_data_list.append(product_data_list_monthwise)

        return product_data_list,product_avg_dict


    def generate_xls_report(self):
        start_date = fields.Date.to_date(self.start_date).replace(day=1)
        end_date = fields.Date.to_date(self.end_date).replace(
            day=calendar.monthrange(self.end_date.year, self.end_date.month)[1])
        prev_last = fields.Date.to_date(self.start_date) - timedelta(days=1)
        prev_first = prev_last.replace(day=1)
        product_data_list = []
        product_avegare_list = []
        product_avg_dict = {}
        stockmoveline = self.env['stock.move.line']
        count = 0
        for beg in pd.date_range(start_date, end_date, freq='MS'):
            product_data_list_monthwise = []
            count = count + 1
            print(beg.strftime(DEFAULT_SERVER_DATE_FORMAT), (beg + MonthEnd(1)).strftime(DEFAULT_SERVER_DATE_FORMAT))
            start_date_m = beg.strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date_m = (beg + MonthEnd(1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            res_out = stockmoveline.read_group(
                [('date', '>=', start_date_m), ('date', '<=', end_date_m), ('state', '=', 'done'),
                 ('picking_type_id.code', '=', 'outgoing')], ['product_id', 'qty_done', 'date'],
                groupby=['product_id', 'date:month'], orderby='id DESC')

            for res1 in res_out:
                molprod = res1['product_id'][0]
                product_object = self.env['product.product'].sudo().browse(molprod)
                res_in = stockmoveline.read_group(
                    [('date', '>=', start_date_m), ('date', '<=', end_date_m), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'incoming'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_res_in = stockmoveline.read_group(
                    [('date', '>=', prev_first), ('date', '<=', prev_last), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'incoming'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_res_out = stockmoveline.read_group(
                    [('date', '>=', prev_first), ('date', '<=', prev_last), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'outgoing'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_stock = prev_res_in[0].get('qty_done') if prev_res_in else 0 - prev_res_out[0].get(
                    'qty_done') if prev_res_out else 0
                avail_stock = res_in[0].get('qty_done') if res_in else 0 - res1.get('qty_done') if res1 else 0
                if fields.Date.to_date(start_date_m) - timedelta(days=1) == prev_last:
                    intial_stock = prev_stock
                else:
                    intial_stock = avail_stock
                product_data_dict = {
                    'start_date': fields.Date.to_date(start_date_m).strftime('%B') + ' - ' + fields.Date.to_date(
                        start_date_m).strftime('%Y'), 'product_id': product_object.display_name,
                    'category': product_object.categ_id.display_name, 'intial_stock': intial_stock,
                    'in_qty': res_in[0].get('qty_done') if res_in else 0,
                    'out_qty': res1.get('qty_done') if res1 else 0, 'total_stock': intial_stock,
                    'in_qty': intial_stock + res_in[0].get('qty_done') if res_in else 0 - res1.get(
                        'qty_done') if res1 else 0}
                if product_object not in product_avg_dict:
                    product_avg_dict[product_object] = res1.get('qty_done') if res1 else 0
                else:
                    product_avg_dict[product_object] += res1.get('qty_done') if res1 else 0
                    if count > 1:
                        product_avg_dict[product_object] = product_avg_dict[product_object] / count

                product_data_list_monthwise.append(product_data_dict)
            product_data_list.append(product_data_list_monthwise)
        # Create the report
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Stock In Out Analysis')

        heading_style = xlwt.easyxf('font: bold on; align: horiz center;')
        worksheet.write_merge(0, 0, 0, 4, 'Inventory Stock In Out Analysis Report', heading_style)
        worksheet.write_merge(1, 1, 0, 1, 'Date:', xlwt.easyxf('font: bold on;'))
        worksheet.write_merge(1, 1, 2, 3, str(self.start_date)+'-->'+ str(self.end_date))

        header_style = xlwt.easyxf('font: bold on;')

        row = 3
        worksheet.write(row, 0, 'Product', header_style)
        worksheet.write(row, 1, 'Category', header_style)
        worksheet.write(row, 2, 'Intial stock', header_style)
        worksheet.write(row, 3, 'In stock', header_style)
        worksheet.write(row, 4, 'Out stock', header_style)
        row += 1
        print ("=============",product_data_list)
        for analysis in product_data_list:
            # print ("----start date--------",analysis)
            if analysis:
                print ("----start date--------",analysis[0].get("start_date"))
                worksheet.write(row, 0, analysis[0].get("start_date"),header_style)
            # else:
                # worksheet.write(row, 0, str(self.start_date),header_style)
            row += 1
            for data in analysis:
                worksheet.write(row, 0, data['product_id'])
                worksheet.write(row, 1, data['category'])
                worksheet.write(row, 2, data['intial_stock'])
                worksheet.write(row, 3, data['in_qty'])
                worksheet.write(row, 4, data['out_qty'])
                row += 1
        worksheet.write(row, 0,'Average out Stock', heading_style)
        row += 1
        for k, v in product_avg_dict.items():
            worksheet.write(row, 0, k.display_name)
            worksheet.write(row, 1, v)

            row += 1


        report_file = BytesIO()
        workbook.save(report_file)
        report_file.seek(0)

        filename = 'inventory_stock_inout.xls'
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
        return self.env.ref('inventory_reports_adv_axis.inv_valuation_stock_in_out_pdf_report').report_action(self, config=False)

    def generate_report_preview(self):
        start_date = fields.Date.to_date(self.start_date).replace(day=1)
        end_date = fields.Date.to_date(self.end_date).replace(
            day=calendar.monthrange(self.end_date.year, self.end_date.month)[1])
        prev_last = fields.Date.to_date(self.start_date) - timedelta(days=1)
        prev_first = prev_last.replace(day=1)
        product_data_list = []
        product_avegare_list = []
        product_avg_dict = {}
        stockmoveline = self.env['stock.move.line']
        count = 0
        for beg in pd.date_range(start_date, end_date, freq='MS'):
            product_data_list_monthwise = []
            count = count + 1
            print(beg.strftime(DEFAULT_SERVER_DATE_FORMAT), (beg + MonthEnd(1)).strftime(DEFAULT_SERVER_DATE_FORMAT))
            start_date_m = beg.strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date_m = (beg + MonthEnd(1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            res_out = stockmoveline.read_group(
                [('date', '>=', start_date_m), ('date', '<=', end_date_m), ('state', '=', 'done'),
                 ('picking_type_id.code', '=', 'outgoing')], ['product_id', 'qty_done', 'date'],
                groupby=['product_id', 'date:month'], orderby='id DESC')

            for res1 in res_out:
                molprod = res1['product_id'][0]
                product_object = self.env['product.product'].sudo().browse(molprod)
                res_in = stockmoveline.read_group(
                    [('date', '>=', start_date_m), ('date', '<=', end_date_m), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'incoming'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_res_in = stockmoveline.read_group(
                    [('date', '>=', prev_first), ('date', '<=', prev_last), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'incoming'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_res_out = stockmoveline.read_group(
                    [('date', '>=', prev_first), ('date', '<=', prev_last), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'outgoing'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_stock = prev_res_in[0].get('qty_done') if prev_res_in else 0 - prev_res_out[0].get(
                    'qty_done') if prev_res_out else 0
                avail_stock = res_in[0].get('qty_done') if res_in else 0 - res1.get('qty_done') if res1 else 0
                if fields.Date.to_date(start_date_m) - timedelta(days=1) == prev_last:
                    intial_stock = prev_stock
                else:
                    intial_stock = avail_stock
                product_data_dict = {
                    'start_date': fields.Date.to_date(start_date_m).strftime('%B') + ' - ' + fields.Date.to_date(
                        start_date_m).strftime('%Y'), 'product_id': product_object.display_name,
                    'category': product_object.categ_id.display_name, 'intial_stock': intial_stock,
                    'in_qty': res_in[0].get('qty_done') if res_in else 0,
                    'out_qty': res1.get('qty_done') if res1 else 0, 'total_stock': intial_stock,
                    'in_qty': intial_stock + res_in[0].get('qty_done') if res_in else 0 - res1.get(
                        'qty_done') if res1 else 0}
                if product_object not in product_avg_dict:
                    product_avg_dict[product_object] = res1.get('qty_done') if res1 else 0
                else:
                    product_avg_dict[product_object] += res1.get('qty_done') if res1 else 0
                    if count > 1:
                        product_avg_dict[product_object] = product_avg_dict[product_object] / count

                product_data_list_monthwise.append(product_data_dict)
            product_data_list.append(product_data_list_monthwise)
            html_table = '<table style="border-collapse: collapse; width: 100%;">'
            html_table += '<tr><th style="border: 1px solid black; padding: 8px;color: black;font-family:"Roboto-Bold";">Product Name</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;color: black;font-family:"Roboto-Bold";">Category</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;color: black;font-family:"Roboto-Bold";">Intial stock</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;color: black;font-family:"Roboto-Bold";">In Stock</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;color: black;font-family:"Roboto-Bold";">Out Stock</th>'
            html_table += '<th style="border: 1px solid black; padding: 8px;color: black;font-family:"Roboto-Bold";">Stock</th>'
            # html_table += '<th style="border: 1px solid black; padding: 8px;">Class</th>'
            html_table += '</tr>'
            total_out_stock = 0
            for monthwise in product_data_list:
                # total_out_stock +=  0
                if monthwise:
                    html_table += '<tr>'
                    html_table += f'<td colspan=6 style="font-size: large;border: 1px solid black; padding: 8px;text-align:center"><b>{monthwise[0].get("start_date")}</b></td>'

                    html_table += '</tr>'
                for data in monthwise:
                    total_out_stock += data["out_qty"]
                    html_table += '<tr>'
                    html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["product_id"]}</td>'
                    html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["category"]}</td>'
                    html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["intial_stock"]}</td>'
                    html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["in_qty"]}</td>'
                    html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["out_qty"]}</td>'
                    html_table += f'<td style="border: 1px solid black; padding: 8px;">{data["total_stock"]}</td>'
                    # html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[4]}</td>'
                    html_table += '</tr>'



            html_table += '</table>'
            self.body_html = html_table

            html_table += '<tr>'
            html_table += f'<td colspan=6 style="border: 1px solid black; padding: 8px;text-align:center;color: blueviolet;FONT-SIZE: large;"><b style="color: blueviolet;font-size: large;">Average Stock Of out</b></td>'
            html_table += '</tr>'

            html_table1 = '<table style="border-collapse: collapse; width: 100%;">'
            for k,v in product_avg_dict.items():

                html_table1 += '<tr>'
                html_table1 += f'<td style="border: 1px solid black; padding: 8px;">{k.display_name}</td>'
                html_table1 += f'<td style="border: 1px solid black; padding: 8px;">{v}</td>'

                # html_table += f'<td style="border: 1px solid black; padding: 8px;">{data[4]}</td>'
                html_table1 += '</tr>'
            html_table1 += '</table>'

            self.body_html = html_table + html_table1

    @api.model
    def product_in_data_js(self,activeid):
        self = self.env['product.in.out.stock'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        start_date = fields.Date.to_date(self.start_date).replace(day=1)
        end_date = fields.Date.to_date(self.end_date).replace(
            day=calendar.monthrange(self.end_date.year, self.end_date.month)[1])
        prev_last = fields.Date.to_date(self.start_date) - timedelta(days=1)
        prev_first = prev_last.replace(day=1)
        product_data_list = []
        product_avegare_list = []
        product_avg_dict = {}
        stockmoveline = self.env['stock.move.line']
        count = 0
        for beg in pd.date_range(start_date, end_date, freq='MS'):
            product_data_list_monthwise = []
            count = count + 1
            print(beg.strftime(DEFAULT_SERVER_DATE_FORMAT), (beg + MonthEnd(1)).strftime(DEFAULT_SERVER_DATE_FORMAT))
            start_date_m = beg.strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date_m = (beg + MonthEnd(1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            res_out = stockmoveline.read_group(
                [('date', '>=', start_date_m), ('date', '<=', end_date_m), ('state', '=', 'done'),
                 ('picking_type_id.code', '=', 'outgoing')], ['product_id', 'qty_done', 'date'],
                groupby=['product_id', 'date:month'], orderby='id DESC')

            for res1 in res_out:
                molprod = res1['product_id'][0]
                product_object = self.env['product.product'].sudo().browse(molprod)
                res_in = stockmoveline.read_group(
                    [('date', '>=', start_date_m), ('date', '<=', end_date_m), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'incoming'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_res_in = stockmoveline.read_group(
                    [('date', '>=', prev_first), ('date', '<=', prev_last), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'incoming'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_res_out = stockmoveline.read_group(
                    [('date', '>=', prev_first), ('date', '<=', prev_last), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'outgoing'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_stock = prev_res_in[0].get('qty_done') if prev_res_in else 0 - prev_res_out[0].get(
                    'qty_done') if prev_res_out else 0
                avail_stock = res_in[0].get('qty_done') if res_in else 0 - res1.get('qty_done') if res1 else 0
                if fields.Date.to_date(start_date_m) - timedelta(days=1) == prev_last:
                    intial_stock = prev_stock
                else:
                    intial_stock = avail_stock
                payroll_label.append(product_object.display_name)
                payroll_dataset.append(res_in[0].get('qty_done') if res_in else 0)
        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set


    @api.model
    def product_out_data_js(self,activeid):
        self = self.env['product.in.out.stock'].browse(int(activeid))
        data_set = {}
        payroll_label = []
        payroll_dataset = []
        start_date = fields.Date.to_date(self.start_date).replace(day=1)
        end_date = fields.Date.to_date(self.end_date).replace(
            day=calendar.monthrange(self.end_date.year, self.end_date.month)[1])
        prev_last = fields.Date.to_date(self.start_date) - timedelta(days=1)
        prev_first = prev_last.replace(day=1)
        product_data_list = []
        product_avegare_list = []
        product_avg_dict = {}
        stockmoveline = self.env['stock.move.line']
        count = 0
        for beg in pd.date_range(start_date, end_date, freq='MS'):
            product_data_list_monthwise = []
            count = count + 1
            print(beg.strftime(DEFAULT_SERVER_DATE_FORMAT), (beg + MonthEnd(1)).strftime(DEFAULT_SERVER_DATE_FORMAT))
            start_date_m = beg.strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date_m = (beg + MonthEnd(1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            res_out = stockmoveline.read_group(
                [('date', '>=', start_date_m), ('date', '<=', end_date_m), ('state', '=', 'done'),
                 ('picking_type_id.code', '=', 'outgoing')], ['product_id', 'qty_done', 'date'],
                groupby=['product_id', 'date:month'], orderby='id DESC')

            for res1 in res_out:
                molprod = res1['product_id'][0]
                product_object = self.env['product.product'].sudo().browse(molprod)
                res_in = stockmoveline.read_group(
                    [('date', '>=', start_date_m), ('date', '<=', end_date_m), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'incoming'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_res_in = stockmoveline.read_group(
                    [('date', '>=', prev_first), ('date', '<=', prev_last), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'incoming'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_res_out = stockmoveline.read_group(
                    [('date', '>=', prev_first), ('date', '<=', prev_last), ('state', '=', 'done'),
                     ('picking_type_id.code', '=', 'outgoing'), ('product_id', '=', molprod)],
                    ['product_id', 'qty_done'],
                    groupby=['product_id', 'date:month'], orderby='id DESC')
                prev_stock = prev_res_in[0].get('qty_done') if prev_res_in else 0 - prev_res_out[0].get(
                    'qty_done') if prev_res_out else 0
                avail_stock = res_in[0].get('qty_done') if res_in else 0 - res1.get('qty_done') if res1 else 0
                if fields.Date.to_date(start_date_m) - timedelta(days=1) == prev_last:
                    intial_stock = prev_stock
                else:
                    intial_stock = avail_stock

                payroll_label.append(product_object.display_name)
                payroll_dataset.append(res1.get('qty_done') if res1 else 0)
        data_set.update({"payroll_dataset": payroll_dataset})
        data_set.update({"payroll_label": payroll_label})
        return data_set





