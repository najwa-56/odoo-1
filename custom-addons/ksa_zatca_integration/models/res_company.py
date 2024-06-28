# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api, _
from .compliance import Standard, Simplified
from odoo.tools import mute_logger
import lxml.etree as ET
import requests
import base64
import math
import json
import odoo
import uuid
import os
import re

# ZATCA SDK Dummy Values
zatca_sdk_private_key = "MHQCAQEEIDyLDaWIn/1/g3PGLrwupV4nTiiLKM59UEqUch1vDfhpoAcGBSuBBAAKoUQDQgAEYYMMoOaFYAhMO/steotf" \
                        "Zyavr6p11SSlwsK9azmsLY7b1b+FLhqMArhB2dqHKboxqKNfvkKDePhpqjui5hcn0Q=="
zatca_sdk_secret = "Xlj15LyMCgSC66ObnEO/qVPfhSbs3kDTjWnGheYhfSs="
zatca_sdk_bsToken = "TUlJRDFEQ0NBM21nQXdJQkFnSVRid0FBZTNVQVlWVTM0SS8rNVFBQkFBQjdkVEFLQmdncWhrak9QUVFEQWpCak1SVXdFd1lL" \
                    "Q1pJbWlaUHlMR1FCR1JZRmJHOWpZV3d4RXpBUkJnb0praWFKay9Jc1pBRVpGZ05uYjNZeEZ6QVZCZ29Ka2lhSmsvSXNaQUVa" \
                    "RmdkbGVIUm5ZWHAwTVJ3d0dnWURWUVFERXhOVVUxcEZTVTVXVDBsRFJTMVRkV0pEUVMweE1CNFhEVEl5TURZeE1qRTNOREEx" \
                    "TWxvWERUSTBNRFl4TVRFM05EQTFNbG93U1RFTE1Ba0dBMVVFQmhNQ1UwRXhEakFNQmdOVkJBb1RCV0ZuYVd4bE1SWXdGQVlE" \
                    "VlFRTEV3MW9ZWGxoSUhsaFoyaHRiM1Z5TVJJd0VBWURWUVFERXdreE1qY3VNQzR3TGpFd1ZqQVFCZ2NxaGtqT1BRSUJCZ1Vy" \
                    "Z1FRQUNnTkNBQVRUQUs5bHJUVmtvOXJrcTZaWWNjOUhEUlpQNGI5UzR6QTRLbTdZWEorc25UVmhMa3pVMEhzbVNYOVVuOGpE" \
                    "aFJUT0hES2FmdDhDL3V1VVk5MzR2dU1ObzRJQ0p6Q0NBaU13Z1lnR0ExVWRFUVNCZ0RCK3BId3dlakViTUJrR0ExVUVCQXdT" \
                    "TVMxb1lYbGhmREl0TWpNMGZETXRNVEV5TVI4d0hRWUtDWkltaVpQeUxHUUJBUXdQTXpBd01EYzFOVGc0TnpBd01EQXpNUTB3" \
                    "Q3dZRFZRUU1EQVF4TVRBd01SRXdEd1lEVlFRYURBaGFZWFJqWVNBeE1qRVlNQllHQTFVRUR3d1BSbTl2WkNCQ2RYTnphVzVs" \
                    "YzNNek1CMEdBMVVkRGdRV0JCU2dtSVdENmJQZmJiS2ttVHdPSlJYdkliSDlIakFmQmdOVkhTTUVHREFXZ0JSMllJejdCcUNz" \
                    "WjFjMW5jK2FyS2NybVRXMUx6Qk9CZ05WSFI4RVJ6QkZNRU9nUWFBL2hqMW9kSFJ3T2k4dmRITjBZM0pzTG5waGRHTmhMbWR2" \
                    "ZGk1ellTOURaWEowUlc1eWIyeHNMMVJUV2tWSlRsWlBTVU5GTFZOMVlrTkJMVEV1WTNKc01JR3RCZ2dyQmdFRkJRY0JBUVNC" \
                    "b0RDQm5UQnVCZ2dyQmdFRkJRY3dBWVppYUhSMGNEb3ZMM1J6ZEdOeWJDNTZZWFJqWVM1bmIzWXVjMkV2UTJWeWRFVnVjbTlz" \
                    "YkM5VVUxcEZhVzUyYjJsalpWTkRRVEV1WlhoMFoyRjZkQzVuYjNZdWJHOWpZV3hmVkZOYVJVbE9WazlKUTBVdFUzVmlRMEV0" \
                    "TVNneEtTNWpjblF3S3dZSUt3WUJCUVVITUFHR0gyaDBkSEE2THk5MGMzUmpjbXd1ZW1GMFkyRXVaMjkyTG5OaEwyOWpjM0F3" \
                    "RGdZRFZSMFBBUUgvQkFRREFnZUFNQjBHQTFVZEpRUVdNQlFHQ0NzR0FRVUZCd01DQmdnckJnRUZCUWNEQXpBbkJna3JCZ0VF" \
                    "QVlJM0ZRb0VHakFZTUFvR0NDc0dBUVVGQndNQ01Bb0dDQ3NHQVFVRkJ3TURNQW9HQ0NxR1NNNDlCQU1DQTBrQU1FWUNJUUNW" \
                    "d0RNY3E2UE8rTWNtc0JYVXovdjFHZGhHcDdycVNhMkF4VEtTdjgzOElBSWhBT0JOREJ0OSszRFNsaWpvVmZ4enJkRGg1MjhX" \
                    "QzM3c21FZG9HV1ZyU3BHMQ=="


class ResCompany(models.Model):
    _inherit = 'res.company'

    # BR-KSA-08
    license = fields.Selection([('CRN', 'Commercial Registration number'),
                                ('MOM', 'Momrah license'), ('MLS', 'MHRSD license'),
                                ('SAG', 'MISA license'), ('OTH', 'Other OD'),
                                ('700', '700 Number')],
                               required=0, string="License",
                               help="In case multiple IDs exist then one of the above must be entered")
    license_no = fields.Char(string="License Number (Other seller ID)", required=0)

    building_no = fields.Char(related='partner_id.building_no', readonly=False)
    additional_no = fields.Char(related='partner_id.additional_no', readonly=False)
    district = fields.Char(related='partner_id.district', readonly=False)
    industry_id = fields.Many2one(related="partner_id.industry_id", readonly=False)
    country_id_name = fields.Char(related="country_id.name")

    def sanitize_int(self, value):
        return re.sub(r'\D', '', str(value))

    @api.constrains('building_no', 'zip')
    def constrains_brksa64(self):
        for record in self:
            # if record._context.get('params', False) and record._context['params'].get('model', False) == 'res.company':
            if record.parent_is_zatca:
                # BR-KSA-37
                if len(str(record.sanitize_int(record.building_no))) != 4:
                    raise exceptions.ValidationError(_('Building Number must be exactly 4 digits'))
                # BR-KSA-66
                if len(str(record.sanitize_int(record.zip))) != 5:
                    raise exceptions.ValidationError(_('zip must be exactly 5 digits'))
                if record.is_group_vat and len(str(record.csr_individual_vat)) != 10:
                    raise exceptions.ValidationError(_('Individual Vat must be exactly 10 digits'))

    is_zatca = fields.Boolean()
    parent_is_zatca = fields.Boolean(compute="_compute_zatca_parent_id", compute_sudo=True)
    parent_root_id = fields.Many2one('res.company', compute='_compute_zatca_parent_id', compute_sudo=True)
    is_self_billed = fields.Boolean("Self Billed")

    zatca_certificate_status = fields.Boolean()
    zatca_icv_counter = fields.Char(default=1, readonly=1)

    zatca_status = fields.Char()
    zatca_onboarding_status = fields.Boolean()
    zatca_on_board_status_details = fields.Char()
    l10n_sa_phase1_end_date = fields.Date("Phase 1 ending date")

    # Required fields
    zatca_link = fields.Char("Api Link")
    api_type = fields.Selection([('Sandbox', 'Sandbox'), ('Simulation', 'Simulation'), ('Live', 'Live')])

    is_group_vat = fields.Boolean("Is Group Vat", compute="_compute_is_group_vat", store=True)
    csr_common_name = fields.Char("Common Name")  # CN
    csr_serial_number = fields.Char("EGS Serial Number")  # SN
    # csr_organization_identifier = fields.Char("Organization Identifier", required="1")  # UID
    csr_organization_unit_name = fields.Char("Organization Unit Name")  # OU
    csr_individual_vat = fields.Char("Individual Vat")  # OU
    csr_organization_name = fields.Char("Organization Name")  # O
    # csr_country_name = fields.Char("Country Name", required="1")  # C
    csr_invoice_type = fields.Char("Invoice Type")  # title
    zatca_invoice_type = fields.Selection([('Standard', 'Standard'), ('Simplified', 'Simplified'),
                                           ('Standard & Simplified', 'Standard & Simplified')])
    csr_location_address = fields.Char("Location")  # registeredAddress
    csr_industry_business_category = fields.Char("Industry ")  # BusinessCategory

    csr_otp = fields.Char("Otp")
    zatca_send_from_pos = fields.Boolean('Send to Zatca on Post invoice')
    parent_zatca_send_from_pos = fields.Boolean('Send to Zatca on Post invoice',
                                                compute="_compute_zatca_parent_id", store=True)
    zatca_pos_pay = fields.Boolean('Show POS payments in pos receipts')

    zatca_is_sandbox = fields.Boolean('Testing ? (to check simplified invoices)')
    zatca_is_fatoora_simulation_portal = fields.Boolean('FATOORA Simulation Portal')

    # Never show these fields on front (Security and Integrity of zatca could be compromised.)
    csr_certificate = fields.Char("Certificate", required=False)

    zatca_sb_bsToken = fields.Char()
    zatca_sb_secret = fields.Char()
    zatca_sb_reqID = fields.Char()
    zatca_bsToken = fields.Char()
    zatca_secret = fields.Char()
    zatca_reqID = fields.Char()
    zatca_cert_sig_algo = fields.Char()
    zatca_prod_private_key = fields.Char()
    zatca_cert_public_key = fields.Char()
    zatca_csr_base64 = fields.Char()

    @api.onchange('parent_id')
    @api.depends('parent_id')
    def _compute_zatca_parent_id(self):
        for record in self:
            record.parent_is_zatca = record.parent_ids.filtered(lambda x: not x.parent_id).is_zatca or record.is_zatca
            record.parent_root_id = record.parent_ids.filtered(lambda x: not x.parent_id) or record
            for res in record.child_ids + record:
                res.parent_zatca_send_from_pos = res.parent_root_id.zatca_send_from_pos

    @api.onchange('vat')
    @api.depends('vat', 'is_zatca')
    def _compute_is_group_vat(self):
        for record in self:
            record.is_group_vat = 0
            if record.is_zatca and len(str(record.vat)) > 10 and int(record.vat[10]) == 1:
                record.is_group_vat = 1

    @mute_logger('Zatca Debugger for account.move :')
    def auto_compliance(self):
        # x = base64.b64encode(bytes(ubl_2_1, 'utf-8')).decode()
        # ecdsa_signature = "zatca_l10n_sa_ecdsa_signature".encode()

        # for i in range(1, math.ceil(len(x) / 170)):
        #     x = x[:170 * i + i - 1] + '\n' + x[170 * i + i - 1:]
        #

        conf = self.sudo()
        move = self.env['account.move'].sudo()

        if not conf.is_zatca:
            raise exceptions.AccessDenied(_("Zatca is not activated."))

        if conf.zatca_status in ["production credentials received", "production credentials renewed."]:
            raise exceptions.AccessError(_("auto_compliance already done."))

        if conf.zatca_status in [None, False, '']:
            conf.generate_zatca_certificate(auto_compliance=1)
            if 'Onboarding started, required ' not in conf.zatca_status:
                # code should never come here, exception would already have been raised.
                raise exceptions.AccessError(_("Unexpected Error in getting CSID") + "\n" +
                                             _("Try Again."))

        if 'Onboarding started, required ' in conf.zatca_status:
            # compliance checks
            zatca_invoice_hash = 'NWZlY2ViNjZmZmM4NmYzOGQ5NTI3ODZjNmQ2OTZjNzljMmRiYzIzOWRkNGU5MWI0NjcyOWQ3M2EyN2ZiNTdlOQ=='
            types = ['standard', 'simplified'] if conf.zatca_invoice_type == 'Standard & Simplified' else (['standard'] if conf.zatca_invoice_type == "Standard" else ['simplified'])
            for type in types:
                if type == "standard":
                    xmls = {'invoice': Standard.invoice(""), 'credit': Standard.credit(""), 'debit': Standard.debit("")}
                else:
                    xmls = {'invoice': Simplified.invoice(""), 'credit': Simplified.credit(""), 'debit': Simplified.debit("")}
                for check in xmls:
                    invoice = base64.b64decode(xmls[check]).decode()
                    is_tax_invoice = 1 if type == "standard" else 0
                    signature, signature_certificate, base_64_5 = move.get_signature(conf=conf)
                    if signature and not is_tax_invoice:
                        ubl_2_1 = '''
                        <ext:UBLExtensions>
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
                        ubl_2_1 += '''      </ds:Signature>
                                        </sac:SignatureInformation>
                                    </sig:UBLDocumentSignatures>
                                </ext:ExtensionContent>
                            </ext:UBLExtension>
                        </ext:UBLExtensions>
                        <cbc:UBLVersionID>2.1</cbc:UBLVersionID>'''
                        invoice = invoice.replace("<cbc:UBLVersionID>2.1</cbc:UBLVersionID>", ubl_2_1)
                    invoice = invoice.replace("zatca_invoice_pih", str(zatca_invoice_hash))
                    if type == "standard":
                        invoice = invoice[:invoice.find("<cac:AccountingSupplierParty>")] + "l10n_AccountingSupplierParty" + invoice[invoice.find("</cac:AccountingSupplierParty>") + 31:]
                    AccountingSupplierParty = move.get_AccountingSupplierParty(conf)
                    invoice = invoice.replace('l10n_AccountingSupplierParty', str(AccountingSupplierParty))
                    zatca_invoice_hash = move.hash_with_c14n_canonicalization(conf, xml=invoice, auto_compliance=1)
                    xml_file = ET.fromstring(invoice).getroottree()
                    invoice_uuid = xml_file.find("//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UUID").text
                    zdate = xml_file.find("//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate").text
                    ztime = xml_file.find("//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueTime").text
                    bt_115 = xml_file.find("//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PayableAmount").text
                    bt_110 = xml_file.find("//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount").text
                    timestamp_enc = zdate + "T" + ztime

                    if not is_tax_invoice:
                        signature_value = move.apply_signature(conf, auto_compliance=1, zatca_invoice_hash=zatca_invoice_hash)
                        invoice = invoice.replace('zatca_signature_hash', str(base_64_5))
                        invoice = invoice.replace('zatca_signature_value', str(signature_value))
                        qr_code = move.compliance_qr_code(conf, bt_115, bt_110, zatca_invoice_hash, signature_value, timestamp_enc)
                        invoice = invoice.replace("l10n_zatca_qr", str(qr_code))

                    invoice = invoice.replace('zatca_invoice_hash', str(zatca_invoice_hash))

                    move.compliance_invoices_api(auto_compliance=1, conf=conf, is_tax_invoice=type, bt_3=check,
                                                 zatca_invoice_hash=zatca_invoice_hash, zatca_invoice=invoice,
                                                 invoice_uuid=invoice_uuid)

                    if 'Onboarding was failed in invoice' in conf.zatca_status:
                        raise exceptions.ValidationError(_("Compliance Failed") + "\n" +
                                                         _("Try Again."))
            # compliance checks ended
            if conf.zatca_status != "Onboarding completed, request for production credentials now":
                # code should never come here, exception would already have been raised.
                raise exceptions.AccessError(_("Unexpected Error in getting PCSID") + "\n" +
                                             _("Try Again."))

        if conf.zatca_status in ["Requesting for production credentials now.", "Onboarding completed, request for production credentials now"]:
            conf.zatca_status = "Requesting for production credentials now."
            conf.production_credentials()

        if conf.zatca_status != "production credentials received.":
            # code should never come here, exception would already have been raised.
            raise exceptions.AccessError(_("Unexpected Error in auto_compliance") + "\n" +
                                         _("Reset ZATCA and Try Again."))

    def generate_zatca_certificate(self, auto_compliance=0):
        conf = self.sudo()

        # seq check
        sequence = conf.env['ir.sequence'].search([('code', '=', 'zatca.move.line.seq'),
                                                   ('company_id', 'in', [self.id, False])],
                                                  order='company_id', limit=1)
        if not sequence:
            conf.env['ir.sequence'].create({
                'name': 'zatca move line seq',
                'code': 'zatca.move.line.seq',
                'company_id': self.id,
                'number_increment': 1,
                'number_next': 1,
            })

        conf.zatca_is_fatoora_simulation_portal = False
        conf.zatca_is_sandbox = False

        if conf.api_type == 'Sandbox':
            conf.zatca_is_sandbox = True
            conf.zatca_link = 'https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal'
            conf.csr_otp = 12345
        elif conf.api_type == 'Simulation':
            conf.zatca_link = 'https://gw-fatoora.zatca.gov.sa/e-invoicing/simulation'
            conf.zatca_is_fatoora_simulation_portal = True
        elif conf.api_type == 'Live':
            conf.zatca_link = 'https://gw-fatoora.zatca.gov.sa/e-invoicing/core'

        try:
            if not conf.is_zatca:
                raise exceptions.AccessDenied(_("Zatca is not activated."))
            conf.zatca_onboarding_status = False
            if conf.csr_otp in [None, False]:
                raise exceptions.MissingError(_("OTP required."))
            if conf.zatca_is_fatoora_simulation_portal:
                # https://zatca.gov.sa/en/E-Invoicing/Introduction/Guidelines/Documents/Fatoora_Portal_User_Manual_English.pdf
                # version 3, page 31
                certificateTemplateName = "ASN1:PRINTABLESTRING:PREZATCA-Code-Signing"
            else:
                certificateTemplateName = "ASN1:PRINTABLESTRING:ZATCA-Code-Signing"

            # zatca fields
            conf_name = conf.name[0:64]
            conf.csr_common_name = (odoo.release.description + odoo.release.version.replace("+e", "e") + "-" + str(self.id)).replace(" ", '').replace("e", '').replace("+", '').replace("_", '')
            conf.csr_serial_number = ("1-Odoo|2-17|3-%s_%s_%s" % (odoo.release.version.replace('17.0', '').replace("+e", "e").replace("-", ""), self.id, str(uuid.uuid4()).replace("-", ""))).encode('utf-8')
            conf.csr_organization_unit_name = conf.csr_individual_vat if conf.is_group_vat else conf_name
            conf.csr_organization_name = conf_name
            conf.csr_invoice_type = '1000' if conf.zatca_invoice_type == 'Standard' else ('0100' if conf.zatca_invoice_type == 'Simplified' else '1100')
            conf.csr_location_address = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            conf.csr_industry_business_category = conf.partner_id.industry_id.name or "IT"

            config_cnf = '''
                oid_section = OIDs
                [ OIDs ]
                certificateTemplateName= 1.3.6.1.4.1.311.20.2

                [ req ]
                default_bits = 2048
                emailAddress = ''' + str(conf.email) + '''
                req_extensions = v3_req
                x509_extensions = v3_ca
                prompt = no
                default_md = sha256
                req_extensions = req_ext
                distinguished_name = dn
                utf8 = yes

                [ dn ]
                C = ''' + str(conf.country_id.code) + '''
                OU = ''' + str(conf.csr_organization_unit_name) + '''
                O = ''' + str(conf.csr_organization_name) + '''
                CN = ''' + str(conf.csr_common_name) + '''

                [ v3_req ]
                basicConstraints = CA:FALSE
                keyUsage = digitalSignature, nonRepudiation, keyEncipherment

                [ req_ext ]
                certificateTemplateName = ''' + str(certificateTemplateName) + '''
                subjectAltName = dirName:alt_names

                [ alt_names ]
                SN = ''' + str(conf.csr_serial_number) + '''
                UID = ''' + str(conf.vat) + '''
                title = ''' + str(conf.csr_invoice_type) + '''
                registeredAddress = ''' + str(conf.csr_location_address) + '''
                businessCategory = ''' + str(conf.csr_industry_business_category) + '''
            '''

            f = open('/tmp/zatca.cnf', 'w+')
            f.write(config_cnf)
            f.close()

            # Certificate calculation moved to new function
            if self.zatca_is_sandbox:
                # ZATCA sanbox private key
                private_key = zatca_sdk_private_key
                private_key = private_key.replace('-----BEGIN EC PRIVATE KEY-----', '') \
                                         .replace('-----END EC PRIVATE KEY-----', '')\
                                         .replace(' ', '').replace('\n', '')
                self.zatca_prod_private_key = private_key
            else:
                private_key = 'openssl ecparam -name secp256k1 -genkey -noout'
            public_key = 'openssl ec -in /tmp/zatcaprivatekey.pem -pubout -conv_form compressed -out /tmp/zatcapublickey.pem'
            public_key_bin = 'openssl base64 -d -in /tmp/zatcapublickey.pem -out /tmp/zatcapublickey.bin'
            csr = 'openssl req -new -sha256 -key /tmp/zatcaprivatekey.pem -extensions v3_req -config /tmp/zatca.cnf -out /tmp/zatca_taxpayper.csr'
            csr_base64 = "openssl base64 -in /tmp/zatca_taxpayper.csr"
            if not self.zatca_is_sandbox:
                private_key = os.popen(private_key).read()
                private_key = private_key.replace('-----BEGIN EC PRIVATE KEY-----', '') \
                                         .replace('-----END EC PRIVATE KEY-----', '')\
                                         .replace(' ', '')\
                                         .replace('\n', '')
                self.zatca_prod_private_key = private_key

            for x in range(1, math.ceil(len(private_key) / 64)):
                private_key = private_key[:64 * x + x - 1] + '\n' + private_key[64 * x + x - 1:]
            private_key = "-----BEGIN EC PRIVATE KEY-----\n" + private_key + "\n-----END EC PRIVATE KEY-----"

            f = open('/tmp/zatcaprivatekey.pem', 'w+')
            f.write(private_key)
            f.close()

            os.system(public_key)
            os.system(public_key_bin)
            os.system(csr)
            conf.zatca_csr_base64 = os.popen(csr_base64).read()
            conf.zatca_status = 'CSR, private & public key generated'
            csr_invoice_type = conf.csr_invoice_type

            qty = 3
            if csr_invoice_type[0:2] == '11':
                zatca_on_board_status_details = {
                    'standard': {
                        'credit': 0,
                        'debit': 0,
                        'invoice': 0,
                    },
                    'simplified': {
                        'credit': 0,
                        'debit': 0,
                        'invoice': 0,
                    }
                }
                message = "Standard: invoice, debit, credit, \nSimplified: invoice, debit, credit, "
                qty = 6
            elif csr_invoice_type[0:2] == '10':
                zatca_on_board_status_details = {
                    'standard': {
                        'credit': 0,
                        'debit': 0,
                        'invoice': 0,
                    }
                }
                message = "Standard: invoice, debit, credit, "
            elif csr_invoice_type[0:2] == '01':
                zatca_on_board_status_details = {
                    'simplified': {
                        'credit': 0,
                        'debit': 0,
                        'invoice': 0,
                    }
                }
                message = "Simplified: invoice, debit, credit, "
            else:
                raise exceptions.ValidationError(_("Invalid Invoice Type defined."))
            conf.zatca_on_board_status_details = json.dumps(zatca_on_board_status_details)
            conf.zatca_status = 'Onboarding started, required ' + str(qty) + ' invoices' + "\n" + message

        except Exception as e:
            if 'odoo.exceptions' in str(type(e)):
                raise e
            raise exceptions.AccessError(_("Server Error, Contact administrator.") + "\n" + str(e))
        finally:
            # For security purpose, files should not exist out of odoo
            os.system('''rm  /tmp/zatcaprivatekey.pem''')
            os.system('''rm  /tmp/zatca.cnf''')
            os.system('''rm  /tmp/zatcapublickey.pem''')
            os.system('''rm  /tmp/zatcapublickey.bin''')
            os.system('''rm  /tmp/zatca_taxpayper.csr''')
            os.system('''rm  /tmp/zatca_taxpayper_64.csr''')

        self.compliance_api()
        conf.csr_otp = None
        # self.compliance_api('/production/csids', 1)
        #     CNF, PEM, CSR created

    def compliance_api(self, endpoint='/compliance', renew=0):
        # link = "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal"
        conf = self.sudo()
        link = conf.zatca_link

        if endpoint == '/compliance':
            zatca_otp = conf.csr_otp
            headers = {'accept': 'application/json',
                       'OTP': zatca_otp,
                       'Accept-Version': 'V2',
                       'Content-Type': 'application/json'}

            csr = conf.zatca_csr_base64
            data = {'csr': csr.replace('\n', '')}
        elif endpoint == '/production/csids' and not renew:
            user = conf.zatca_sb_bsToken
            password = conf.zatca_sb_secret
            compliance_request_id = conf.zatca_sb_reqID
            auth = base64.b64encode(('%s:%s' % (user, password)).encode('utf-8')).decode('utf-8')
            headers = {'accept': 'application/json',
                       'Accept-Version': 'V2',
                       'Authorization': 'Basic ' + auth,
                       'Content-Type': 'application/json'}

            data = {'compliance_request_id': compliance_request_id}
        elif endpoint == '/production/csids' and renew:
            user = conf.zatca_bsToken
            password = conf.zatca_secret
            auth = base64.b64encode(('%s:%s' % (user, password)).encode('utf-8')).decode('utf-8')
            zatca_otp = conf.csr_otp
            headers = {'accept': 'application/json',
                       'OTP': zatca_otp,
                       'Accept-Language': 'en',
                       'Accept-Version': 'V2',
                       'Authorization': 'Basic ' + auth,
                       'Content-Type': 'application/json'}
            csr = conf.zatca_csr_base64
            data = {'csr': csr.replace('\n', '')}
        try:
            req = requests.post(link + endpoint, headers=headers, data=json.dumps(data), timeout=(30, 60))
            if req.status_code == 500:
                try:
                    response = req.text
                    raise exceptions.AccessError(response)
                except Exception as e:
                    if 'odoo.exceptions' in str(type(e)):
                        raise e
                    response = json.loads(req.text)
                    raise exceptions.AccessError(self.error_message(response))
                raise exceptions.AccessError(_("Invalid Request, zatca, \ncontact system administer."))
            elif req.status_code == 400:
                try:
                    response = req.text
                    raise exceptions.AccessError(response)
                except Exception as e:
                    if 'odoo.exceptions' in str(type(e)):
                        raise e
                    response = json.loads(req.text)
                    raise exceptions.AccessError(self.error_message(response))
                raise exceptions.AccessError(_("Invalid Request, odoo, \ncontact system administer."))
            elif req.status_code == 401:
                try:
                    response = req.text
                    raise exceptions.AccessError(response)
                except Exception as e:
                    if 'odoo.exceptions' in str(type(e)):
                        raise e
                    response = json.loads(req.text)
                    raise exceptions.AccessError(self.error_message(response))
                raise exceptions.AccessError(_("Unauthorized, \ncontact system administer."))
            elif req.status_code == 200:
                response = json.loads(req.text)
                if endpoint == '/compliance':
                    conf.zatca_sb_bsToken = response['binarySecurityToken']
                    conf.zatca_sb_reqID = response['requestID']
                    conf.zatca_sb_secret = response['secret']
                    conf.csr_certificate = base64.b64decode(conf.zatca_sb_bsToken)
                    self.register_certificate()
                else:
                    conf.zatca_bsToken = response['binarySecurityToken']
                    conf.zatca_reqID = response['requestID']
                    conf.zatca_secret = response['secret']
                    conf.csr_certificate = base64.b64decode(conf.zatca_bsToken)
                    self.register_certificate()
                # if endpoint == '/compliance':
                #     self.compliance_api('/production/csids')
                # else:
                #     response['tokenType']
                #     response['dispositionMessage']
        except Exception as e:
            if 'odoo.exceptions' in str(type(e)):
                raise
            raise exceptions.AccessDenied(e)

    def production_credentials(self):
        conf = self.sudo()
        if not conf.is_zatca:
            raise exceptions.AccessDenied(_("Zatca is not activated."))
        if self.zatca_is_sandbox:
            conf.zatca_bsToken = zatca_sdk_bsToken
            conf.zatca_reqID = 'N/A'
            conf.zatca_secret = zatca_sdk_secret
            conf.csr_certificate = base64.b64decode(conf.zatca_bsToken)
            self.register_certificate()
        else:
            self.compliance_api('/production/csids', 0)
        conf.zatca_status = 'production credentials received.'
        conf.csr_otp = None

    def production_credentials_renew(self):
        conf = self.sudo()
        if not conf.is_zatca:
            raise exceptions.AccessDenied(_("Zatca is not activated."))
        if conf.csr_otp in [None, False]:
            raise exceptions.MissingError(_("OTP required."))
        if self.zatca_is_sandbox:
            conf.zatca_bsToken = zatca_sdk_bsToken
            conf.zatca_reqID = 'N/A'
            conf.zatca_secret = zatca_sdk_secret
            conf.csr_certificate = base64.b64decode(conf.zatca_bsToken)
            self.register_certificate()
        else:
            self.compliance_api('/production/csids', 1)
        conf.zatca_status = 'production credentials renewed.'
        conf.csr_otp = None

    def register_certificate(self):
        conf = self.sudo()
        if not conf.is_zatca:
            raise exceptions.AccessDenied(_("Zatca is not activated."))
        certificate = conf.csr_certificate
        if not certificate:
            conf.zatca_certificate_status = 0
            raise exceptions.MissingError(_("Certificate not found."))
        certificate = certificate.replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '')\
                                 .replace(' ', '').replace('\n', '')
        for x in range(1, math.ceil(len(certificate) / 64)):
            certificate = certificate[:64 * x + x - 1] + '\n' + certificate[64 * x + x - 1:]
        certificate = "-----BEGIN CERTIFICATE-----\n" + certificate + "\n-----END CERTIFICATE-----"

        f = open('/tmp/zatca_cert.pem', 'w+')
        f.write(certificate)
        f.close()

        certificate_public_key = "openssl x509 -pubkey -noout -in /tmp/zatca_cert.pem"

        certificate_signature_algorithm = "openssl x509 -in /tmp/zatca_cert.pem -text -noout"
        zatca_cert_public_key = os.popen(certificate_public_key).read()
        zatca_cert_public_key = zatca_cert_public_key.replace('-----BEGIN PUBLIC KEY-----', '')\
                                                     .replace('-----END PUBLIC KEY-----', '')\
                                                     .replace('\n', '').replace(' ', '')
        conf.zatca_cert_public_key = zatca_cert_public_key
        cert = os.popen(certificate_signature_algorithm).read()
        cert_find = cert.rfind("Signature Algorithm: ecdsa-with-SHA256")
        if cert_find > 0 and cert_find + 38 < len(cert):
            cert_sig_algo = cert[cert.rfind("Signature Algorithm: ecdsa-with-SHA256") + 38:].replace('\n', '')\
                                                                                            .replace(':', '')\
                                                                                            .replace(' ', '')\
                                                                                            .replace('SignatureValue', '')
            conf.zatca_cert_sig_algo = cert_sig_algo
        else:
            raise exceptions.ValidationError(_("Invalid Certificate (CSID) Provided."))

        conf.zatca_certificate_status = 1
        # For security purpose, files should not exist out of odoo
        os.system('''rm  /tmp/zatca_cert.pem''')
        os.system('''rm  /tmp/zatca_cert_publickey.pem''')
        os.system('''rm  /tmp/zatca_cert_publickey.bin''')

    def error_message(self, response):
        try:
            if response.get('messsage', False):
                return response['message']
            elif response.get('errors', False):
                return response['errors']
            else:
                return str(response)
        except:
            return str(response)

    def write(self, vals):
        vals_dict = [vals] if type(vals) == dict else vals
        sanitize = self[0].sanitize_int if self else self.sanitize_int
        recompute_phase1_ending_date = False
        for val_dict in vals_dict:
            if 'vat' in val_dict:
                val_dict['vat'] = sanitize(val_dict['vat'])
            if 'building_no' in val_dict:
                val_dict['building_no'] = sanitize(val_dict['building_no'])
            if 'additional_no' in val_dict:
                val_dict['additional_no'] = sanitize(val_dict['additional_no'])
            if 'zip' in val_dict:
                val_dict['zip'] = sanitize(val_dict['zip'])
            if 'l10n_sa_phase1_end_date' in val_dict:
                recompute_phase1_ending_date = 0
        res = super(ResCompany, self).write(vals)
        for record in self:
            # if recompute_phase1_ending_date:
            #     records = self.env['account.move'].sudo().search([('company_id', '=', self.id)])
            #     records._compute_l10n_sa_zatca_status()
            if record.parent_is_zatca:
                if len(str(record.vat)) != 15:
                    raise exceptions.ValidationError('Vat must be exactly 15 digits')
                if str(record.vat)[0] != '3' or str(record.vat)[-1] != '3':
                    raise exceptions.ValidationError(_("Vat must start/end with 3."))
        return res

    # ONLY FOR DEBUGGING
    def reset_zatca(self):
        conf = self.sudo()

        conf.csr_otp = None
        conf.csr_certificate = None
        conf.zatca_certificate_status = 0

        conf.zatca_status = None
        conf.zatca_onboarding_status = 0
        conf.zatca_on_board_status_details = None

        conf.zatca_is_sandbox = 0

        conf.zatca_sb_bsToken = None
        conf.zatca_sb_secret = None
        conf.zatca_sb_reqID = None

        conf.zatca_bsToken = None
        conf.zatca_secret = None
        conf.zatca_reqID = None

        conf.zatca_csr_base64 = None
        conf.zatca_cert_sig_algo = None
        conf.zatca_prod_private_key = None
        conf.zatca_cert_public_key = None
