/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class AutoCloseDialog extends ConfirmationDialog {
    setup() {
        super.setup();
        if (this.props && this.props.autoCloseAfter){
            browser.setTimeout(()=>{
                this.props.close();
            },this.props.autoCloseAfter);
        }
    }
}

AutoCloseDialog.template = "sh_barcode_scanner.InventoryAdjustmentAutoCloseDialog";
AutoCloseDialog.props = {
    ...ConfirmationDialog.props,
    autoCloseAfter: {type : Number, optional:true}
};
