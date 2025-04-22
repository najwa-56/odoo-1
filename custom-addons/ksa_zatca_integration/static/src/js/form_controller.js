/** @odoo-module **/

import {FormController} from '@web/views/form/form_controller';
import {patch} from "@web/core/utils/patch";


patch(FormController.prototype, {
    get actionMenuItems() {
        var ret_dict = super.actionMenuItems;
        var record = this.model?.root?.data;
        var context = this.props?.context;

        if (this.model?.root?.resModel === 'account.move') {
            if (ret_dict?.print.length > 1) {
                if (record?.is_zatca)
                    ret_dict.print = ret_dict.print
                        .reduce((result, item) => {
                            if (item.name.includes("ZATCA")) {
                                result.unshift(item);
                            } else {
                                result.push(item);
                            }
                            return result;
                        }, []);
                // remove zatca report print, for non zatca companies
                else
                    ret_dict.print = ret_dict.print
                        .filter(item => !item.name.includes("ZATCA"));
            }

            if (record?.is_zatca && record?.disable_odoo_invoices && (
                ["out_invoice", "out_refund"].includes(context?.default_move_type) ||
                (("in_invoice").includes(context?.default_move_type) && record?.l10n_is_self_billed_invoice))) {
                const unwantedNames = ["Invoices without Payment", "Invoices", 'الفواتير غير المدفوعة ', 'فواتير العملاء '];
                ret_dict.print = ret_dict.print.filter(item => !unwantedNames.includes(item.name));
            }
        }

        return ret_dict;
    }
});
