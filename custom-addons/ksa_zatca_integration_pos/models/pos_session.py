# -*- coding: utf-8 -*-
from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_res_company(self):
        result = super()._loader_params_res_company()
        result['search_params']['fields'].extend(['parent_zatca_send_from_pos', 'parent_is_zatca','street','street2','city','state_id','vat'])
        return result

    
    def _loader_params_res_partner(self):
        result = super()._loader_params_res_partner()
        result['search_params']['fields'].append('buyer_identification_no')
        return result

    def _loader_params_product_product(self):
        res = super(PosSession, self)._loader_params_product_product()
        fields = res.get('search_params').get('fields')
        fields.extend(['name','name_arabic'])
        res['search_params']['fields'] = fields
        return res



