/** @odoo-module **/

//import { patch } from "@web/core/utils/patch";
//import { Composer } from "@mail/core/common/composer";
//import { _t } from "@web/core/l10n/translation";
//
//patch(Composer.prototype,{
//
//    get placeholder() {
//        if (this.props.placeholder) {
//            return this.props.placeholder;
//        }
//        if (this.thread) {
//            if (this.thread.type === "channel") {
//                return _t("Message #%(thread name)s…", { "thread name": this.thread.displayName ? this.thread.displayName : ''});
//            }
//            return _t("Message %(thread name)s…", { "thread name": this.thread.displayName ? this.thread.displayName : '' });
//        }
//        return "";
//    }
//});