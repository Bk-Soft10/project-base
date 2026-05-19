import base64
import binascii
import json
import logging
import operator
from typing import Any

import requests

from odoo import api, http, models
from odoo.http import content_disposition, request
from odoo.tools import json_default, osutil

from odoo.addons.web.controllers.export import (
    Export,
    ExportFormat,
)

_logger = logging.getLogger(__name__)


class JsonExport(Export):
    @http.route("/web/export/formats", type="jsonrpc", auth="user")
    def formats(self):
        res = super().formats()
        res.append({"tag": "json", "label": "JSON"})
        return res


class JsonExportFormat(ExportFormat, http.Controller):
    @http.route("/web/export/json", type="http", auth="user")
    def index(self, data: str) -> "requests.Response":
        return self.base(data)

    @property
    def content_type(self) -> str:
        """
        :return: str, json format
        """
        return "text/json;charset=utf8"

    @property
    def extension(self) -> str:
        """
        Return extension for file, that will be generated later.
        :return: json extension
        """
        return ".json"

    @api.model
    def _detect_image_mime_type(self, value: bytes) -> str:
        if not value:
            return "application/octet-stream"

        # Cas 1 : les bytes contiennent du base64 ASCII
        try:
            as_text = value.decode("utf-8").strip()
            decoded = base64.b64decode(as_text, validate=True)
            value = decoded
        except (UnicodeDecodeError, binascii.Error, ValueError):
            pass

        # Cas 2 : détection par signature binaire
        if value.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if value.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if value.startswith(b"GIF87a") or value.startswith(b"GIF89a"):
            return "image/gif"
        if value.startswith(b"RIFF") and len(value) >= 12 and value[8:12] == b"WEBP":
            return "image/webp"
        if value.startswith(b"BM"):
            return "image/bmp"
        if value.startswith(b"II*\x00") or value.startswith(b"MM\x00*"):
            return "image/tiff"
        if value.startswith(b"\x00\x00\x01\x00"):
            return "image/x-icon"

        return "application/octet-stream"

    @api.model
    def _transform_json_value(self, value):
        if isinstance(value, bytes):
            mime_type = self._detect_image_mime_type(value)

            try:
                as_text = value.decode("utf-8").strip()
                encoded = base64.b64encode(base64.b64decode(as_text, validate=True)).decode("utf-8")
            except (UnicodeDecodeError, binascii.Error, ValueError):
                encoded = base64.b64encode(value).decode("utf-8")

            return f"data:{mime_type};base64,{encoded}"

        if isinstance(value, dict):
            return {key: self._transform_json_value(val) for key, val in value.items()}

        if isinstance(value, list):
            return [self._transform_json_value(item) for item in value]

        return value

    @api.model
    def format_data(self, fields) -> str:
        transformed_fields = self._transform_json_value(fields)
        return json.dumps(transformed_fields, indent=4, default=json_default)

    @api.model
    def _insert_simple_field(self, fields_name: list, field_groups: dict, parser: list[dict]):
        """
        This function is used to add "simple" field like "partner_id", "name", in the parser that will be export.
        Field name like "partner_id/child_ids, partner_id/child_ids/name" will be processed in another method.
        :param fields_name: list of field name to export, display like ["partner_id", "partner_id/child_ids", ...].
        :param field_groups: The dict is not return
        :param parser: list of key's name field, define in a specific way
        (exemple in function "define_parser" docstring).
        :return: None, but "field_groups" and "parser" parameters are modified by side effect.
        """
        for field in fields_name:
            name = field["name"]

            if "/" in name:
                parts = name.split("/")
                main_field = parts[0]
                subfield = "/".join(parts[1:])

                if main_field not in field_groups:
                    field_groups[main_field] = []

                field_groups[main_field].append({"name": subfield})
            else:
                parser.append(name)

    @api.model
    def _insert_nested_field(self, field_groups, parser):
        for main_field, subfields in field_groups.items():
            if any("/" in subfield["name"] for subfield in subfields):
                nested_fields = [subfield for subfield in subfields]
                nested_parser = self.define_parser(nested_fields)
                parser.append((main_field, nested_parser))
            else:
                sub_names = [subfield["name"] for subfield in subfields]
                parser.append((main_field, sub_names))

    @api.model
    def define_parser(self, fields_name: list[dict[str, str]]) -> tuple[str | dict[str, Any]]:
        """
        Args:
            :param fields_name: list of dictionaries with two or three keys: 'label', 'name' which are field names
             and optionally 'type', that is not use.
            :return: list of field names to export. Example of parser:
            parser = [
                'name',
                'number',
                'create_date',
                ('partner_id', ['id', 'display_name', 'ref'])
                ('line_id', ['id', ('product_id', ['name']), 'price_unit'])
            ]
        """
        parser = []
        field_groups = {}

        self._insert_simple_field(fields_name, field_groups, parser)
        self._insert_nested_field(field_groups, parser)

        return parser

    def base(self, data: str) -> "requests.Response":
        params = json.loads(data)
        model, fields, ids, domain, import_compat = operator.itemgetter(
            "model", "fields", "ids", "domain", "import_compat"
        )(params)
        Model = request.env[model].with_context(import_compat=import_compat, **params.get("context", {}))
        response_data = self.perform_json_export(domain, fields, ids, Model)

        return request.make_response(
            response_data,
            headers=[
                (
                    "Content-Disposition",
                    content_disposition(osutil.clean_filename(self.filename(model) + self.extension)),
                ),
                ("Content-Type", self.content_type),
            ],
        )

    @api.model
    def _convert_simple_list(self, fields_name) -> list[dict[str, str]]:
        """
        Use to convert a list of fields names that it is not a dict with 'name' key
        :param fields_name: list of field names, either str or dict.
        :return: converted list of field names in dict{'name' : 'field_name'}.
        """
        converted_fields_name = []

        for element in fields_name:
            if type(element) is not dict:
                element_to_append = {"name": element}
            else:
                element_to_append = element
            converted_fields_name.append(element_to_append)
        return converted_fields_name

    # region merge_lang_dict
    @api.model
    def process_keys(
        self,
        all_keys: set,
        dicts_at_idx: dict,
        merged_dict: dict,
        parent_key: str = False,
    ):
        """
        Traite un ensemble de clés en regroupant leurs valeurs depuis plusieurs dictionnaires par langue.

        La méthode itère sur toutes les clés fournies et collecte leurs valeurs correspondantes
        depuis différents dictionnaires organisés par langue. Pour chaque clé, on rassemble
        les valeurs disponibles dans chaque langue et les transmet à "process_key_values" pour
        un traitement ultérieur.
        """
        for key in all_keys:
            key_values = {}
            for lang, d in dicts_at_idx.items():
                if key in d:
                    key_values[lang] = d[key]
            self.process_key_values(key, key_values, merged_dict, parent_key)

    @api.model
    def process_key_values(
        self,
        current_key: str,
        key_values: dict,
        merged_item: dict,
        parent_key: str = False,
    ):
        if key_values:
            first_val = list(key_values.values())[0]
            item_added = self.add_list_or_dict_on_merge_item(
                current_key, first_val, key_values, merged_item, parent_key
            )
            if not item_added:
                self.add_lang_key(current_key, first_val, key_values, merged_item, parent_key)

    @api.model
    def add_list_or_dict_on_merge_item(
        self,
        current_key,
        current_val: list | dict,
        values_by_lang: dict,
        merged_item: dict,
        parent_key: str = False,
    ) -> bool:
        """Permets de différencier l'ajout de dict ou de list dans le dictionnaire final.
        Le paramètre merged_item est modifié par référence.
        Retourne un boolean qui permet de ne pas continuer le process d'ajouts de données,
        si la valeur courante a déjà été ajoutée.
        """

        # Si la clé courante et la clé parente sont définies, qu'elles ne sont pas identiques,
        # et que la valeur courante est un dict (ou une list) ?
        # Alors la clé parente devient la concaténation de la clé parente et courante,
        # étant donnée que nous sommes dans des dicts imbriquées
        if parent_key and current_key and parent_key != current_key and isinstance(current_val, dict):
            parent_key = f"{parent_key}/{current_key}"
        else:
            parent_key = parent_key or current_key

        # Gérer les listes de dictionnaires
        if isinstance(current_val, list):
            if current_val and isinstance(current_val[0], dict):
                merged_item[current_key] = self._merge_list_of_dicts(values_by_lang, parent_key)
                return True
        # Gérer les dictionnaires imbriqués
        elif isinstance(current_val, dict):
            merged_item[current_key] = self._merge_nested_dict(values_by_lang, parent_key)
            return True
        return False

    @api.model
    def retrieve_all_keys(self, items: dict) -> set:
        assert all(isinstance(v, dict) for v in items.values()), "All values must be dictionaries."
        all_keys = set()
        for vals in items.values():
            all_keys.update(vals.keys())
        return all_keys

    @api.model
    def add_unique_vals(self, key_values: dict) -> set:
        """Vérifier si toutes les valeurs sont identiques"""
        unique_values = set()
        for val in key_values.values():
            if isinstance(val, list | dict):
                unique_values.add(str(val))
            else:
                unique_values.add(val)
        return unique_values

    @api.model
    def get_country_code(self, lang_code):
        if "_" in lang_code:
            return lang_code.split("_")[1]
        else:
            return lang_code

    @api.model
    def add_lang_key(
        self,
        current_key: str,
        first_val: str | list,
        key_values: dict,
        merged_dict: dict,
        parent_key: str = False,
    ):
        """Permets d'ajouter au dict final, soit une valeur avec une clé unique, s'il n'existe pas
        de différence dans les dict de chaque langue, ou bien une clé par lang, s'il y a des différences.
        """
        # Vérifier si toutes les valeurs sont identiques
        unique_values = self.add_unique_vals(key_values)
        if len(unique_values) <= 1:
            # Valeurs identiques
            merged_dict[current_key] = first_val
        else:
            # On ajoute un ensemble {key : val}, avec pour key la clé courante sans ajout, et pour valeur,
            # le chemin de la key.
            if parent_key:
                merged_dict[current_key] = f"{parent_key}/{current_key}"
            else:
                merged_dict[current_key] = current_key

            # Valeurs différentes, créer des clés avec suffixes, qui serviront provisoirement à stocker les traductions
            # de la clé
            for lang, val in key_values.items():
                lang_suffix = self.get_country_code(lang)
                merged_dict[f"{current_key}_{lang_suffix}"] = val

    @api.model
    def merge_multilingual_dicts(self, multilingual_data: dict) -> list:
        """
        Fusionne les dictionnaires de différentes langues en un seul dictionnaire.
        Pour chaque clé:
        - Si toutes les valeurs sont identiques -> garde la clé originale
        - Si les valeurs diffèrent -> crée des clés suffixées par le code langue
        - Si la valeur est une liste de dicts -> fusionne récursivement
        - Si la valeur est un dict -> fusionne récursivement
        """

        languages = list(multilingual_data.keys())

        if not languages:
            return []

        base_lang = languages[0]
        base_data = multilingual_data[base_lang]

        merged_data = []

        for idx, base_item in enumerate(base_data):
            merged_item = {}

            # Récupérer tous les éléments correspondants dans les autres langues
            lang_items = {base_lang: base_item}
            for lang in languages[1:]:
                if idx < len(multilingual_data[lang]):
                    lang_items[lang] = multilingual_data[lang][idx]

            # Analyser chaque clé
            all_keys = self.retrieve_all_keys(lang_items)

            # Récupérer les valeurs pour cette clé dans toutes les langues
            self.process_keys(all_keys, lang_items, merged_item)
            merged_data.append(merged_item)

        return merged_data

    @api.model
    def _merge_nested_dict(self, values_by_lang: dict, parent_key: str = False) -> dict:
        """
        Fusionne des dictionnaires imbriqués provenant de différentes langues.
        Args:
            parent_key: str, key parent du dict imbriqué
            values_by_lang: dict {lang_code: dict}
        Returns:
            dict: dictionnaire fusionné
        """
        merged_dict = {}

        # Récupérer toutes les clés possibles
        all_keys = self.retrieve_all_keys(values_by_lang)

        # Pour chaque clé, comparer les valeurs
        for key in all_keys:
            key_values = {}
            for lang, d in values_by_lang.items():
                if isinstance(d, dict) and key in d:
                    key_values[lang] = d[key]

            if key_values:
                # Modification du paramètre merged_dict par référence
                first_val = list(key_values.values())[0]
                self.add_lang_key(key, first_val, key_values, merged_dict, parent_key)

        return merged_dict

    @api.model
    def _merge_list_of_dicts(self, values_by_lang: dict, parent_key: str = False) -> list[dict]:
        """
        Fusionne des listes de dictionnaires provenant de différentes langues.

        Args:
            values_by_lang: dict {lang_code: [dict1, dict2, ...]}
            parent_key : str

        Returns:
            list: liste fusionnée de dictionnaires
        """
        languages = list(values_by_lang.keys())

        if not languages:
            return []

        # Utiliser la première langue comme référence pour la longueur
        base_lang = languages[0]
        base_list = values_by_lang[base_lang]

        merged_list = []

        # Pour chaque index dans la liste
        for idx in range(len(base_list)):
            merged_dict = {}

            # Récupérer tous les dictionnaires à cet index
            dicts_at_idx = {}
            for lang in languages:
                if idx < len(values_by_lang[lang]):
                    dicts_at_idx[lang] = values_by_lang[lang][idx]

            # Récupérer toutes les clés possibles
            all_keys = self.retrieve_all_keys(dicts_at_idx)
            self.process_keys(all_keys, dicts_at_idx, merged_dict, parent_key)
            merged_list.append(merged_dict)

        return merged_list

    # endregion merge_lang_dict

    def perform_json_export(
        self,
        domain: list[list[Any]],
        field_names: list[str],
        ids: list[int],
        model: models.BaseModel,
        langs_code: list[str] = False,
    ) -> str:
        """
        Method to prepare and format json data for the export.

        Args:
            :param domain: condition (domain) needed for the search method
            :param field_names: list of dictionaries with two keys : 'label' and 'name' which are field names
            :param ids: list with ids of selected records
            :param model: model on which the export is done
            :param langs_code: languages code
            :return: string with json_data
        """
        if not model._is_an_ordinary_table():
            field_names = [field for field in field_names if field != "id"]
        field_names = self._convert_simple_list(field_names)
        field_paths = [field.get("name") for field in field_names if isinstance(field, dict) and field.get("name")]

        records = model.browse(ids) if ids else model.search(domain, offset=0, limit=False, order=False)
        parser = self.define_parser(field_names)

        if not langs_code:
            langs_code = [request.env.context.get("lang")] or [request.env.user.lang]
        tz = request.env.context.get("tz") or request.env.user.tz
        if len(langs_code) == 1:
            result = records.with_context(lang=langs_code[0], tz=tz).jsonify(parser)
            self._add_selection_tech_fields_to_json(result, records, field_paths)
            return self.format_data(result)

        result = {}
        for lang in langs_code:
            result[lang] = records.with_context(lang=lang, tz=tz).jsonify(parser)
        merged_list = self.merge_multilingual_dicts(result)
        self._add_selection_tech_fields_to_json(merged_list, records, field_paths)
        response_data = self.format_data(merged_list)
        return response_data

    def _add_selection_tech_fields_to_json(self, data_list, records, field_paths):
        """Inject tech_<field> keys with selection raw values (single-lang export only)."""
        if not isinstance(data_list, list) or not records or not field_paths:
            return
        for data_node, record in zip(data_list, records, strict=False):
            if not isinstance(data_node, dict):
                continue
            for field_path in field_paths:
                self._inject_selection_tech_for_path(data_node, record, field_path)

    def _inject_selection_tech_for_path(self, data_node: dict, record_node: models.BaseModel, field_path: str):
        """Walk a field path and inject selection tech keys at the right level."""
        if not field_path or not record_node or not isinstance(data_node, dict):
            return
        parts = field_path.split("/")
        self._inject_selection_tech_in_nodes(data_node, record_node, parts)

    def _inject_selection_tech_in_nodes(self, data_node: dict, record_node: models.BaseModel, parts: list[str]):
        """Dispatch selection tech injection based on field type and path."""
        if not parts or not record_node or not isinstance(data_node, dict):
            return
        field_name = parts[0]
        if field_name not in record_node._fields:
            return

        field = record_node._fields[field_name]
        value = record_node[field_name]

        if len(parts) == 1:
            self._inject_selection_tech_leaf(data_node, field_name, field, value, record_node)
            return

        self._inject_selection_tech_relation(data_node, field_name, field, value, parts)

    def _inject_selection_tech_leaf(
        self, data_node: dict, field_name: str, field, value, record_node: models.BaseModel
    ):
        """Inject tech key for a leaf selection field."""
        tech_field_name = f"tech_{field_name}"
        if field.type != "selection" or not isinstance(data_node, dict) or tech_field_name in record_node._fields:
            return
        elif tech_field_name in record_node._fields:
            _logger.info(
                f"Unable to add the technical field 'tech_{{field_name}}' for field {field.name}; "
                "this name already exists for a field in the current model."
            )
            return
        data_node[tech_field_name] = None if value in (False, None) else value

    def _inject_selection_tech_relation(self, data_node, field_name: str, field, value, parts: list[str]):
        """Traverse relations and inject tech keys into nested structures."""
        if field.type in ("many2one", "reference"):
            self._inject_selection_tech_many2one(data_node, field_name, value, parts)
            return
        if field.type in ("one2many", "many2many"):
            self._inject_selection_tech_x2many(data_node, field_name, value, parts)
            return

    def _inject_selection_tech_many2one(self, data_node: dict, field_name: str, value, parts: list[str]):
        """Inject tech keys inside a many2one/reference subtree."""
        if not value or not isinstance(data_node, dict):
            return
        sub_data = data_node.get(field_name)
        if isinstance(sub_data, dict):
            self._inject_selection_tech_in_nodes(sub_data, value, parts[1:])

    def _inject_selection_tech_x2many(self, data_node: dict, field_name: str, value, parts: list[str]):
        """Inject tech keys inside a one2many/many2many subtree."""
        if not value or not isinstance(data_node, dict):
            return
        sub_data_list = data_node.get(field_name)
        if not isinstance(sub_data_list, list):
            return
        for sub_data, sub_record in zip(sub_data_list, value, strict=False):
            if isinstance(sub_data, dict):
                self._inject_selection_tech_in_nodes(sub_data, sub_record, parts[1:])
