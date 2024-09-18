from odoo import models,fields,api,_


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_product_multi_uom_price(self):
        return {'search_params': {'domain': [], 'fields': ['product_id', 'uom_id', 'price', 'barcode', 'product_variant_id','name_field'],},}

    def _get_pos_ui_product_multi_uom_price(self, params):
        products_uom_price = self.env['product.multi.uom.price'].search_read(**params['search_params'])
        product_uom_price = {}

        if products_uom_price:
            for unit in products_uom_price:
                product_id = unit.get('product_id')
                uom_id = unit.get('uom_id')
                barcode = unit.get('barcode')

                if product_id and uom_id:
                    if product_id[0] not in product_uom_price:
                        product_uom_price[product_id[0]] = {'uom_id': {}}

                    if uom_id[0] not in product_uom_price[product_id[0]]['uom_id']:
                        product_uom_price[product_id[0]]['uom_id'][uom_id[0]] = {
                            'id': uom_id[0],
                            'name': uom_id[1],
                            'name_field': unit.get('name_field', ''),
                            'price': unit['price'],
                            'barcodes': [],
                            'product_id': product_id,
                            'product_variant_id': unit['product_variant_id'],
                        }
                    if barcode:
                        product_uom_price[product_id[0]]['uom_id'][uom_id[0]]['barcodes'].append(barcode)

        return product_uom_price


def find_product_by_barcode(self, barcode):
    # Search for the product by barcode in the product.product model
    product = self.env['product.product'].search([
        ('barcode', '=', barcode),
        ('sale_ok', '=', True),
        ('available_in_pos', '=', True),
    ])
    if product:
        return {'product_id': [product.id]}

    # Search for the product packaging by barcode
    packaging_params = self._loader_params_product_packaging()
    packaging_params['search_params']['domain'] = [['barcode', '=', barcode]]
    packaging = self.env['product.packaging'].search_read(**packaging_params['search_params'])
    if packaging:
        product_id = packaging[0]['product_id']
        if product_id:
            return {'product_id': [product_id[0]], 'packaging': packaging}

    # Search in the product.multi.uom.price model for barcode
    multi_uom = self.env['product.multi.uom.price'].search([('barcode', '=', barcode)])
    if multi_uom:
        # Retrieve the related product from product_tmpl_id and its first variant
        product_id = multi_uom.product_tmpl_id.product_variant_id.id
        return {'product_id': [product_id], 'multi_uom_id': multi_uom.id}

    # Return empty if no match is found
    return {}