# -*- coding: utf-8 -*-
from odoo.http import request, route, Controller
import lxml.etree as ET
from odoo import http
import base64


class Update(Controller):

    @http.route('/zatca/module/set', auth='public')
    def update(self, **kw):
        # request._cr.execute("UPDATE account_move SET l10n_sa_confirmation_datetime = invoice_datetime WHERE zatca_invoice_hash IS NOT NULL ")
        request._cr.execute("UPDATE account_move SET zatca_unique_seq = id WHERE zatca_invoice_hash IS NOT NULL AND zatca_unique_seq IS NULL")
        request._cr.execute("UPDATE account_move_line SET zatca_id = id WHERE move_id IN (Select Id From account_move Where zatca_invoice_hash IS NOT NULL) AND zatca_id IS NULL")

        records = request.env['account.move'].sudo().search([])
        records = records.filtered(lambda x: x.zatca_invoice_hash not in [False, None, ''])
        for record in records:
            invoice = base64.b64decode(record.zatca_invoice).decode()
            xml_file = ET.fromstring(invoice).getroottree()
            icv = xml_file.xpath('//*[local-name()="ID"][text()="ICV"]/following-sibling::*[1]')[0].text
            record.zatca_icv_counter = icv

        return "All done"
