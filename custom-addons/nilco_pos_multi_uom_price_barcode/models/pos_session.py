from odoo import models,fields,api,_


class PosSession(models.Model):
    _inherit = 'pos.session'
    def _loader_params_product_multi_uom_price(self):
        return {'search_params': {'domain': [], 'fields': ['product_id', 'uom_id', 'price','barcode','product_variant_id'],},}

    def _get_pos_ui_product_multi_uom_price(self, params):
        products_uom_price = self.env['product.multi.uom.price'].search_read(**params['search_params'])
        product_uom_price = {}

        if products_uom_price:
            for unit in products_uom_price:
                product_id = unit.get('product_id')  # Get product_id from unit
                uom_id = unit.get('uom_id')  # Get uom_id from unit

                if product_id and uom_id:
                    if product_id[0] not in product_uom_price:
                        product_uom_price[product_id[0]] = {}
                        product_uom_price[product_id[0]]['uom_id'] = {}

                    product_uom_price[product_id[0]]['uom_id'][uom_id[0]] = {
                        'id': uom_id[0],
                        'name': uom_id[1],
                        'price': unit['price'],
                        'barcode': unit['barcode'],
                        'product_id': product_id,
                        'product_variant_id': unit['product_variant_id'],
                    }

        return product_uom_price
