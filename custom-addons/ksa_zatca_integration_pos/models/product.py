
from odoo import models, fields, api, _

class product_template(models.Model):
	_inherit = 'product.template'

	name_arabic = fields.Char(string="Arabic Name")

