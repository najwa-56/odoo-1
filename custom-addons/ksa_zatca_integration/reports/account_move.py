from odoo.tools.pdf import OdooPdfFileReader, OdooPdfFileWriter
from PyPDF2.generic import DictionaryObject, NameObject
from odoo import fields, models, exceptions, _
from odoo.tools.float_utils import float_round
from odoo.tools import mute_logger
import lxml.etree as ET
import logging
import base64
import qrcode
import io
_logger = logging.getLogger(__name__)

_zatca = logging.getLogger('Zatca Debugger for account.move :')
ubl_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
ubl_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"


class AccountMoveReport(models.Model):
    _inherit = 'account.move'

    def get_context_datetime(self):
        # %H:%M can be removed.
        return fields.Datetime.context_timestamp(
            self.with_context(tz='Asia/Riyadh'), self.l10n_sa_confirmation_datetime) \
            .strftime('%Y-%m-%d %H:%M')

    def _l10n_sa_pdf_conversion(self, collected_streams):
        is_tax_invoice = 1 if self.l10n_sa_invoice_type == 'Standard' else 0
        xml = self.zatca_hash_cleared_invoice if is_tax_invoice else self.zatca_invoice

        # Only proceed with attachment and PDF/A if XML is available and valid
        if xml and isinstance(xml, (str, bytes)):
            try:
                xml_facturx = base64.b64decode(xml)
            except Exception as decode_err:
                _logger.warning("Failed to decode ZATCA XML for invoice %s: %s", self.name, decode_err)
                return collected_streams  # Skip PDF/A logic, allow report to continue

            try:
                pdf_stream = collected_streams[self.id]['stream']
                pdf_content = pdf_stream.getvalue()
                reader_buffer = io.BytesIO(pdf_content)
                reader = OdooPdfFileReader(reader_buffer, strict=False)
                writer = OdooPdfFileWriter()
                writer.cloneReaderDocumentRoot(reader)

                # Ensure /Outlines key exists
                if '/Outlines' not in writer._root_object:
                    outlines_dict = DictionaryObject()
                    outlines_dict.update({NameObject("/Count"): 0})
                    writer._root_object.update({NameObject("/Outlines"): outlines_dict})

                writer.addAttachment(self.zatca_invoice_name, xml_facturx, subtype='text/xml')

                try:
                    writer.convert_to_pdfa()
                except Exception as e:
                    _zatca.exception("Error while converting to PDF/A for invoice %s: %s", self.name, e)

                metadata_xml = self.env['ir.qweb']._render(
                    'account_edi_ubl_cii.account_invoice_pdfa_3_facturx_metadata',
                    {'title': self.name, 'date': fields.Date.context_today(self)}
                )
                writer.add_file_metadata(metadata_xml.encode())

                pdf_stream.close()
                writer_buffer = io.BytesIO()
                writer.write(writer_buffer)
                collected_streams[self.id]['stream'] = writer_buffer
                reader_buffer.close()
                # writer_buffer.close()  # Usually not needed, let GC handle it
            except Exception as final_error:
                _logger.exception("Unhandled error in ZATCA PDF/A conversion for invoice %s: %s", self.name, final_error)

        else:
            _logger.info("ZATCA XML not available for invoice %s; skipping PDF/A embedding.", self.name)

        return collected_streams


    # def _l10n_sa_pdf_conversion(self, collected_streams):
    #     is_tax_invoice = 1 if self.l10n_sa_invoice_type == 'Standard' else 0
    #     xml = self.zatca_hash_cleared_invoice if is_tax_invoice else self.zatca_invoice
    #     # if not xml:
    #     #     raise exceptions.MissingError(
    #     #         _("Cleared invoice from zatca is required.") if is_tax_invoice else _(
    #     #             "xml not generated."))
    #     if xml:
    #         xml_facturx = base64.b64decode(xml)
    #         pdf_stream = collected_streams[self.id]['stream']

    #         pdf_content = pdf_stream.getvalue()
    #         reader_buffer = io.BytesIO(pdf_content)
    #         reader = OdooPdfFileReader(reader_buffer, strict=False)
    #         writer = OdooPdfFileWriter()
    #         writer.cloneReaderDocumentRoot(reader)
    #         if '/Outlines' not in writer._root_object:
    #             outlines_dict = DictionaryObject()
    #             outlines_dict.update({
    #                 NameObject("/Count"): 0,
    #             })
    #             writer._root_object.update({
    #                 NameObject("/Outlines"): outlines_dict
    #             })

    #         writer.addAttachment(self.zatca_invoice_name, xml_facturx, subtype='text/xml')

    #         try:
    #             writer.convert_to_pdfa()
    #         except Exception as e:
    #             _zatca.exception("Error while converting to PDF/A: %s", e)

    #         content = self.env['ir.qweb']._render(
    #             'account_edi_ubl_cii.account_invoice_pdfa_3_facturx_metadata',
    #             {'title': self.name, 'date': fields.Date.context_today(self)})
    #         writer.add_file_metadata(content.encode())

    #         pdf_stream.close()
    #         writer_buffer = io.BytesIO()
    #         writer.write(writer_buffer)
    #         collected_streams[self.id]['stream'] = writer_buffer
    #         reader_buffer.close()
    #         # writer_buffer.close()
    #     return collected_streams

    def get_zatca_onboarding_status(self):
        com = self.company_id.parent_root_id.sudo()
        if (com.is_zatca and com.zatca_onboarding_status and
                (not self.zatca_compliance_invoices_api or
                 ("Onboarding failed, restart process !!" not in self.zatca_compliance_invoices_api
                  and "Onboarding in progress" not in self.zatca_compliance_invoices_api))):
            return 1
        else:
            return 0

    def print_einv_auto(self, is_pdf=0):
        is_tax_invoice = 1 if self.l10n_sa_invoice_type == 'Standard' else 0
        if not self.zatca_invoice:
            raise exceptions.MissingError(_("Xml not created yet."))
        if not self.get_zatca_onboarding_status():
            raise exceptions.MissingError(_("Qr code can't be created with CCSID."))
        if is_tax_invoice:
            if not self.zatca_hash_cleared_invoice:
                raise exceptions.MissingError(_("Cleared invoice from zatca is required."))

            report = self._get_zatca_invoice()[0]
        else:
            report = self._get_zatca_invoice()[1]
        if is_pdf:
            self.env.ref(report)._render_qweb_pdf(res_ids=self.ids)
        return self.env.ref(report).report_action(self)

    def print_einv_b2b(self):
        is_tax_invoice = 1 if self.l10n_sa_invoice_type == 'Standard' else 0
        if not is_tax_invoice:
            raise exceptions.MissingError(_("Not a standard invoice."))
        if not self.zatca_invoice:
            raise exceptions.MissingError(_("Xml not created yet."))
        if not self.get_zatca_onboarding_status():
            raise exceptions.MissingError(_("Qr code can't be created with CCSID."))
        if not self.zatca_hash_cleared_invoice:
            raise exceptions.MissingError(_("Cleared invoice from zatca is required."))
        return self.env.ref(self._get_zatca_invoice()[0]).report_action(self)

    def print_einv_b2c(self):
        is_tax_invoice = 1 if self.l10n_sa_invoice_type == 'Standard' else 0
        if is_tax_invoice:
            raise exceptions.MissingError(_("Not a simplified invoice."))
        if not self.zatca_invoice:
            raise exceptions.MissingError(_("Xml not created yet."))
        if not self.get_zatca_onboarding_status():
            raise exceptions.MissingError(_("Qr code can't be created with CCSID."))
        return self.env.ref(self._get_zatca_invoice()[1]).report_action(self)

    def get_invoice_type_code(self):
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        ksa_2 = xml_file.find("//{%s}InvoiceTypeCode" % ubl_CBC).attrib.get('name', '')
        return ksa_2

    def get_other_id(self, eng):
        other_id = {
            "Tax Identification Number": "رقم التعريف الضريبي",
            "Commercial Registration number": "رقم السجل التجاري",
            "Momrah license": "رخصة معمره",
            "MHRSD license": "رخصة MHRSD",
            "700 Number": "700 رقم",
            "MISA license": "رخصة ميسا",
            "National ID": "الهوية الوطنية",
            "GCC ID": "معرف دول مجلس التعاون الخليجي",
            "Iqama Number": "رقم الاقامة",
            "Passport ID": "رقم جواز السفر",
            "Other OD": "التطوير التنظيمي الآخر",
        }
        return other_id.get(eng, 'error')

    def get_bt_109(self):
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        legal_monetary_total = xml_file.find('./{%s}LegalMonetaryTotal' % ubl_CAC)
        bt_109 = legal_monetary_total.find('.//{%s}TaxExclusiveAmount' % ubl_CBC)
        return float(bt_109.text) if float(bt_109.text) else 0

    def get_bt_112(self):
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        legal_monetary_total = xml_file.find('./{%s}LegalMonetaryTotal' % ubl_CAC)
        bt_112 = legal_monetary_total.find('.//{%s}TaxInclusiveAmount' % ubl_CBC)
        return float(bt_112.text) if float(bt_112.text) else 0

    def get_bt_111(self):
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        legal_monetary_total = xml_file.findall('./{%s}TaxTotal' % ubl_CAC)
        bt_111 = legal_monetary_total[-1].find('.//{%s}TaxAmount' % ubl_CBC)
        return float(bt_111.text) if float(bt_111.text) else 0

    def get_bt_110(self):
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        legal_monetary_total = xml_file.findall('./{%s}TaxTotal' % ubl_CAC)
        bt_110 = legal_monetary_total[0].find('.//{%s}TaxAmount' % ubl_CBC)
        return float(bt_110.text) if float(bt_110.text) else 0

    def get_bt_114(self):
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        legal_monetary_total = xml_file.find('./{%s}LegalMonetaryTotal' % ubl_CAC)
        bt_114 = legal_monetary_total.find('.//{%s}PayableRoundingAmount' % ubl_CBC)
        return float(bt_114.text) if bt_114 is not None else 0

    def get_bt_115(self):
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        legal_monetary_total = xml_file.find('./{%s}LegalMonetaryTotal' % ubl_CAC)
        bt_115 = legal_monetary_total.find('.//{%s}PayableAmount' % ubl_CBC)
        return float(bt_115.text) if float(bt_115.text) else 0

    def get_bt_131(self, id, line):
        id = str(int(id))
        if not int(id):
            return line.price_subtotal
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        bt_131_find = "//{%s}ID[.='%s']" % (ubl_CBC, id)
        bt_126 = xml_file.find(bt_131_find).getparent()
        bt_131 = bt_126.find('{%s}LineExtensionAmount' % ubl_CBC)
        return float(bt_131.text) if float(bt_131.text) else 0

    def get_bt_136(self, id, line):
        id = str(int(id))
        if not int(id):
            return 0
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        bt_136_find = "//{%s}ID[.='%s']" % (ubl_CBC, id)
        bt_126 = xml_file.find(bt_136_find).getparent()
        bg_27 = bt_126.find('{%s}AllowanceCharge' % ubl_CAC)
        if bg_27 is None:
            return 0.0
        bt_136 = bg_27.find('{%s}Amount' % ubl_CBC)
        return float(bt_136.text) if float(bt_136.text) else 0

    def get_bt_146(self, id, line):
        id = str(int(id))
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        if not int(id):
            invoice_line_ids = self.invoice_line_ids.filtered(lambda x: not x.zatca_id)
            index = [idx for idx, invoice_line_id in enumerate(invoice_line_ids) if
                     invoice_line_id.id == line.id][0]
            bg_20_find = '{%s}AllowanceCharge' % ubl_CAC
            bg_20 = xml_file.findall(bg_20_find)[index]
            bt_92 = bg_20.find('{%s}Amount' % ubl_CBC)
            return float(bt_92.text) * -1 if float(bt_92.text) else 0
        bt_136_find = "//{%s}ID[.='%s']" % (ubl_CBC, id)
        bt_126 = xml_file.find(bt_136_find).getparent()
        bg_29 = bt_126.find('{%s}Price' % ubl_CAC)
        bt_146 = bg_29.find('{%s}PriceAmount' % ubl_CBC)
        return float(bt_146.text) if float(bt_146.text) else 0

    def get_ksa_11(self, id, line):
        id = str(int(id))
        if not int(id):
            return line.price_total - self.get_bt_146(id, line)
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        ksa_11_find = "//{%s}ID[.='%s']" % (ubl_CBC, id)
        bt_126 = xml_file.find(ksa_11_find).getparent()
        tax_total = bt_126.find('{%s}TaxTotal' % ubl_CAC)
        if tax_total is None:
            return 0.0
        ksa_11 = tax_total.find('{%s}TaxAmount' % ubl_CBC)
        return float(ksa_11.text) if float(ksa_11.text) else 0

    def get_ksa_12(self, id, line):
        id = str(int(id))
        if not int(id):
            return line.price_total
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        ksa_12_find = "//{%s}ID[.='%s']" % (ubl_CBC, id)
        bt_126 = xml_file.find(ksa_12_find).getparent()
        tax_total = bt_126.find('{%s}TaxTotal' % ubl_CAC)
        if tax_total is None:
            bt_131 = self.get_bt_131(id, line)
            if bt_131 == 0:
                return 0
            bg_31 = bt_126.find('{%s}Item' % ubl_CAC)
            bg_20 = bg_31.find('{%s}ClassifiedTaxCategory' % ubl_CAC)
            bt_152 = bg_20.find('{%s}Percent' % ubl_CBC)
            bt_152 = 0 if bt_152 is None else (float(bt_152.text) if float(bt_152.text) else 0)
            ksa_11 = float('{:0.2f}'.format(
                float_round(bt_131 * bt_152 / 100, precision_rounding=0.01)))  # BR-KSA-50
            ksa_12 = float('{:0.2f}'.format(
                float_round(bt_131 + ksa_11, precision_rounding=0.01)))  # BR-KSA-51
            return ksa_12
        ksa_12 = tax_total.find('{%s}RoundingAmount' % ubl_CBC)
        return float(ksa_12.text) if float(ksa_12.text) else 0

    def get_bt_120(self):
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        tax_total = xml_file.find('./{%s}TaxTotal' % ubl_CAC)
        if tax_total is None:
            return 0.0
        bt_120 = tax_total.findall('.//{%s}TaxExemptionReason' % ubl_CBC)
        if not len(bt_120):
            return ""
        return [bt_120_text.text for bt_120_text in bt_120] if len(bt_120) > 0 else False

    def get_bg_25_bt_120(self, id, line):
        id = str(int(id))
        if not int(id):
            return ""
        invoice = base64.b64decode(self.zatca_invoice).decode()
        xml_file = ET.fromstring(invoice).getroottree()
        bt_136_find = "//{%s}ID[.='%s']" % (ubl_CBC, id)
        bt_126 = xml_file.find(bt_136_find).getparent()
        bg_31 = bt_126.find('{%s}Item' % ubl_CAC)
        bg_20 = bg_31.find('{%s}ClassifiedTaxCategory' % ubl_CAC)
        bt_120 = bg_20.find('{%s}TaxExemptionReason' % ubl_CBC)
        bt_120_text = False if bt_120 is None else bt_120.text
        get_bt_120 = self.get_bt_120()
        if bt_120_text and get_bt_120 not in [0, False, '', None] and len(get_bt_120) > 0:
            bt_120_text = '*' * (get_bt_120.index(bt_120_text) + 1)
        return bt_120_text

    @mute_logger('Zatca Debugger for account.move :')
    def get_qrcode(self):
        # qr = qrcode.QRCode(version=1,
        #                    box_size=10,
        #                    border=5)
        #
        # # Adding data to the instance 'qr'
        # qr.add_data(self.l10n_sa_qr_code_str)
        #
        # qr.make(fit=True)
        # img = qr.make_image(fill_color='red',
        #                     back_color='white')
        # x = img
        if not self.zatca_invoice:
            raise exceptions.MissingError(_("Xml not created yet."))
        if not self.get_zatca_onboarding_status():
            raise exceptions.MissingError(_("Qr code can't be created with CCSID."))

        self._compute_qr_code_str()
        _zatca.info("l10n_sa_qr_code_str:: %s", self.l10n_sa_qr_code_str)
        qr = qrcode.make(self.l10n_sa_qr_code_str)
        from PIL import Image
        import io

        def image_to_byte_array(image: Image) -> bytes:
            # BytesIO is a fake file stored in memory
            buffered = io.BytesIO()
            # image.save expects a file as an argument, passing a bytes io ins
            image.save(buffered, format=image.format)
            # Turn the BytesIO object back into a bytes object
            img_str = base64.b64encode(buffered.getvalue())
            return img_str

        _zatca.info("image_to_byte_array(qr).decode():: %s", image_to_byte_array(qr).decode())
        return "data:image/png;base64," + image_to_byte_array(qr).decode()
