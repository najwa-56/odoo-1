/** @odoo-module **/
import {registry} from "@web/core/registry";
import {onMounted, Component} from "@odoo/owl";
import {onWillStart, useState} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {formatMonetary} from "@web/views/fields/formatters";

export class MainDashboard extends Component {
    static template = 'zatca.DashboardMain';
    static props = ["*"];

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.rpc = this.env.services.rpc
        this.state = useState({
            dashboards_templates: ['zatca.DashboardMain'],
        })
        this.custom_props = {};
        onMounted(async () => {
            this.title = 'Dashboard'
            var self = this
            await self.getTransmissionsToday();
            await self.getInvoicesThisYear();
            await self.getTaxAmountThisYear();
            await self.getPostedInvoices();
            this.render();
        });
    }

    async getPostedInvoices() {
        var yearlyRecords = await this.getThisYearRecords();
        if (yearlyRecords) {
            var invoiceCount = 0;
            var standardCount = 0;
            var simplifiedCount = 0;
            yearlyRecords.forEach(record => {
                if (record.state == 'posted' && record.zatca_invoice == false) {
                    invoiceCount++;
                    if (record.l10n_sa_invoice_type === 'Standard') {
                        standardCount++;
                    } else if (record.l10n_sa_invoice_type === 'Simplified') {
                        simplifiedCount++;
                    }
                }
            });

            this.custom_props.posted_invoice = invoiceCount;
            this.custom_props.standard_posted_invoice = "Standard: " + standardCount;
            this.custom_props.simplified_posted_invoice = "Simplified: " + simplifiedCount;
        }
    }

    async getTransmissionsToday() {
        var company_ids = await this.getCompany();
        if (company_ids) {
            const currentDate = new Date();
            const startOfDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate());
            const endOfDay = new Date(startOfDay.getTime() + (24 * 60 * 60 * 1000) - 1);

            // Construct the domain to fetch all records for today
            var domain = [['company_id', 'in', company_ids],
                ['move_type', '=', 'out_invoice'],
                ['l10n_sa_response_datetime', '>=', startOfDay.toISOString()],
                ['l10n_sa_response_datetime', '<=', endOfDay.toISOString()]];

            // Fetch all records for today
            var todayRecords = await this.orm.call('account.move', 'search_read', [domain, ['name', 'l10n_sa_invoice_type', 'l10n_sa_zatca_status', 'l10n_sa_response_datetime']]);
            // Initialize counts for each invoice type
            var standardCount = 0;
            var simplifiedCount = 0;
            var success_records = 0;
            var failed_records = 0;
            // Iterate through records to count each type
            todayRecords.forEach(record => {
                if (record.l10n_sa_invoice_type === 'Standard') {
                    standardCount++;
                } else if (record.l10n_sa_invoice_type === 'Simplified') {
                    simplifiedCount++;
                }
                if (record.l10n_sa_zatca_status === 'CLEARED' || record.l10n_sa_zatca_status === 'REPORTED') {
                    success_records++;
                }
            });
            failed_records = todayRecords.length - success_records;
            // Update HTML elements with the counts
            this.custom_props.transmissions_today = todayRecords.length;
            this.custom_props.simplified_today = "Simplified: " + simplifiedCount;
            this.custom_props.standard_today = "Standard: " + standardCount;
            this.custom_props.transmissions_success_today = success_records;
            this.custom_props.transmissions_failed_today = failed_records;

            if (todayRecords.length > 0) {
                var lastTransmissionName = todayRecords[0].name;
                var lastTransmissionDateTime = todayRecords[0].l10n_sa_response_datetime;
                // Update HTML elements with the last transmission information
                this.custom_props.last_transmission_name = lastTransmissionName;
                this.custom_props.last_transmission_date_time = lastTransmissionDateTime;
            } else {
                // If no records found, display appropriate message
                this.custom_props.last_transmission_name = "No transmissions today";
                this.custom_props.last_transmission_date_time = "";
            }
        }
    }

    async getCompany() {
        var domain = [['is_zatca', '=', true]];
        var company = await this.orm.call('res.company', 'search_read', [domain], {fields: ['id']});
        if (company) {
            var company_ids = company.map(company => company.id);
            return company_ids;
        }
        return 0;
    }

    async getThisYearRecords() {
        var company_ids = await this.getCompany();
        if (company_ids) {
            const currentDate = new Date();
            const startOfYear = new Date(currentDate.getFullYear(), 0, 1); // January 1st of the current year
            const endOfYear = new Date(currentDate.getFullYear() + 1, 0, 0); // December 31st of the current year
            // var domain = [['company_id', 'in', company_ids], ['move_type', '=', 'out_invoice'],
            //     ['l10n_sa_confirmation_datetime', '>=', startOfYear.toISOString()],
            //     ['l10n_sa_confirmation_datetime', '<=', endOfYear.toISOString()]];

            // // use this domain from 2025
            var domain = [['company_id', 'in', company_ids], ['move_type', '=', 'out_invoice'],
                ['l10n_sa_response_datetime', '>=', startOfYear.toISOString()],
                ['l10n_sa_response_datetime', '<=', endOfYear.toISOString()]];

            var records = await this.orm.call('account.move', 'search_read', [domain], {fields: ['l10n_sa_invoice_type', 'l10n_sa_zatca_status', 'amount_tax_signed', 'state', 'zatca_invoice']});
            return records

        } else
            return false
    }

    async getInvoicesThisYear() {
        var yearlyRecords = await this.getThisYearRecords();
        if (yearlyRecords) {
            // Initialize counts for each invoice type
            var invoiceCountYearly = 0;
            var standardCountYearly = 0;
            var simplifiedCountYearly = 0;
            var approved_yearly = 0;
            var simplified_yearly_approved = 0;
            var standard_yearly_approved = 0;

            // Iterate through records to count each type
            yearlyRecords.forEach(record => {
                if (record.l10n_sa_invoice_type && record.l10n_sa_zatca_status !== 'Phase 1') {
                    invoiceCountYearly++;
                    if (record.l10n_sa_invoice_type === 'Standard') {
                        standardCountYearly++;
                    } else if (record.l10n_sa_invoice_type === 'Simplified') {
                        simplifiedCountYearly++;
                    }
                }
                if (record.l10n_sa_zatca_status === 'CLEARED' || record.l10n_sa_zatca_status === 'REPORTED') {
                    approved_yearly++;
                    if (record.l10n_sa_invoice_type === 'Standard') {
                        standard_yearly_approved++;
                    } else if (record.l10n_sa_invoice_type === 'Simplified') {
                        simplified_yearly_approved++;
                    }
                }
            });

            // Update HTML elements with the counts
            this.custom_props.invoices_yearly = invoiceCountYearly;
            this.custom_props.simplified_yearly = "Simplified: " + simplifiedCountYearly;
            this.custom_props.standard_yearly = "Standard: " + standardCountYearly;
            this.custom_props.yearly_approved = approved_yearly;
            this.custom_props.yearly_approved_simplified = "Simplified: " + simplified_yearly_approved;
            this.custom_props.yearly_approved_standard = "Standard: " + standard_yearly_approved;
        }
    }

    async getTaxAmountThisYear() {
        var yearlyRecords = await this.getThisYearRecords();
        if (yearlyRecords) {
            // Initialize tax amounts for each invoice type and approved tax amounts
            var simplifiedTaxAmount = 0;
            var standardTaxAmount = 0;
            var simplifiedTaxApprovedAmount = 0;
            var standardTaxApprovedAmount = 0;

            // Iterate through records to sum tax amounts and approved tax amounts for each type
            yearlyRecords.forEach(record => {
                if (record.l10n_sa_zatca_status !== 'Phase 1') {
                    if (record.l10n_sa_invoice_type === 'Standard') {
                        standardTaxAmount += record.amount_tax_signed;
                        if (record.l10n_sa_zatca_status === 'CLEARED' || record.l10n_sa_zatca_status === 'REPORTED') {
                            standardTaxApprovedAmount += record.amount_tax_signed;
                        }
                    } else if (record.l10n_sa_invoice_type === 'Simplified') {
                        simplifiedTaxAmount += record.amount_tax_signed;
                        if (record.l10n_sa_zatca_status === 'CLEARED' || record.l10n_sa_zatca_status === 'REPORTED') {
                            simplifiedTaxApprovedAmount += record.amount_tax_signed;
                        }
                    }
                }
            });

            // Calculate total tax amount and approved tax amount for the year
            var totalTaxAmountYearly = simplifiedTaxAmount + standardTaxAmount;
            var totalTaxApprovedAmountYearly = simplifiedTaxApprovedAmount + standardTaxApprovedAmount;
            var domain = [['name', '=', 'SAR']];
            var res_currency_id = await this.orm.call('res.currency', 'search_read', [domain], {fields: ['id']});
            res_currency_id = res_currency_id && res_currency_id[0]['id'];

            // Update HTML elements with the tax amounts and approved tax amounts
            this.custom_props.tax_amount_yearly = this.formatCost(totalTaxAmountYearly, res_currency_id);
            this.custom_props.simplified_tax_amount = "Simplified: " + this.formatCost(simplifiedTaxAmount, res_currency_id);
            this.custom_props.standard_tax_amount = "Standard: " + this.formatCost(standardTaxAmount, res_currency_id);
            this.custom_props.tax_approved_yearly = this.formatCost(totalTaxApprovedAmountYearly, res_currency_id);
            this.custom_props.simplified_tax_approved_yearly = "Simplified: " + this.formatCost(simplifiedTaxApprovedAmount, res_currency_id);
            this.custom_props.standard_tax_approved_yearly = "Standard: " + this.formatCost(standardTaxApprovedAmount, res_currency_id);
        }
    }

    formatCost(cost, res_currency_id) {
        return formatMonetary(cost, {currencyId: res_currency_id});
    }
}

registry.category("actions").add("zatca_main_dashboard", MainDashboard)