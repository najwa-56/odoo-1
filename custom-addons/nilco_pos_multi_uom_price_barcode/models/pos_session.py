from odoo import models,fields,api,_


class PosSession(models.Model):
    _inherit = 'pos.session'


    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result['search_params']['fields'].extend(['new_barcode'])
        return result


    def _loader_params_product_multi_uom_price(self):
        domain = []
        if self.config_id.iface_available_categ_ids:
            domain = [('product_id.pos_categ_ids','in',self.config_id.iface_available_categ_ids.ids)]

        return {'search_params': {'domain': domain, 'fields': ['product_id', 'uom_id', 'price', 'barcode', 'product_variant_id','name_field'],},}

    # def _get_pos_ui_product_multi_uom_price(self, params):
    #     products_uom_price = self.env['product.multi.uom.price'].search_read(**params['search_params'])
    #     product_uom_price = {}

    #     if products_uom_price:
    #         for unit in products_uom_price:
    #             product_id = unit.get('product_id')
    #             uom_id = unit.get('uom_id')
    #             barcode = unit.get('barcode')

    #             if product_id and uom_id:
    #                 if product_id[0] not in product_uom_price:
    #                     product_uom_price[product_id[0]] = {'uom_id': {}}

    #                 if uom_id[0] not in product_uom_price[product_id[0]]['uom_id']:
    #                     product_uom_price[product_id[0]]['uom_id'][uom_id[0]] = {
    #                         'id': uom_id[0],
    #                         'name': uom_id[1],
    #                         'name_field': unit.get('name_field', ''),
    #                         'price': unit['price'],
    #                         'barcodes': [],
    #                         'product_id': product_id,
    #                         'product_variant_id': unit['product_variant_id'],
    #                     }
    #                 if barcode:
    #                     product_uom_price[product_id[0]]['uom_id'][uom_id[0]]['barcodes'].append(barcode)

    #     return product_uom_price
    def _get_pos_ui_product_multi_uom_price(self, params):
        print("params=================",params)
        products_uom_price = self.env['product.multi.uom.price'].search_read(**params['search_params'])
        product_uom_price = {}

        if products_uom_price:
            for unit in products_uom_price:
                product_id = unit.get('product_id')
                uom_id = unit.get('uom_id')
                barcode = unit.get('barcode')

                if product_id and uom_id and barcode:
                    # Use the barcode as the primary key
                    if product_id[0] not in product_uom_price:
                        product_uom_price[product_id[0]] = {'barcodes': {}}

                    if barcode not in product_uom_price[product_id[0]]['barcodes']:
                        product_uom_price[product_id[0]]['barcodes'][barcode] = {
                            'id': uom_id[0],
                            'name': uom_id[1],
                            'name_field': unit.get('name_field', ''),
                            'price': unit['price'],
                            'uom_id': uom_id,
                            'product_id': product_id,
                            'product_variant_id': unit['product_variant_id'],
                        }
        print("len of  product_uom_price========================",len(product_uom_price))
        return product_uom_price


    def find_product_by_barcode(self, barcode):
        if self.config_id.iface_available_categ_ids:
            product = self.env['product.product'].search([
                ('barcode', '=', barcode),
                ('sale_ok', '=', True),
                ('available_in_pos', '=', True),
                ('pos_categ_ids','in',self.config_id.iface_available_categ_ids.ids)
            ])
            if product:
                return {'product_id': [product.id]}

            packaging_params = self._loader_params_product_packaging()
            packaging_params['search_params']['domain'] = [['barcode', '=', barcode]]
            packaging = self.env['product.packaging'].search_read(**packaging_params['search_params'])
            if packaging:
                product_id = packaging[0]['product_id']
                if product_id:
                    return {'product_id': [product_id[0]], 'packaging': packaging}
            return {}
        else:
            return super().find_product_by_barcode(barcode = barcode)