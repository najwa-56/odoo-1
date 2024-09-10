# -*- coding: utf-8 -*-

from ast import literal_eval
from odoo import api, fields, models, _
import json
from odoo.tools import date_utils


class pos_data_partner_cache(models.Model):
    _name = 'pos.data.partner.cache'

    partner_id = fields.Integer("Partner id")
    partner_data = fields.Text("Partner Data")
    cache_id = fields.Integer("Cache id")

class pos_product_cache(models.Model):
    _name = 'pos.product.cache'

    product_id = fields.Integer("Product id")
    product_data = fields.Text("product_data")
    cache_id = fields.Integer("Cache id")

class pos_cache(models.Model):
    _name = 'pos.cache'

    product_domain = fields.Text(required=True)
    product_fields = fields.Text(required=True)
    config_id = fields.Many2one('pos.config', ondelete='cascade', required=True)
    compute_user_id = fields.Many2one('res.users', 'Cache compute user', required=True)

    def refresh_cache(self):
        for cache in self:
            product_cache = self.env['pos.product.cache']
            products = self.env['product.product'].search(self.get_product_domain())
            prod_ctx = products.with_context(pricelist=cache.config_id.pricelist_id.id,
                    display_default_code=False, lang=cache.compute_user_id.lang)     
            prod_ctx = prod_ctx.sudo(cache.compute_user_id.id)
            result = prod_ctx.read(self.get_product_fields())
            for res in result:
                product_cache.create({'cache_id':self.id,'product_id':res['id'],'product_data': json.dumps(res, default=date_utils.json_default).encode('utf-8')})

    @api.model
    def get_product_domain(self):
        return literal_eval(self.product_domain)

    @api.model
    def get_product_fields(self):
        return literal_eval(self.product_fields)

    def get_cache(self, domain, fields):
        for res in self:
            if domain != self.get_product_domain() or fields != self.get_product_fields():
                self.product_domain = str(domain)
                self.product_fields = str(fields)
                self.refresh_cache()
            self._cr.execute("SELECT  product_data FROM pos_product_cache where cache_id="+str(res.id))
            result = self._cr.fetchall()
        return result

class pos_partner_cache(models.Model):
    _name = 'pos.partner.cache'

    partner_domain = fields.Text(required=True)
    partner_fields = fields.Text(required=True)
    # config_id = fields.Many2one('pos.config', ondelete='cascade')
    compute_user_id = fields.Many2one('res.users', 'Cache compute user', required=True)

    def refresh_cache(self):
        partner_cache = self.env['pos.data.partner.cache']
        partners = self.env['res.partner'].search(self.get_partner_domain())
        # prod_ctx = products.with_context(pricelist=self.config_id.pricelist_id.id, display_default_code=False,
        #                                  lang=self.compute_user_id.lang,location=self.config_id.stock_location_id.id)
        # prod_ctx = prod_ctx.sudo(self.compute_user_id.id)
        result = partners.read(self.get_partner_fields())
        for res in result:
            res['write_date'] = str(res['write_date'])
            partner_cache.create({'cache_id':self.id,'partner_id':res['id'],'partner_data': json.dumps(res, default=date_utils.json_default).encode('utf-8')})

    @api.model
    def get_partner_domain(self):
        return literal_eval(self.partner_domain)

    @api.model
    def get_partner_fields(self):
        return literal_eval(self.partner_fields)

    @api.model
    def get_cache(self, domain, fields):
        if domain != self.get_partner_domain() or fields != self.get_partner_fields():
            self.partner_domain = str(domain)
            self.partner_fields = str(fields)
            self.refresh_cache()
        self._cr.execute("SELECT  partner_data FROM pos_data_partner_cache")
        result = self._cr.fetchall()
        return result


class pos_config(models.Model):
    _inherit = 'pos.config'

    @api.depends('cache_ids')
    def _get_oldest_cache_time(self):
        for cache in self:
            pos_cache = self.env['pos.cache']
            oldest_cache = pos_cache.search([('config_id', '=', cache.id)], order='write_date', limit=1)
            cache.oldest_cache_time = oldest_cache.write_date

    cache_ids = fields.One2many('pos.cache', 'config_id')
    oldest_cache_time = fields.Datetime(compute='_get_oldest_cache_time', string='Oldest cache time', readonly=True)

    def _get_cache_for_user(self):
        pos_cache = self.env['pos.cache']
        cache_for_user = pos_cache.search([])  #('id', 'in', self.cache_ids.ids), ('compute_user_id', '=', self.env.uid)

        if cache_for_user:
            return cache_for_user[0]
        else:
            return None

    def get_products_from_cache(self, fields, domain):
        cache_for_user = self._get_cache_for_user()
        if cache_for_user:
            return cache_for_user.get_cache(domain, fields)
        else:
            pos_cache = self.env['pos.cache']
            pos_cache.create({
                'config_id': self.id,
                'product_domain': str(domain),
                'product_fields': str(fields),
                'compute_user_id': self.env.uid
            })
            new_cache = self._get_cache_for_user()
            new_cache.refresh_cache()
            return new_cache.get_cache(domain, fields)

    def _get_partner_cache_for_user(self):
        pos_partner_cache = self.env['pos.partner.cache']
        cache_for_user = pos_partner_cache.search([])
        if cache_for_user:
            return cache_for_user[0]
        else:
            return None

    def get_partner_from_cache(self, fields, domain):
        cache_for_user = self._get_partner_cache_for_user()
        n_domain = domain or []
        if cache_for_user:
            return cache_for_user.get_cache(n_domain, fields)
        else:
            pos_cache = self.env['pos.partner.cache']
            pos_cache.create({
                'partner_domain': str(n_domain),
                'partner_fields': str(fields),
                'compute_user_id': self.env.uid
            })
            new_cache = self._get_partner_cache_for_user()

            new_cache.refresh_cache()
            return new_cache.get_cache(n_domain, fields)

    def delete_cache(self):
        self.cache_ids.unlink()
        self.env['pos.data.partner.cache'].search([]).unlink()
        self.env['pos.product.cache'].search([]).unlink()
        self.env['pos.partner.cache'].search([]).unlink()
        self.env['pos.cache'].search([]).unlink()


class product_product(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, values):
        product_cache = self.env['pos.product.cache']
        res = super(product_product, self).create(values)
        pos_cache = self.env['pos.cache'].search([])
        for cache in pos_cache:
            cache_deomain = cache.get_product_domain()
            cache_fields = cache.get_product_fields()
            cache_deomain.append(['id','=',res.id])
            allo_data = self.env['product.product'].with_context(pricelist=cache.config_id.pricelist_id.id).search_read(cache_deomain,cache_fields)
            cachecr = product_cache.create({'cache_id':cache.id,'product_id':res.id,'product_data': json.dumps(allo_data[0], default=date_utils.json_default)})
        return res

    def write(self, vals):
        product_cache = self.env['pos.product.cache']
        result = super(product_product, self).write(vals)
        for re in self:
            pos_cache = self.env['pos.cache'].search([])
            for cache in pos_cache:
                cache_deomain = cache.get_product_domain()
                cache_fields = cache.get_product_fields()
                cache_pro = product_cache.search([('cache_id','=',cache.id),('product_id','=',re.id)])
                if cache_pro:
                    if re.active:
                        cache_deomain.append(['id','=',re.id])
                        allo_data = self.env['product.product'].with_context(pricelist=cache.config_id.pricelist_id.id).search_read(cache_deomain,cache_fields)
                        if allo_data:
                            cache_pro[0].product_data = json.dumps(allo_data[0], default=date_utils.json_default)
                    else:
                        cache_pro[0].sudo().unlink()
                else:
                    if re.active and re.available_in_pos:
                        cache_deomain.append(['id','=',re.id])
                        allo_data = self.env['product.product'].with_context(pricelist=cache.config_id.pricelist_id.id).search_read(cache_deomain,cache_fields)
                        if allo_data:
                            cachecr = product_cache.create({'cache_id':cache.id,'product_id':re.id,'product_data': json.dumps(allo_data[0], default=date_utils.json_default)})

        return result

class product_template(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        product_cache = self.env['pos.product.cache']
        result = super(product_template, self).write(vals)
        for re in self:
            product_ids = self.env['product.product'].search([('product_tmpl_id','=',re.id)])
            for pid in product_ids.ids:
                pos_cache = self.env['pos.cache'].search([])
                for cache in pos_cache:
                    cache_deomain = cache.get_product_domain()
                    cache_fields = cache.get_product_fields()
                    cache_pro = product_cache.search([('cache_id','=',cache.id),('product_id','=',pid)])
                    if cache_pro:
                        if re.active:
                            cache_deomain.append(['id','=',pid])
                            allo_data = self.env['product.product'].with_context(pricelist=cache.config_id.pricelist_id.id).search_read(cache_deomain,cache_fields)
                            if allo_data:
                                cache_pro[0].product_data = json.dumps(allo_data[0], default=date_utils.json_default)
                        else:
                            cache_pro[0].sudo().unlink()
                    else:
                        if re.active and re.available_in_pos:
                            cache_deomain.append(['id','=',re.id])
                            allo_data = self.env['product.product'].with_context(pricelist=cache.config_id.pricelist_id.id).search_read(cache_deomain,cache_fields)
                            if allo_data:
                                cachecr = product_cache.create({'cache_id':cache.id,'product_id':re.id,'product_data': json.dumps(allo_data[0], default=date_utils.json_default)})
        return result

class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, values):
        partner_cache = self.env['pos.data.partner.cache']
        res = super(res_partner, self).create(values)
        pos_cache = self.env['pos.partner.cache'].search([])
        if pos_cache:
            cache_deomain = pos_cache[0].get_partner_domain()
            cache_fields = pos_cache[0].get_partner_fields()
            cache_deomain.append(['id','=',res.id])
            allo_data = self.env['res.partner'].search_read(cache_deomain,cache_fields)
            allo_data[0]['write_date'] = str(allo_data[0]['write_date'])
            cachecr = partner_cache.create({'cache_id':pos_cache[0].id,'partner_id':res.id,'partner_data': json.dumps(allo_data[0], default=date_utils.json_default)})
        return res

    def write(self, vals):
        partner_cache = self.env['pos.data.partner.cache']
        result = super(res_partner, self).write(vals)
        for re in self:
            pos_cache = self.env['pos.partner.cache'].search([])
            if pos_cache:
                cache_deomain = pos_cache[0].get_partner_domain()
                cache_fields = pos_cache[0].get_partner_fields()
                cache_pro = partner_cache.search([('partner_id','=',re.id)])
                if cache_pro:
                    if re.active:
                        cache_deomain.append(['id','=',re.id])
                        allo_data = self.env['res.partner'].search_read(cache_deomain,cache_fields)
                        allo_data[0]['write_date'] = str(allo_data[0]['write_date'])
                        cache_pro[0].partner_data = json.dumps(allo_data[0], default=date_utils.json_default)
                    else:
                        cache_pro[0].sudo().unlink()
                else:
                    if re.active:
                        cache_deomain.append(['id','=',re.id])
                        allo_data = self.env['res.partner'].search_read(cache_deomain,cache_fields)
                        if allo_data:
                            allo_data[0]['write_date'] = str(allo_data[0]['write_date'])
                            cachecr = partner_cache.create({'cache_id':pos_cache[0].id,'partner_id':re.id,'partner_data': json.dumps(allo_data[0], default=date_utils.json_default)})
        return result

