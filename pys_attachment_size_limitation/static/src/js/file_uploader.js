/** @odoo-module **/

import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { FileUploader } from "@web/views/fields/file_handler";
import { humanSize } from "@web/core/utils/binary";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

patch(FileUploader.prototype, {
    setup() {
        super.setup();

        // max_attachment_size comes from ir.http session_info (BYTES)
        this.max_attachment_size =
            session.max_attachment_size;

//        console.log(
//            "[Attachment Limit] Max size:",
//            humanSize(this.max_attachment_size)
//        );

         this.max_attachment_size = session.max_attachment_size;

        if (this.max_attachment_size && this.max_attachment_size > 0) {
            console.log(
                "[Attachment Limit] Max size:",
                humanSize(this.max_attachment_size)
            );
        } else {
            console.log("[Attachment Limit] Unlimited attachments");
        }


        this.dialogService = useService("dialog");
    },

    async onFileChange(ev) {
      if (!this.max_attachment_size) {
        return super.onFileChange(...arguments);
    }

    const largerFiles = [];

    for (const file of ev.target.files) {
        if (file.size > this.max_attachment_size) {
            largerFiles.push(file);
        }
    }


    if (largerFiles.length) {
        const file = largerFiles[0]; // first oversized file

        this.dialogService.add(ConfirmationDialog, {
            title: _t("Validation Error"),
            body: _t(
                "The selected file \"%s\" is %s, which exceeds the maximum allowed size of %s.",
                file.name,
                humanSize(file.size),
                humanSize(this.max_attachment_size)
            ),
        });
        return;
    }

    return super.onFileChange(...arguments);
}
});
