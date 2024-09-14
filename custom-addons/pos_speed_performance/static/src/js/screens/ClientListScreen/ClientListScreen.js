//odoo.define('pos_speed_performance.PartnerListScreen', function (require) {
//    "use strict";
//
//    const PartnerListScreen = require('point_of_sale.PartnerListScreen');
//    const Registries = require('point_of_sale.Registries');
//
//
//    let PartnerListScreenOnline = PartnerListScreen =>
//        class extends PartnerListScreen {
//            async _onPressEnterKey() {
//                if (this.env.pos.company.x_allow_online_search){
//                    if (!this.state.query) return;
//                    const result = await this.searchPartner();
//                    this.showNotification(
//                        _.str.sprintf(this.env._t('%s customer(s) found for "%s".'),
//                            result.length,
//                            this.state.query)
//                        , 3000);
//                    if(!result.length) this._clearSearch();
//                } else {
//                    super._onPressEnterKey();
//                }
//            }
//        }
//
//    Registries.Component.extend(PartnerListScreen, PartnerListScreenOnline);
//
//    return PartnerListScreen;
//
//});