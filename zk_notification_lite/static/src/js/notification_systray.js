/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

export class NotificationSystray extends Component {
    static template = "zk_notification_lite.NotificationSystray";
    static components = { Dropdown, DropdownItem };
    static props = {};

    setup() {
        this.webNotificationService = useService("webNotification");
        this.state = useState({
            notifications: [],
            hasNew: false,
            isAnimating: false,
            activeTab: 'new',
            historyNotifications: [],
        });

        onWillStart(async () => {
            const notifications = this.webNotificationService.getNotifications();
            this.updateNotifications(notifications);
        });

        onMounted(() => {
            this.unsubscribe = this.webNotificationService.subscribe((notifications) => {
                this.updateNotifications(notifications);
            });
        });

        onWillUnmount(() => {
            if (this.unsubscribe) {
                this.unsubscribe();
            }
        });
    }

    updateNotifications(notifications) {
        const allNotifs = [
            ...(notifications.popup || []),
            ...(notifications.breaking_news || [])
        ];

        // Check if there are new notifications
        if (allNotifs.length > this.state.notifications.length) {
            this.state.hasNew = true;
            this.state.isAnimating = true;
            // Stop animation after 3 seconds
            setTimeout(() => {
                this.state.isAnimating = false;
            }, 3000);
        }

        this.state.notifications = allNotifs;
    }

    get notificationCount() {
        return this.state.notifications.length;
    }

    get hasNotifications() {
        return this.state.notifications.length > 0;
    }

    onDropdownOpen() {
        this.state.hasNew = false;
        this.state.activeTab = 'new';
    }

    async setTab(tab) {
        this.state.activeTab = tab;
        if (tab === 'history') {
            const history = await this.webNotificationService.fetchHistory();
            this.state.historyNotifications = history;
        }
    }

    dismissNotification(notificationId) {
        this.webNotificationService.dismissNotification(notificationId);
    }

    markAsRead(notificationId) {
        this.webNotificationService.markAsRead(notificationId);
    }
}

// Register in systray category with unique name
registry.category("systray").add("zk_notification_lite.NotificationSystray", {
    Component: NotificationSystray,
}, { sequence: 100 });
