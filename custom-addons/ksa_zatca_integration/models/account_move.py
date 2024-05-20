from cryptography.hazmat.backends import default_backend
from odoo import api, fields, models, exceptions, tools, _
from cryptography import x509
from odoo.tools.float_utils import float_round
from odoo.tools import mute_logger
import lxml.etree as ET
import datetime
import binascii
import requests
import logging
import hashlib
import base64
import uuid
import json
import math
import re
import os

phase_1_ending_date = fields.datetime.strptime("1/jan/2000", "%d/%b/%Y").date() # last day for phase 1 invoices.

_logger = logging.getLogger(__name__)
_zatca = logging.getLogger('Zatca Debugger for account.move :')
message = "Based on the VAT regulation, after issuing an invoice, it is prohibited to " \
          "modify or cancel the invoice. and according the regulation, a debit/credit " \
          "notes must be generated to modify or cancel the generated invoice. Therefore" \
          " the supplier should issue an electronic credit/debit note linked to the original." \
          " modified invoice"


class AccountMove(models.Model):
    _inherit = "account.move"

    zatca_hash_cleared_invoice = fields.Binary("cleared invoice returned from ZATCA", attachment=True, readonly=True, copy=False)
    zatca_hash_cleared_invoice_name = fields.Char(copy=False)

    pdf_report = fields.Binary(attachment=True, readonly=True, copy=False)
    zatca_invoice = fields.Binary("generated invoice for ZATCA", attachment=True, readonly=True, copy=False)
    zatca_invoice_name = fields.Char(copy=False)
    credit_debit_reason = fields.Char(string="Reasons for issuance of credit / debit note", copy=False,
                                   help="Reasons as per Article 40 (paragraph 1) of KSA VAT regulations")
    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False,
                               states={'draft': [('readonly', False)]}, default=lambda self: fields.Datetime.now().date())
    zatca_compliance_invoices_api = fields.Html(readonly=True, copy=False)

    def _default_l10n_sa_invoice_type_is_readonly(self):
        return 1 if self.env.company.sudo().zatca_invoice_type != "Standard & Simplified" else 0

    l10n_sa_invoice_type_is_readonly = fields.Boolean(
        default=lambda self: self._default_l10n_sa_invoice_type_is_readonly(), copy=False)

    def _default_l10n_sa_invoice_type(self):
        company = self.env.company.sudo()
        return "Simplified" if company.is_zatca and company.zatca_invoice_type == "Simplified" else "Standard"
            
    l10n_sa_invoice_type = fields.Selection([('Standard', 'Standard'), ('Simplified', 'Simplified')],
                                            string="Invoice Type", copy=False,
                                            default=lambda self: self._default_l10n_sa_invoice_type())

    l10n_is_third_party_invoice = fields.Boolean(string="Is Third Party",
                                                 help="Flag indicating whether the invoice was created by a third party")
    l10n_is_nominal_invoice = fields.Boolean(string="Is Nominal",
                                             help="The invoice is issued for goods that are provided without "
                                                  "consideration as per KSA VAT regulation.")
    l10n_is_exports_invoice = fields.Boolean(string="Is Export",
                                             help="The invoice is issued to a foreign buyer as per KSA VAT regulation.")
    l10n_is_summary_invoice = fields.Boolean(string="Is Summary",
                                             help="The invoice is issued for sales occurring over a period of time and "
                                                  "occurs for some types of invoicing arrangements between seller and "
                                                  "buyer.")
    l10n_is_self_billed_invoice = fields.Boolean(string="Is Self Billed",
                                                 help="The invoice is issued by the buyer instead of the supplier. It "
                                                      "is only applicable in B2B scenarios. It will not have any effect"
                                                      " on the fields, however its mandated that the invoice states "
                                                      "that it is self-billed.")
    zatca_status_code = fields.Char(default="200", copy=False)
    l10n_payment_means_code = fields.Selection([('10', 'cash'), ('30', 'credit'), ('42', 'bank account'),
                                                ('48', 'bank card'), ('1', 'others')], default="10",
                                               string="Payment Means Code",
                                               help='The means, expressed as code, for how a payment is expected to be or has been settled.'
                                                    '(subset of UNTDID 4461)')
    ksa_note = fields.Char(size=1000, required=False)

    # Never show these fields on front
    is_zatca = fields.Boolean(related="company_id.parent_is_zatca")
    is_self_billed = fields.Boolean(related="company_id.parent_root_id.is_self_billed")
    l10n_sa_phase1_end_date = fields.Date(related="company_id.parent_root_id.l10n_sa_phase1_end_date")
    zatca_unique_seq = fields.Char(readonly=True, copy=False)
    zatca_icv_counter = fields.Char(readonly=True, copy=False)
    invoice_uuid = fields.Char('zatca uuid', readonly=True, copy=False)
    zatca_invoice_hash = fields.Char(readonly=True, copy=False)
    zatca_invoice_hash_hex = fields.Char(readonly=True, copy=False)
    zatca_hash_invoice = fields.Binary("ZATCA generated invoice for hash", attachment=True, readonly=True, copy=False)
    zatca_hash_invoice_name = fields.Char(readonly=True, copy=False)
    l10n_sa_response_datetime = fields.Datetime(string='Response DateTime', readonly=True, copy=False)

    def _compute_zatca_onboarding_status(self):
        for record in self:
            com = record.company_id.parent_root_id.sudo()
            if (com.is_zatca and com.zatca_onboarding_status and
                    (not record.zatca_compliance_invoices_api or
                     ("Onboarding failed, restart process !!" not in record.zatca_compliance_invoices_api
                      and "Onboarding in progress" not in record.zatca_compliance_invoices_api))):
                record.zatca_onboarding_status = 1
            else:
                record.zatca_onboarding_status = 0

    zatca_onboarding_status = fields.Boolean(readonly=True, compute="_compute_zatca_onboarding_status", copy=False)

    l10n_sa_qr_code_str = fields.Char(string='Zatka QR Code ', copy=False)
    sa_qr_code_str = fields.Char(string='Zatka QR Code', copy=False, readonly=True)
    # l10n_sa_is_tax_invoice = fields.Boolean(readonly=1, copy=False)

    @api.depends('zatca_compliance_invoices_api', 'l10n_sa_confirmation_datetime')
    def _compute_l10n_sa_zatca_status(self):
        for res in self:
            res.l10n_sa_zatca_status = "Not Sended to Zatca"
            if res.l10n_sa_confirmation_datetime and res.l10n_sa_phase1_end_date and res.l10n_sa_confirmation_datetime.date() <= res.l10n_sa_phase1_end_date:
                res.l10n_sa_zatca_status = "Phase 1"
            elif res.zatca_compliance_invoices_api:
                # res.l10n_sa_zatca_status = res.zatca_compliance_invoices_api
                if res.zatca_compliance_invoices_api.find('<b>reportingStatus</b></td><td colspan="4">REPORTED</td>') > 0:
                    res.l10n_sa_zatca_status = 'REPORTED'
                elif res.zatca_compliance_invoices_api.find('<b>clearanceStatus</b></td><td colspan="4">CLEARED</td>') > 0:
                    res.l10n_sa_zatca_status = 'CLEARED'
                elif res.zatca_compliance_invoices_api.find('<b>reportingStatus</b></td>') > 0:
                    res.l10n_sa_zatca_status = 'Error in reporting'
                elif res.zatca_compliance_invoices_api.find('<b>clearanceStatus</b></td>') > 0:
                    res.l10n_sa_zatca_status = 'Error in clearance'
                else:
                    res.l10n_sa_zatca_status = 'N/A'

    l10n_sa_zatca_status = fields.Char("E-Invoice status", copy=False, readonly=True, store=True,
                                       compute="_compute_l10n_sa_zatca_status")

    @api.onchange('partner_id')
    def _l10n_sa_onchnage_partner_id(self):
        for record in self:
            if not record.l10n_sa_invoice_type_is_readonly:
                if record.partner_id.company_type == 'person':
                    record.l10n_sa_invoice_type = "Simplified"
                else:
                    record.l10n_sa_invoice_type = "Standard"

    @api.onchange('l10n_sa_invoice_type')
    def _l10n_sa_onchnage_invoice_type(self):
        for record in self:
            record.l10n_is_third_party_invoice = 0
            record.l10n_is_nominal_invoice = 0
            record.l10n_is_exports_invoice = 0
            record.l10n_is_summary_invoice = 0
            record.l10n_is_self_billed_invoice = 0

    def get_signature(self, conf=0):
        conf = self.company_id.parent_root_id.sudo() if not conf else conf

        # STEP # 3 in "5. Signing Process"
        # in https://zatca.gov.sa/ar/E-Invoicing/Introduction/Guidelines/Documents/E-invoicing%20Detailed%20Technical%20Guidelines.pdf
        zatca_certificate_status = conf.zatca_certificate_status
        if not zatca_certificate_status:
            raise exceptions.MissingError(_("Register Certificate before proceeding."))

        certificate = conf.csr_certificate
        if not certificate:
            conf.zatca_certificate_status = 0
            raise exceptions.MissingError(_("Certificate not found."))
        original_certificate = certificate.replace('-----BEGIN CERTIFICATE-----', '')\
                                          .replace('-----END CERTIFICATE-----', '')\
                                          .replace(' ', '').replace('\n', '')
        for x in range(1, math.ceil(len(original_certificate) / 64)):
            certificate = certificate[:64 * x + x - 1] + '\n' + certificate[64 * x + x - 1:]
        certificate = "-----BEGIN CERTIFICATE-----\n" + certificate + "\n-----END CERTIFICATE-----"

        sha_256_3 = hashlib.sha256()
        sha_256_3.update(original_certificate.encode())
        base_64_3 = base64.b64encode(sha_256_3.hexdigest().encode()).decode('UTF-8')

        try:
            cert = x509.load_pem_x509_certificate(certificate.encode(), default_backend())
            cert_issuer = ''
            for x in range(len(cert.issuer.rdns) - 1, -1, -1):
                cert_issuer += cert.issuer.rdns[x].rfc4514_string() + ", "
            cert_issuer = cert_issuer[:-2]
        except Exception as e:
            _logger.info("ZATCA: Certificate Decode Issue: " + str(e))
            raise exceptions.AccessError(_("Error decoding Certificate."))
        signature_certificate = '''<ds:Object>
                            <xades:QualifyingProperties Target="signature" xmlns:xades="http://uri.etsi.org/01903/v1.3.2#">
                                <xades:SignedProperties Id="xadesSignedProperties">
                                    <xades:SignedSignatureProperties>
                                        <xades:SigningTime>''' + fields.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ') + '''</xades:SigningTime>
                                        <xades:SigningCertificate>
                                            <xades:Cert>
                                                <xades:CertDigest>
                                                    <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
                                                    <ds:DigestValue>''' + str(base_64_3) + '''</ds:DigestValue>
                                                </xades:CertDigest>
                                                <xades:IssuerSerial>
                                                    <ds:X509IssuerName>''' + str(cert_issuer) + '''</ds:X509IssuerName>
                                                    <ds:X509SerialNumber>''' + str(cert.serial_number) + '''</ds:X509SerialNumber>
                                                </xades:IssuerSerial>
                                            </xades:Cert>
                                        </xades:SigningCertificate>
                                    </xades:SignedSignatureProperties>
                                </xades:SignedProperties>
                            </xades:QualifyingProperties>
                        </ds:Object>'''
        # STEP # 5 in "5. Signing Process"
        # in https://zatca.gov.sa/ar/E-Invoicing/Introduction/Guidelines/Documents/E-invoicing%20Detailed%20Technical%20Guidelines.pdf

        signature_certificate_for_hash = '''<xades:SignedProperties xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" Id="xadesSignedProperties">
                                    <xades:SignedSignatureProperties>
                                        <xades:SigningTime>''' + fields.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ') + '''</xades:SigningTime>
                                        <xades:SigningCertificate>
                                            <xades:Cert>
                                                <xades:CertDigest>
                                                    <ds:DigestMethod xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
                                                    <ds:DigestValue xmlns:ds="http://www.w3.org/2000/09/xmldsig#">''' + str(base_64_3) + '''</ds:DigestValue>
                                                </xades:CertDigest>
                                                <xades:IssuerSerial>
                                                    <ds:X509IssuerName xmlns:ds="http://www.w3.org/2000/09/xmldsig#">''' + str(cert_issuer) + '''</ds:X509IssuerName>
                                                    <ds:X509SerialNumber xmlns:ds="http://www.w3.org/2000/09/xmldsig#">''' + str(cert.serial_number) + '''</ds:X509SerialNumber>
                                                </xades:IssuerSerial>
                                            </xades:Cert>
                                        </xades:SigningCertificate>
                                    </xades:SignedSignatureProperties>
                                </xades:SignedProperties>'''
        sha_256_5 = hashlib.sha256()
        sha_256_5.update(signature_certificate_for_hash.encode())
        base_64_5 = base64.b64encode(sha_256_5.hexdigest().encode()).decode('UTF-8')

        signature = '''      <ds:SignedInfo>
                                <ds:CanonicalizationMethod Algorithm="http://www.w3.org/2006/12/xml-c14n11"/>
                                <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
                                <ds:Reference Id="invoiceSignedData" URI="">
                                    <ds:Transforms>
                                        <ds:Transform Algorithm="http://www.w3.org/TR/1999/REC-xpath-19991116">
                                            <ds:XPath>not(//ancestor-or-self::ext:UBLExtensions)</ds:XPath>
                                        </ds:Transform>
                                        <ds:Transform Algorithm="http://www.w3.org/TR/1999/REC-xpath-19991116">
                                            <ds:XPath>not(//ancestor-or-self::cac:Signature)</ds:XPath>
                                        </ds:Transform>
                                        <ds:Transform Algorithm="http://www.w3.org/TR/1999/REC-xpath-19991116">
                                            <ds:XPath>not(//ancestor-or-self::cac:AdditionalDocumentReference[cbc:ID="QR"])</ds:XPath>
                                        </ds:Transform>
                                        <ds:Transform Algorithm="http://www.w3.org/2006/12/xml-c14n11"/>
                                    </ds:Transforms>
                                    <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
                                    <ds:DigestValue>zatca_invoice_hash</ds:DigestValue>
                                </ds:Reference>
                                <ds:Reference Type="http://www.w3.org/2000/09/xmldsig#SignatureProperties" URI="#xadesSignedProperties">
                                    <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
                                    <ds:DigestValue>zatca_signature_hash</ds:DigestValue>
                                </ds:Reference>
                            </ds:SignedInfo>
                            <ds:SignatureValue>zatca_signature_value</ds:SignatureValue>
                            <ds:KeyInfo>
                                <ds:X509Data>
                                    <ds:X509Certificate>''' + str(original_certificate) + '''</ds:X509Certificate>
                                </ds:X509Data>
                            </ds:KeyInfo>'''

        return signature, signature_certificate, base_64_5

    def invoice_ksa_validations(self):
        message = ""
        partner_id, company_id, buyer_identification, buyer_identification_no, license, license_no = self._get_partner_comapny(self.company_id)

        if self.move_type in ['in_invoice', 'in_refund'] and not self.l10n_is_self_billed_invoice:
            raise exceptions.MissingError(_('Must be is self billed vendor bill.'))

        if company_id.currency_id.name != 'SAR':
            # BR-KSA-CL-02
            message += _("currency must be SAR.") + "\n"    # BR-KSA-CL-02
        if len(self.invoice_line_ids.ids) <= 0:
            message += _("at least one invoice line is required.") + "\n"

        if len(self.invoice_line_ids.ids) != len([inv_line.product_id.id for inv_line in self.invoice_line_ids if inv_line.product_id.id]):
            message += _("one or more invoice line does not have a product.") + "\n"

        invoice_fields = ['l10n_sa_invoice_type', 'l10n_payment_means_code', 'delivery_date']
        missing_company_fields = [self._fields[invoice_field].string for invoice_field in invoice_fields if not self[invoice_field]]
        if len(missing_company_fields) > 0:
            raise exceptions.MissingError(' , '.join(missing_company_fields) + ' ' + _("are missing in invoice"))

        missing_product_fields = []
        for invoice_line in self.invoice_line_ids:
            product_data = self._get_zatca_product_name(invoice_line)
            product_fields = [product_data["name"]['field']]
            missing_product_fields += [invoice_line._fields[product_field].string + " " + _("in product") + " " + invoice_line.name + "\n"  for product_field in product_fields if not invoice_line[product_field]]

        if len(missing_product_fields) > 0:
            message += ' , '.join(missing_product_fields) + _("are missing.") + '\n'

        company_data = self._get_zatca_partner_data() if self.l10n_is_self_billed_invoice else self._get_zatca_company_data(self.company_id.parent_root_id)
        company_fields = [company_data["district"]['field'], company_data["city"]['field'], company_data["street"]['field'], 'building_no', 'zip', 'vat']
        company_fields += ["buyer_identification", "buyer_identification_no"] if self.l10n_is_self_billed_invoice else ['license', 'license_no']
        company_fields_ids = ['country_id']
        missing_company_fields = [company_id._fields[company_field].string for company_field in company_fields if not company_id[company_field]]
        missing_company_fields_ids = [company_id._fields[company_field].string for company_field in company_fields_ids if not company_id[company_field]['id']]
        if company_id.state_id.id:
            state_fields = [company_data['state_id_name']['field']]
            missing_state_field_fields = [company_id.state_id._fields[state_field].string for state_field in state_fields if not company_id.state_id[state_field]]
            if len(missing_state_field_fields) > 0:
                message += ' , '.join(missing_state_field_fields) + ' ' + _("are missing in Company State.") + '\n'

        if len(missing_company_fields) > 0 or len(missing_company_fields_ids) > 0:
            message += ' , '.join(missing_company_fields_ids + missing_company_fields) + ' ' + _("are missing in Company Address.") + '\n'

        if company_id.building_no and len(company_id.building_no) != 4:
            message += _('Company Building Number must be exactly 4 digits.') + "\n"
        if company_id.zip and len(company_id.zip) != 5:
            message += _('Company zip must be exactly 5 digits.') + "\n"
        if company_id.vat:
            if len(company_id.vat) != 15:
                message += _('Company Vat must be exactly 15 digits.') + "\n"
            if str(company_id.vat)[0] != '3' or str(company_id.vat)[-1] != '3':
                message += _('Company Vat must start/end with 3.') + "\n"
        if license not in ['CRN', "MOM", "MLS", "SAG", "OTH", "700"]:
            company_field = "buyer_identification" if self.l10n_is_self_billed_invoice else 'license'
            message += _("Company ") + company_id._fields[company_field].string + " " + _("must be one of these") +\
                       "\n['Commercial Registration number', 'Momrah license', 'MHRSD license', 'MISA license', 'Other OD', '700 Number']." + "\n"

        if message != "":
            raise exceptions.ValidationError(message)

    def _get_partner_comapny(self, company_id, no_parent=0):
        if self.l10n_is_self_billed_invoice:
            self_company = company_id
            partner_id = company_id.parent_root_id
            company_id = self.partner_id
            license = self.partner_id.buyer_identification
            license_no = self.partner_id.buyer_identification_no
            buyer_identification = self_company.license
            buyer_identification_no = self_company.license_no
        else:
            partner_id = self.partner_id
            buyer_identification = self.partner_id.buyer_identification
            buyer_identification_no = self.partner_id.buyer_identification_no
            license = company_id.license
            license_no = company_id.license_no
            company_id = company_id.parent_root_id

        return partner_id, company_id, buyer_identification, buyer_identification_no, license, license_no

    def tax_invoice_validations(self):
        message = "For tax invoice \n"
        conf = self.company_id.parent_root_id.sudo()
        partner_id, company_id, buyer_identification, buyer_identification_no, license, license_no = self._get_partner_comapny(self.company_id)

        if (not (buyer_identification and buyer_identification_no) and not (partner_id.vat)):
            message += _("customer vat or buyer_identification is required") + "\n"

        if conf.csr_invoice_type[0:1] != '1':
            raise exceptions.AccessDenied(_("Certificate not allowed for Standard Invoices."))
        if self.l10n_is_exports_invoice:
            if partner_id.country_id.code == 'SA':
                message += _("Country can't be KSA for exports invoice") + "\n"
            if not (buyer_identification or buyer_identification_no):
                message += _("buyer_identification is required for exports invoice") + "\n"

        partner_data = self._get_zatca_company_data(self.company_id.parent_root_id) if self.l10n_is_self_billed_invoice else self._get_zatca_partner_data()
        partner_fields = [partner_data["city"]['field'], partner_data["street"]['field'], 'zip']
        partner_fields_ids = ['country_id']
        if partner_id.country_id.code == 'SA':
            partner_fields += ['building_no', partner_data["city"]['field']]
        if partner_id.state_id.id:
            state_fields = [partner_data['state_id_name']['field']]
            missing_state_fields = [partner_id.state_id._fields[state_field].string for state_field in state_fields if not partner_id.state_id[state_field]]
            if len(missing_state_fields) > 0:
                message += ' , '.join(missing_state_fields) + ' ' + _("are missing in Customer State.") + '\n'

        missing_partner_fields = [partner_id._fields[partner_field].string for partner_field in partner_fields if not partner_id[partner_field]]
        missing_partner_fields_ids = [partner_id._fields[partner_fields_id].string for partner_fields_id in partner_fields_ids if not partner_id[partner_fields_id]['id']]

        if len(missing_partner_fields) > 0 or len(missing_partner_fields_ids) > 0:
            message += ' , '.join(missing_partner_fields_ids + missing_partner_fields) +\
                       ' ' + _("are missing in Customer Address, which are required for tax invoices") + "\n"

        if (partner_id.country_id.code == "SA" and partner_id.zip and
                (len(str(partner_id.zip)) != 5 or not partner_id.zip.isdigit())):
            message += _("Customer PostalZone/Zip must be exactly 5 digits") + "\n"

        if partner_id.vat and not self.l10n_is_exports_invoice:
            if len(str(partner_id.vat)) != 15:
                message += _("Customer Vat must be exactly 15 digits") + "\n"
            if str(partner_id.vat)[0] != '3' or str(partner_id.vat)[-1] != '3':
                message += _("Customer Vat must start/end with 3") + "\n"
            if company_id.vat == partner_id.vat:
                message += _("Vat can't be same for customer and company.") + "\n"

        if message != "For tax invoice \n":
            raise exceptions.ValidationError(message)

    def check_allowed_size(self, start, end, value, field):
        if not(start <= len(str(value)) <= end):
            message = _("ksa limit error for field)" + " %s :: %s , " + _("allowed limit is between") + " %s - %s " % (field, value, start, end))
            _logger.info(message)
            raise exceptions.ValidationError(message.replace('::',''))
        return str(value)

    def _get_zatca_company_data(self, company_id):
        # arabic only fields
        lang = self.env.user.partner_id.lang
        # lang = 'ar_001'
        conf = company_id.with_context(lang=lang).sudo()
        # These fields must be in res.company
        data = {
            "name": {'value': conf.name, 'field': 'name'},
            "street": {'value': conf.street, 'field': 'street'},
            "street2": {'value': conf.street2, 'field': 'street2'},
            "district": {'value': conf.district, 'field': 'district'},
            "city": {'value': conf.city, 'field': 'city'}
        }
        # These fields must be in res.country.state
        data.update({
            "state_id_name": {'value': conf.state_id.name, 'field': 'name'}, #state_id.name
        })
        # These fields must be in res.country
        data.update({
            "country_id_name": {'value': conf.country_id.name, 'field': 'name'}, # only for reports
        })

        return data

    def _get_zatca_product_name(self, invoice_line_id):
        # arabic only fields
        lang = self.env.user.partner_id.lang
        # lang = 'ar_001'
        # product = invoice_line_id.product_id.with_context(lang=lang)
        # These fields must be in account.move.line
        product = invoice_line_id.with_context(lang=lang)
        return {"name": {'value': product.name, 'field': 'name'}}

    def _get_zatca_partner_data(self):
        # arabic only fields
        lang = self.env.user.partner_id.lang
        # lang = 'ar_001'
        partner = self.partner_id.with_context(lang=lang)
        # These fields must be in res.partner
        data = {
            "name": {'value': partner.name, 'field': 'name'},
            "street": {'value': partner.street, 'field': 'street'},
            "street2": {'value': partner.street2, 'field': 'street2'},
            "district": {'value': partner.district, 'field': 'district'},
            "city": {'value': partner.city, 'field': 'city'}
        }
        # These fields must be in res.country.state
        data.update({
            "state_id_name": {'value': partner.state_id.name, 'field': 'name'}, #state_id.name
        })
        # These fields must be in res.country
        data.update({
            "country_id_name": {'value': partner.country_id.name, 'field': 'name'}, # only for reports
        })

        return data

    @mute_logger('Zatca Debugger for account.move :')
    def create_xml_file(self, previous_hash=0, pos_refunded_order_id=0):
        amount_verification = 0  # for debug mode
        conf = self.company_id.parent_root_id.sudo()
        conf_company = self._get_zatca_partner_data() if self.l10n_is_self_billed_invoice else self._get_zatca_company_data(self.company_id.parent_root_id)
        conf_partner = self._get_zatca_company_data(self.company_id.parent_root_id) if self.l10n_is_self_billed_invoice else self._get_zatca_partner_data()
        if not conf.is_zatca:
            raise exceptions.AccessDenied(_("Zatca is not activated."))
        # No longer needed
        # if not previous_hash:
        #     self.create_xml_file(previous_hash=1)

        partner_id, company_id, buyer_identification, buyer_identification_no, license, license_no = self._get_partner_comapny(self.company_id)
        signature, signature_certificate, base_64_5 = self.get_signature()

        # UBL 2.1 sequence
        self.invoice_ksa_validations()
        l10n_sa_delivery_date = self.delivery_date

        bt_3 = '383' if self.debit_origin_id.id else ('381' if self.move_type in ['out_refund', 'in_refund'] else '388')
        bt_25 = self.env['account.move']
        if bt_3 != '388':
            # if 'Shop' in self.ref:
            #     bt_25 = self.env['pos.order'].search([('account_move', '=', self.id)])
            #     bt_25_name = str(self.ref.replace(' REFUND', '')[0: len(self.ref.replace(' REFUND', ''))])
            #     bt_25 = self.env['pos.order'].search(
            #         [('name', '=', bt_25_name), ('session_id', '=', bt_25.session_id.id)]).account_move
            if pos_refunded_order_id:
                bt_25 = self.env['account.move'].browse(int(pos_refunded_order_id))
            else:
                bt_25 = self.reversed_entry_id or self.debit_origin_id
                if not self.ref or not bt_25.id:
                    raise exceptions.MissingError(_('Original Invoice Ref not found.'))
            if bt_25.l10n_sa_invoice_type != self.l10n_sa_invoice_type:
                self.l10n_sa_invoice_type = bt_25.l10n_sa_invoice_type
                raise exceptions.ValidationError(_("Mismatched Invoice Type for original and associated invoice."))
            if not bt_25.l10n_sa_confirmation_datetime:
                bt_25.l10n_sa_confirmation_datetime = datetime.datetime.combine(bt_25.invoice_date, datetime.time(0, 0))

        is_tax_invoice = 1 if self.l10n_sa_invoice_type == 'Standard' else 0
        if is_tax_invoice:
            self.tax_invoice_validations()

            if self.l10n_is_exports_invoice:
                partner_data = self._get_zatca_partner_data()
                partner_fields_ids = ['state_id']
                missing_partner_fields_ids = [partner_id._fields[partner_fields_id].string for partner_fields_id in partner_fields_ids if not partner_id[partner_fields_id]['id']]
                if len(missing_partner_fields_ids) > 0:
                    message = ' , '.join(missing_partner_fields_ids) + ' ' + _("are missing in Customer Address") + ', '\
                              + _("which are required for tax invoices, in case of non-ksa resident.")
                    raise exceptions.ValidationError(message)

        if not is_tax_invoice and conf.csr_invoice_type[1:2] != '1':
            raise exceptions.AccessDenied(_("Certificate not allowed for Simplified Invoices."))

        self.invoice_uuid = self.invoice_uuid if self.invoice_uuid and self.invoice_uuid != '' else str(str(uuid.uuid4()))

        ksa_16 = int(conf.zatca_icv_counter)
        ksa_16 += 1
        conf.zatca_icv_counter = str(ksa_16)

        company_vat = 0
        # BR-KSA-26
        # ksa_13 = 0
        # ksa_13 = base64.b64encode(bytes(hashlib.sha256(str(ksa_13).encode('utf-8')).hexdigest(), encoding='utf-8')).decode('UTF-8')

        def get_pih(self, icv):
            try:
                pih = self.search([('zatca_icv_counter', '=', str(int(icv) - 1))])
                if icv < 0:
                    raise
                if not pih.id:
                    icv = icv -1
                    pih = get_pih(self, icv)
            except:
                return False
            return pih

        pih = get_pih(self, ksa_16)
        self.zatca_icv_counter = str(ksa_16)
        ksa_13 = pih.zatca_invoice_hash if pih else 'NWZlY2ViNjZmZmM4NmYzOGQ5NTI3ODZjNmQ2OTZjNzljMmRiYzIzOWRkNGU5MWI0NjcyOWQ3M2EyN2ZiNTdlOQ=='
        # signature = 0 if is_tax_invoice else 1
        # BR-KSA-31 (KSA-2)
        ksa_2 = '01' if is_tax_invoice else '02'  # Simplified in case of tax category O
        ksa_2 += str(int(self.l10n_is_third_party_invoice))
        ksa_2 += str(int(self.l10n_is_nominal_invoice))
        # ksa_2 += str(int(self.l10n_is_exports_invoice))
        ksa_2 += "0" if not is_tax_invoice else str(int(self.l10n_is_exports_invoice))
        ksa_2 += str(int(self.l10n_is_summary_invoice))
        ksa_2 += "0" if self.l10n_is_exports_invoice or not is_tax_invoice else str(int(self.l10n_is_self_billed_invoice))

        document_currency = self.currency_id.name
        document_level_allowance_charge = 0
        vat_tax = 0
        bt_31 = company_id.vat
        bg_23_list = {}
        bt_92 = 0  # No document level allowance, in default odoo
        bt_106 = float('{:0.2f}'.format(float_round(0, precision_rounding=0.01)))  # Sum of bt-131 Calculated in invoice line loop.
        bt_107 = float('{:0.2f}'.format(float_round(bt_92, precision_rounding=0.01)))
        delivery = 1
        not_know = 0
        ksa_note = 0
        # bt_81 = 10 if 'cash' else (30 if 'credit' else (42 if 'bank account' else (48 if 'bank card' else 1)))
        bt_81 = self.l10n_payment_means_code
        accounting_seller_party = 0
        self.zatca_unique_seq = self.name
        bt_1 = self.zatca_unique_seq
        ubl_2_1 = '''
        <Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
                 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
                 xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2">'''
        # if not ksa_13 and signature:  # need to check this
        if signature and not previous_hash and not is_tax_invoice:
            ubl_2_1 += '''
            <ext:UBLExtensions>'''
            if signature:
                ubl_2_1 += '''
                <ext:UBLExtension>
                    <ext:ExtensionURI>urn:oasis:names:specification:ubl:dsig:enveloped:xades</ext:ExtensionURI>
                    <ext:ExtensionContent>
                        <sig:UBLDocumentSignatures xmlns:sac="urn:oasis:names:specification:ubl:schema:xsd:SignatureAggregateComponents-2" 
                                                   xmlns:sbc="urn:oasis:names:specification:ubl:schema:xsd:SignatureBasicComponents-2"
                                                   xmlns:sig="urn:oasis:names:specification:ubl:schema:xsd:CommonSignatureComponents-2">
                            <sac:SignatureInformation>
                                <cbc:ID>urn:oasis:names:specification:ubl:signature:1</cbc:ID>
                                <sbc:ReferencedSignatureID>urn:oasis:names:specification:ubl:signature:Invoice</sbc:ReferencedSignatureID>
                                <ds:Signature Id="signature" xmlns:ds="http://www.w3.org/2000/09/xmldsig#">'''
                ubl_2_1 += signature
                ubl_2_1 += signature_certificate
                ubl_2_1 += '''  </ds:Signature>
                            </sac:SignatureInformation>
                        </sig:UBLDocumentSignatures>
                    </ext:ExtensionContent>
                </ext:UBLExtension>      '''
            ubl_2_1 += '''
            </ext:UBLExtensions>'''
        if not previous_hash:
            ubl_2_1 += '''
                <cbc:UBLVersionID>2.1</cbc:UBLVersionID>'''
        ubl_2_1 += '''
            <cbc:ProfileID>reporting:1.0</cbc:ProfileID>
            <cbc:ID>''' + str(self.check_allowed_size(1,127, bt_1, 'bt_1')) + '''</cbc:ID>
            <cbc:UUID>''' + self.invoice_uuid + '''</cbc:UUID>
            <cbc:IssueDate>''' + self.l10n_sa_confirmation_datetime.strftime('%Y-%m-%d') + '''</cbc:IssueDate>
            <cbc:IssueTime>''' + self.l10n_sa_confirmation_datetime.strftime('%H:%M:%SZ') + '''</cbc:IssueTime>
            <cbc:InvoiceTypeCode name="''' + ksa_2 + '''">''' + bt_3 + '''</cbc:InvoiceTypeCode>'''
        if self.ksa_note:
            ubl_2_1 += '''
            <cbc:Note>''' + self.check_allowed_size(0,1000, self.ksa_note, self._fields['ksa_note'].string) + '''</cbc:Note>'''
        ubl_2_1 += '''
            <cbc:DocumentCurrencyCode>''' + document_currency + '''</cbc:DocumentCurrencyCode>
            <cbc:TaxCurrencyCode>SAR</cbc:TaxCurrencyCode>'''
        if self.purchase_id.id:
            ubl_2_1 += '''
            <cac:OrderReference>
                <cbc:ID>''' + str(self.check_allowed_size(0,127, self.purchase_id.id, self._fields['purchase_id'].string)) + '''</cbc:ID>
            </cac:OrderReference>'''
        if bt_3 != '388':  # BR-KSA-56
            ubl_2_1 += '''
            <cac:BillingReference>
                <cac:InvoiceDocumentReference>
                    <cbc:ID>''' + str(self.check_allowed_size(1,5000,bt_25.id,'bt_25')) + '''</cbc:ID>
                    <cbc:IssueDate>''' + str(bt_25.l10n_sa_confirmation_datetime.strftime('%Y-%m-%d')) + '''</cbc:IssueDate>
                </cac:InvoiceDocumentReference>
            </cac:BillingReference>'''
        ubl_2_1 += '''
            <cac:AdditionalDocumentReference>
                <cbc:ID>ICV</cbc:ID>
                <cbc:UUID>''' + str(ksa_16) + '''</cbc:UUID>
            </cac:AdditionalDocumentReference>
            <cac:AdditionalDocumentReference>
                <cbc:ID>PIH</cbc:ID>
                <cac:Attachment>
                    <cbc:EmbeddedDocumentBinaryObject mimeCode="text/plain">''' + str(ksa_13) + '''</cbc:EmbeddedDocumentBinaryObject>
                </cac:Attachment>
            </cac:AdditionalDocumentReference>'''
        if not is_tax_invoice:
        # if is_tax_invoice:
            ubl_2_1 += '''<cac:AdditionalDocumentReference>
                <cbc:ID>QR</cbc:ID>
                <cac:Attachment>
                    <cbc:EmbeddedDocumentBinaryObject mimeCode="text/plain">zatca_l10n_sa_qr_code_str</cbc:EmbeddedDocumentBinaryObject>
                </cac:Attachment>
            </cac:AdditionalDocumentReference>'''
        if not previous_hash and not is_tax_invoice:
            if signature:  # BR-KSA-60
                ubl_2_1 += '''
            <cac:Signature>
                <cbc:ID>urn:oasis:names:specification:ubl:signature:Invoice</cbc:ID>
                <cbc:SignatureMethod>urn:oasis:names:specification:ubl:dsig:enveloped:xades</cbc:SignatureMethod>
            </cac:Signature>'''
        ubl_2_1 += self.get_AccountingSupplierParty(self.company_id)
        ubl_2_1 += '''
            <cac:AccountingCustomerParty>
                <cac:Party>'''
        if buyer_identification and buyer_identification_no:
            ubl_2_1 += '''<cac:PartyIdentification>
                        <cbc:ID schemeID="''' + buyer_identification + '''">''' + buyer_identification_no + '''</cbc:ID>
                    </cac:PartyIdentification>'''
        if is_tax_invoice:
            ubl_2_1 += '''
                    <cac:PostalAddress>
                        <cbc:StreetName>''' + self.check_allowed_size(1, 1000, conf_partner["street"]["value"],"Customer " + partner_id._fields[conf_partner["street"]["field"]].string) + '''</cbc:StreetName>'''
            if partner_id.street2:
                ubl_2_1 += '''
                        <cbc:AdditionalStreetName>''' + self.check_allowed_size(0, 127, conf_partner["street2"]["value"], "Customer %s" % partner_id._fields[conf_partner["street2"]["field"]].string) + '''</cbc:AdditionalStreetName>'''
            if partner_id.country_id.code == 'SA' or partner_id.building_no:
                ubl_2_1 += '''
                        <cbc:BuildingNumber>''' + str(partner_id.building_no) + '''</cbc:BuildingNumber>'''
            if partner_id.additional_no:
                ubl_2_1 += '''
                        <cbc:PlotIdentification>''' + str(
                    partner_id.additional_no) + '''</cbc:PlotIdentification>'''
            if partner_id.country_id.code == 'SA' or conf_partner["district"]["value"]:
                ubl_2_1 += '''
                        <cbc:CitySubdivisionName>''' + self.check_allowed_size(1, 127, conf_partner["district"]["value"], "Customer %s" % partner_id._fields[conf_partner["district"]["field"]].string) + '''</cbc:CitySubdivisionName>'''
            ubl_2_1 += '''
                        <cbc:CityName>''' + self.check_allowed_size(1, 127, conf_partner["city"]["value"], "Customer %s" % partner_id._fields[conf_partner["city"]["field"]].string) + '''</cbc:CityName>'''
            if partner_id.country_id.code == 'SA' or partner_id.zip:
                ubl_2_1 += '''
                        <cbc:PostalZone>''' + str(partner_id.zip) + '''</cbc:PostalZone>'''
            if partner_id.state_id.id:
                ubl_2_1 += '''
                        <cbc:CountrySubentity>''' + self.check_allowed_size(1, 127, conf_partner["state_id_name"]["value"], "Customer %s %s" % (partner_id._fields['state_id'].string, partner_id.state_id._fields[conf_partner["state_id_name"]["field"]].string)) + '''</cbc:CountrySubentity>'''
            ubl_2_1 += '''
                        <cac:Country>
                            <cbc:IdentificationCode>''' + partner_id.country_id.code + '''</cbc:IdentificationCode>
                        </cac:Country>
                    </cac:PostalAddress>
                    <cac:PartyTaxScheme>'''
            if partner_id.vat and not self.l10n_is_exports_invoice:
                ubl_2_1 += '''
                        <cbc:CompanyID>''' + partner_id.vat + '''</cbc:CompanyID>'''
            ubl_2_1 += '''
                        <cac:TaxScheme>
                            <cbc:ID>VAT</cbc:ID>
                        </cac:TaxScheme>
                    </cac:PartyTaxScheme>'''
        bt_121 = 0  # in ['VATEX-SA-EDU', 'VATEX-SA-HEA']
        bt_121 = list(set(self.invoice_line_ids.tax_ids.mapped('tax_exemption_selection')))
        # BR-KSA-25 and BR-KSA-42
        if is_tax_invoice or \
                (not is_tax_invoice and ('VATEX-SA-EDU' in bt_121 or 'VATEX-SA-HEA' in bt_121)) or \
                (not is_tax_invoice and self.l10n_is_summary_invoice):
            ubl_2_1 += '''
                    <cac:PartyLegalEntity>
                        <cbc:RegistrationName>''' + self.check_allowed_size(1, 1000, conf_partner["name"]["value"],
                                                                             "Customer %s" % partner_id._fields[conf_partner["name"]["field"]].string) + '''</cbc:RegistrationName>
                    </cac:PartyLegalEntity>'''
        if ('VATEX-SA-EDU' in bt_121 or 'VATEX-SA-HEA' in bt_121) and buyer_identification != 'NAT':  # BR-KSA-49
            message = _("As tax exemption reason code is in") + " 'VATEX-SA-EDU', 'VATEX-SA-HEA'"
            message += " " + _("then Buyer Identification must be") + " 'NAT'"
            raise exceptions.ValidationError(message)
        ubl_2_1 += '''
                </cac:Party>
            </cac:AccountingCustomerParty>'''
        latest_delivery_date = 1 if not is_tax_invoice and self.l10n_is_summary_invoice else 0
        if delivery and ((bt_3 == '388' and ksa_2[:2] == '01' or not is_tax_invoice and self.l10n_is_summary_invoice) or (latest_delivery_date and not_know)):
            ubl_2_1 += '''
            <cac:Delivery>'''
            ksa_5 = l10n_sa_delivery_date
            if bt_3 == '388' and ksa_2[:2] == '01' or not is_tax_invoice and self.l10n_is_summary_invoice:
                ubl_2_1 += '''
                <cbc:ActualDeliveryDate>''' + str(ksa_5.strftime('%Y-%m-%d')) + '''</cbc:ActualDeliveryDate>'''
            if latest_delivery_date and not_know:
                ksa_24 = l10n_sa_delivery_date
                if ksa_24 < ksa_5:
                    raise exceptions.ValidationError(_('LatestDeliveryDate must be less then or equal to ActualDeliveryDate'))
                ubl_2_1 += '''
                <cbc:LatestDeliveryDate> ''' + str(ksa_24.strftime('%Y-%m-%d')) + ''' </cbc:LatestDeliveryDate> '''
            if not_know:
                ubl_2_1 += '''
                <cac:DeliveryLocation>
                    <cac:Address>
                        <cac:Country>
                            <cbc:IdentificationCode>''' + "" + '''</cbc:IdentificationCode>
                        </cac:Country>
                    </cac:Address>
                </cac:DeliveryLocation'''
            ubl_2_1 += '''
            </cac:Delivery>'''
        ubl_2_1 += '''<cac:PaymentMeans>
            <cbc:PaymentMeansCode>''' + str(bt_81) + '''</cbc:PaymentMeansCode>'''
        if bt_3 != '388':
            ubl_2_1 += '''
            <cbc:InstructionNote>''' + self.check_allowed_size(1, 1000, self.credit_debit_reason,  self._fields['credit_debit_reason'].string) + '''</cbc:InstructionNote>'''
        ubl_2_1 += '''
        </cac:PaymentMeans>'''
        if document_level_allowance_charge:
            bt_96 = float('{:0.2f}'.format(float_round(0, precision_rounding=0.01)))
            bt_96 = 100 if bt_96 > 100 else (0 if bt_96 < 0 else bt_96)
            ubl_2_1 += '''
            <cac:AllowanceCharge>
                <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
                <cbc:AllowanceChargeReason>Discount</cbc:AllowanceChargeReason>
                <cbc:Amount currencyID="''' + document_currency + '''">''' + str(bt_92) + '''</cbc:Amount>
                <cbc:BaseAmount currencyID="''' + document_currency + '''">''' + str(bt_92) + '''</cbc:BaseAmount>
                <cac:TaxCategory>
                    <cbc:ID>''' + "0" + '''</cbc:ID>
                    <cbc:Percent>''' + str(bt_96) + '''</cbc:Percent>
                    <cac:TaxScheme>
                        <cbc:ID>''' + "0" + '''</cbc:ID>
                    </cac:TaxScheme>
                </cac:TaxCategory>
            </cac:AllowanceCharge>'''
        invoice_line_xml = ''
        for invoice_line_id in self.invoice_line_ids:
            if invoice_line_id.discount:
                bt_137 = float('{:0.2f}'.format(float_round(invoice_line_id.price_unit * invoice_line_id.quantity, precision_rounding=0.01)))
                bt_138 = invoice_line_id.discount  # BR-KSA-DEC-01 for BT-138 only done
                bt_136 = float('{:0.2f}'.format(float_round(bt_137 * bt_138 / 100, precision_rounding=0.01)))
            else:
                bt_136 = float('{:0.2f}'.format(float_round(0, precision_rounding=0.01)))
                bt_137 = float('{:0.2f}'.format(float_round(0, precision_rounding=0.01)))
                bt_138 = invoice_line_id.discount  # BR-KSA-DEC-01 for BT-138 only done
            bt_129 = invoice_line_id.quantity
            bt_147 = 0  # NO ITEM PRICE DISCOUNT bt_148 * invoice_line_id.discount/100 if invoice_line_id.discount else 0
            bt_148 = invoice_line_id.price_unit
            bt_146 = bt_148 - bt_147
            bt_149 = 1  # ??
            bt_131 = float('{:0.2f}'.format(float_round(((bt_146 / bt_149) * bt_129), precision_rounding=0.01)))
            bt_131 -= float('{:0.2f}'.format(float_round(bt_136, precision_rounding=0.01)))
            bt_131 = float('{:0.2f}'.format(float_round(bt_131, precision_rounding=0.01)))
            bt_106 += float('{:0.2f}'.format(float_round(bt_131, precision_rounding=0.01)))
            bt_106 = float('{:0.2f}'.format(float_round(bt_106, precision_rounding=0.01)))
            bt_151 = invoice_line_id.tax_ids.classified_tax_category if invoice_line_id.tax_ids else "O"
            bt_152 = float('{:0.2f}'.format(float_round(invoice_line_id.tax_ids.amount, precision_rounding=0.01))) if invoice_line_id.tax_ids else 0
            bt_152 = 100 if bt_152 > 100 else (0 if bt_152 < 0 else bt_152)

            if bt_151 == "Z":
                bt_152 = 0
                if not bg_23_list.get("Z", False):
                    bg_23_list["Z"] = {'bt_116': 0, 'bt_121': invoice_line_id.tax_ids.tax_exemption_code,
                                       'bt_120': invoice_line_id.tax_ids.tax_exemption_text,
                                       'bt_119': bt_152, 'bt_117': 0}
                bg_23_list["Z"]['bt_116'] += bt_131
                # bg_23_list = ["Z"]  # BR-Z-01
            elif bt_151 == "E":
                bt_152 = 0
                if not bg_23_list.get("E", False):
                    bg_23_list["E"] = {'bt_116': 0, 'bt_121': invoice_line_id.tax_ids.tax_exemption_code,
                                       'bt_120': invoice_line_id.tax_ids.tax_exemption_text,
                                       'bt_119': bt_152, 'bt_117': 0}
                bg_23_list["E"]['bt_116'] += bt_131
                # bg_23_list = ["E"]  # BR-E-01
            elif bt_151 == "S":
                if not bg_23_list.get("S", False):
                    bg_23_list["S"] = {'bt_116': 0, 'bt_119': bt_152, 'bt_117': 0}
                bg_23_list["S"]['bt_116'] += bt_131
                # bg_23_list = ["E"]  # BR-S-09
            # elif bt_151 == "O":
            else:
                bt_152 = 0
                if bg_23_list.get('O') and bg_23_list['O'].get('bt_120', False) != (invoice_line_id.tax_ids.tax_exemption_text if len(invoice_line_id.tax_ids) > 0 else 'Not subject to VAT'):
                    raise exceptions.MissingError(_("Multiple tax reasons for tax categpry") + (" 'O' ") + _("can't be applied in one invoice"))
                if not bg_23_list.get("O", False):
                    if invoice_line_id.tax_ids and (not invoice_line_id.tax_ids.tax_exemption_text or
                                                    not invoice_line_id.tax_ids.tax_exemption_code):
                        raise exceptions.MissingError(_("Tax exemption Reason Text  is missing in Tax Category") + " 'O' ")
                    bg_23_list["O"] = {'bt_116': 0,
                                       'bt_121': invoice_line_id.tax_ids.tax_exemption_code if
                                                    len(invoice_line_id.tax_ids) > 0 else 'VATEX-SA-OOS',
                                       'bt_120': invoice_line_id.tax_ids.tax_exemption_text if
                                                    len(invoice_line_id.tax_ids) > 0 else 'Not subject to VAT',
                                       'bt_119': 0, 'bt_117': 0}
                bg_23_list["O"]['bt_116'] += bt_131
                # bg_23_list = ["O"]  # BR-O-01

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

            invoice_line_xml += '''
            <cac:InvoiceLine>
                <cbc:ID>''' + str(invoice_line_id.zatca_id) + '''</cbc:ID>
                <cbc:InvoicedQuantity unitCode="PCE">''' + str(bt_129) + '''</cbc:InvoicedQuantity>
                <cbc:LineExtensionAmount currencyID="''' + document_currency + '''">''' + str(bt_131) + '''</cbc:LineExtensionAmount>'''
            if invoice_line_id.discount: #line_allowance_charge:
                invoice_line_xml += '''
                <cac:AllowanceCharge>
                    <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
                    <cbc:AllowanceChargeReasonCode>95</cbc:AllowanceChargeReasonCode>
                    <cbc:AllowanceChargeReason>Discount</cbc:AllowanceChargeReason>'''
                # invoice_line_xml += '''
                #     <cbc:MultiplierFactorNumeric>''' + str(bt_138) + '''</cbc:MultiplierFactorNumeric>'''
                invoice_line_xml += '''
                    <cbc:Amount currencyID="''' + document_currency + '''">''' + str(bt_136) + '''</cbc:Amount>'''
                # invoice_line_xml += '''
                #     <cbc:BaseAmount currencyID="''' + document_currency + '''">''' + str(bt_137) + '''</cbc:BaseAmount>'''
                if bt_151 != 'O':
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
            ksa_11 = float('{:0.2f}'.format(float_round(bt_131 * bt_152/100, precision_rounding=0.01)))  #BR-KSA-50
            ksa_12 = float('{:0.2f}'.format(float_round(bt_131 + ksa_11, precision_rounding=0.01)))  # BR-KSA-51
            # BR-KSA-52 and BR-KSA-53
            invoice_line_xml += '''
                <cac:TaxTotal>
                    <cbc:TaxAmount currencyID="''' + document_currency + '''">''' + str(ksa_11) + '''</cbc:TaxAmount>
                    <cbc:RoundingAmount currencyID="''' + document_currency + '''">''' + str(ksa_12) + '''</cbc:RoundingAmount>
                </cac:TaxTotal>
                <cac:Item>
                    <cbc:Name>''' + str(self._get_zatca_product_name(invoice_line_id)["name"]["value"]) + '''</cbc:Name>'''
            if invoice_line_id.product_id.barcode and invoice_line_id.product_id.code_type:
                invoice_line_xml += '''
                    <cac:StandardItemIdentification>
                        <cbc:ID schemeID="''' + str(invoice_line_id.product_id.code_type) + '''">''' + str(invoice_line_id.product_id.barcode) + '''</cbc:ID>
                    </cac:StandardItemIdentification>'''
            invoice_line_xml += '''
                    <cac:ClassifiedTaxCategory>
                        <cbc:ID>''' + str(bt_151) + '''</cbc:ID>'''
            if bt_151 != 'O':
                invoice_line_xml += '''
                        <cbc:Percent>''' + str(bt_152) + '''</cbc:Percent>'''
            invoice_line_xml += '''
                        <cac:TaxScheme>
                            <cbc:ID>VAT</cbc:ID>
                        </cac:TaxScheme>
                    </cac:ClassifiedTaxCategory>
                </cac:Item>
                <cac:Price>
                    <cbc:PriceAmount currencyID="''' + document_currency + '''">''' + str(bt_146) + '''</cbc:PriceAmount>
                    <cbc:BaseQuantity unitCode="PCE">''' + str(bt_149) + '''</cbc:BaseQuantity>
                </cac:Price>
            </cac:InvoiceLine>'''
        bt_110 = float('{:0.2f}'.format(float_round(0, precision_rounding=0.01)))  # Sum of bt-117 Calculated in bg_23 loop
        tax_subtotal_xml = ''
        for bg_23 in bg_23_list.keys():
            bt_116 = float('{:0.2f}'.format(float_round(bg_23_list[bg_23]['bt_116'], precision_rounding=0.01)))
            bt_119 = bg_23_list[bg_23]['bt_119']
            bt_118 = bg_23
            if bt_118 == "S":
                bt_117 = float('{:0.2f}'.format(float_round(bt_116 * (bt_119 / 100), precision_rounding=0.01)))
                bt_110 += bt_117
            else:
                bt_117 = float('{:0.2f}'.format(float_round(0, precision_rounding=0.01)))
            tax_subtotal_xml += '''
            <cac:TaxSubtotal>
                <cbc:TaxableAmount currencyID="''' + document_currency + '''">''' + str(bt_116) + '''</cbc:TaxableAmount>
                <cbc:TaxAmount currencyID="''' + document_currency + '''">''' + str(bt_117) + '''</cbc:TaxAmount>
                <cac:TaxCategory>
                    <cbc:ID>''' + str(bt_118) + '''</cbc:ID>
                    <cbc:Percent>''' + str(bt_119) + '''</cbc:Percent>'''
            if bt_118 != "S" and bt_118 in ['E', 'O', 'Z']:
                bt_120 = bg_23_list[bg_23]['bt_120']
                bt_121 = bg_23_list[bg_23]['bt_121']
                tax_subtotal_xml += '''
                    <cbc:TaxExemptionReasonCode>''' + str(bt_121) + '''</cbc:TaxExemptionReasonCode>
                    <cbc:TaxExemptionReason>''' + str(bt_120) + '''</cbc:TaxExemptionReason>'''
            tax_subtotal_xml += '''
                    <cac:TaxScheme>
                        <cbc:ID>VAT</cbc:ID>
                    </cac:TaxScheme>
                </cac:TaxCategory>
            </cac:TaxSubtotal>'''
        bt_109 = float('{:0.2f}'.format(float_round(bt_106 - bt_107, precision_rounding=0.01)))
        bt_111 = float('{:0.2f}'.format(float_round(bt_110 if document_currency == "SAR" else abs(self.amount_tax_signed), precision_rounding=0.01)))  # Same as bt-110
        bt_112 = float('{:0.2f}'.format(float_round(bt_109 + bt_110, precision_rounding=0.01)))
        # bt_113 = float('{:0.2f}'.format(float_round(self.amount_total - self.amount_residual, precision_rounding=0.01)))
        bt_108 = 0
        bt_113 = 0
        bt_114 = 0
        bt_115 = float('{:0.2f}'.format(float_round(bt_112 - bt_113 + bt_114, precision_rounding=0.01)))
        # if bt_110 != float('{:0.2f}'.format(float_round(self.amount_tax, precision_rounding=0.01))):
        #     raise exceptions.ValidationError('Error in Tax Total Calculation')
        ubl_2_1 += '''
            <cac:TaxTotal>
                <cbc:TaxAmount currencyID="''' + document_currency + '''">''' + str(bt_110) + '''</cbc:TaxAmount>'''
        ubl_2_1 += tax_subtotal_xml
        ubl_2_1 += '''
            </cac:TaxTotal>
            <cac:TaxTotal>
                <cbc:TaxAmount currencyID="SAR">''' + str(bt_111) + '''</cbc:TaxAmount>
            </cac:TaxTotal>'''
        ubl_2_1 += '''
            <cac:LegalMonetaryTotal>
                <cbc:LineExtensionAmount currencyID="''' + document_currency + '''">''' + str(bt_106) + '''</cbc:LineExtensionAmount>
                <cbc:TaxExclusiveAmount currencyID="''' + document_currency + '''">''' + str(bt_109) + (" | " + str(self.amount_untaxed) if amount_verification else '') +'''</cbc:TaxExclusiveAmount>
                <cbc:TaxInclusiveAmount currencyID="''' + document_currency + '''">''' + str(bt_112) + (" | " + str(self.amount_total) if amount_verification else '') + '''</cbc:TaxInclusiveAmount>'''
        if bt_108:
            ubl_2_1 += '''
                <cbc:ChargeTotalAmount currencyID="''' + document_currency + '''">''' + str(bt_108) + '''</cbc:ChargeTotalAmount>'''
        if bt_113:
            ubl_2_1 += '''
                <cbc:PrepaidAmount currencyID="''' + document_currency + '''">''' + str(bt_113) + '''</cbc:PrepaidAmount>'''
        if bt_114:
            ubl_2_1 += '''
                <cbc:PayableRoundingAmount currencyID="''' + document_currency + '''">''' + str(bt_114) + '''</cbc:PayableRoundingAmount>'''
        ubl_2_1 += '''
                <cbc:PayableAmount currencyID="''' + document_currency + '''">''' + str(bt_115 if bt_115 > 0 else 0) + (" | " + str(self.amount_residual) if amount_verification else '') + '''</cbc:PayableAmount>
            </cac:LegalMonetaryTotal>'''
        ubl_2_1 += invoice_line_xml
        ubl_2_1 += '''
        </Invoice>'''

        file_name_specification = (str(bt_31) + "_" + self.l10n_sa_confirmation_datetime.strftime('%Y%m%dT%H%M%SZ')
                                   + "_" + str(re.sub(r"[^a-zA-Z0-9]", "-", self.zatca_unique_seq)))
        self.zatca_invoice_name = file_name_specification + ".xml"
        self.hash_with_c14n_canonicalization(conf, xml=ubl_2_1)
        # conf.zatca_pih = self.zatca_invoice_hash
        if signature:
            signature_value = self.apply_signature(conf)

            ubl_2_1 = ubl_2_1.replace('zatca_signature_hash', str(base_64_5))
            ubl_2_1 = ubl_2_1.replace('zatca_signature_value', str(signature_value))
            _zatca.info("compute_qr_code_str")
            self.compute_qr_code_str(signature_value, is_tax_invoice, bt_112, bt_110)
            _zatca.info("l10n_sa_qr_code_str:: %s", self.l10n_sa_qr_code_str)
            if not is_tax_invoice:
            # if is_tax_invoice:
                ubl_2_1 = ubl_2_1.replace('zatca_l10n_sa_qr_code_str', str(self.l10n_sa_qr_code_str))

        ubl_2_1 = ubl_2_1.replace('zatca_invoice_hash', str(self.zatca_invoice_hash))

        try:
            atts = self.env['ir.attachment'].sudo().search([('res_model', '=', 'account.move'), ('res_field', '=', 'zatca_invoice'),
                                                            ('res_id', 'in', self.ids), ('company_id', 'in', [conf.id, False])])
            if atts:
                atts.sudo().write({'datas': base64.b64encode(bytes(ubl_2_1, 'utf-8'))})
            else:
                atts.sudo().create([{
                    'name': file_name_specification + ".xml",
                    'res_model': 'account.move',
                    'res_field': 'zatca_invoice',
                    'res_id': self.id,
                    'type': 'binary',
                    'datas': base64.b64encode(bytes(ubl_2_1, 'utf-8')),
                    'mimetype': 'text/xml',
                    'company_id': conf.id,
                    # 'datas_fname': file_name_specification + ".xml"
                }])
            self._cr.commit()
        except Exception as e:
            _logger.info("ZATCA: Attachment in Odoo Issue: " + str(e))
            exceptions.AccessError(_("Error in creating invoice attachment."))
        _logger.info("ZATCA: Invoice & its hash generated for invoice " + str(self.name))

    def get_AccountingSupplierParty(self, company_id):
        conf_company = self._get_zatca_partner_data() if self.l10n_is_self_billed_invoice else self._get_zatca_company_data(company_id.parent_root_id)
        partner_id, company_id, buyer_identification, buyer_identification_no, license, license_no = self._get_partner_comapny(company_id)
        bt_31 = company_id.vat

        ubl_2_1 = '''
            <cac:AccountingSupplierParty>
                <cac:Party>'''
        ubl_2_1 += '''
                    <cac:PartyIdentification>
                        <cbc:ID schemeID="''' + license + '''">''' + license_no + '''</cbc:ID>
                    </cac:PartyIdentification>
                    <cac:PostalAddress>
                        <cbc:StreetName>''' + self.check_allowed_size(1,1000, conf_company['street']['value'], "Company " + company_id._fields[conf_company['street']['field']].string) + '''</cbc:StreetName>'''
        if conf_company["street2"]['value']:
            ubl_2_1 += '''
                        <cbc:AdditionalStreetName>''' + self.check_allowed_size(0,127, conf_company['street2']['value'], "Company " + company_id._fields[conf_company['street2']['field']].string) + '''</cbc:AdditionalStreetName>'''
        if len(str(company_id.zip)) != 5:
            raise exceptions.ValidationError(_('Company/Seller PostalZone/Zip must be exactly 5 digits'))
        ubl_2_1 += '''  <cbc:BuildingNumber>''' + str(company_id.building_no) + '''</cbc:BuildingNumber>'''
        if company_id.additional_no:
            ubl_2_1 += '''  
                        <cbc:PlotIdentification>''' + str(company_id.additional_no) + '''</cbc:PlotIdentification>'''
        ubl_2_1 += '''  <cbc:CitySubdivisionName>''' + self.check_allowed_size(1, 127, conf_company["district"]['value'], "Company " + company_id._fields[conf_company["district"]['field']].string) + '''</cbc:CitySubdivisionName>
                        <cbc:CityName>''' + self.check_allowed_size(1, 127, conf_company["city"]['value'], "Company " + company_id._fields[conf_company["city"]['field']].string) + '''</cbc:CityName>
                        <cbc:PostalZone>''' + str(company_id.zip) + '''</cbc:PostalZone>
                        <cbc:CountrySubentity>''' + self.check_allowed_size(1, 127, conf_company["state_id_name"]['value'], "Company %s %s" % (company_id._fields['state_id'].string, company_id.state_id._fields[conf_company["state_id_name"]['field']].string)) + '''</cbc:CountrySubentity>
                        <cac:Country>
                            <cbc:IdentificationCode>''' + company_id.country_id.code + '''</cbc:IdentificationCode>
                        </cac:Country>
                    </cac:PostalAddress>
                    <cac:PartyTaxScheme>
                        <cbc:CompanyID>''' + bt_31 + '''</cbc:CompanyID>
                        <cac:TaxScheme>
                            <cbc:ID>VAT</cbc:ID>
                        </cac:TaxScheme>
                    </cac:PartyTaxScheme>
                    <cac:PartyLegalEntity>
                        <cbc:RegistrationName>''' + self.check_allowed_size(1, 1000, conf_company["name"]['value'], "Company " + company_id._fields[conf_company["name"]['field']].string) + '''</cbc:RegistrationName>
                    </cac:PartyLegalEntity>
                </cac:Party>
            </cac:AccountingSupplierParty>'''
        return ubl_2_1

    def apply_signature(self, conf, auto_compliance=0, zatca_invoice_hash=0):
        hash_filename = ''
        private_key_filename = ''
        id = "id" if auto_compliance else self.id
        zatca_invoice_hash = zatca_invoice_hash if auto_compliance else self.zatca_invoice_hash

        try:
            hash_filename = hashlib.sha256(('account_move_' + str(id) + '_signature_value').encode("UTF-8")).hexdigest()
            f = open('/tmp/' + str(hash_filename), 'wb+')
            f.write(base64.b64decode(zatca_invoice_hash))
            f.close()

            private_key = conf.zatca_prod_private_key
            _zatca.info("private_key:: %s", private_key)
            for x in range(1, math.ceil(len(private_key) / 64)):
                private_key = private_key[:64 * x + x -1] + '\n' + private_key[64 * x + x -1:]
            private_key = "-----BEGIN EC PRIVATE KEY-----\n" + private_key + "\n-----END EC PRIVATE KEY-----"
            _zatca.info("private_key:: %s", private_key)

            private_key_filename = hashlib.sha256(('account_move_' + str(id) + '_private_key').encode("UTF-8")).hexdigest()
            f = open('/tmp/' + str(private_key_filename), 'wb+')
            f.write(private_key.encode())
            f.close()

            signature = '''openssl dgst -sha256 -sign /tmp/''' + private_key_filename + ''' /tmp/''' + hash_filename + ''' | base64 /dev/stdin'''
            signature_value = os.popen(signature).read()
            _zatca.info("signature_value:: %s", signature_value)
            signature_value = signature_value.replace('\n', '').replace(' ', '')
            _zatca.info("signature_value:: %s", signature_value)
            if not signature_value or signature_value in [None, '']:
                raise exceptions.ValidationError(_("Error in private key, kindly regenerate credentials."))

            # signature_filename = hashlib.sha256(('account_move_' + str(self.id) + '_signature_value').encode("UTF-8")).hexdigest()
            # os.system('''echo ''' + str(signature_value) + ''' | base64 -d /dev/stdin > /tmp/''' + str(signature_filename))
            # Signature validation
            # signature_verify = '''echo ''' + str(self.zatca_invoice_hash_hex) + ''' | openssl dgst -verify /tmp/zatcapublickey.pem -signature /tmp/''' + str(signature_filename) + ''' /dev/stdin'''
            # if "Verified OK" not in os.popen(signature_verify).read():
            #     raise exceptions.ValidationError("Signature can't be verified, try again.")
            # os.system('''rm  /tmp/''' + str(signature_filename))
            return signature_value
        except Exception as e:
            _logger.info("ZATCA: Private Key Issue: " + str(e))
            if str(e) == _('Error in private key, kindly regenerate credentials.'):
                raise e
            raise exceptions.AccessError(_("Error in signing invoice, kindly try again."))
        finally:
            # For security purpose, files should not exist out of odoo
            os.system('''rm  /tmp/''' + str(hash_filename))
            os.system('''rm  /tmp/''' + str(private_key_filename))

    def generate_signature(self):
        # STEP # 1 => DONE  => NOT NEEDED, DONE ABOVE
        # STEP # 2 => DONE  => NOT NEEDED, DONE ABOVE
        # STEP # 3 => DONE  => NOT NEEDED, DONE ABOVE
        # STEP # 4 => DONE  => NOT NEEDED, DONE ABOVE
        # STEP # 5 => Still remaining
        # STEP # 6 => DONE  => NOT NEEDED, DONE ABOVE
        pass

    def compliance_invoices_api(self, auto_compliance=0, **kwargs):
        # link = "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal"
        endpoint = '/compliance/invoices'

        conf = self.company_id.parent_root_id.sudo() if not auto_compliance else kwargs.get('conf')
        if not conf.is_zatca:
            raise exceptions.AccessDenied(_("Zatca is not activated."))
        link = conf.zatca_link

        if 'Onboarding was failed in invoice' in conf.zatca_status:
            raise exceptions.AccessDenied(conf.zatca_status)

        zatca_on_board_status_details = conf.zatca_on_board_status_details
        if zatca_on_board_status_details in [None, False]:
            zatca_on_board_status_details = json.loads('{"error": "404"}')
        else:
            zatca_on_board_status_details = json.loads(conf.zatca_on_board_status_details)

        zatca_invoice_hash = self.zatca_invoice_hash if not auto_compliance else kwargs.get('zatca_invoice_hash')
        zatca_invoice = self.zatca_invoice.decode('UTF-8') if not auto_compliance else kwargs.get('zatca_invoice')
        invoice_uuid = self.invoice_uuid if not auto_compliance else kwargs.get('invoice_uuid')
        if not auto_compliance:
            is_tax_invoice = 'standard' if self.l10n_sa_invoice_type == 'Standard' else 'simplified'
            bt_3 = 'debit' if self.debit_origin_id.id else ('credit' if self.move_type in ['out_refund', 'in_refund'] else 'invoice')
        else:
            zatca_invoice = base64.b64encode(zatca_invoice.encode()).decode('UTF-8')
            is_tax_invoice = kwargs.get('is_tax_invoice')
            bt_3 = kwargs.get('bt_3')

        user = conf.zatca_sb_bsToken
        password = conf.zatca_sb_secret
        auth = base64.b64encode(('%s:%s' % (user, password)).encode('utf-8')).decode('utf-8')
        headers = {'accept': 'application/json',
                   'Accept-Language': 'en',
                   'Accept-Version': 'V2',
                   'Authorization': 'Basic ' + auth,
                   'Content-Type': 'application/json'}

        data = {
            'invoiceHash': zatca_invoice_hash,
            'uuid': invoice_uuid,
            'invoice': zatca_invoice,
        }
        try:
            string = ''
            req = requests.post(link + endpoint, headers=headers, data=json.dumps(data), timeout=(30, 60))
            if not auto_compliance:
                self.l10n_sa_response_datetime = fields.Datetime.now()
            if req.status_code == 500:
                raise exceptions.AccessError(_('Invalid Request, \ncontact system administer'))
            elif req.status_code == 401:
                raise exceptions.AccessError(_('Unauthorized Request, \nUpdate configuration for sandbox'))
            elif req.status_code == 503:
                raise exceptions.AccessError(_('Zatca Api Service Down, \nkindly report to zatca.'))
            elif req.status_code in [200, 202, 400]:
                if not auto_compliance:
                    self.zatca_status_code = req.status_code
                response = json.loads(req.text)
                string = "<table style='width:100%'>"
                string += "<tr><td  colspan='6'><b>validationResults</b></td></tr>"

                for key, value in response['validationResults'].items():
                    if type(value) == list:
                        string += "<tr><td  colspan='6'><center><b>" + key + "</b></center></td></tr>"
                        qty = 1
                        for val in value:
                            color = 'green' if str(val['status']).lower() == 'pass' else 'red'
                            string += "<tr>"
                            string += "<td colspan='2' style='border: 1px solid black;'>" + str(qty) + "</td>"
                            string += "<td  style='border: 1px solid black;'><b>" + 'type' + "</b></td>"
                            string += "<td  style='border: 1px solid black;'><b>" + 'code' + "</b></td>"
                            string += "<td  style='border: 1px solid black;'><b>" + 'category' + "</b></td>"
                            string += "<td  style='border: 1px solid black;'><b>" + 'status' + "</b></td>"
                            string += "</tr>"
                            string += "<tr>"
                            string += "<td  style='border: 1px solid black;' colspan='2'></td>"
                            string += "<td  style='border: 1px solid black;color: " + color + ";'>" + str(val['type']) + "</td>"
                            string += "<td  style='border: 1px solid black;color: " + color + ";'>" + str(val['code']) + "</td>"
                            string += "<td  style='border: 1px solid black;color: " + color + ";'>" + str(val['category']) + "</td>"
                            string += "<td  style='border: 1px solid black;color: " + color + ";'>" + str(val['status']) + "</td>"
                            string += "</tr>"
                            string += "<tr>"
                            string += "<td colspan='2'  style='border: 1px solid black;'><b>" + 'message' + "</b></td>"
                            string += "<td colspan='4'  style='border: 1px solid black;color: " + color + ";'>" + str(val['message']) + "</td>"
                            string += "</tr>"
                            qty += 1
                    else:
                        string += "<tr>"
                        string += "<td>" + key + "</td><td colspan='3'>" + str(value) + "</td>"
                        string += "</tr>"
                string += "<tr><td colspan='2'><b>reportingStatus</b></td><td colspan='4'>" + str(response['reportingStatus']) + "</td></tr>"
                string += "<tr><td colspan='2'><b>clearanceStatus</b></td><td colspan='4'>" + str(response['clearanceStatus']) + "</td></tr>"
                string += "<tr><td colspan='2'><b>qrSellertStatus</b></td><td colspan='4'>" + str(response['qrSellertStatus']) + "</td></tr>"
                string += "<tr><td colspan='2'><b>qrBuyertStatus </b></td><td colspan='4'>" + str(response['qrBuyertStatus'])+ "</td></tr>"
                string += "<tr><td colspan='6'></td></tr>"

                if response['validationResults']['errorMessages'] == [] and response['validationResults']['status'] == 'PASS' and \
                    (response['reportingStatus'] == "REPORTED" or response['clearanceStatus'] == "CLEARED"):
                    zatca_on_board_status_details[is_tax_invoice][bt_3] = 1
                    conf.zatca_on_board_status_details = json.dumps(zatca_on_board_status_details)
                    total_required = []
                    for x in zatca_on_board_status_details.keys():
                        total_required += list(zatca_on_board_status_details[x].values())
                    invoices_required = str(len(total_required) - sum(total_required))
                    if invoices_required == '0':
                        conf.zatca_status = "Onboarding completed, request for production credentials now"
                        conf.csr_otp = None
                        conf.zatca_onboarding_status = 1
                        string += "<tr><td colspan='6'><center><b>" + \
                                  str("Onboarding completed, request for production credentials now") + "</b></center></td></tr>"
                    else:
                        on_board_status = json.loads(conf.zatca_on_board_status_details)
                        status = ''
                        if on_board_status.get('standard', 0):
                            status += "\nStandard: "
                            if not on_board_status.get('standard', 0).get('invoice', 0):
                                status += "invoice,"
                            if not on_board_status.get('standard', 0).get('credit', 0):
                                status += "credit,"
                            if not on_board_status.get('standard', 0).get('debit', 0):
                                status += "debit,"
                        if on_board_status.get('simplified', 0):
                            status += "\nSimplified: "
                            if not on_board_status.get('simplified', 0).get('invoice', 0):
                                status += "invoice,"
                            if not on_board_status.get('simplified', 0).get('credit', 0):
                                status += "credit,"
                            if not on_board_status.get('simplified', 0).get('debit', 0):
                                status += "debit,"
                        zatca_status = conf.zatca_status
                        if zatca_status in [None, False]:
                            zatca_status = 'invoices\n'
                        conf.zatca_status = zatca_status[:zatca_status.find('invoices\n') + 9] + status

                        conf.zatca_status = conf.zatca_status[:29] + invoices_required + conf.zatca_status[30:]
                        string += "<tr><td colspan='6'><center><b>" + \
                                  str("Onboarding in progress, " + invoices_required + " invoices remaining") + "</b></center></td></tr>"
                        if status.rfind('\n'):
                            string += "<tr><td colspan='6'><center><b>" + \
                                      str(status[:status.rfind('\n')]) + "</b></center></td></tr>"
                            string += "<tr><td colspan='6'><center><b>" + \
                                      str(status[status.rfind('\n'):]) + "</b></center></td></tr>"
                        else:
                            string += "<tr><td colspan='6'><center><b>" + \
                                      str(status) + "</b></center></td></tr>"
                    string += "</table>"
                else:
                    string += "<tr><td colspan='6'><center><b>" + \
                              str('Onboarding failed, restart process !!') + "</b></center></td></tr>"
                    string += "</table>"
                    conf.zatca_on_board_status_details = json.dumps(zatca_on_board_status_details)
                    conf.zatca_status = 'Onboarding was failed in invoice (' + str(self.name) + '), Kindly restart onboarding process.'
                    conf.zatca_onboarding_status = 0
                    conf.zatca_certificate_status = 0
                    conf.csr_certificate = None
                    conf.csr_otp = None
            else:
                raise exceptions.AccessError(_("Zatca status") + ' ' + str(req.status_code) + "\n" + req.text)
            json_iterated = string
            self.zatca_compliance_invoices_api = json_iterated
            return {
                'type': 'ir.actions.act_window',
                'name': "Zatca Response",
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.id,
                'views': [(self.env.ref('ksa_zatca_integration.zatca_response').id, 'form')],
            }
        except Exception as e:
            if 'odoo.exceptions' in str(type(e)):
                raise
            raise exceptions.AccessDenied(e)

    def invoices_clearance_single_api(self):
        # link = "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal"
        endpoint = '/invoices/clearance/single'

        conf = self.company_id.parent_root_id.sudo()
        if not conf.is_zatca:
            raise exceptions.AccessDenied(_("Zatca is not activated."))
        link = conf.zatca_link

        user = conf.zatca_bsToken
        password = conf.zatca_secret
        auth = base64.b64encode(('%s:%s' % (user, password)).encode('utf-8')).decode('utf-8')
        headers = {'accept': 'application/json',
                   'Accept-Language': 'en',
                   'Clearance-Status': '1',
                   'Accept-Version': 'V2',
                   'Authorization': 'Basic ' + auth,
                   'Content-Type': 'application/json'}

        data = {
            'invoiceHash': self.zatca_invoice_hash,
            # 'invoiceHash': self.hash_with_c14n_canonicalization(api_invoice=1),
            'uuid': self.invoice_uuid,
            'invoice': self.zatca_invoice.decode('UTF-8'),
        }
        try:
            req = requests.post(link + endpoint, headers=headers, data=json.dumps(data), timeout=(30, 60))
            self.l10n_sa_response_datetime = fields.Datetime.now()
            if req.status_code == 500:
                raise exceptions.AccessError(_('Invalid Request, \ncontact system administer'))
            elif req.status_code == 401:
                raise exceptions.AccessError(_('Unauthorized Request, \nUpdate configuration for production'))
            elif req.status_code == 503:
                raise exceptions.AccessError(_('Zatca Api Service Down, \nkindly report to zatca.'))
            elif req.status_code in [200, 202, 400]:
                self.zatca_status_code = req.status_code
                response = json.loads(req.text)
                string = "<table style='width:100%'>"
                string += "<tr><td  colspan='6'><b>validationResults</b></td></tr>"

                for key, value in response['validationResults'].items():
                    if type(value) == list:
                        string += "<tr><td  colspan='6'><center><b>" + key + "</b></center></td></tr>"
                        qty = 1
                        for val in value:
                            color = 'green' if str(val['status']).lower() == 'pass' else 'red'
                            string += "<tr>"
                            string += "<td colspan='2' style='border: 1px solid black;'>" + str(qty) + "</td>"
                            string += "<td  style='border: 1px solid black;'><b>" + 'type' + "</b></td>"
                            string += "<td  style='border: 1px solid black;'><b>" + 'code' + "</b></td>"
                            string += "<td  style='border: 1px solid black;'><b>" + 'category' + "</b></td>"
                            string += "<td  style='border: 1px solid black;'><b>" + 'status' + "</b></td>"
                            string += "</tr>"
                            string += "<tr>"
                            string += "<td  style='border: 1px solid black;' colspan='2'></td>"
                            string += "<td  style='border: 1px solid black;color: " + color + ";'>" + str(val['type']) + "</td>"
                            string += "<td  style='border: 1px solid black;color: " + color + ";'>" + str(val['code']) + "</td>"
                            string += "<td  style='border: 1px solid black;color: " + color + ";'>" + str(val['category']) + "</td>"
                            string += "<td  style='border: 1px solid black;color: " + color + ";'>" + str(val['status']) + "</td>"
                            string += "</tr>"
                            string += "<tr>"
                            string += "<td colspan='2'  style='border: 1px solid black;'><b>" + 'message' + "</b></td>"
                            string += "<td colspan='4'  style='border: 1px solid black;color: " + color + ";'>" + str(val['message']) + "</td>"
                            string += "</tr>"
                            qty += 1
                    else:
                        string += "<tr>"
                        string += "<td>" + key + "</td><td colspan='3'>" + str(value) + "</td>"
                        string += "</tr>"
                string += "<tr><td colspan='2'><b>clearanceStatus</b></td><td colspan='4'>" + str(response['clearanceStatus']) + "</td></tr>"
                string += "<tr><td colspan='2' style='vertical-align: baseline;'><b>clearedInvoice</b></td><td colspan='4'>" + ("Yes" if response['clearedInvoice'] else "No") + "</td></tr>"
                string += "<tr style='display: none;'><td colspan='2' style='vertical-align: baseline;'><b>clearedInvoice</b></td><td colspan='4' style='word-wrap: anywhere;border: 1px solid black;'>" + str(response['clearedInvoice']) + "</td></tr>"
                string += "</table>"

                json_iterated = string
                self.zatca_compliance_invoices_api = json_iterated

                partner_id, company_id, unknown, unknown, unknown, unknown = self._get_partner_comapny(self.company_id)
                file_name_specification = (str(company_id.vat) + "_" + self.l10n_sa_confirmation_datetime.strftime('%Y%m%dT%H%M%SZ')
                                           + "_" + str(re.sub(r"[^a-zA-Z0-9]", "-", self.zatca_unique_seq)))
                atts = self.env['ir.attachment'].sudo().search([('res_model', '=', 'account.move'),
                                                                ('res_field', '=', 'zatca_hash_cleared_invoice'),
                                                                ('res_id', 'in', self.ids),
                                                                ('company_id', 'in', [conf.id, False])])
                if response['clearedInvoice']:
                    if atts:
                        atts.sudo().write({'datas': response['clearedInvoice']})
                    else:
                        atts.sudo().create([{
                            'name': file_name_specification + ".xml",
                            'res_model': 'account.move',
                            'res_field': 'zatca_hash_cleared_invoice',
                            'res_id': self.id,
                            'type': 'binary',
                            'datas': response['clearedInvoice'],
                            'mimetype': 'text/xml',
                            'company_id': conf.id,
                        }])
                    self.zatca_hash_cleared_invoice_name = file_name_specification + ".xml"
            else:
                raise exceptions.AccessError(_("Zatca status") + ' ' + str(req.status_code) + "\n" + req.text)
            return {
                'type': 'ir.actions.act_window',
                'name': "Zatca Response",
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.id,
                'views': [(self.env.ref('ksa_zatca_integration.zatca_response').id, 'form')],
            }
        except Exception as e:
            if 'odoo.exceptions' in str(type(e)):
                raise
            raise exceptions.AccessDenied(e)

    def invoices_reporting_single_api(self, no_xml_generate):
        # link = "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal"
        endpoint = '/invoices/reporting/single'

        conf = self.company_id.parent_root_id.sudo()
        if not conf.is_zatca:
            raise exceptions.AccessDenied(_("Zatca is not activated."))
        link = conf.zatca_link

        user = conf.zatca_bsToken
        password = conf.zatca_secret

        auth = base64.b64encode(('%s:%s' % (user, password)).encode('utf-8')).decode('utf-8')
        headers = {'accept': 'application/json',
                   'Accept-Language': 'en',
                   'Clearance-Status': '1',
                   'Accept-Version': 'V2',
                   'Authorization': 'Basic ' + auth,
                   'Content-Type': 'application/json'}

        data = {
            'invoiceHash': self.zatca_invoice_hash,
            # 'invoiceHash': self.hash_with_c14n_canonicalization(api_invoice=1),
            'uuid': self.invoice_uuid,
            'invoice': self.zatca_invoice.decode('UTF-8'),
        }
        try:
            req = requests.post(link + endpoint, headers=headers, data=json.dumps(data), timeout=(30, 60))
            self.l10n_sa_response_datetime = fields.Datetime.now()
            if req.status_code == 500:
                raise exceptions.AccessError(_('Invalid Request, \ncontact system administer'))
            elif req.status_code == 401:
                raise exceptions.AccessError(_('Unauthorized Request, \nUpdate configuration for production'))
            elif req.status_code == 503:
                raise exceptions.AccessError(_('Zatca Api Service Down, \nkindly report to zatca.'))
            elif req.status_code in [200, 202, 400]:
                self.zatca_status_code = req.status_code
                response = json.loads(req.text)
                string = "<table style='width:100%'>"
                string += "<tr><td  colspan='6'><b>validationResults</b></td></tr>"

                for key, value in response['validationResults'].items():
                    if type(value) == list:
                        string += "<tr><td  colspan='6'><center><b>" + key + "</b></center></td></tr>"
                        qty = 1
                        for val in value:
                            color = 'green' if str(val['status']).lower() == 'pass' else 'red'
                            string += "<tr>"
                            string += "<td colspan='2' style='border: 1px solid black;'>" + str(qty) + "</td>"
                            string += "<td  style='border: 1px solid black;'><b>" + 'type' + "</b></td>"
                            string += "<td  style='border: 1px solid black;'><b>" + 'code' + "</b></td>"
                            string += "<td  style='border: 1px solid black;'><b>" + 'category' + "</b></td>"
                            string += "<td  style='border: 1px solid black;'><b>" + 'status' + "</b></td>"
                            string += "</tr>"
                            string += "<tr>"
                            string += "<td  style='border: 1px solid black;' colspan='2'></td>"
                            string += "<td  style='border: 1px solid black;color: " + color + ";'>" + str(val['type']) + "</td>"
                            string += "<td  style='border: 1px solid black;color: " + color + ";'>" + str(val['code']) + "</td>"
                            string += "<td  style='border: 1px solid black;color: " + color + ";'>" + str(val['category']) + "</td>"
                            string += "<td  style='border: 1px solid black;color: " + color + ";'>" + str(val['status']) + "</td>"
                            string += "</tr>"
                            string += "<tr>"
                            string += "<td colspan='2'  style='border: 1px solid black;'><b>" + 'message' + "</b></td>"
                            string += "<td colspan='4'  style='border: 1px solid black;color: " + color + ";'>" + str(val['message']) + "</td>"
                            string += "</tr>"
                            qty += 1
                    else:
                        string += "<tr>"
                        string += "<td>" + key + "</td><td colspan='3'>" + str(value) + "</td>"
                        string += "</tr>"
                string += "<tr><td colspan='2'><b>reportingStatus</b></td><td colspan='4'>" + str(response['reportingStatus']) + "</td></tr>"
                string += "</table>"

                json_iterated = string
                self.zatca_compliance_invoices_api = json_iterated
            else:
                raise exceptions.AccessError(_("Zatca status") + ' ' + str(req.status_code) + "\n" + req.text)
            if no_xml_generate:
                return self.zatca_compliance_invoices_api
            return {
                'type': 'ir.actions.act_window',
                'name': "Zatca Response",
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.id,
                'views': [(self.env.ref('ksa_zatca_integration.zatca_response').id, 'form')],
            }
        except Exception as e:
            if 'odoo.exceptions' in str(type(e)):
                raise
            raise exceptions.AccessDenied(e)

    def hash_with_c14n_canonicalization(self, conf, api_invoice=0, xml=0, auto_compliance=0):
        invoice = base64.b64decode(self.zatca_invoice).decode() if not xml else xml
        try:
            xml_file = ET.fromstring(invoice)
        except Exception as e:
            raise exceptions.ValidationError(_("Xml Validation error\npossible reasons\n"
                                             "special character is present in address of company or customer"))

        if not api_invoice:
            xsl_file = ET.fromstring('''<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                            xmlns:xs="http://www.w3.org/2001/XMLSchema"
                            xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
                            xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                            xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
                            xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
                            exclude-result-prefixes="xs"
                            version="2.0">
                <xsl:output omit-xml-declaration="yes" encoding="utf-8" indent="no"/>
                <xsl:template match="node() | @*">
                    <xsl:copy>
                        <xsl:apply-templates select="node() | @*"/>
                    </xsl:copy>
                </xsl:template>
                <xsl:template match="//*[local-name()='Invoice']//*[local-name()='UBLExtensions']"></xsl:template>
                <xsl:template match="//*[local-name()='AdditionalDocumentReference'][cbc:ID[normalize-space(text()) = 'QR']]"></xsl:template>
                 <xsl:template match="//*[local-name()='Invoice']/*[local-name()='Signature']"></xsl:template>
            </xsl:stylesheet>''')
            transform = ET.XSLT(xsl_file.getroottree())
            transformed_xml = transform(xml_file.getroottree())

            def _l10n_sa_get_namespaces():
                """
                    Namespaces used in the final UBL declaration, required to canonalize the finalized XML document of the Invoice
                """
                return {
                    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
                    'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
                    'sig': 'urn:oasis:names:specification:ubl:schema:xsd:CommonSignatureComponents-2',
                    'sac': 'urn:oasis:names:specification:ubl:schema:xsd:SignatureAggregateComponents-2',
                    'sbc': 'urn:oasis:names:specification:ubl:schema:xsd:SignatureBasicComponents-2',
                    'ds': 'http://www.w3.org/2000/09/xmldsig#',
                    'xades': 'http://uri.etsi.org/01903/v1.3.2#'
                }

            # root = etree.fromstring(xml_content)
            # invoice_xsl = etree.parse(get_module_resource('l10n_sa_edi', 'data', 'pre-hash_invoice.xsl'))
            # transform = etree.XSLT(invoice_xsl)
            # content = transform(root)
            transformed_xml = ET.tostring(transformed_xml, method="c14n", exclusive=False, with_comments=False,
                                          inclusive_ns_prefixes=_l10n_sa_get_namespaces())
        else:
            transformed_xml = xml_file.getroottree()
        #
        # transformed_xml.find("//{http://uri.etsi.org/01903/v1.3.2#}SignedSignatureProperties")
        sha256_hash = hashlib.sha256()
        transformed_xml = transformed_xml if not api_invoice else ET.tostring(transformed_xml)
        sha256_hash.update(transformed_xml)
        generated_hash = base64.b64encode(sha256_hash.hexdigest().encode()).decode()
        base64_encoded = base64.b64encode(sha256_hash.digest()).decode()
        if auto_compliance:
            return base64_encoded

        if not api_invoice:
            self.zatca_invoice_hash = base64_encoded
            self.zatca_invoice_hash_hex = generated_hash
        else:
            return base64_encoded

        atts = self.env['ir.attachment'].sudo().search([('res_model', '=', 'account.move'),
                                                        ('res_field', '=', 'zatca_hash_invoice'),
                                                        ('res_id', 'in', self.ids),
                                                        ('company_id', 'in', [conf.id, False])])
        if atts:
            atts.sudo().write({'datas': base64.b64encode(transformed_xml)})
        else:
            atts.sudo().create([{
                'name': self.zatca_invoice_name.replace('.xml', '_hash.xml'),
                'res_model': 'account.move',
                'res_field': 'zatca_hash_invoice',
                'res_id': self.id,
                'type': 'binary',
                'datas': base64.b64encode(transformed_xml),
                'mimetype': 'text/xml',
                'company_id': conf.id,
            }])
        self.zatca_hash_invoice_name = self.zatca_invoice_name.replace('.xml', '_hash.xml')

    # TODO: multi record suppport
    def _compute_qr_code_str(self):
        _zatca.info('_compute_qr_code_str')
        try:
            if not self.is_zatca or (self.l10n_sa_phase1_end_date and self.invoice_date <= self.l10n_sa_phase1_end_date):
                return super()._compute_qr_code_str()
            is_tax_invoice = 1 if self.l10n_sa_invoice_type == 'Standard' else 0
            if not self.zatca_onboarding_status:
                self.l10n_sa_qr_code_str = ""
                self.sa_qr_code_str = ""
            elif is_tax_invoice:
                _zatca.info("is_tax_invoice:: %s", self.l10n_sa_invoice_type)
                _zatca.info("zatca_hash_cleared_invoice:: %s", self.zatca_hash_cleared_invoice)
                invoice = base64.b64decode(self.zatca_hash_cleared_invoice).decode()
                _zatca.info("invoice:: %s", invoice)
                invoice = invoice.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
                _zatca.info("invoice:: %s", invoice)
                xml_file = ET.fromstring(invoice).getroottree()
                qr_code_str = xml_file.xpath('//*[local-name()="ID"][text()="QR"]/following-sibling::*/*')[0].text
                _zatca.info("qr_code_str:: %s", qr_code_str)
                self.l10n_sa_qr_code_str = qr_code_str
                self.sa_qr_code_str = qr_code_str
            else:
                invoice = base64.b64decode(self.zatca_invoice).decode()
                xml_file = ET.fromstring(invoice).getroottree()
                signature_value = xml_file.find("//{http://www.w3.org/2000/09/xmldsig#}SignatureValue").text
                bt_112 = xml_file.find(
                    "//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxInclusiveAmount").text
                bt_110 = xml_file.find(
                    "//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount").text
                self.compute_qr_code_str(signature_value, is_tax_invoice, bt_112, bt_110)
        except Exception as e:
            _logger.info("QR code can't be generated. " + str(e))
            self.l10n_sa_qr_code_str = ""
            self.sa_qr_code_str = ""

    def compute_qr_code_str(self, signature_value, is_tax_invoice, bt_112, bt_110, auto_compliance=0):
        def get_qr_encoding(tag, field):
            _zatca.info("tag:: %s", tag)
            _zatca.info("field:: %s", field)
            company_name_byte_array = field if tag in [8, 9] else field.encode()
            _zatca.info("company_name_byte_array:: %s", company_name_byte_array)
            company_name_tag_encoding = tag.to_bytes(length=1, byteorder='big')
            _zatca.info("company_name_tag_encoding:: %s", company_name_tag_encoding)
            company_name_length_encoding = len(company_name_byte_array).to_bytes(length=1, byteorder='big')
            _zatca.info("company_name_length_encoding:: %s", company_name_length_encoding)
            return company_name_tag_encoding + company_name_length_encoding + company_name_byte_array

        try:
            for record in self:
                qr_code_str = ''
                conf_company = self._get_zatca_partner_data() if self.l10n_is_self_billed_invoice else self._get_zatca_company_data(self.company_id.parent_root_id)
                partner_id, company_id, buyer_identification, buyer_identification_no, license, license_no = self._get_partner_comapny(record.company_id)

                if record.l10n_sa_confirmation_datetime and company_id.vat:
                    seller_name_enc = get_qr_encoding(1, conf_company["name"]['value'])
                    company_vat_enc = get_qr_encoding(2, company_id.vat)
                    time_sa = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'), record.l10n_sa_confirmation_datetime)
                    timestamp_enc = get_qr_encoding(3, self.l10n_sa_confirmation_datetime.strftime('%Y-%m-%dT%H:%M:%SZ'))
                    # invoice_total_enc = get_qr_encoding(4, float_repr(abs(record.amount_total_signed), 2))
                    invoice_total_enc = get_qr_encoding(4, str(bt_112))
                    # total_vat_enc = get_qr_encoding(5, float_repr(abs(record.amount_tax_signed), 2))
                    total_vat_enc = get_qr_encoding(5, str(bt_110))

                    invoice_hash = get_qr_encoding(6, record.zatca_invoice_hash)
                    ecdsa_signature = get_qr_encoding(7, signature_value)

                    conf = self.company_id.parent_root_id.sudo()
                    _zatca.info("zatca_cert_public_key:: %s", conf.zatca_cert_public_key)
                    cert_pub_key = base64.b64decode(conf.zatca_cert_public_key)
                    _zatca.info("cert_pub_key:: %s", cert_pub_key)
                    ecdsa_public_key = get_qr_encoding(8, cert_pub_key)
                    if not is_tax_invoice:
                        _zatca.info("zatca_cert_sig_algo:: %s", conf.zatca_cert_sig_algo)
                        ecdsa_cert_value = get_qr_encoding(9, binascii.unhexlify(conf.zatca_cert_sig_algo))

                    str_to_encode = seller_name_enc + company_vat_enc + timestamp_enc + invoice_total_enc + total_vat_enc
                    _zatca.info("str_to_encode:: %s", str_to_encode)
                    str_to_encode += invoice_hash + ecdsa_signature + ecdsa_public_key
                    _zatca.info("str_to_encode:: %s", str_to_encode)
                    if not is_tax_invoice:
                        str_to_encode += ecdsa_cert_value
                    qr_code_str = base64.b64encode(str_to_encode).decode()
                record.l10n_sa_qr_code_str = qr_code_str
                record.sa_qr_code_str = qr_code_str
        except Exception as e:
            _logger.info("QR code can't be generated via compute_qr_code_str " + str(e))
            self.l10n_sa_qr_code_str = ""
            self.sa_qr_code_str = ""

    def compliance_qr_code(self, company_id, bt_112, bt_110, zatca_invoice_hash, signature_value, timestamp_enc):
        def get_qr_encoding(tag, field):
            company_name_byte_array = field if tag in [8, 9] else field.encode()
            company_name_tag_encoding = tag.to_bytes(length=1, byteorder='big')
            company_name_length_encoding = len(company_name_byte_array).to_bytes(length=1, byteorder='big')
            return company_name_tag_encoding + company_name_length_encoding + company_name_byte_array

        conf_company = self._get_zatca_company_data(company_id)
        partner_id, company_id, buyer_identification, buyer_identification_no, license, license_no = self._get_partner_comapny(company_id)

        try:
            seller_name_enc = get_qr_encoding(1, conf_company["name"]['value'])
            company_vat_enc = get_qr_encoding(2, company_id.vat)
            timestamp_enc = get_qr_encoding(3, timestamp_enc)
            invoice_total_enc = get_qr_encoding(4, str(bt_112))
            total_vat_enc = get_qr_encoding(5, str(bt_110))
            invoice_hash = get_qr_encoding(6, zatca_invoice_hash)
            ecdsa_signature = get_qr_encoding(7, signature_value)
            conf = company_id.sudo()
            cert_pub_key = base64.b64decode(conf.zatca_cert_public_key)
            ecdsa_public_key = get_qr_encoding(8, cert_pub_key)
            ecdsa_cert_value = get_qr_encoding(9, binascii.unhexlify(conf.zatca_cert_sig_algo))

            str_to_encode = seller_name_enc + company_vat_enc + timestamp_enc + invoice_total_enc + total_vat_enc
            str_to_encode += invoice_hash + ecdsa_signature + ecdsa_public_key
            str_to_encode += ecdsa_cert_value
            qr_code_str = base64.b64encode(str_to_encode).decode()
            return qr_code_str
        except Exception as e:
            _logger.info("QR code can't be generated via compute_qr_code_str " + str(e))

    def zatca_response(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Zatca Response",
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(self.env.ref('ksa_zatca_integration.zatca_response').id, 'form')],
        }

    def send_for_compliance(self):
        if self._context.get('xml_generate', 0) or not self.zatca_invoice:
            self.create_xml_file()
        return self.compliance_invoices_api()

    def send_for_clearance(self):
        if self._context.get('xml_generate', 0) or not self.zatca_invoice:
            self.create_xml_file()
        return self.invoices_clearance_single_api()

    def send_for_reporting(self, no_xml_generate=0):
        if (self._context.get('xml_generate', 0) or not self.zatca_invoice) and not no_xml_generate:
            self.create_xml_file()
        return self.invoices_reporting_single_api(no_xml_generate)

    def send_multiple_to_zatca(self):
        self = self.filtered(lambda x: x.zatca_icv_counter).sorted(key='zatca_icv_counter')

        # if int(self[0].zatca_icv_counter) > 1:
        #     def get_last_zatca_invoice(self, icv):
        #         record = self.search([('zatca_icv_counter', '=', icv -1)], limit=1)
        #         if not record.id:
        #             icv = icv - 1
        #             record = get_last_zatca_invoice(self, icv)
        #         return record
        #     seq_id = get_last_zatca_invoice(self, int(self[0].zatca_icv_counter))
        #     if seq_id.l10n_sa_zatca_status == 'Not Sended to Zatca':
        #         raise exceptions.MissingError("Invoice " + str(seq_id.name) + " must be submitted first.")
        for record in self:
            try:
                if record.state == 'posted':
                    if not record.zatca_invoice_name or not record.zatca_compliance_invoices_api or \
                            record.zatca_status_code == '400':
                        if not record.zatca_onboarding_status:
                            pass
                            # record.send_for_compliance()
                        else:
                            if record.l10n_sa_invoice_type == 'Standard':
                                record.send_for_clearance()
                            elif record.l10n_sa_invoice_type == 'Simplified':
                                record.send_for_reporting()
            except Exception as e:
                # Bypass errors.
                _logger.info("Multi Send To Zatca Errors :: " + str(e))

    def action_post(self):
        res = super().action_post()
        for record in self:
            conf = record.company_id.parent_root_id.sudo()
            if (conf.is_zatca
                    and ((not conf.is_self_billed and record.move_type in ['out_invoice', 'out_refund']) or
                         (conf.is_self_billed and record.move_type in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']) )
                    and record.l10n_sa_invoice_type and record.l10n_sa_phase1_end_date and record.invoice_date > record.l10n_sa_phase1_end_date):
                if (record.move_type in ['in_invoice', 'in_refund'] and record.l10n_is_self_billed_invoice) or record.move_type in ['out_invoice', 'out_refund']:
                    record.create_xml_file()
                    if record.company_id.parent_root_id.zatca_send_from_pos:
                        if not record.zatca_onboarding_status:
                            record.send_for_compliance()
                        elif record.l10n_sa_invoice_type == 'Standard':
                            record.send_for_clearance()
                        elif record.l10n_sa_invoice_type == 'Simplified':
                            record.send_for_reporting()
        return res

    @api.depends('country_code', 'move_type')
    def _compute_show_delivery_date(self):
        # EXTENDS 'account'
        super()._compute_show_delivery_date()
        for move in self:
            if move.country_code == 'SA':
                conf = move.company_id.parent_root_id.sudo()
                move.show_delivery_date = ((not conf.is_self_billed and move.move_type in ['out_invoice', 'out_refund'])
                                           or (conf.is_self_billed and move.move_type in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']))

    def _post(self, soft=True):
        res = super()._post(soft)
        for record in self:
            record.write({'l10n_sa_confirmation_datetime': fields.Datetime.now()})
        return res

    # ZATCA Exceptions
    def unlink(self):
        for record in self:
            if record.l10n_sa_prohibited_exception() and record.state != 'draft':
                raise exceptions.AccessDenied(_(message))
        return super(AccountMove, self).unlink()

    def button_draft(self):
        for record in self:
            if record.l10n_sa_prohibited_exception() and record.state == 'posted' and record.zatca_status_code != '400':
                raise exceptions.AccessDenied(_(message))
        return super(AccountMove, self).button_draft()

    def button_cancel(self):
        for record in self:
            if record.l10n_sa_prohibited_exception() and record.state == 'posted':
                raise exceptions.AccessDenied(_(message))
        return super(AccountMove, self).button_cancel()

    def l10n_sa_prohibited_exception(self):
        conf = self.company_id.parent_root_id.sudo()
        if (conf.is_zatca and ((not conf.is_self_billed and self.move_type in ['out_invoice', 'out_refund'])
               or (conf.is_self_billed and self.move_type in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']))
                and self.l10n_sa_phase1_end_date and self.invoice_date > self.l10n_sa_phase1_end_date):
            return True
        return False

