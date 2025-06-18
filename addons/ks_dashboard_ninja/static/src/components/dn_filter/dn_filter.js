/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { PreDefinedFilter } from "@ks_dashboard_ninja/components/predefined_filter/predefined_filter";
import { FavFilterWizard } from "@ks_dashboard_ninja/components/favourite_filter/favourite_filter";
import { FavouriteFilter } from "@ks_dashboard_ninja/components/favourite_filter/favourite_filter";
import { Domain } from "@web/core/domain";
import { CustomFilter } from '@ks_dashboard_ninja/components/custom_filter/custom_filter';
import { ModelDrivenFilterApplicator } from '@ks_dashboard_ninja/components/model_driven_filter_applicator/model_driven_filter_applicator';
import { setObjectInSession, getObjectFromSession, eraseSessionItem } from "@ks_dashboard_ninja/js/cookies";


/*
* TODO : Applying filters , updating facets , removing facets,
    and applying domain have some functionalities common , can be reviewed
    there is a possibility to make common methods and reduce some lines of code
*/

export class DNFilter extends Component{
    static props = {
        dashboard_data: { type: Object, optional: true },
    };
    static defaultProps = {

    };
    static template = "ks_dashboard_ninja.dn_filter"
    static components = { PreDefinedFilter, Dropdown, CustomFilter, FavouriteFilter, ModelDrivenFilterApplicator }

    setup(){
        this.dashboard_domain_data = {}
        this.isShowPredefinedFilter = Object.keys(this.props.dashboard_data.ks_dashboard_pre_domain_filter).length
        this.isShowCustomFilter = Object.keys(this.props.dashboard_data.ks_dashboard_custom_domain_filter).length

        this.state = useState({
            dashboard_favourite_filter: this.props.dashboard_data.ks_dashboard_favourite_filter,
            removeAllFilters: false,
            filters_count: 0,
        })
        onWillStart( this.willStart );
    }

    willStart(){
        this.setObjFromCookies();
        this.state.filters_count = this.filters_count
    }

    get options(){
        return {
            ks_dashboard_id : this.props.dashboard_data.ks_dashboard_id,
        }
    }

    get filters_count(){
        let count = 0;
        Object.values(this.dashboard_domain_data).forEach( (model_domain_data) => {
            Object.keys(model_domain_data.sub_domains).forEach( (group_key_name) => {
                group_key_name.startsWith('FF') ? count : ++count;
            })
        })
        return count;
    }

    setObjFromCookies(){
        let dashboard_domain_data_from_cky = getObjectFromSession('Filter' + this.props.dashboard_data.ks_dashboard_id)
        this.dashboard_domain_data = dashboard_domain_data_from_cky ?? {}
    }

    update_sub_domains(modelDomainsToUpdate){
        this.state.removeAllFilters = false
        Object.keys(modelDomainsToUpdate).forEach( (model) => {
            this.dashboard_domain_data[model] ??= { sub_domains: {}}
            Object.keys(modelDomainsToUpdate[model]).forEach( (group) => {
                this.dashboard_domain_data[model].sub_domains[group] ??= {}
                this.dashboard_domain_data[model].sub_domains[group] = modelDomainsToUpdate[model][group].domain
            })
        })
        this.update(Object.keys(modelDomainsToUpdate))
    }

    applyFavouriteFilter(modelDomainsToUpdate){
        eraseSessionItem('Filter' + this.props.dashboard_data.ks_dashboard_id)
        delete this.dashboard_domain_data
        this.state.removeAllFilters = true
        this.dashboard_domain_data = modelDomainsToUpdate
        this.state.filters_count = this.filters_count
        setObjectInSession('Filter' + this.props.dashboard_data.ks_dashboard_id, this.dashboard_domain_data, 1)
        this.env.replace_dashboard_filters(modelDomainsToUpdate)
    }

    remove_sub_domains(models, groups){
        models.forEach( (model) => {
            groups.forEach( ( group) => {
                delete this.dashboard_domain_data[model].sub_domains[group]
            })
        })
        this.update(models)
    }


    update(models){
        eraseSessionItem('Filter' + this.props.dashboard_data.ks_dashboard_id)
        let domainsToUpdate = {};
        for( let model of models){
            let domain = Domain.and([ ...Object.values(this.dashboard_domain_data[model].sub_domains) ]).toList();
            this.dashboard_domain_data[model].domain = domain
            domainsToUpdate[model] = { domain, sub_domains: this.dashboard_domain_data[model].sub_domains }
        }
        setObjectInSession('Filter' + this.props.dashboard_data.ks_dashboard_id, this.dashboard_domain_data, 1)
        this.state.filters_count = this.filters_count
        this.env.update_dashboard_filters(domainsToUpdate)
    }

    onSaveAsFavouriteClick(){
        this.env.services.dialog.add(FavFilterWizard,{
            save_favourite_filter: this.save_favourite_filter.bind(this),
            dashboard_favourite_filter: this.state.dashboard_favourite_filter,
            dashboard_data: this.props.dashboard_data,
            dashboard_domain_data: this.dashboard_domain_data
        });
    }

    save_favourite_filter(ks_filter_name, ks_filter_obj){
        this.state.dashboard_favourite_filter[ks_filter_name] = ks_filter_obj
    }

    delete_favourite_filter(ks_filter_name){
        delete this.state.dashboard_favourite_filter[ks_filter_name]
    }

    hideFilterTab() {
        Collapse.getInstance('#collapseExample').hide()
    }

}


