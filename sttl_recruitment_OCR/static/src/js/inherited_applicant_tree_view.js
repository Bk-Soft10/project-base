/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { listView } from '@web/views/list/list_view';
import { useService } from "@web/core/utils/hooks";

class CustomListController extends ListController {
    setup() {
        super.setup();
        debugger;
        this.orm = useService("orm");
    }

    get buttonsTemplate() {
        return 'sttl_recruitment_OCR.upload_doc';
    }

    onUploadList() {
        const self = this;
        const OnSelectedDocument = function(e) {
            for (let i = 0; i < this.files.length; i++) {
                (function(file) {
                    const reader = new FileReader();
                    reader.onloadend = function(e) {
                        const dataurl = e.target.result;

                        console.log(self.modelName);

                        self.orm.call('hr.applicant', 'document_file_create', [dataurl, file.name, self.modelName])
                            .then(function(result) {
                                location.reload();
                                console.log('File uploaded successfully');
                            });
                    };
                    reader.readAsDataURL(file);
                })(this.files[i]);
            }
        };
        const UploadFileDocument = document.createElement('input');
        UploadFileDocument.type = 'file';
        UploadFileDocument.multiple = true;
        UploadFileDocument.click();
        UploadFileDocument.addEventListener('change', OnSelectedDocument);
    }
}
registry.category("views").add("button_in_tree", {
   ...listView,
   Controller: CustomListController,
   buttonTemplate: "sttl_recruitment_OCR.upload_doc",
});
