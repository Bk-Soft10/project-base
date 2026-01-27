/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

export class BreakingNews extends Component {
    static template = "zk_notification_lite.BreakingNews";
    static props = {};

    setup() {
        this.webNotificationService = useService("webNotification");
        this.state = useState({
            notifications: [],
            currentIndex: 0,
            dismissedIds: new Set(),
        });

        onWillStart(async () => {
            const notifications = this.webNotificationService.getNotifications();
            this.state.notifications = notifications.breaking_news || [];
        });

        onMounted(() => {
            this.unsubscribe = this.webNotificationService.subscribe((notifications) => {
                // Filter out dismissed notifications
                this.state.notifications = (notifications.breaking_news || []).filter(
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

    get currentNotification() {
        if (this.state.notifications.length === 0) {
            return null;
        }
        return this.state.notifications[this.state.currentIndex % this.state.notifications.length];
    }

    get bannerStyle() {
        const notif = this.currentNotification;
        if (!notif) return "";

        return `
            background-color: ${notif.background_color || '#FFFFFF'};
            color: ${notif.font_color || '#000080'};
            font-size: ${notif.font_size || 30}px;
        `;
    }

    get textClass() {
        const notif = this.currentNotification;
        if (!notif || !notif.is_moving_text) {
            return "";
        }
        return notif.moving_text_direction === 'ltr' ? 'marquee-ltr' : 'marquee-rtl';
    }

    closeBanner() {
        const notif = this.currentNotification;
        if (notif) {
            this.state.dismissedIds.add(notif.id);
            this.state.notifications = this.state.notifications.filter(n => n.id !== notif.id);
        }
    }

    markAsRead() {
        const notif = this.currentNotification;
        if (notif) {
            this.webNotificationService.markAsRead(notif.id);
            this.state.notifications = this.state.notifications.filter(n => n.id !== notif.id);
        }
    }
}

// Register the component in the main components
registry.category("main_components").add("BreakingNews", {
    Component: BreakingNews,
});
