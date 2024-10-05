/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

import {
    formatDate,
    formatDateTime,
    serializeDateTime,
    deserializeDate,
    deserializeDateTime,
} from "@web/core/l10n/dates";
import { random5Chars, uuidv4, qrCodeSrc, constructFullProductName } from "@point_of_sale/utils";

patch(Order.prototype, {
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.l10n_is_third_party_invoice = json.l10n_is_third_party_invoice;
        this.l10n_is_nominal_invoice = json.l10n_is_nominal_invoice;
        this.l10n_is_summary_invoice = json.l10n_is_summary_invoice;
		this.is_invoice = json.is_invoice;
		this.is_invoice_b2c = json.is_invoice_b2c;
		
		// Set default value for credit_debit_reason
        this.credit_debit_reason = json.credit_debit_reason || "مرتجع عميل"; // Change this to your desired default value
    },
	

    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        	let headerdata = result.headerData;
        	headerdata['config'] = this.pos.config || '';
        	headerdata['pos'] = this.pos || '';
        	result.headerData = headerdata;
        	// json.ksa_qr_code =  qrCodeSrc(
            //         `${this.get_qrcode_data()}`
            //     )
					const company = this.pos.company;
					const codeWriter = new window.ZXing.BrowserQRCodeSvgWriter();
					const qr_values = this.compute_sa_qr_code(
						company.name,
						company.vat,
						this.date_order.toISO(),
						this.get_total_with_tax(),
						this.get_total_tax()
					);
					const qr_code_svg = new XMLSerializer().serializeToString(
						codeWriter.write(qr_values, 150, 150)
					);
					result.qr_code = "data:image/svg+xml;base64," + window.btoa(qr_code_svg);
				
        
        return result;
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.l10n_is_third_party_invoice = this.l10n_is_third_party_invoice ? 1 : 0;
        json.l10n_is_nominal_invoice = this.l10n_is_nominal_invoice ? 1 : 0;
        json.l10n_is_summary_invoice = this.l10n_is_summary_invoice ? 1 : 0;
		json.is_invoice = this.is_invoice ? 1 : 0;
		json.is_invoice_b2c = this.is_invoice_b2c ? 1 : 0;
		
        json.credit_debit_reason = this.credit_debit_reason || 'مرتجع العميل';
        return json;
    },


	compute_sa_qr_code(name, vat, date_isostring, amount_total, amount_tax) {
        /* Generate the qr code for Saudi e-invoicing. Specs are available at the following link at page 23
    https://zatca.gov.sa/ar/E-Invoicing/SystemsDevelopers/Documents/20210528_ZATCA_Electronic_Invoice_Security_Features_Implementation_Standards_vShared.pdf
    */
        const seller_name_enc = this._compute_qr_code_field(1, name);
        const company_vat_enc = this._compute_qr_code_field(2, vat);
        const timestamp_enc = this._compute_qr_code_field(3, date_isostring);
        const invoice_total_enc = this._compute_qr_code_field(4, amount_total.toString());
        const total_vat_enc = this._compute_qr_code_field(5, amount_tax.toString());

        const str_to_encode = seller_name_enc.concat(
            company_vat_enc,
            timestamp_enc,
            invoice_total_enc,
            total_vat_enc
        );

        let binary = "";
        for (let i = 0; i < str_to_encode.length; i++) {
            binary += String.fromCharCode(str_to_encode[i]);
        }
        return btoa(binary);
    },
    _compute_qr_code_field(tag, field) {
        const textEncoder = new TextEncoder();
        const name_byte_array = Array.from(textEncoder.encode(field));
        const name_tag_encoding = [tag];
        const name_length_encoding = [name_byte_array.length];
        return name_tag_encoding.concat(name_length_encoding, name_byte_array);
    },


    decimalToHex(rgb) {
		let hex = Number(rgb).toString(16);
		if(hex.length < 2) {
			hex = "0" + hex;
		}
		return hex;
	},

	ascii_to_hexa(str) {
		let arr1 = [];
		for (let n = 0, l = str.length; n < l; n++) {
			let hex = Number(str.charCodeAt(n)).toString(16);
			arr1.push(hex);
		}
		return arr1.join('');
	},

	hexToBase64(hexstring) {
		return btoa(hexstring.match(/\w{2}/g).map(function (a) {
			return String.fromCharCode(parseInt(a, 16));
		}).join(""));
	},

	getTLV(tag, field) {
		const textEncoder = new TextEncoder();
		const name_byte_array = Array.from(textEncoder.encode(field));
		const name_tag_encoding = [tag];
		const name_length_encoding = [name_byte_array.length];
		return name_tag_encoding.concat(name_length_encoding, name_byte_array);
	},

	get_qrcode_data() {
		let self = this;
		let seller_name = self.pos.company.name;
		let seller_vat_no = self.pos.company.vat;
		let date = formatDateTime(luxon.DateTime.now());
		let total_vat =  self.get_total_tax();
		let total_with_vat = self.get_total_with_tax();

		let sallerName = self.getTLV("01",seller_name);
		let sallerVat = self.getTLV("02",seller_vat_no);
		let timeStamp = self.getTLV("03",date);
		let invoiceAmt = self.getTLV("04",total_with_vat);
		let vatAmt = self.getTLV("05",total_vat);

		const str_to_encode = sallerName.concat(sallerVat, timeStamp, invoiceAmt, vatAmt);

		let binary = '';
		for (let i = 0; i < str_to_encode.length; i++) {
			binary += String.fromCharCode(str_to_encode[i]);
		}
		return btoa(binary);
	},



});
