/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { escape } from "@web/core/utils/strings";
import { markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class partner_select_current_point extends Component {

    setup(){
        super.setup();
        this.rpc = useService('rpc');
        this.action = useService('action')
        var self = this;
        this.context = this.action.context || {};
        this.actionManager = parent;
        this.options = {};
        this.dialogService = useService("dialog");
        console.log("props.action.context.active_model=======================",this.props.action.context.active_model)
        // if (this.props.action.context.active_model === "res.partnerr") {
            this.rpc("/google_cred_customer", {}).then(function (data){
                if(data && data.res_partner_use_gmap){
                    navigator.geolocation.getCurrentPosition(success);
                    function success(position) {
                        const latitude  = position.coords.latitude;
                        const longitude = position.coords.longitude;
                        if (latitude && longitude){
                            self.get_address_location(latitude, longitude, data.res_partner_use_gmap);
                        }else{
                            self.fail()
                        }
                    }
                }
            })
        // }
    }

    get_address_location(latitude, longitude, res_partner_use_gmap) {
        var self = this;
        $.getScript("https://maps.googleapis.com/maps/api/js?key="+ res_partner_use_gmap + "&libraries=places&signed_in=true", function() {
            document.getElementById("map-canvas").style.width = "97%";
            document.getElementById("map-canvas").style.height = "90%";
            document.getElementById("map-canvas").style.position = "absolute";
            $(".modal-content").css({'height': '90%', 'width': '90%', 'position': 'absolute'});
            $(".modal-title").text('Select End Location');
            $(".modal-footer");

            const newButton = document.createElement("button");
            newButton.classList.add("btn", "btn-primary");
            newButton.innerText = "SAVE";
            newButton.addEventListener("click", () => {
                self._OpenConfirmationDialog();
            });
            $(".modal-footer").prepend(newButton);

            const closeButton = $(".btn.btn-primary.o-default-button")[0];
            closeButton.innerText = "CANCEL";


            var myOptions = {
                zoom: 18,
            },
            geocoder = new google.maps.Geocoder(),
            map = new google.maps.Map(document.getElementById('map-canvas'), myOptions);
            var icon = {
                path: "M27.648-41.399q0-3.816-2.7-6.516t-6.516-2.7-6.516 2.7-2.7 6.516 2.7 6.516 6.516 2.7 6.516-2.7 2.7-6.516zm9.216 0q0 3.924-1.188 6.444l-13.104 27.864q-.576 1.188-1.71 1.872t-2.43.684-2.43-.684-1.674-1.872l-13.14-27.864q-1.188-2.52-1.188-6.444 0-7.632 5.4-13.032t13.032-5.4 13.032 5.4 5.4 13.032z",
                fillColor: '#E32831',
                fillOpacity: 1,
                strokeWeight: 0,
                scale: 0.65
            };
            var marker = new google.maps.Marker({
                map: map,
                icon: icon,
                animation: google.maps.Animation.DROP,
            });

            map.setCenter(new google.maps.LatLng(latitude, longitude));
            $.when(marker.setPosition(map.getCenter())).then(function () {
                // {
                    self.onClickMarker(marker, map.getCenter(), geocoder);
                // }
            })
            map.addListener('click', function(e) {
                self.onClickMarker(marker, e.latLng, geocoder);
            });
        });
    }

    async onClickMarker(marker, latLng, geocoder) {
        if (!marker || !latLng) {
            return
        }
        var self = this;
        function animatedMove(marker, n, current, moveto) {
            var lat = current.lat();
            var lng = current.lng();
            var deltalat = (moveto.lat() - current.lat()) / 100;
            var deltalng = (moveto.lng() - current.lng()) / 100;

            for (var i = 0; i < 100; i++) {
                (function(ind) {
                    setTimeout(function() {
                        var lat = marker.position.lat();
                        var lng = marker.position.lng();

                        lat += deltalat;
                        lng += deltalng;
                        var latlng = new google.maps.LatLng(lat, lng);
                        marker.setPosition(latlng);
                    }, 5 * ind);
                })(i)
            }
        }
        animatedMove(marker, 10, marker.position, latLng);
        geocoder.geocode({
            'latLng': latLng
        }, function(results, status) {
            if (status == google.maps.GeocoderStatus.OK) {
                if (results[0]) {
                    if (results[0].address_components && results[0].address_components.length > 1) {
                        var address = results[0];
                        var location = results[0].formatted_address;
                    } else {
                        if (results.length > 2) {
                            var address = results[results.length-2];
                            var location = results[0].formatted_address + ", " + results[results.length-2].formatted_address;
                        } else {
                            var address = results[0];
                            var location = results[0].formatted_address;
                        }
                    }
                    self.location_name = location;
                    self.address = address.address_components;
                    self.addres_component_length = address.address_components.length;
                    self.latitude = latLng.lat();
                    self.longitude = latLng.lng();
                    document.getElementById("current_address").textContent = 'Current Address: '+location;
                }
            }
        });
    }

    _OpenConfirmationDialog () {
        var self = this;
        if (this.location_name && this.address && this.addres_component_length && this.latitude && this.longitude){
            this.rpc('/set_current_location_name_contact/',{
                        active_id: self.props.action.context.active_id,
                        location_name: this.location_name,
                        address: this.address,
                        addres_component_length: this.addres_component_length,
                        latitude : this.latitude,
                        longitude : this.longitude,
                    }
                ).then(() => {
                        this._onSaveAddress();
                    });
            }else {
                console.error("Location data not found")
            }
        }

    _onSaveAddress() {
        window.location.reload();
    }
}

partner_select_current_point.template = "partner_select_current_point";

registry.category("actions").add("partner_select_current_point", partner_select_current_point);
export default partner_select_current_point;