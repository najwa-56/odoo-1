from odoo import exceptions, _

amount_verification = 0  # for debug mode


class ZatcaUBL():

    def set_zatca_id(self, invoice_line_id):
        def next_invoice_line_id(invoice_line_id):
            id = self.env['ir.sequence'].with_company(self.company_id.parent_root_id).next_by_code('zatca.move.line.seq')
            if invoice_line_id.sudo().search([('zatca_id', '=', id)]).id:
                id = next_invoice_line_id(invoice_line_id)
            return id

        # seq check
        sequence = self.env['ir.sequence'].search([('code', '=', 'zatca.move.line.seq'),
                                                   ('company_id', 'in', [self.company_id.parent_root_id.id, False])],
                                                  order='company_id', limit=1)
        if not sequence:
            raise exceptions.MissingError(_("Sequence") + " 'zatca.move.line.seq' " + _("not found for this company"))
        invoice_line_id.zatca_id = next_invoice_line_id(invoice_line_id)

    def _get_bg_23_list(self, invoice_line_id, bg_23_list, bt, tax_category, tax_rate, net_amount, is_bg_20, bt_120, bt_121, is_bg_25=False):
        if not bg_23_list.get(tax_category, False):
            bg_23_list[tax_category] = {}
        if not bg_23_list[tax_category].get(bt_121, False):
            bg_23_list[tax_category][bt_121] = {'∑bt_92': 0, '∑bt_99': 0, '∑bt_116': 0,
                                                'bt_117': 0, 'bt_119': tax_rate, 'bt_120': bt_120}
        if tax_category == "O":
            # if bt_120 not in bg_23_list[tax_category][bt_121]['bt_120']:
            #     bg_23_list[tax_category][bt_121]['bt_120'] += ",%s" % bt_120
            if invoice_line_id.id:
                if invoice_line_id.tax_ids and (not invoice_line_id.tax_ids.tax_exemption_text or
                                                not invoice_line_id.tax_ids.tax_exemption_code):
                    raise exceptions.MissingError(_("Tax exemption Reason Text is missing in Tax Category") + " 'O' ")
        if is_bg_25:
            bg_23_list[tax_category][bt_121]['∑bt_116'] += net_amount
        elif is_bg_20:
            bg_23_list[tax_category][bt_121]['∑bt_92'] += net_amount
        else:
            bg_23_list[tax_category][bt_121]['∑bt_99'] += net_amount

        return bg_23_list, bt

    def _get_tax_category(self, tax_category, tax_rate, bt_120, bt_121, is_tax_subtotal=False):
        self.l10n_check_allowed_size(1, 1000, bt_120, "TaxExemptionReason")
        tax_category_xml = '''
                        <cbc:ID>%s</cbc:ID>''' % tax_category
        tax_category_xml += '''
                        <cbc:Percent>%s</cbc:Percent>''' % tax_rate
        if tax_category in ['E', 'O', 'Z']:
            if not is_tax_subtotal:
                tax_category_xml += '''
                        <cbc:TaxExemptionReasonCode>%s</cbc:TaxExemptionReasonCode>
                        <cbc:TaxExemptionReason>%s</cbc:TaxExemptionReason>''' % (bt_121, bt_120)
            else:
                tax_category_xml += '''
                        <cbc:TaxExemptionReasonCode>%s</cbc:TaxExemptionReasonCode>''' % bt_121
                if tax_category != 'O':
                    tax_category_xml += '''
                        <cbc:TaxExemptionReason>%s</cbc:TaxExemptionReason>''' % bt_120
                if tax_category == 'O':
                    for reason in bt_120.split(','):
                        tax_category_xml += '''
                        <cbc:TaxExemptionReason>%s</cbc:TaxExemptionReason>''' % reason
        tax_category_xml += '''
                        <cac:TaxScheme>
                            <cbc:ID>VAT</cbc:ID>
                        </cac:TaxScheme>'''
        return tax_category_xml

    def get_document_level_allowance(self, bt, ubl_2_1, document_currency, bg_23_list):
        document_level_allowance = 0
        if document_level_allowance:
            bt[120] = False
            bt[121] = False
            bt[92] = self.get_l10n_field_type('amount', 0)
            bt['∑92'] += bt[92]
            bt[93] = self.get_l10n_field_type('amount', 0)
            bt[96] = self.get_l10n_field_type('percentage', self.get_l10n_field_type('amount', 0))
            bt[97] = self.get_l10n_field_type('text', "Discount")
            bt[98] = "95"
            # allowance on document level (bg-20)
            if bt[95] == 'S' and bt[96] <= 0:
                raise exceptions.ValidationError(_('In Document level allowance for Tax Category') + " %s " % bt[95] + _("must be greater then 0"))
            if bt[95] in ['Z', 'E', 'O'] and bt[96] != 0:
                raise exceptions.ValidationError(_('In Document level allowance for Tax Category') + " %s " % bt[95] + _("must be 0"))

            ubl_2_1 += '''
            <cac:AllowanceCharge>
                <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
                <cbc:AllowanceChargeReasonCode>%s</cbc:AllowanceChargeReasonCode>
                <cbc:AllowanceChargeReason>%s</cbc:AllowanceChargeReason>
                <cbc:Amount currencyID="%s">%s</cbc:Amount>
                <cac:TaxCategory>''' % (bt[98], bt[97], document_currency, self.l10n_is_positive("AllowanceChargeAmount (bt-92)", bt[92]))
            ubl_2_1 += ZatcaUBL._get_tax_category(self, bt[95], bt[96], bt[120], bt[121])
            ubl_2_1 += '''
                </cac:TaxCategory>
            </cac:AllowanceCharge>'''
            bg_23_list, bt = ZatcaUBL._get_bg_23_list(self, False, bg_23_list, bt, bt[95], bt[96], bt[92], 1, bt[120], bt[121])
        return bt, ubl_2_1, bg_23_list

    def _get_invoice_line(self, bg_23_list, bt, ksa):
        if not self._is_downpayment():
            invoice_line_ids = self.invoice_line_ids.filtered(lambda x: x.display_type not in ['line_section', 'line_note'] and not x.sale_line_ids.is_downpayment)
        else:
            invoice_line_ids = self.invoice_line_ids.filtered(lambda x: x.display_type not in ['line_section', 'line_note'])
        # invoice_line_ids = self.invoice_line_ids.filtered(lambda x: not x.display_type)
        document_currency = self.currency_id.name
        invoice_line_xml = ''
        item_price_charge = 0
        for invoice_line_id in invoice_line_ids:
            bt[137] = self.get_l10n_field_type('amount', invoice_line_id.price_unit * invoice_line_id.quantity)
            bt[138] = self.get_bt_138(invoice_line_id, bt)
            bt[136] = self.get_l10n_field_type('amount', bt[137] * bt[138] / 100)
            bt[129] = abs(invoice_line_id.quantity)
            bt[141] = self.get_l10n_field_type('amount', 0)
            bt[147] = 0  # NO ITEM PRICE DISCOUNT bt[148] * invoice_line_id.discount/100 if invoice_line_id.discount else 0
            bt[148] = invoice_line_id.price_unit
            bt[146] = bt[148] - bt[147]
            bt[149] = 1  # ??

            bt[131] = self.get_l10n_field_type('amount', ((bt[146] / bt[149]) * bt[129]))
            bt[131] = self.get_l10n_field_type('amount', bt[131] - bt[136] + bt[141])

            bt['∑131'] = bt[131]
            bt[151] = invoice_line_id.tax_ids.classified_tax_category if invoice_line_id.tax_ids else "O"
            bt[152] = self.get_l10n_field_type('percentage', self.get_l10n_field_type('amount', invoice_line_id.tax_ids.amount))
            if bt[151] in ['O', 'Z', 'E'] and bt[152] != 0:
                raise exceptions.ValidationError(_('In Invoice line the tax rate for tax category') + " " + bt[151] + " " + _("must be 0"))
                # bt[152] = 100 if bt[152] > 100 else (0 if bt[152] < 0 else bt[152])

            bt_120 = invoice_line_id.tax_ids.tax_exemption_text if len(invoice_line_id.tax_ids) > 0 else 'Not subject to VAT'
            bt_121 = invoice_line_id.tax_ids.tax_exemption_code if len(invoice_line_id.tax_ids) > 0 else 'VATEX-SA-OOS'
            bg_23_list, bt = ZatcaUBL._get_bg_23_list(self, invoice_line_id, bg_23_list, bt, bt[151], bt[152], bt[131], False, bt_120, bt_121, True)

            ZatcaUBL.set_zatca_id(self, invoice_line_id)

            invoice_line_xml += ('''
            <cac:InvoiceLine>
                <cbc:ID>%s</cbc:ID>
                <cbc:InvoicedQuantity unitCode="PCE">%s</cbc:InvoicedQuantity>
                <cbc:LineExtensionAmount currencyID="%s">%s</cbc:LineExtensionAmount>''' %
                                 (self.l10n_check_allowed_size(1, 6, invoice_line_id.zatca_id, "bt-126"),
                                  self.l10n_is_positive("AllowanceChargeAmount (bt-129)", bt[129]),
                                  document_currency, bt[131]))
            if bt[138]:  # allowance on invoice line: (BG-27)
                invoice_line_xml += '''
                <cac:AllowanceCharge>
                    <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
                    <cbc:AllowanceChargeReasonCode>95</cbc:AllowanceChargeReasonCode>
                    <cbc:AllowanceChargeReason>Discount</cbc:AllowanceChargeReason>'''
                invoice_line_xml += ('''
                    <cbc:MultiplierFactorNumeric>%s</cbc:MultiplierFactorNumeric>
                    <cbc:Amount currencyID="%s">%s</cbc:Amount>
                    <cbc:BaseAmount currencyID="%s">%s</cbc:BaseAmount>''' %
                                     (bt[138], document_currency,
                                      self.get_l10n_field_type('amount', self.l10n_is_positive("AllowanceChargeAmount (bt-136)", bt[136])),
                                      document_currency,
                                      self.get_l10n_field_type('amount', self.l10n_is_positive("AllowanceChargeBaseAmount (bt-137)", bt[137]))))
                if bt[151] != 'O':
                    invoice_line_xml += '''
                        <cac:TaxCategory>
                            <cbc:ID>S</cbc:ID>
                            <cbc:Percent>15</cbc:Percent>
                            <cac:TaxScheme>
                                <cbc:ID>VAT</cbc:ID>
                            </cac:TaxScheme>
                        </cac:TaxCategory>'''
                invoice_line_xml += '''
                    </cac:AllowanceCharge>'''
            if bt[141]:  # charge on invoice line: (BG-28)
                bt[142] = self.get_l10n_field_type('amount', 0)
                bt[144] = "Cleaning"
                bt[145] = "CG"  # from UNTDID 7161 code list
                invoice_line_xml += ('''
                <cac:AllowanceCharge>
                    <cbc:ChargeIndicator>true</cbc:ChargeIndicator>
                    <cbc:AllowanceChargeReasonCode>%s</cbc:AllowanceChargeReasonCode>
                    <cbc:AllowanceChargeReason>%s</cbc:AllowanceChargeReason>
                    <cbc:Amount currencyID="%s">%s</cbc:Amount>
                    <cac:TaxCategory>
                        <cbc:ID>S</cbc:ID>
                        <cbc:Percent>15</cbc:Percent>
                        <cac:TaxScheme>
                            <cbc:ID>VAT</cbc:ID>
                        </cac:TaxScheme>
                    </cac:TaxCategory>
                </cac:AllowanceCharge>''' %
                                     (bt[145], self.l10n_check_allowed_size(0, 1000, bt[144], 'AllowanceChargeReason'),
                                      document_currency, self.l10n_is_positive("AllowanceChargeAmount (bt-141)", bt[141])))

            ksa[11] = self.get_l10n_field_type('amount', bt[131] * bt[152]/100)
            ksa[12] = self.get_l10n_field_type('amount', bt[131] + ksa[11])
            # BR-KSA-52 and BR-KSA-53
            invoice_line_xml += ('''
                <cac:TaxTotal>
                    <cbc:TaxAmount currencyID="%s">%s</cbc:TaxAmount>
                    <cbc:RoundingAmount currencyID="%s">%s</cbc:RoundingAmount>
                </cac:TaxTotal>
                <cac:Item>
                    <cbc:Name>%s</cbc:Name>''' %
                                 (document_currency, self.l10n_is_positive("TaxAmount (ksa-11)", ksa[11]),
                                  document_currency, self.l10n_is_positive("RoundingAmount (ksa-12)", ksa[12]),
                                  self.l10n_check_allowed_size(1, 1000, self._get_zatca_product_name(invoice_line_id)["name"]["value"],
                                                               "Partner " + self._get_zatca_product_name(invoice_line_id)["name"]["field"])))
            if invoice_line_id.product_id.barcode and invoice_line_id.product_id.code_type:
                invoice_line_xml += '''
                    <cac:StandardItemIdentification>
                        <cbc:ID schemeID="%s">%s</cbc:ID>
                    </cac:StandardItemIdentification>''' % (invoice_line_id.product_id.code_type, invoice_line_id.product_id.barcode)
            invoice_line_xml += '''
                    <cac:ClassifiedTaxCategory>'''
            invoice_line_xml += ZatcaUBL._get_tax_category(self, bt[151], bt[152], bt_120, bt_121)
            invoice_line_xml += ('''
                    </cac:ClassifiedTaxCategory>
                </cac:Item>
                <cac:Price>
                    <cbc:PriceAmount currencyID="%s">%s</cbc:PriceAmount>
                    <cbc:BaseQuantity unitCode="PCE">%s</cbc:BaseQuantity>''' %
                                 (document_currency, self.l10n_is_positive("TaxAmount (bt-146)", bt[146]),
                                  self.l10n_is_positive("BaseQuantity (bt-149)", bt[149])))
            if bt[147]:  # item price discount
                invoice_line_xml += ('''
                    <cac:AllowanceCharge>
                        <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
                        <cbc:Amount currencyID="%s">%s</cbc:Amount>
                        <cbc:BaseAmount currencyID="%s">%s</cbc:Amount>
                    </cac:AllowanceCharge>''' %
                                     (document_currency,
                                      self.get_l10n_field_type('amount', self.l10n_is_positive("AllowanceChargeAmount (bt-147)", bt[147])),
                                      document_currency,
                                      self.get_l10n_field_type('amount', self.l10n_is_positive("AllowanceChargeBaseAmount (bt-148)", bt[148]))))
            if item_price_charge:  # item price charge
                invoice_line_xml += ('''
                    <cac:AllowanceCharge>
                        <cbc:ChargeIndicator>true</cbc:ChargeIndicator>
                        <cbc:Amount currencyID="%s">%s</cbc:Amount>
                        <cbc:BaseAmount currencyID="%s">%s</cbc:Amount>
                    </cac:AllowanceCharge>''' %
                                     (document_currency,
                                      self.l10n_is_positive("AllowanceChargeAmount (bt-??)", bt['??']),
                                      document_currency,
                                      self.l10n_is_positive("AllowanceChargeBaseAmount (bt-??)", bt['??'])))
            invoice_line_xml += '''
                </cac:Price>
            </cac:InvoiceLine>'''

        return invoice_line_xml, bt, bg_23_list, ksa

    def _get_legal_monetary_total(self, bt):
        document_currency = self.currency_id.name
        self.l10n_is_positive("LineExtensionAmount (bt-106)", bt[106])
        self.l10n_is_positive("TaxExclusiveAmount (bt-109)", bt[109])
        self.l10n_is_positive("TaxInclusiveAmount (bt-112)", bt[112])

        LegalMonetaryTotal = [
            "<cac:LegalMonetaryTotal>",
            "<cbc:%s currencyID='%s'>%s</cbc:%s>" % ("LineExtensionAmount", document_currency, bt[106], "LineExtensionAmount"),
            "<cbc:%s currencyID='%s'>%s%s</cbc:%s>" % ("TaxExclusiveAmount", document_currency, bt[109], (" | " + str(self.amount_untaxed) if amount_verification else ''), "TaxExclusiveAmount"),
            "<cbc:%s currencyID='%s'>%s%s</cbc:%s>" % ("TaxInclusiveAmount", document_currency, bt[112], (" | " + str(self.amount_total) if amount_verification else ''), "TaxInclusiveAmount"),
        ]
        if bt[107]:
            self.l10n_is_positive("AllowanceTotalAmount (bt-107)", bt[107])
            LegalMonetaryTotal.append("<cbc:%s currencyID='%s'>%s</cbc:%s>" % ("AllowanceTotalAmount", document_currency, bt[107], "AllowanceTotalAmount"))
        if bt[108]:
            self.l10n_is_positive("ChargeTotalAmount (bt-108)", bt[108])
            LegalMonetaryTotal.append("<cbc:%s currencyID='%s'>%s</cbc:%s>" % ("ChargeTotalAmount", document_currency, bt[108], "ChargeTotalAmount"))
        if bt[114]:
            LegalMonetaryTotal.append("<cbc:%s currencyID='%s'>%s</cbc:%s>" % ("PayableRoundingAmount", document_currency, bt[114], "PayableRoundingAmount"))
        LegalMonetaryTotal.append("<cbc:%s currencyID='%s'>%s%s</cbc:%s>" % ("PayableAmount", document_currency, bt[115], (" | " + str(self.amount_residual) if amount_verification else ''), "PayableAmount"))
        LegalMonetaryTotal.append("</cac:LegalMonetaryTotal>")

        return LegalMonetaryTotal
