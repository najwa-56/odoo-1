/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { renderToString } from "@web/core/utils/render";
import { renderToElement } from "@web/core/utils/render";
import { useService } from "@web/core/utils/hooks";
import { debounce } from "@web/core/utils/timing";
import { Component, onWillUnmount, onWillUpdateProps, useEffect, useRef, useState } from "@odoo/owl";

export class MapRenderer extends Component {
    setup() {
        this.orm = useService("orm");
        this.markers = [];
        this.mapContainerRef = useRef("mapContainer");
        this.state = useState({
            googlemap: null,
            closedGroupIds: [],
            expendedPartnerList: false,
        });
        this.nextId = 1;
        this.infowindow = null;

        useEffect(
            () => {
                if (typeof google === 'object' && typeof google.maps === 'object') {
                    this.state.googlemap = new google.maps.Map(this.mapContainerRef.el, {
                        center: { lat: -33.8688, lng: 151.2195 },
                        mapTypeId: google.maps.MapTypeId.ROADMAP,                
                        fullscreenControl: true,
                        mapTypeControl: true,
                        gestureHandling: 'cooperative',
                        mapTypeControlOptions: {
                            mapTypeIds: ['satellite', 'hybrid', 'terrain'],
                            style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
                        },
                        zoom: 12,
                        minZoom: 3,
                        maxZoom: 20,
                        mapId: "o_google_map",
                    });

                    if(this.state.googlemap){
                        this.addMarkers();
                        this.loadSearchControls();
                        this.mapFitbounds();
                    }
                }
            },
            () => []
        );
        useEffect(() => {

        });

        onWillUpdateProps(this.onWillUpdateProps);
        onWillUnmount(this.onWillUnmount);
    }
    mapFitbounds(){
        if (this.props.model.data.coordinateFetchRequired) {
            const initialCoords = this.getLatLng();
            if (initialCoords) {
                var bounds = new google.maps.LatLngBounds();
                for (var i = 0, initialCoord; initialCoord = initialCoords[i]; i++) {
                    bounds.extend(initialCoord);
                }
                this.state.googlemap.fitBounds(bounds);
            } else {
                const worldCenter = { lat: 0, lng: 0 };
                this.state.googlemap.setCenter(worldCenter);
                this.state.googlemap.setZoom(1);
            }
        }
    }
    async onWillUpdateProps(nextProps) {
        if (this.props.model.data.groupByKey !== nextProps.model.data.groupByKey) {
            this.state.closedGroupIds = [];
        }
    }

    onWillUnmount() {
        this.removeMarkers();
    }

    addMarkers() {
        var self = this;
        this.removeMarkers();

        const markersData = {};
        let records = this.props.model.data.records;
        if (this.props.model.data.isGrouped) {
            records = Object.entries(this.props.model.data.recordGroups)
                .filter(([key]) => !this.state.closedGroupIds.includes(key))
                .flatMap(([groupId, value]) => value.records.map((elem) => ({ ...elem, groupId })));
        }

        for (const record of records) {
            const partner = record.partner;
            if (partner && partner.partner_latitude && partner.partner_longitude) {
                const key = partner.id;
                if (key && !(key in markersData)) {
                    markersData[key] = {
                        record: record,
                        ids: [record.id],
                    };
                }
            }
        }

        for (const markerData of Object.values(markersData)) {
            if (this.props.model.data.isGrouped) {
                const groupId = markerData.record.groupId;
            }
            var latLng = new google.maps.LatLng(markerData.record.partner.partner_latitude, markerData.record.partner.partner_longitude);
            var marker = new google.maps.Marker({
                map: self.state.googlemap,
                position: latLng,
                draggable: true,
            });
            marker.markerData = markerData;
            
            google.maps.event.addListener(marker, 'dragstart', function(event) {
                if (self.infowindow ) {
                    self.infowindow .close();
                }
            });

            google.maps.event.addListener(marker, 'dragend', function(event) {
                if (self.infowindow ) {
                    self.infowindow .close();
                }
                debounce(self.setLocation(event, this), 300);
            });

            google.maps.event.addListener(marker, 'click', function(event) {
                if (self.infowindow ) {
                    self.infowindow .close();
                }
                debounce(self.popupInfowindow(event, this), 300);
            });
            this.markers.push(marker);
        }
    }
    async popupInfowindow(event, data){
        var self = this;
        var lat = data.getPosition().lat();
        var lng = data.getPosition().lng();
        if (!lat || !lng){
            return;
        }

        if (self.infowindow ) {
            self.infowindow .close();
        }
        self.infowindow = new google.maps.InfoWindow({
            maxWidth: 350,
            pixelOffset: new google.maps.Size(-10,-25)
        });
        const infoFields = self.getInfowindowFields(data.markerData);
        const partner = data.markerData.record.partner;
        const encodedAddress = encodeURIComponent(partner.complete_contact_address);
        const content = renderToString("web_googlemap.markerPopup", {
            fields: infoFields,
            hasFormView: self.props.model.metaData.hasFormView,
            url: `https://www.google.com/maps/dir/?api=1&destination=${encodedAddress}`,
        });

        self.infowindow.setContent(content);
        self.infowindow.open(self.state.googlemap);
        self.infowindow.setPosition(new google.maps.LatLng(lat,lng));

        google.maps.event.addListener(self.infowindow, 'domready', function() {
            document.querySelector("button.o-googlemap-renderer--popup-buttons-open").addEventListener("click", () => {
                self.props.onMarkerClick(data.markerData.ids);
            });                   
        });
    }

    async setLocation(event, data) {
        var self = this;
        var lat = event.latLng.lat();
        var lng = event.latLng.lng();

        const marker = this.markers.find(marker => marker.markerData && marker.markerData.record.partner.id === data.markerData.record.partner.id);
        new google.maps.event.trigger( marker, 'click' );
        
        if (data.markerData.record.partner && data.markerData.record.partner.id && lat != undefined && lng != undefined){
            await this.orm.call("res.partner", "write_latitude_longitude", [data.markerData.record.partner.id], {
                context: {
                    'partner_latitude': lat,
                    'partner_longitude': lng,
                },
            });
        }
    }

    async centerAndOpenPartner(event, record) {
        var self = this;
        this.state.expendedPartnerList = false;
        await new Promise(resolve => setTimeout(resolve, 0));
        const marker = await this.markers.find(marker => marker.markerData && marker.markerData.record.partner.id === record.partner.id);
        new google.maps.event.trigger( marker, 'click' );
        const latlng = new google.maps.LatLng(record.partner.partner_latitude, record.partner.partner_longitude);
        self.state.googlemap.panTo(latlng);
    }
    
    createInfowindow(markerData){
        var self = this;
        return function (e) {
            if (self.infowindow ) {
                self.infowindow .close();
            }
            self.infowindow = new google.maps.InfoWindow({
                maxWidth: 350,
                pixelOffset: new google.maps.Size(-10,-25)
            });
            const infoFields = self.getInfowindowFields(markerData);
            const partner = markerData.record.partner;
            const encodedAddress = encodeURIComponent(partner.complete_contact_address);
            const content = renderToString("web_googlemap.markerPopup", {
                fields: infoFields,
                hasFormView: self.props.model.metaData.hasFormView,
                url: `https://www.google.com/maps/dir/?api=1&destination=${encodedAddress}`,
            });

            self.infowindow.setContent(content);
            self.infowindow.open(self.state.googlemap);
            self.infowindow.setPosition(new google.maps.LatLng(markerData.record.partner.partner_latitude, markerData.record.partner.partner_longitude));

            google.maps.event.addListener(self.infowindow, 'domready', function() {
                document.querySelector("button.o-googlemap-renderer--popup-buttons-open").addEventListener("click", () => {
                    self.props.onMarkerClick(markerData.ids);
                });                   
            });
        }
    }

    getLatLng() {
        const LatLng = [];
        for (const record of this.props.model.data.records) {
            const partner = record.partner;
            if (partner && partner.partner_latitude && partner.partner_longitude) {
                LatLng.push(new google.maps.LatLng(partner.partner_latitude, partner.partner_longitude));
            }
        }
        if (!LatLng.length) {
            return false;
        }
        return LatLng;
    }
    
    getInfowindowFields(markerData) {
        const infoFields = [];
        const record = markerData.record;
        const metaData = this.props.model.metaData;

        if (markerData.ids.length > 1) {
            if (!metaData.hideAddress) {
                infoFields.push({
                    id: this.nextId++,
                    value: record.partner.complete_contact_address,
                    string: _t("Address"),
                });
            }
            return infoFields;
        }
        if (!metaData.hideName) {
            infoFields.push({
                id: this.nextId++,
                value: record.display_name,
                string: _t("Name"),
            });
        }
        if (!metaData.hideAddress) {
            infoFields.push({
                id: this.nextId++,
                value: record.partner.complete_contact_address,
                string: _t("Address"),
            });
        }
        const fields = metaData.fields;
        for (const field of metaData.fieldNamesInfowindow) {
            if (record[field.fieldName]) {
                let value = record[field.fieldName];
                if (fields[field.fieldName].type === "many2one") {
                    value = record[field.fieldName].display_name;
                } 
                else if (["one2many", "many2many"].includes(fields[field.fieldName].type)) {
                    value = record[field.fieldName]
                        ? record[field.fieldName].map((r) => r.display_name).join(", ")
                        : "";
                }
                infoFields.push({
                    id: this.nextId++,
                    value,
                    string: field.string,
                });
            }
        }
        return infoFields;
    }

    removeMarkers() {
        this.markers = [];
    }

    loadSearchControls(){
        var self = this;            
        if (this.$btnSearchInput === undefined) {
            
            this.$btnSearchInput = renderToElement("web_googlemap.MapRenderer.SearchInput", {
                widget: this
            });

            const searchBox = new google.maps.places.SearchBox(this.$btnSearchInput);
            this.state.googlemap.controls[google.maps.ControlPosition.TOP_LEFT].push(this.$btnSearchInput);
            
            this.state.googlemap.addListener("bounds_changed", () => {
                searchBox.setBounds(this.state.googlemap.getBounds());
            });

            searchBox.addListener("places_changed", () => {
                searchBox.set('map', null);
                
                const places = searchBox.getPlaces();
                if (places.length == 0) {
                    return;
                }
                var bounds = new google.maps.LatLngBounds();
                var i, place;
                for (i = 0; place = places[i]; i++) {
                    (function(place) {
                        var marker = new google.maps.Marker({
                            position: place.geometry.location
                        });
                        marker.bindTo('map', searchBox, 'map');
                        google.maps.event.addListener(marker, 'map_changed', function() {
                            if (!this.getMap()) {
                                this.unbindAll();
                            }
                        });
                        bounds.extend(place.geometry.location);
                    }(place));
                }
                this.state.googlemap.fitBounds(bounds);
                searchBox.set('map', self.googlemap);
                this.state.googlemap.setZoom(Math.min(this.state.googlemap.getZoom(),12));
            });
        }            
    }

    toggleGroup(id) {
        if (this.state.closedGroupIds.includes(id)) {
            const index = this.state.closedGroupIds.indexOf(id);
            this.state.closedGroupIds.splice(index, 1);
        } else {
            this.state.closedGroupIds.push(id);
        }
    }

    togglePartnerList() {
        this.state.expendedPartnerList = !this.state.expendedPartnerList;
    }

    get expendedPartnerList() {
        return this.env.isSmall ? this.state.expendedPartnerList : false;
    }

    get canDisplayPartnerList() {
        return !this.env.isSmall || this.expendedPartnerList;
    }
}

MapRenderer.template = "web_googlemap.MapRenderer";
MapRenderer.props = {
    model: Object,
    onMarkerClick: Function,
};
