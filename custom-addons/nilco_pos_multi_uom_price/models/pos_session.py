from odoo import models,fields,api,_


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        new_model = 'product.multi.uom.price'
        if new_model not in result:
            result.append(new_model)
        return result


    def _loader_params_product_multi_uom_price(self):
        return {'search_params': {'domain': [], 'fields': ['product_id', 'uom_id', 'price'],},}

    def _get_pos_ui_product_multi_uom_price(self, params):
        products_uom_price = self.env['product.multi.uom.price'].search_read(**params['search_params'])
        product_uom_price = {}

        if products_uom_price:
            for unit in products_uom_price:
                product_id = unit.get('product_id', False)
                uom_id = unit.get('uom_id', False)

                if product_id and uom_id:
                    if product_id[0] not in product_uom_price:
                        product_uom_price[product_id[0]] = {}

                    if uom_id[0] not in product_uom_price[product_id[0]]['uom_id']:
                        product_uom_price[product_id[0]]['uom_id'][uom_id[0]] = {
                            'id': uom_id[0],
                            'name': uom_id[1],
                            'price': unit['price']*.85,
                        }

        return product_uom_price

    def _loader_params_product_product(self):
        return {
            'search_params': {
                'domain': self.config_id._get_available_product_domain(),
                'fields': [
                    'display_name', 'lst_price', 'standard_price', 'categ_id', 'pos_categ_ids', 'taxes_id', 'barcode',
                    'default_code', 'to_weight', 'uom_id', 'description_sale', 'description', 'product_tmpl_id', 'tracking',
                    'write_date', 'available_in_pos', 'attribute_line_ids', 'active', 'image_128', 'combo_ids',],
                'order': 'sequence,default_code,name',
            },
            'context': {'display_default_code': False},
        }

    def pos_active_user_group(self, current_user):
        user = self.env['res.users'].search([('id', '=', current_user['id'])])
        zero = user.has_group('pos_access_rights_app.group_zero_button')
        return {'zero': zero}

