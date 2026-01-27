import { KanbanController } from "@web/views/kanban/kanban_controller";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { registry } from "@web/core/registry";
import { MessengerViewControllerMixin } from "../messenger_view_controller_mixin";

class DiscussChannelKanbanController extends MessengerViewControllerMixin(KanbanController) {}

const discussChannelKanbanView = {
    ...kanbanView,
    Controller: DiscussChannelKanbanController,
};

registry.category("views").add("us_messenger.discuss_channel_kanban", discussChannelKanbanView);