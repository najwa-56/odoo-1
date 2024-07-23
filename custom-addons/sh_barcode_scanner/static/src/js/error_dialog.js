/** @odoo-module **/

import { WarningDialog } from "@web/core/errors/error_dialogs";
import { browser } from "@web/core/browser/browser";
import { patch } from "@web/core/utils/patch";

patch(WarningDialog.prototype, {
    setup() {
        super.setup();
        /****************************************************************
         * softhealer custom code start here
         * SH_BARCODE_SCANNER_ is a code to identify
         * that message is coming from barcode scanner.
         * here we remove code for display valid message and play sound.
         * **************************************************************/
        var self = this;
        if (this.message.length) {
            //for auto close popup start here
            var auto_close_ms = this.message.match("AUTO_CLOSE_AFTER_(.*)_MS&");
            if (auto_close_ms && auto_close_ms.length == 2) {
                auto_close_ms = auto_close_ms[1];
                var original_msg = "AUTO_CLOSE_AFTER_" + auto_close_ms + "_MS&";
                this.message = this.message.replace(original_msg, "");
                if(auto_close_ms){
                    browser.setTimeout(function () {
                        self.props.close();
                    }, auto_close_ms);
                }
            }
            //for auto close popup ends here
            //for play sound start here
            //if message has SH_BARCODE_SCANNER_
            var str_msg = this.message.match("SH_BARCODE_SCANNER_");
            if (str_msg) {
                //remove SH_BARCODE_SCANNER_ from message and make valid message
                this.message = this.message.replace("SH_BARCODE_SCANNER_", "");
                //play sound
                var src = "/sh_barcode_scanner/static/src/sounds/error.wav";
                $("body").append('<audio src="' + src + '" autoplay="true"></audio>');
            }
            //for play sound ends here
        }
        //softhealer custom code ends here		
    }
});
