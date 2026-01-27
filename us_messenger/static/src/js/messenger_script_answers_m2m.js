import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import {
    Many2ManyTagsField,
    many2ManyTagsField,
} from "@web/views/fields/many2many_tags/many2many_tags_field";

const fieldRegistry = registry.category("fields");

export class MessengerScriptTriggeringAnswersMany2Many extends Many2ManyTagsField {
    /**
     * Force the chatbot script ID we are currently editing into the context.
     * This allows to filter triggering question answers on steps of this script.
     */
    setup() {
        super.setup();

        if (this.props.record.model.root.resId) {
            user.updateContext({
                force_domain_messenger_script_id: this.props.record.model.root.resId,
            });
        }
    }
}

export const messengerScriptTriggeringAnswersMany2Many = {
    ...many2ManyTagsField,
    component: MessengerScriptTriggeringAnswersMany2Many,
};

fieldRegistry.add("messenger_triggering_answers_widget", messengerScriptTriggeringAnswersMany2Many);
