from odoo import fields, models, exceptions, api, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    # reports invoice fields
    other_seller_id = fields.Char(store=True, readonly=False, string='Other Seller Id')
    arabic_name = fields.Char('Name')
    arabic_street = fields.Char('Street')
    arabic_street2 = fields.Char('Street2')
    arabic_city = fields.Char('City')
    arabic_state = fields.Char('State')
    arabic_country = fields.Char('Country')
    arabic_zip = fields.Char('Zip')