from odoo import api, fields, models
    
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    googlemap_api_key = fields.Char(string='Partners Google Maps Api Key',config_parameter='web_googlemap.googlemap_api_key')