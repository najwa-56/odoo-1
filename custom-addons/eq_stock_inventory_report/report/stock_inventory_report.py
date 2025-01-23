# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

import pytz
import time
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, date


class eq_stock_inventory_report_stock_inventory_report(models.AbstractModel):
    _name = 'report.eq_stock_inventory_report.stock_inventory_report'
    _description = "Report Stock Inventory"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('eq_stock_inventory_report.stock_inventory_template_report')
        record_id = data['form']['id'] if data and data['form'] and data['form']['id'] else docids[0]
        records = self.env['wizard.stock.inventory'].browse(record_id)
        return {
           'doc_model': report.model,
           'docs': records,
           'data': data,
           'get_location_wise_product':self.get_location_wise_product,
           'get_product_valuation_data':self.get_product_valuation_data
        }

    def get_location_wise_product(self, record, warehouse, location_ids):
        product_ids = self._get_products(record)
        product_datas = {}
        lst = ['product_qty_out','product_qty_in','product_qty_internal','product_qty_adjustment']
        warehouse_wise_locations = self.get_location(record, warehouse)
        location_ids = location_ids.filtered(lambda l:l.id in warehouse_wise_locations)

        for product in product_ids:
            location_data_lst = []
            location_header_data = []
            product_datas.setdefault(product,{'location_wise_data':[],'location_header_data':[]})
            location_header_data_dict = {'beg_qty':0,'product_qty_in':0,'product_qty_out':0,
                'product_qty_internal':0,'product_qty_adjustment':0,'product_ending_qty':0,'product_id':product}
            for location in location_ids:
                product_beg_qty_data = self._get_beginning_inventory(record,product.ids,warehouse,location.ids)
                product_inventory_movement_data = self.get_product_sale_qty(record,warehouse,product.ids,location.ids)
                beg_qty = product_beg_qty_data.get(product.id,0)
                location_data_dict = {'beg_qty':beg_qty,'product_qty_in':0,'product_qty_out':0,'product_qty_internal':0,
                    'product_qty_adjustment':0,'product_ending_qty':beg_qty,'location_id':location}
                location_header_data_dict['beg_qty'] += beg_qty
                location_header_data_dict['product_ending_qty'] += beg_qty
                product_sale_data = product_inventory_movement_data.get(product.id) or {}
                for each in lst:
                    value = product_sale_data.get(each,0)
                    location_data_dict[each] = value
                    location_data_dict['product_ending_qty'] += value
                    location_header_data_dict[each] += value
                    location_header_data_dict['product_ending_qty'] += value
                location_data_lst.append(location_data_dict)

            location_header_data.append(location_header_data_dict)
            product_datas[product]['location_wise_data'] +=location_data_lst
            product_datas[product]['location_header_data'] +=location_header_data

        if record.group_by_categ:
            product_datas_with_product_category = {}
            for key,value in product_datas.items():
                product_datas_with_product_category.setdefault(key.categ_id,{})
                product_datas_with_product_category[key.categ_id].update({key:value})
            return product_datas_with_product_category
        return product_datas

    def get_product_valuation_data(self,record,warehouse):
        product_ids = self._get_products(record)
        product_beg_qty_data = self._get_beginning_inventory(record,product_ids.ids,warehouse)
        product_inventory_movement_data = self.get_product_sale_qty(record,warehouse,product_ids.ids)

        lst = ['product_qty_out','product_qty_in','product_qty_internal','product_qty_adjustment']
        product_datas = {}
        for product in product_ids:
            product_datas.setdefault(product,{'beg_qty':0,'product_qty_in':0,'product_qty_out':0,'product_qty_internal':0,
                'product_qty_adjustment':0,'product_ending_qty':0.00})
            beg_qty = product_beg_qty_data.get(product.id,0)
            product_datas[product]['beg_qty'] = beg_qty
            product_datas[product]['product_ending_qty'] += beg_qty
            if product_inventory_movement_data:
                product_sale_data = product_inventory_movement_data.get(product.id) or {}
                for each in lst:
                    value = product_sale_data.get(each,0)
                    product_datas[product][each] = value
                    product_datas[product]['product_ending_qty'] += value
        if record.group_by_categ:
            product_datas_with_product_category = {}
            for key,value in product_datas.items():
                product_datas_with_product_category.setdefault(key.categ_id,{})
                product_datas_with_product_category[key.categ_id].update({key:value})
            return product_datas_with_product_category
        return product_datas

    def get_warehouse_wise_location(self, record, warehouse):
        stock_location_obj = self.env['stock.location']
        location_ids = stock_location_obj.search([('location_id', 'child_of', warehouse.view_location_id.id)])
        final_location_ids = record.location_ids & location_ids
        return final_location_ids or location_ids

    def get_location(self, records, warehouse):
        stock_location_obj = self.env['stock.location'].sudo()
        location_ids = []
        location_ids.append(warehouse.view_location_id.id)
        domain = [('company_id', '=', records.company_id.id), ('usage', '=', 'internal'), ('location_id', 'child_of', location_ids)]
        return stock_location_obj.search(domain).ids

    def convert_withtimezone(self, userdate):
        timezone = pytz.timezone(self._context.get('tz') or 'UTC')
        if timezone:
            utc = pytz.timezone('UTC')
            end_dt = timezone.localize(fields.Datetime.from_string(userdate),is_dst=False)
            end_dt = end_dt.astimezone(utc)
            return end_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return userdate.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    def _get_products(self, record):
        domain = [('type', '=', 'product')]
        if record.product_ids:
            return record.product_ids
        if record.category_ids:
            domain.append(('categ_id', 'in', record.category_ids.ids))
        return self.env['product.product'].search(domain) or False

    def _get_beginning_inventory(self, record, product, warehouse, location=None):
        locations_ids = location if location else self.get_location(record, warehouse)
        from_date = self.convert_withtimezone((record.start_date.strftime("%Y-%m-%d")  + ' 00:00:00'))
        warehouse_wise_locations = self.get_location(record, warehouse)
        locations = self.get_unique_locations(warehouse_wise_locations,locations_ids)
        query = """
            SELECT pp.id as product_id,
            sum((
                CASE WHEN smline.location_id in %s
                THEN (smline.quantity * pu.factor / u.factor)
                ELSE 0.0 
                END
                )) AS product_beg_out_qty,

            sum((
                CASE WHEN smline.location_dest_id in %s
                THEN (smline.quantity * pu.factor / u.factor)
                ELSE 0.0 
                END
                )) AS product_beg_in_qty

            FROM product_product pp
            LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
            LEFT JOIN stock_move_line smline ON (smline.product_id = pp.id)
            LEFT JOIN uom_uom pu ON (pt.uom_id=pu.id)
            LEFT JOIN uom_uom u ON (smline.product_uom_id=u.id)
            WHERE smline.state='done' AND smline.date <  %s AND pp.active=True AND pp.id in %s

            GROUP BY pp.id
        """
        params = [tuple(locations),tuple(locations),from_date,tuple(product)]
        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        product_beg_qty_data = {}
        for each in result:
            product_beg_qty_data.setdefault(each['product_id'],(each['product_beg_in_qty'] - each['product_beg_out_qty']))
        return product_beg_qty_data

    def get_unique_locations(self,warehouse_wise_locations,locations_ids):
        locations = []
        for each_loc in locations_ids:
            if each_loc in warehouse_wise_locations:
                locations.append(each_loc)
        return locations

    def get_product_sale_qty(self, record, warehouse, product, location=None):
        product_data = tuple(product)
        if not product_data:
            return
        locations_ids = location if location else self.get_location(record, warehouse)
        start_date = self.convert_withtimezone((record.start_date.strftime("%Y-%m-%d")  + ' 00:00:00'))
        end_date = self.convert_withtimezone((record.end_date.strftime("%Y-%m-%d")  + ' 23:59:59'))
        warehouse_wise_locations = self.get_location(record, warehouse)
        locations = self.get_unique_locations(warehouse_wise_locations,locations_ids)
        self._cr.execute('''
                        SELECT pp.id AS product_id,pt.categ_id,
                            sum((
                            CASE WHEN spt.code in ('outgoing') AND smline.location_id in %s AND sourcel.usage !='inventory' AND destl.usage !='inventory'
                            THEN -(smline.quantity * pu.factor / pu2.factor)
                            ELSE 0.0 
                            END
                            )) AS product_qty_out,
                                sum((
                            CASE WHEN spt.code in ('incoming') AND smline.location_dest_id in %s AND sourcel.usage !='inventory' AND destl.usage !='inventory' 
                            THEN (smline.quantity * pu.factor / pu2.factor) 
                            ELSE 0.0 
                            END
                            )) AS product_qty_in,

                            sum((
                            CASE WHEN (spt.code ='internal') AND smline.location_dest_id in %s AND sourcel.usage !='inventory' AND destl.usage !='inventory' 
                            THEN (smline.quantity * pu.factor / pu2.factor)  
                            WHEN (spt.code ='internal' OR spt.code is null) AND smline.location_id in %s AND sourcel.usage !='inventory' AND destl.usage !='inventory' 
                            THEN -(smline.quantity * pu.factor / pu2.factor) 
                            ELSE 0.0 
                            END
                            )) AS product_qty_internal,

                            sum((
                            CASE WHEN sourcel.usage = 'inventory' AND smline.location_dest_id in %s  
                            THEN  (smline.quantity * pu.factor / pu2.factor)
                            WHEN destl.usage ='inventory' AND smline.location_id in %s 
                            THEN -(smline.quantity * pu.factor / pu2.factor)
                            ELSE 0.0 
                            END
                            )) AS product_qty_adjustment
                        FROM product_product pp 
                        LEFT JOIN stock_move_line smline ON (smline.product_id = pp.id)
                        LEFT JOIN stock_move sm ON (sm.id = smline.move_id)
                        LEFT JOIN stock_picking sp ON (sm.picking_id=sp.id)
                        LEFT JOIN stock_picking_type spt ON (spt.id=sp.picking_type_id)
                        LEFT JOIN stock_location sourcel ON (smline.location_id=sourcel.id)
                        LEFT JOIN stock_location destl ON (smline.location_dest_id=destl.id)
                        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                        LEFT JOIN uom_uom pu ON (pt.uom_id=pu.id)
                        LEFT JOIN uom_uom pu2 ON (smline.product_uom_id=pu2.id)
                        WHERE pp.id in %s AND smline.state = 'done' AND smline.date >= %s AND smline.date <= %s AND smline.location_id != smline.location_dest_id
                        GROUP BY pt.categ_id, pp.id order by pt.categ_id
                        ''', (tuple(locations), tuple(locations), tuple(locations), tuple(locations), tuple(locations), tuple(locations), product_data, start_date, end_date))
        values = self._cr.dictfetchall()
        product_sale_data = {}
        for each in values:
            product_sale_data.setdefault(each['product_id'],each)
        return product_sale_data

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: