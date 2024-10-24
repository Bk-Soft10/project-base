/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";
import { onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
const { Component } = owl;
import { useState, useExternalListener } from "@odoo/owl";

export class UserNotificationMenu extends Component {
  setup() {
    this.busService = this.env.services.bus_service;
    this.notifications = this._getActivityData();
    this.action = useService("action");
    onWillStart(this.onWillStart);
    this._updateCounter();
    useExternalListener(window, "click", this.onWindowClick, true);
    this.state = useState({ custom_display: "none" });
    console.log("notifications : ", this.notifications);
  }
  onWindowClick(ev) {
    if (!ev.target.closest(".sh_bell_notification_contant")) {
      this.state.custom_display = "none";
    }
  }
  async onWillStart() {
    this.busService.subscribe("sh_notif", (sale_records) => {
      this._getActivityData();
    });

    this.busService.addEventListener(
      "notification",
      ({ detail: notifications }) => {
        for (let i = 0; i < notifications.length; i++) {
          const channel = notifications[i]["type"];
          if (channel == "sh.user.push.notifications") {
            this._getActivityData();
            this._updateCounter();

            // Triggering a click on the search input using vanilla JS
            const searchInput = document.querySelector(".o_searchview_input");
            if (searchInput) {
              searchInput.click();
            }
            // Simulating a click on the document using vanilla JS
            document.dispatchEvent(new Event("click"));
          }
        }
      }
    );

    rpc(
      "/web/dataset/call_kw/sh.user.push.notification/has_bell_notification_enabled",
      {
        model: "sh.user.push.notification",
        method: "has_bell_notification_enabled",
        args: [],
        kwargs: {},
      }
    ).then(function (result) {
      const bellNotification = document.querySelector(".js_bell_notification");
      if (result.has_bell_notification_enabled) {
        bellNotification.classList.remove("d-none");
      } else {
        bellNotification.classList.add("d-none");
      }
    });
  }

  async _onPushNotificationClick(notification) {
    // fetch the data from the button otherwise fetch the ones from the parent (.o_mail_preview).
    var data = notification;
    var context = {};
    var self = this;

    await rpc("/web/dataset/call_kw/sh.user.push.notification/write", {
      model: "sh.user.push.notification",
      method: "write",
      args: [data.id, { msg_read: true }],
      kwargs: {},
    }).then(function () {
      self._getActivityData();
      self._updateCounter();
      if (data.res_model != "") {
        self.action.doAction(
          {
            type: "ir.actions.act_window",
            name: data.res_model,
            res_model: data.res_model,
            views: [
              [false, "form"],
              [false, "list"],
            ],
            search_view_id: [false],
            domain: [["id", "=", data.res_id]],
            res_id: data.res_id,
            context: context,
          },
          {
            clear_breadcrumbs: true,
          }
        );
      }
    });
  }

  _onClickReadAllNotification(ev) {
    var self = this;

    rpc(
      "/web/dataset/call_kw/res.users/systray_get_firebase_all_notifications",
      {
        model: "res.users",
        method: "systray_get_firebase_all_notifications",
        args: [],
        kwargs: { context: user },
      }
    ).then(function (data, counter) {
      self._notifications = data[0];
      data[0].forEach((each_data) => {
        rpc("/web/dataset/call_kw/sh.user.push.notification/write", {
          model: "sh.user.push.notification",
          method: "write",
          args: [each_data.id, { msg_read: true }],
          kwargs: {},
        }).then(function () {
          self._getActivityData();
          self._updateCounter();
        });
      });
    });
    this._onActivityMenuShow();
  }
  _onClickAllNotification(ev) {
    this.action.doAction(
      {
        type: "ir.actions.act_window",
        name: "Notifications",
        res_model: "sh.user.push.notification",
        views: [[false, "list"]],
        view_mode: "list",
        domain: [["user_id", "=", user.userId]],
      },
      {
        clear_breadcrumbs: true,
      }
    );
  }

  _updateCounter() {
    const notificationCounter = document.querySelector(
      ".o_notification_counter"
    );
    if (notificationCounter) {
      const counter = this._counter;
      notificationCounter.textContent = counter > 0 ? counter : "";
    } else {
      console.warn("Notification counter element not found.");
    }
  }

  _getActivityData() {
    var self = this;

    return rpc(
      "/web/dataset/call_kw/res.users/systray_get_firebase_notifications",
      {
        model: "res.users",
        method: "systray_get_firebase_notifications",
        args: [],
        kwargs: { context: user },
      }
    ).then(function (data, counter) {
      console.log("\n\n\n\n\n\n\n\n\n Data : ", data);

      self._notifications = data[0];
      self._counter = data[1];

      data[0].forEach((each_data) => {
        each_data["datetime"] = self.formatRelativeTime(each_data["datetime"]);
      });
      self._updateCounter();
      return data;
    });
  }

  _updateActivityPreview() {
    this.notifications = this._notifications;
    const dropdownItems = document.querySelector(
      ".o_notification_systray_dropdown_items"
    );
    if (dropdownItems) {
      dropdownItems.classList.remove("d-none");
    }
  }

  async _onActivityMenuShow() {
    if (this.state.custom_display == "none") {
      this.state.custom_display = "block";
    } else {
      this.state.custom_display = "none";
    }

    this.render(true);
    await this._updateActivityPreview();
  }

  _onActivityActionClick(ev) {
    ev.stopPropagation();
    const actionXmlid = ev.currentTarget.getAttribute("data-action_xmlid");
    this.do_action(actionXmlid);
  }

  /**
   * Get particular model view to redirect on click of activity scheduled on that model.
   * @private
   * @param {string} model
   */
  _getActivityModelViewID(model) {
    return rpc.query({
      model: model,
      method: "get_activity_view_id",
    });
  }

  formatRelativeTime(dateTime) {
    const now = new Date();
    console.log(dateTime);

    dateTime = new Date(dateTime);

    let offset = now.getTimezoneOffset();
    const offsetHours = Math.floor(Math.abs(offset / 60));
    const offsetMinutes = Math.floor(Math.abs(offset % 60));
    const sign = offset > 0 ? "-" : "+";

    if (sign == "+") {
      dateTime.setHours(dateTime.getHours() + offsetHours);
      dateTime.setMinutes(dateTime.getMinutes() + offsetMinutes);
    } else {
      dateTime.setHours(dateTime.getHours() - offsetHours);
      dateTime.setMinutes(dateTime.getMinutes() - offsetMinutes);
    }

    const diffInSeconds = Math.floor((now - dateTime) / 1000);

    if (diffInSeconds < 60) {
      return _t("less than a minute ago");
    } else if (diffInSeconds < 120) {
      return _t("about a minute ago");
    } else if (diffInSeconds < 3600) {
      return _t(`${Math.floor(diffInSeconds / 60)} minutes ago`);
    } else if (diffInSeconds < 7200) {
      return _t("about an hour ago");
    } else if (diffInSeconds < 86400) {
      return _t(`${Math.floor(diffInSeconds / 3600)} hours ago`);
    } else if (diffInSeconds < 172800) {
      return _t("a day ago");
    } else if (diffInSeconds < 2592000) {
      return _t(`${Math.floor(diffInSeconds / 86400)} days ago`);
    } else if (diffInSeconds < 5184000) {
      return _t("about a month ago");
    } else if (diffInSeconds < 31536000) {
      return _t(`${Math.floor(diffInSeconds / 2592000)} months ago`);
    } else if (diffInSeconds < 63072000) {
      return _t("about a year ago");
    } else {
      return _t(`${Math.floor(diffInSeconds / 31536000)} years ago`);
    }
  }
}
UserNotificationMenu.template = "mail.systray.UserNotificationMenu";

export const systrayItem = {
  Component: UserNotificationMenu,
};

registry.category("systray").add("UserNotificationMenu", systrayItem);
