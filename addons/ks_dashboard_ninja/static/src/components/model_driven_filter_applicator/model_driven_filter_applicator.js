/** @odoo-module **/

import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { Domain } from "@web/core/domain";
import { useBus } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { useGetDomainTreeDescription } from "@web/core/domain_selector/utils";
import { treeFromDomain } from "@web/core/tree_editor/condition_tree";
import { setObjectInSession, getObjectFromSession, eraseSessionItem } from "@ks_dashboard_ninja/js/cookies";


export class ModelDrivenFilterApplicator extends Component {

    /*
        * This component is based on event bus
        * Takes any model name , group [ domain with key ]
        * Applies it to dashboard and maintains its history
    */

    static template = "ks_dashboard_ninja.model_driven_filter_applicator"
    static props = {
        update: { type: Function },
        remove: { type: Function },
        removeAllFilters: { type: Boolean },
        options: { type: Object, optional: true },
    };
    static defaultProps = {
        options: {},
    };

    setup(){
        this.getDomainTreeDescription = useGetDomainTreeDescription();
        this.state = useState({
            'facets' : {}
        })
        if(!this.env.inDialog)
            useBus(this.env.bus, 'APPLY: Dashboard Filter', ({ detail }) => this.addFacet(detail.model_display_name, detail.model_name, detail.field_name,
                                                                                detail.operator, detail.value))

        onWillStart( () => this.apply_cookies_data() )
        onWillUpdateProps((nextProps) => this.onPropsUpdated(nextProps))
    }

    onPropsUpdated(nextProps){
        if(nextProps.removeAllFilters){
            eraseSessionItem('ChartFilter' + this.props.options.ks_dashboard_id)
            this.clearFacets();
        }
    }

    apply_cookies_data(){
        let facets_data = getObjectFromSession('ChartFilter' + this.props.options.ks_dashboard_id)
        this.state.facets = facets_data ?? {}
    }

    clearFacets(){
        this.state.facets = {}
    }

    async make_label(model, domain){
        let label = await this.getDomainTreeDescription(model, treeFromDomain(domain));
        return label;
    }

    async addFacet(model_display_name, model_name, field_name, operator, value){
        let group_name = `${model_name + '_' + field_name + operator + value}`
        let domain = new Domain([[field_name , operator, value]]).toList();

        let facets_to_update = this.state.facets[model_name] || { groups: {}, model_name: model_display_name }

        if(!facets_to_update.groups[group_name]){
            let label = await this.make_label(model_name, domain)

            facets_to_update.groups[group_name] = { label: label, domain: domain }
            this.state.facets[model_name] = facets_to_update
            this.apply_domain(model_name, group_name, domain);
        }
    }

    onRemoveFacet(model, group){
        /**
        * This method remove the facet or domain showing through facet from the dashboard
        */
        eraseSessionItem('ChartFilter' + this.props.options.ks_dashboard_id)
        delete this.state.facets[model].groups[group];

        if(!Object.values(this.state.facets[model].groups).length)  delete this.state.facets[model];
        setObjectInSession('ChartFilter' + this.props.options.ks_dashboard_id, this.state.facets, 1)
        this.props.remove([model], [group]);
    }

    apply_domain(model_name, group_name, domain){
        /**
        * This method create the domain and update to the dashboards domain data
        */
        eraseSessionItem('ChartFilter' + this.props.options.ks_dashboard_id)
        let domain_data_to_update = { [model_name]: { [group_name]: { domain: domain}}}
        setObjectInSession('ChartFilter' + this.props.options.ks_dashboard_id, this.state.facets, 1)

        this.props.update(domain_data_to_update)
    }

}
