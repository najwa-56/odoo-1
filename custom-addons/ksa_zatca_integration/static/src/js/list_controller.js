/** @odoo-module **/
import {ListController} from '@web/views/list/list_controller';
import {patch} from '@web/core/utils/patch';

patch(ListController.prototype, {
    get actionMenuItems() {
        var ret_dict = super.actionMenuItems;
        var record = this.model?.root?.selection[0]?.data;
        var context = this.props?.context;

        if (this.model?.root?.resModel === 'account.move') {
            if (record?.is_zatca && record?.disable_odoo_invoices && (
                ["out_invoice", "out_refund"].includes(context?.default_move_type) ||
                (("in_invoice").includes(context?.default_move_type) && record?.l10n_is_self_billed_invoice))) {
                const unwantedNames = ["Invoices without Payment", "Invoices", 'الفواتير غير المدفوعة ', 'فواتير العملاء '];
                ret_dict.print = ret_dict.print.filter(item => !unwantedNames.includes(item.name));
            }
        }
        return ret_dict;
    },
});
