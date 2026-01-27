/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

export class PopupNotification extends Component {
    static template = "zk_notification_lite.PopupNotification";
    static props = {};

    setup() {
        this.webNotificationService = useService("webNotification");
        this.state = useState({
            notifications: [],
            dismissedIds: new Set(),
        });

        onWillStart(async () => {
            const notifications = this.webNotificationService.getNotifications();
            this.state.notifications = notifications.popup || [];
        });

        onMounted(() => {
            this.unsubscribe = this.webNotificationService.subscribe((notifications) => {
                // Filter out dismissed notifications
                this.state.notifications = (notifications.popup || []).filter(
                    n => !this.state.dismissedIds.has(n.id)
                );
            });
        });

        onWillUnmount(() => {
            if (this.unsubscribe) {
                this.unsubscribe();
            }
        });
    }

    dismissNotification(notificationId) {
        this.state.dismissedIds.add(notificationId);
        this.state.notifications = this.state.notifications.filter(n => n.id !== notificationId);
    }

    markAsRead(notificationId) {
        // Mark as read in database - won't show again even after refresh
        this.webNotificationService.markAsRead(notificationId);
        this.state.notifications = this.state.notifications.filter(n => n.id !== notificationId);
    }
}

// Register the component in the systray
registry.category("main_components").add("PopupNotification", {
    Component: PopupNotification,
});
