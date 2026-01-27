/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { MessengerViewControllerMixin } from "../messenger_view_controller_mixin";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

class DiscussChannelListController extends MessengerViewControllerMixin(ListController) {}

const discussChannelListView = {
    ...listView,
    Controller: DiscussChannelListController,
};

registry.category("views").add("us_messenger.discuss_channel_list", discussChannelListView);
