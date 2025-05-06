import json
import odoo
from odoo import http, models, fields, _
from odoo.http import request

class WebsiteBinary(http.Controller):
    
    @http.route('/web_googlemap/_get_googlemap_api_key', type='json', auth='public', website=True)
    def _get_googlemap_api_key(self):
        key = request.env['ir.config_parameter'].sudo().get_param('web_googlemap.googlemap_api_key')
        return json.dumps({
            'googlemap_api_key': key
        })