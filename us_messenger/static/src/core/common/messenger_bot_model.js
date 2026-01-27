import { Record } from "@mail/core/common/record";

export class MessengerProject extends Record {
    static _name = "us.messenger.project";
    static id = "id";

    /** @type {boolean} */
    are_you_inside;
    /** @type {number} */
    id;
    /** @type {string} */
    name;
}
MessengerProject.register();
