from odoo import _, api, models
from lxml.builder import E
from odoo.exceptions import UserError

class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def _get_default_googlemap_view(self):
        view = E.googlemap()
        if 'partner_id' in self._fields:
            view.set('res_partner', 'partner_id')
        else:
            raise UserError(_("You need to set a Contact field on this model to enable the use of the Gooele Map View."))
        return view
