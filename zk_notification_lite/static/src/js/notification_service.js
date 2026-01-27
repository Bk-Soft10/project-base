/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onMounted } from "@odoo/owl";

const serviceRegistry = registry.category("services");

export const webNotificationService = {
    dependencies: [],

    start(env) {
        let notifications = {
            popup: [],
            breaking_news: []
        };
        let listeners = [];
        let intervalId = null;

        const fetchNotifications = async () => {
            try {
                const result = await rpc("/web/notifications/get", {});
                notifications = result || { popup: [], breaking_news: [] };
                // Notify all listeners
                listeners.forEach(callback => callback(notifications));
            } catch (error) {
                console.error("Error fetching notifications:", error);
            }
        };

        const fetchHistory = async () => {
            try {
                const result = await rpc("/web/notifications/history", {});
                return result || [];
            } catch (error) {
                console.error("Error fetching notification history:", error);
                return [];
            }
        };

        const startPolling = () => {
            // Fetch immediately
            fetchNotifications();
            // Then poll every 30 seconds
            if (!intervalId) {
                intervalId = setInterval(fetchNotifications, 30000);
            }
        };

        const stopPolling = () => {
            if (intervalId) {
                clearInterval(intervalId);
                intervalId = null;
            }
        };

        const subscribe = (callback) => {
            listeners.push(callback);
            // Return unsubscribe function
            return () => {
                listeners = listeners.filter(cb => cb !== callback);
            };
        };

        const getNotifications = () => notifications;

        const dismissNotification = async (notificationId) => {
            try {
                await rpc("/web/notifications/dismiss", { notification_id: notificationId });
                // Remove from local list
                notifications.popup = notifications.popup.filter(n => n.id !== notificationId);
                notifications.breaking_news = notifications.breaking_news.filter(n => n.id !== notificationId);
                listeners.forEach(callback => callback(notifications));
            } catch (error) {
                console.error("Error dismissing notification:", error);
            }
        };

        const markAsRead = async (notificationId) => {
            try {
                await rpc("/web/notifications/mark_read", { notification_id: notificationId });
                // Remove from local list - it won't show again even after refresh
                notifications.popup = notifications.popup.filter(n => n.id !== notificationId);
                notifications.breaking_news = notifications.breaking_news.filter(n => n.id !== notificationId);
                listeners.forEach(callback => callback(notifications));
            } catch (error) {
                console.error("Error marking notification as read:", error);
            }
        };

        // Start polling when service starts
        startPolling();

        return {
            fetchNotifications,
            fetchHistory,
            getNotifications,
            subscribe,
            dismissNotification,
            markAsRead,
            startPolling,
            stopPolling,
        };
    },
};

serviceRegistry.add("webNotification", webNotificationService);
