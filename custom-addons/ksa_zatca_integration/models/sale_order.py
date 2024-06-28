from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        conf = self.company_id.parent_root_id.sudo()
        if invoice_vals['partner_id']:
            partner = self.env['res.partner'].sudo().browse(invoice_vals['partner_id'])
            if conf.is_zatca:
                if conf.zatca_invoice_type == "Standard & Simplified":
                    if partner.company_type == 'person':
                        invoice_vals['l10n_sa_invoice_type'] = "Simplified"
                    else:
                        invoice_vals['l10n_sa_invoice_type'] = "Standard"
                else:
                    invoice_vals['l10n_sa_invoice_type'] = conf.zatca_invoice_type
            else:
                invoice_vals['l10n_sa_invoice_type'] = None
        return invoice_vals
