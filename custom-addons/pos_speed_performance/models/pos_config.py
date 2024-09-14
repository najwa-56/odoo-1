# -*- coding: utf-8 -*-

from odoo import models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def get_limited_product_count(self):
        default_limit = 20000
        if self.company_id.x_allow_online_search == True:
            config_param = self.company_id.x_limit_product
        else:
            config_param = self.env['ir.config_parameter'].sudo().get_param('point_of_sale.limited_product_count', default_limit)
        try:
            return int(config_param)
        except (TypeError, ValueError, OverflowError):
            return default_limit

    def get_limited_partners_loading(self):
        default_limit = 100
        if self.company_id.x_allow_online_search == True:
            default_limit = self.company_id.x_limit_partner
        self.env.cr.execute("""
            WITH pm AS
            (
                     SELECT   partner_id,
                              Count(partner_id) order_count
                     FROM     pos_order
                     GROUP BY partner_id)
            SELECT    id
            FROM      res_partner AS partner
            LEFT JOIN pm
            ON        (
                                partner.id = pm.partner_id)
            WHERE (
                partner.company_id=%s OR partner.company_id IS NULL
            )
            ORDER BY  COALESCE(pm.order_count, 0) DESC,
                      NAME limit %s;
        """, [self.company_id.id, str(default_limit)])
        result = self.env.cr.fetchall()
        return result