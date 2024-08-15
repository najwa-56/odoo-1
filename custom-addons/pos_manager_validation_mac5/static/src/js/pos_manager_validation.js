/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { RefundButton } from "@point_of_sale/app/screens/product_screen/control_buttons/refund_button/refund_button";



patch(PosStore.prototype, {
    async _processData(loadedData) {
        this.users = loadedData['res.users.all'];
        await super._processData(loadedData);
    },

    async closePos() {
        if (this.config.iface_validate_close) {
            var managerUserIDs = this.config.manager_user_ids;
            var cashier = this.get_cashier().user_id;
            if( cashier && managerUserIDs.indexOf(cashier[0]) > -1 ){
                return await super.closePos();
            }

            const { confirmed, payload } = await this.env.services.popup.add(NumberPopup, {
                title: _t("Manager Validation"),
                isPassword: true,
            })
            var password = payload ? payload.toString() : ''

            if (confirmed) {
                this.manager = false;
                var users = this.users;
                for (var i = 0; i < users.length; i++) {
                    if (managerUserIDs.indexOf(users[i].id) > -1
                            && password === (users[i].pos_security_pin || '')) {
                        this.manager = users[i];
                    }
                }
                if (this.manager) {
                    await super.closePos();
                } else {
                    await this.env.services.popup.add(ErrorPopup, {
                        title: _t("Access Denied"),
                        body: _t("Incorrect password!"),
                    })
                }
            }
        } else {
            await super.closePos();
        }
    },
});


patch(Navbar.prototype, {
    async closeSession() {
        if (this.pos.config.iface_validate_close) {
            var managerUserIDs = this.pos.config.manager_user_ids;
            var cashier = this.pos.get_cashier().user_id;
            if( cashier && managerUserIDs.indexOf(cashier[0]) > -1 ){
                return await super.closeSession();
            }

            const { confirmed, payload } = await this.env.services.popup.add(NumberPopup, {
                title: _t("Manager Validation"),
                isPassword: true,
            })
            var password = payload ? payload.toString() : ''

            if (confirmed) {
                this.pos.manager = false;
                var users = this.pos.users;
                for (var i = 0; i < users.length; i++) {
                    if (managerUserIDs.indexOf(users[i].id) > -1
                            && password === (users[i].pos_security_pin || '')) {
                        this.pos.manager = users[i];
                    }
                }
                if (this.pos.manager) {
                    await super.closeSession();
                } else {
                    await this.env.services.popup.add(ErrorPopup, {
                        title: _t("Access Denied"),
                        body: _t("Incorrect password!"),
                    })
                }
            }
        } else {
            await super.closeSession();
        }
    },

    onCashMoveButtonClick() {
        if (this.pos.config.iface_validate_cash_move) {
            var managerUserIDs = this.pos.config.manager_user_ids;
            var cashier = this.pos.get_cashier().user_id;
            if( cashier && managerUserIDs.indexOf(cashier[0]) > -1 ){
                return super.onCashMoveButtonClick();
            }

            this.popup.add(NumberPopup, {
                title: _t("Manager Validation"),
                isPassword: true,
            }).then(({ confirmed, payload }) => {
                var password = payload ? payload.toString() : ''

                if (confirmed) {
                    this.pos.manager = false;
                    var users = this.pos.users;
                    for (var i = 0; i < users.length; i++) {
                        if (managerUserIDs.indexOf(users[i].id) > -1
                                && password === (users[i].pos_security_pin || '')) {
                            this.pos.manager = users[i];
                        }
                    }
                    if (this.pos.manager) {
                        super.onCashMoveButtonClick();
                    } else {
                        this.popup.add(ErrorPopup, {
                            title: _t("Access Denied"),
                            body: _t("Incorrect password!"),
                        })
                    }
                }
            });
        } else {
            super.onCashMoveButtonClick();
        }
    },
});


patch(Order.prototype, {
    async pay() {
        if (this.pos.config.iface_validate_payment) {
            var managerUserIDs = this.pos.config.manager_user_ids;
            var cashier = this.pos.get_cashier().user_id;
            if( cashier && managerUserIDs.indexOf(cashier[0]) > -1 ){
                return await super.pay();
            }

            const { confirmed, payload } = await this.env.services.popup.add(NumberPopup, {
                title: _t("Manager Validation"),
                isPassword: true,
            })
            var password = payload ? payload.toString() : ''

            if (confirmed) {
                this.pos.manager = false;
                var users = this.pos.users;
                for (var i = 0; i < users.length; i++) {
                    if (managerUserIDs.indexOf(users[i].id) > -1
                            && password === (users[i].pos_security_pin || '')) {
                        this.pos.manager = users[i];
                    }
                }
                if (this.pos.manager) {
                    await super.pay();
                } else {
                    await this.env.services.popup.add(ErrorPopup, {
                        title: _t("Access Denied"),
                        body: _t("Incorrect password!"),
                    })
                }
            }
        } else {
            await super.pay();
        }
    },
});


patch(ProductScreen.prototype, {
    _setValue(val) {
        var newQty = this.numberBuffer.get() ? parseFloat(this.numberBuffer.get()) : 0;
        var orderLines = !!this.currentOrder ? this.currentOrder.get_orderlines() : undefined;
        if (orderLines !== undefined && orderLines.length > 0) {
            var currentOrderLine = this.currentOrder.get_selected_orderline();
            var currentQty = this.currentOrder.get_selected_orderline().get_quantity();
            if (currentOrderLine && this.pos.numpadMode === 'quantity'
                    && ((newQty < currentQty && this.pos.config.iface_validate_decrease_quantity)
                        || (val === 'remove' && this.pos.config.iface_validate_delete_orderline))) {
                var managerUserIDs = this.pos.config.manager_user_ids;
                var cashier = this.pos.get_cashier().user_id;
                if( cashier && managerUserIDs.indexOf(cashier[0]) > -1 ){
                    return super._setValue(val);
                }

                this.popup.add(NumberPopup, {
                    title: _t("Manager Validation"),
                    isPassword: true,
                }).then(({ confirmed, payload }) => {
                    var password = payload ? payload.toString() : ''

                    if (confirmed) {
                        this.pos.manager = false;
                        var users = this.pos.users;
                        for (var i = 0; i < users.length; i++) {
                            if (managerUserIDs.indexOf(users[i].id) > -1
                                    && password === (users[i].pos_security_pin || '')) {
                                this.pos.manager = users[i];
                            }
                        }
                        if (this.pos.manager) {
                            super._setValue(val);
                        } else {
                            this.popup.add(ErrorPopup, {
                                title: _t("Access Denied"),
                                body: _t("Incorrect password!"),
                            })
                        }
                    }
                });
            } else {
                super._setValue(val);
            }
        } else {
            super._setValue(val)
        }
    },

    onNumpadClick(buttonValue) {
        if ((buttonValue === 'discount' && this.pos.config.iface_validate_discount)
                || (buttonValue === 'price' && this.pos.config.iface_validate_price)) {
            var managerUserIDs = this.pos.config.manager_user_ids;
            var cashier = this.pos.get_cashier().user_id;
            if( cashier && managerUserIDs.indexOf(cashier[0]) > -1 ){
                return super.onNumpadClick(buttonValue);
            }

            this.popup.add(NumberPopup, {
                title: _t("Manager Validation"),
                isPassword: true,
            }).then(({ confirmed, payload }) => {
                var password = payload ? payload.toString() : ''

                if (confirmed) {
                    this.pos.manager = false;
                    var users = this.pos.users;
                    for (var i = 0; i < users.length; i++) {
                        if (managerUserIDs.indexOf(users[i].id) > -1
                                && password === (users[i].pos_security_pin || '')) {
                            this.pos.manager = users[i];
                        }
                    }
                    if (this.pos.manager) {
                        super.onNumpadClick(buttonValue);
                    } else {
                        this.popup.add(ErrorPopup, {
                            title: _t("Access Denied"),
                            body: _t("Incorrect password!"),
                        })
                    }
                }
            });
        } else {
            super.onNumpadClick(buttonValue);
        }
    },
});


patch(TicketScreen.prototype, {
    async onDeleteOrder(order) {
     // Iterate through each order line to check for quantity 0
    const orderLinesToRemove = order.get_orderlines().filter(line => line.get_quantity() === 0);

    if (orderLinesToRemove.length > 0) {
        // If there are order lines with quantity 0, remove them
        for (const line of orderLinesToRemove) {
            order.remove_orderline(line);
        }

        // Optionally notify the user about the removal
        this.popup.add(InfoPopup, {
            title: _t("Order Lines Removed"),
            body: _t("Order lines with quantity 0 have been removed."),
        });

        // Update the order after removing lines
        if (order.get_orderlines().length === 0) {
            // If all lines are removed, proceed with the full order deletion
            const screen = order.get_screen_data();
            if (
                ["ProductScreen", "PaymentScreen"].includes(screen.name) &&
                order.get_orderlines().length === 0
            ) {
                const { confirmed } = await this.popup.add(ConfirmPopup, {
                    title: _t("Empty Order"),
                    body: _t("This order is now empty. Are you sure you want to delete it?"),
                });
                if (!confirmed) {
                    return confirmed;
                }
            }
        }
    }
        if (this.pos.config.iface_validate_delete_order) {
            var managerUserIDs = this.pos.config.manager_user_ids;
            var cashier = this.pos.get_cashier().user_id;
            if( cashier && managerUserIDs.indexOf(cashier[0]) > -1 ){
                return await super.onDeleteOrder(order);
            }

            const { confirmed, payload } = await this.popup.add(NumberPopup, {
                title: _t("Manager Validation"),
                isPassword: true,
            });
            var password = payload ? payload.toString() : ''

            if (confirmed) {
                this.pos.manager = false;
                var users = this.pos.users;
                for (var i = 0; i < users.length; i++) {
                    if (managerUserIDs.indexOf(users[i].id) > -1
                            && password === (users[i].pos_security_pin || '')) {
                        this.pos.manager = users[i];
                    }
                }
                if (this.pos.manager) {
                    await super.onDeleteOrder(order);
                } else {
                    await this.popup.add(ErrorPopup, {
                        title: _t("Access Denied"),
                        body: _t("Incorrect password!"),
                    })
                }
            }
        } else {
            await super.onDeleteOrder(order);
        }
    },

});
patch(RefundButton.prototype, {
      click() {
    if (this.pos.config.iface_validate_Refund) {
        var managerUserIDs = this.pos.config.manager_user_ids;
        var cashier = this.pos.get_cashier().user_id;
        if (cashier && managerUserIDs.indexOf(cashier[0]) > -1) {
            // If manager validation is not required, or the cashier is a manager, proceed with the click
            return super.click();
        }

        this.env.services.popup.add(NumberPopup, {
            title: _t("Manager Validation"),
            isPassword: true,
        }).then(({ confirmed, payload }) => {
            var password = payload ? payload.toString() : '';

            if (confirmed) {
                this.pos.manager = false;
                var users = this.pos.users;
                for (var i = 0; i < users.length; i++) {
                    if (managerUserIDs.indexOf(users[i].id) > -1
                            && password === (users[i].pos_security_pin || '')) {
                        this.pos.manager = users[i];
                    }
                }
                if (this.pos.manager) {
                    // Call the superclass method
                    super.click();

                    // Additional functionality after manager validation
                    const order = this.pos.get_order();
                    const partner = order.get_partner();
                    const searchDetails = partner ? { fieldName: "PARTNER", searchTerm: partner.name } : {};
                    this.pos.showScreen("TicketScreen", {
                        ui: { filter: "SYNCED", searchDetails },
                        destinationOrder: order,
                    });
                } else {
                    this.env.services.popup.add(ErrorPopup, {
                        title: _t("Access Denied"),
                        body: _t("Incorrect password!"),
                    });
                }
            }
        });
    } else {
        // If manager validation is not required, proceed with the click
        super.click();

        // Additional functionality when validation is not required
        const order = this.pos.get_order();
        const partner = order.get_partner();
        const searchDetails = partner ? { fieldName: "PARTNER", searchTerm: partner.name } : {};
        this.pos.showScreen("TicketScreen", {
            ui: { filter: "SYNCED", searchDetails },
            destinationOrder: order,
        });
    }
}




});
