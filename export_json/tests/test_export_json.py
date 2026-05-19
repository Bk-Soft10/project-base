import json
import re
from unittest.mock import MagicMock, patch

from odoo.tests import common, tagged

from odoo.addons.export_json.controller import main as controller_module
from odoo.addons.export_json.controller.main import JsonExportFormat


@tagged("export_json")
class TestExportJson(common.HttpCase):
    def setUp(self):
        self.partner = self.env["res.partner"].create(
            {
                "name": "TEST",
                "email": "test@test.fr",
                "type": "contact",
                "child_ids": [
                    (
                        0,
                        None,
                        {
                            "name": "test child 1",
                            "email": "test_child_1@test.fr",
                            "type": "delivery",
                        },
                    ),
                    (
                        0,
                        None,
                        {
                            "name": "test child 2",
                            "email": "test_child_2@test.fr",
                            "type": "invoice",
                        },
                    ),
                ],
            }
        )

        self.data_dict = {
            "model": "res.partner",
            "fields": [
                {"name": "id", "label": "External ID"},
                {"name": "name", "label": "Name"},
                {"name": "email", "label": "Email"},
                {"name": "type", "label": "Type"},
                {"name": "child_ids/name", "label": "Name"},
                {"name": "child_ids/email", "label": "Email"},
                {"name": "child_ids/type", "label": "Type"},
            ],
            "ids": [self.partner.id],
            "domain": [["type", "in", ("contact", "delivery")]],
            "groupby": [],
            "context": {
                "lang": "en_US",
                "tz": "Europe/Paris",
                "uid": 2,
                "allowed_company_ids": [1],
            },
            "import_compat": True,
        }
        child_records = self.partner.child_ids.sorted("id")
        self.basic_expect_dict = {
            "id": self.partner.id,
            "name": "TEST",
            "email": "test@test.fr",
            "type": self.partner.type,
            "tech_type": self.partner.type,
            "child_ids": [
                {
                    "name": child_records[0].name,
                    "email": child_records[0].email,
                    "type": child_records[0].type,
                    "tech_type": child_records[0].type,
                },
                {
                    "name": child_records[1].name,
                    "email": child_records[1].email,
                    "type": child_records[1].type,
                    "tech_type": child_records[1].type,
                },
            ],
        }

        self.expected_list_dict_merge = [
            {
                "amount_total": 300.0,
                "amount_untaxed": 250.0,
                "company_id": "My Company",
                "currency_id": "EUR",
                "invoice_status": "invoice_status",
                "invoice_status_FR": "Rien à facturer",
                "invoice_status_US": "Nothing to Bill",
                "order_line": [
                    {
                        "company_id": "My Company",
                        "currency_id": "EUR",
                        "display_type": "Section",
                        "name": "Exmple de section",
                        "state": "order_line/state",
                        "state_FR": "Bon de commande fournisseur",
                        "state_US": "Purchase Order",
                        "tax_calculation_rounding_method": "order_line/tax_calculation_rounding_method",
                        "tax_calculation_rounding_method_FR": "Arrondir à la ligne",
                        "tax_calculation_rounding_method_US": "Round per Line",
                        "taxes_id": [],
                    },
                    {
                        "company_id": "My Company",
                        "currency_id": "EUR",
                        "name": "Produit test 2",
                        "price_subtotal": 75.0,
                        "price_unit": 75.0,
                        "product_id": "order_line/product_id",
                        "product_id_FR": "Produit test 2",
                        "product_id_US": "ENGLISH Produit test 2",
                        "product_type": "order_line/product_type",
                        "product_type_FR": "Biens",
                        "product_type_US": "Goods",
                        "product_uom": "order_line/product_uom",
                        "product_uom_FR": "Unité(s)",
                        "product_uom_US": "Units",
                        "product_uom_category_id": "order_line/product_uom_category_id",
                        "product_uom_category_id_FR": "Unité",
                        "product_uom_category_id_US": "Unit",
                        "state": "order_line/state",
                        "state_FR": "Bon de commande fournisseur",
                        "state_US": "Purchase Order",
                        "tax_calculation_rounding_method": "order_line/tax_calculation_rounding_method",
                        "tax_calculation_rounding_method_FR": "Arrondir à la ligne",
                        "tax_calculation_rounding_method_US": "Round per Line",
                        "taxes_id": ["20%"],
                    },
                ],
                "payment_term_id": "payment_term_id",
                "payment_term_id_FR": "21 jours ",
                "payment_term_id_US": "21 Days",
                "tax_country_id": "tax_country_id",
                "tax_country_id_FR": "États-Unis",
                "tax_country_id_US": "United States",
            }
        ]

        self.data_str = str(self.data_dict)
        self.data = json.dumps(self.data_dict)

        self.json_export_format = JsonExportFormat()
        self.mock_request = MagicMock()
        self.mock_request.env = self.env
        super().setUp()

    def helper_get_csrf_token(self):
        resp = self.url_open("/web/login")
        html = resp.content.decode()
        match = re.search(r'csrf_token:\s*"([^"]+)"', html)
        return match and match.group(1) or False

    def test_generate_export_json(self):
        # Perform the json export
        fields = [field["name"] for field in self.data_dict["fields"]]
        model = self.env[self.data_dict["model"]]

        with patch.object(controller_module, "request", self.mock_request):
            result_json = self.json_export_format.perform_json_export(
                self.data_dict["domain"], fields, self.data_dict["ids"], model
            )

        dict_result_json = json.loads(result_json)
        self.assertDictEqual(
            self.basic_expect_dict,
            dict_result_json[0],
            "Check if json export is equal to expected data",
        )
        self.assertIn("tech_type", dict_result_json[0])
        self.assertIn("tech_type", dict_result_json[0]["child_ids"][0])

    def test_perform_json_export_with_lang(self):
        self.env["res.lang"]._activate_lang("fr_FR")

        # category_id is a M2M, not a M2O
        self.data_dict["fields"].append({"name": "category_id/name", "label": "Tags"})
        self.data_dict["fields"].append({"name": "country_id/name", "label": "Country"})
        fields = [field["name"] for field in self.data_dict["fields"]]
        model = self.env[self.data_dict["model"]]

        # Ajouts de traductions
        category = (
            self.env["res.partner.category"]
            .with_context(lang="en_US")
            .create(
                {
                    "name": "Customer",
                }
            )
        )
        category.with_context(lang="fr_FR").name = "Client"
        self.partner.category_id = category

        self.env.ref("base.es").with_context(lang="fr_FR").name = "Espagne"
        self.partner.country_id = self.env.ref("base.es")

        with patch.object(controller_module, "request", self.mock_request):
            result_json = self.json_export_format.perform_json_export(
                self.data_dict["domain"],
                fields,
                self.data_dict["ids"],
                model,
                langs_code=["fr_FR", "en_US"],
            )

        dict_result_json = json.loads(result_json)
        child_records = self.partner.child_ids.sorted("id")
        expected_dict = {
            "id": self.partner.id,
            "name": "TEST",
            "email": "test@test.fr",
            "type": self.partner.type,
            "tech_type": self.partner.type,
            "category_id": [
                {
                    "name": "category_id/name",
                    "name_FR": "Client",
                    "name_US": "Customer",
                }
            ],
            "country_id": {
                "name": "country_id/name",
                "name_FR": "Espagne",
                "name_US": "Spain",
            },
            "child_ids": [
                {
                    "name": child_records[0].name,
                    "email": child_records[0].email,
                    "type": child_records[0].type,
                    "tech_type": child_records[0].type,
                },
                {
                    "name": child_records[1].name,
                    "email": child_records[1].email,
                    "type": child_records[1].type,
                    "tech_type": child_records[1].type,
                },
            ],
        }
        self.assertDictEqual(expected_dict, dict_result_json[0], "Le json doit contenir les traductions")
        self.assertNotIn("tech_type_FR", dict_result_json[0])
        self.assertNotIn("tech_type_US", dict_result_json[0])

    def test_convert_simple_list(self):
        """La fonction _convert_simple_list prend en entrée une liste de clée, correspondant
        à des noms de champs, et retourne une liste de dict{"name": nom_de_champ}"""
        res_partner_fields_names = list(self.partner._fields.keys())

        res = self.json_export_format._convert_simple_list(res_partner_fields_names)

        self.assertEqual(
            len(res_partner_fields_names),
            len(res),
            "Tous les noms de champs du modèle res.partner doivent être retourné sous la forme {'name': nom_de_champ}",
        )

        # Si on ajoute un dict dans les noms de champ du res_partner, le dict doit être retourné tel quel, lors
        # du passage de la fonction _convert_simple_list

        mock_dict = {
            "random_key": "random_value",
            "random_key1": "random_value1",
            "random_key2": "random_value2",
        }
        res_partner_fields_names.append(mock_dict)

        res = self.json_export_format._convert_simple_list(res_partner_fields_names)

        self.assertEqual(len(res_partner_fields_names), len(res))
        self.assertIn(
            mock_dict,
            res,
            "Le dict ajouté dans les champs de res.partner est bien retourner telquel dans la list",
        )

    def test_get_country_code(self):
        """La fonction prend un paramètre un string de lang, elle doit retourner la deuxième partie du code
        (séparé par le premier '_' du string)"""

        for test_val, expected in [
            ("fr_FR", "FR"),
            ("_fr_FR", "fr"),
            ("FR_", ""),
            ("", ""),
        ]:
            self.assertEqual(self.json_export_format.get_country_code(test_val), expected)

    def test_add_unique_vals(self):
        """La fonction prend en paramètre un dict, et retourne un set de valeur unique.
        La fonction stringify les list et les dicts, si dans le dict d'entrée, des valeurs sont
        des dicts ou des lists."""

        mock_dict_same_value = {
            "random_key": "random_value",
            "random_key1": "random_value",
            "random_key2": "random_value",
        }
        res = self.json_export_format.add_unique_vals(mock_dict_same_value)

        self.assertEqual(
            len(res),
            1,
            "Le dict d'entrée contenait 3 clés valeurs, mais les valeurs liées aux clés étaient identiques.",
        )
        self.assertIn("random_value", res)

        mock_dict_different_value = {
            "random_key": "random_value",
            "random_key1": "random_value1",
            "random_key2": "random_value",
        }
        res = self.json_export_format.add_unique_vals(mock_dict_different_value)
        self.assertEqual(len(res), 2)
        for expected in ["random_value", "random_value1"]:
            self.assertIn(expected, res)

        mock_dict_with_dict_list = {
            "random_key": {"an_other": "one"},
            "random_key1": [10, 20, 40],
            "random_key2": [10, 20, 40],
        }
        res = self.json_export_format.add_unique_vals(mock_dict_with_dict_list)

        self.assertEqual(len(res), 2)
        for expected in ["{'an_other': 'one'}", "[10, 20, 40]"]:
            self.assertIn(expected, res)

        self.assertEqual(0, len(self.json_export_format.add_unique_vals({})))

    def test_retrieve_all_keys(self):
        test_dict = {
            "fr_FR": {
                "champ_1": "valeur",
                "champ_2": "valeur",
                "champ_3": "valeur",
                "champ_4": "valeur",
            },
            "zn_CN": {
                "champ_5": "valeur",
                "champ_6": "valeur",
                "champ_3": "valeur",
                "champ_4": "valeur",
            },
        }

        res = self.json_export_format.retrieve_all_keys(test_dict)
        for expected in [
            "champ_1",
            "champ_2",
            "champ_3",
            "champ_4",
            "champ_5",
            "champ_6",
        ]:
            self.assertIn(expected, res)

        other_dict = {
            "champ_1": "valeur",
            "champ_2": "valeur",
            "champ_3": "valeur",
        }
        with self.assertRaises(AssertionError):
            self.json_export_format.retrieve_all_keys(other_dict)

    def test_process_keys_without_parent_key(self):
        test_dict = {
            "fr_FR": {
                "champ_1": "valeur",
                "champ_2": "valeur",
                "champ_3": "valeur",
                "champ_4": "valeur",
            },
            "zn_CN": {
                "champ_5": "valeur",
                "champ_6": "valeur",
                "champ_3": "valeur",
                "champ_4": "valeur",
            },
        }

        merged_dict = {}
        all_keys = self.json_export_format.retrieve_all_keys(test_dict)

        self.json_export_format.process_keys(all_keys, test_dict, merged_dict)

        for expected in [
            "champ_1",
            "champ_2",
            "champ_3",
            "champ_4",
            "champ_5",
            "champ_6",
        ]:
            self.assertIn(
                expected,
                merged_dict,
                "Chaque champ doit être inclus dans le dictionnaire final, qui fusionne"
                "l'ensemble des champs des dictionnaires d'entrées, par langue.",
            )

        self.json_export_format.process_keys(all_keys, test_dict, merged_dict)

        # Si pour un même nom de champ donné, la valeur est différente entre des langues, les deux clés concaténées
        # du suffixe du code la langue,
        # doivent être présent dans le dict final.
        test_dict_2 = {
            "fr_FR": {
                "champ_1": "valeur",
                "champ_2": "valeur",
                "champ_3": "VALEUR EN FRANÇAIS",
                "champ_4": "valeur",
            },
            "zn_CN": {
                "champ_5": "valeur",
                "champ_6": "valeur",
                "champ_3": "VALEUR PAS EN FRANÇAIS",
                "champ_4": "valeur",
            },
        }
        self.json_export_format.process_keys(all_keys, test_dict_2, merged_dict)
        for expected in [
            "champ_1",
            "champ_2",
            "champ_3",
            "champ_4",
            "champ_5",
            "champ_6",
            "champ_3_FR",
            "champ_3_CN",
        ]:
            self.assertIn(
                expected,
                merged_dict,
                "Chaque champ doit être inclus dans le dictionnaire final, qui fusionne"
                "l'ensemble des champs des dictionnaires d'entrées, par langue.",
            )
        self.assertEqual(merged_dict.get("champ_3_FR"), "VALEUR EN FRANÇAIS")
        self.assertEqual(merged_dict.get("champ_3_CN"), "VALEUR PAS EN FRANÇAIS")

    def test_process_keys_with_parent_key(self):
        test_dict = {
            "fr_FR": {
                "champ_1": "valeur",
                "champ_2": "valeur",
                "champ_3": {
                    "cle_dict_imbrique_1": "valeur1",
                    "cle_dict_imbrique_2": "valeur2",
                    "cle_dict_imbrique_3": [
                        "element_liste_imbriqueFR",
                        "element_autre_listeFR",
                    ],
                },
            },
            "zn_CN": {
                "champ_1": "valeur",
                "champ_2": "valeur",
                "champ_3": {
                    "cle_dict_imbrique_1": "valeur1489",
                    "cle_dict_imbrique_2": "valeur24996",
                    "cle_dict_imbrique_3": [
                        "element_liste_imbrique",
                        "element_autre_liste",
                    ],
                },
            },
        }
        merged_dict = {}
        all_keys = self.json_export_format.retrieve_all_keys(test_dict)

        self.json_export_format.process_keys(all_keys, test_dict, merged_dict, "champ_3")

        # Le dict attendu doit contenir toutes les valeurs de chaque langues, même si les valeurs sont eux mêmes dans
        # des dict ou dans des listes. Un regroupement doit être effectué autour du champ_3 :
        # le dict du champ_3 doit contenir la clé original de chaque dict (cle_dict_imbrique_1, cle_dict_imbrique_2,
        # cle_dict_imbrique_3)
        # avec pour valeurs le chemin absolu de la valeur (champ_3/cle_dict_imbrique_1, champ_3/cle_dict_imbrique_2,
        # champ_3/cle_dict_imbrique_3)

        expected_dict = {
            "champ_1": "valeur",
            "champ_2": "valeur",
            "champ_3": {
                "cle_dict_imbrique_1": "champ_3/cle_dict_imbrique_1",
                "cle_dict_imbrique_1_CN": "valeur1489",
                "cle_dict_imbrique_1_FR": "valeur1",
                "cle_dict_imbrique_2": "champ_3/cle_dict_imbrique_2",
                "cle_dict_imbrique_2_CN": "valeur24996",
                "cle_dict_imbrique_2_FR": "valeur2",
                "cle_dict_imbrique_3": "champ_3/cle_dict_imbrique_3",
                "cle_dict_imbrique_3_CN": [
                    "element_liste_imbrique",
                    "element_autre_liste",
                ],
                "cle_dict_imbrique_3_FR": [
                    "element_liste_imbriqueFR",
                    "element_autre_listeFR",
                ],
            },
        }
        self.assertDictEqual(expected_dict, merged_dict)

    def test_process_keys_nested_dict(self):
        test_dict = {
            "fr_FR": {
                "champ_1": [
                    {
                        "cle_dict_imbrique_1": "valeur1",
                        "cle_dict_imbrique_2": "valeur2",
                        "cle_dict_imbrique_3": [
                            "element_liste_imbriqueFR",
                            "element_autre_listeFR",
                        ],
                    },
                    {
                        "cle_dict_imbrique_1": "valeur44",
                        "cle_dict_imbrique_2": "valeur4858",
                        "cle_dict_imbrique_3": [
                            "element_liste_imbriqueFR",
                            "element_autre_liste",
                        ],
                    },
                ],
                "champ_2": "valeur",
            },
            "zn_CN": {
                "champ_1": [
                    {
                        "cle_dict_imbrique_1": "valeur1",
                        "cle_dict_imbrique_2": "valeur2",
                        "cle_dict_imbrique_3": [
                            "element_liste_imbriqueFR",
                            "element_autre_listeFR",
                        ],
                    },
                    {
                        "cle_dict_imbrique_1": "valeur44",
                        "cle_dict_imbrique_2": "valeur4858",
                        "cle_dict_imbrique_3": [
                            "element_liste_imbrique",
                            "element_autre_liste",
                        ],
                    },
                ],
            },
        }
        merged_dict = {}
        all_keys = self.json_export_format.retrieve_all_keys(test_dict)
        self.json_export_format.process_keys(all_keys, test_dict, merged_dict)

        expected_dict = {
            "champ_1": [
                {
                    "cle_dict_imbrique_1": "valeur1",
                    "cle_dict_imbrique_2": "valeur2",
                    "cle_dict_imbrique_3": [
                        "element_liste_imbriqueFR",
                        "element_autre_listeFR",
                    ],
                },
                {
                    "cle_dict_imbrique_1": "valeur44",
                    "cle_dict_imbrique_2": "valeur4858",
                    "cle_dict_imbrique_3": "champ_1/cle_dict_imbrique_3",
                    "cle_dict_imbrique_3_CN": [
                        "element_liste_imbrique",
                        "element_autre_liste",
                    ],
                    "cle_dict_imbrique_3_FR": [
                        "element_liste_imbriqueFR",
                        "element_autre_liste",
                    ],
                },
            ],
            "champ_2": "valeur",
        }
        self.assertDictEqual(expected_dict, merged_dict)

    def test_merge_list_of_dicts_without_lang(self):
        self.assertEqual(
            [],
            self.json_export_format._merge_list_of_dicts({}),
            "Sans langue, cette fonction ne doit rien faire et retourner une liste vide",
        )
        self.assertEqual(
            [],
            self.json_export_format.merge_multilingual_dicts({}),
            "Même chose, sans langue, pas de dict",
        )

    def test_merge_multilingual_dicts(self):
        test_dict = {
            "en_US": [
                {
                    "amount_total": 300.0,
                    "amount_untaxed": 250.0,
                    "company_id": "My Company",
                    "currency_id": "EUR",
                    "invoice_status": "Nothing to Bill",
                    "order_line": [
                        {
                            "company_id": "My Company",
                            "currency_id": "EUR",
                            "display_type": "Section",
                            "name": "Exmple de section",
                            "state": "Purchase Order",
                            "tax_calculation_rounding_method": "Round per Line",
                            "taxes_id": [],
                        },
                        {
                            "company_id": "My Company",
                            "currency_id": "EUR",
                            "name": "Produit test 2",
                            "price_subtotal": 75.0,
                            "price_unit": 75.0,
                            "product_type": "Goods",
                            "product_id": "ENGLISH Produit test 2",
                            "product_uom": "Units",
                            "product_uom_category_id": "Unit",
                            "state": "Purchase Order",
                            "tax_calculation_rounding_method": "Round per Line",
                            "taxes_id": ["20%"],
                        },
                    ],
                    "payment_term_id": "21 Days",
                    "tax_country_id": "United States",
                }
            ],
            "fr_FR": [
                {
                    "amount_total": 300.0,
                    "amount_untaxed": 250.0,
                    "company_id": "My Company",
                    "currency_id": "EUR",
                    "invoice_status": "Rien à facturer",
                    "order_line": [
                        {
                            "company_id": "My Company",
                            "currency_id": "EUR",
                            "display_type": "Section",
                            "name": "Exmple de section",
                            "state": "Bon de commande fournisseur",
                            "tax_calculation_rounding_method": "Arrondir à la ligne",
                            "taxes_id": [],
                        },
                        {
                            "company_id": "My Company",
                            "currency_id": "EUR",
                            "name": "Produit test 2",
                            "price_subtotal": 75.0,
                            "price_unit": 75.0,
                            "product_id": "Produit test 2",
                            "product_type": "Biens",
                            "product_uom": "Unité(s)",
                            "product_uom_category_id": "Unité",
                            "state": "Bon de commande fournisseur",
                            "tax_calculation_rounding_method": "Arrondir à la ligne",
                            "taxes_id": ["20%"],
                        },
                    ],
                    "payment_term_id": "21 jours ",
                    "tax_country_id": "États-Unis",
                }
            ],
        }
        self.assertDictEqual(
            self.expected_list_dict_merge[0],
            self.json_export_format.merge_multilingual_dicts(test_dict)[0],
        )

    def test_format_data(self):
        fields = self.expected_list_dict_merge
        res_json = self.json_export_format.format_data(fields)
        self.assertTrue(json.loads(res_json), "Le résultat de la fonction doit être au format .json")

        fields[0].update({"mock_bytes_key": b"mock_bytes_value"})
        res_json = self.json_export_format.format_data(fields)

        list_dict_from_json = json.loads(res_json)
        bytes_key = list_dict_from_json[0].get("mock_bytes_key")
        self.assertEqual(
            "data:application/octet-stream;base64,bW9ja19ieXRlc192YWx1ZQ==",
            bytes_key,
            "La présence d'une clé contenant une valeur en bytes, dans les champs d'entrée, doit obligatoirement "
            "être modifié en sorti dans le json, pour y inclure un préfixe.",
        )

    def test_define_parser(self):
        res_partner_fields_names = list(self.partner._fields.keys())
        set_fields_names = set(res_partner_fields_names)

        # Ajouts de faux nom de champs qui sont concaténés.
        res_partner_fields_names.append("company_id/name")
        res_partner_fields_names.append("company_id/street1")
        res_partner_fields_names.append("company_id/siret")

        res_partner_fields_names.append("country_id/currency_id/name")
        res_partner_fields_names.append("country_id/currency_id/iso_numeric")
        converted_fields_name = self.json_export_format._convert_simple_list(res_partner_fields_names)

        parser = self.json_export_format.define_parser(converted_fields_name)

        self.assertTrue(
            set_fields_names.issubset(parser),
            "Tous les champs du modèle res.partner doivent être présent dans le parser.",
        )
        expected_tuple_1 = ("company_id", ["name", "street1", "siret"])
        expected_tuple_2 = ("country_id", [("currency_id", ["name", "iso_numeric"])])
        for expected_tuple in [expected_tuple_1, expected_tuple_2]:
            self.assertIn(
                expected_tuple,
                parser,
                "Un tuple nom_de_champ et liste de nom de champ (qui peut lui même contenir un tuple avec "
                "la même combinaison), doit être présent, pour les champs de type M2O, avec un accès à un "
                "des champs du M2O",
            )

    def test_add_list_or_dict_on_merge_item(self):
        # Faire la version avec un parent_key qui est un dict
        test_dict = {
            "fr_FR": {
                "champ_2": "valeur",
                "champ_3": {
                    "cle_dict_imbrique_1": "valeur1",
                    "cle_dict_imbrique_2": "valeur2",
                    "cle_dict_imbrique_3": [
                        "element_liste_imbriqueFR",
                        "element_autre_listeFR",
                    ],
                },
            },
            "zn_CN": {
                "champ_2": "valeur",
                "champ_3": {
                    "cle_dict_imbrique_1": "valeur1489",
                    "cle_dict_imbrique_2": "valeur24996",
                    "cle_dict_imbrique_3": [
                        "element_liste_imbrique",
                        "element_autre_liste",
                    ],
                },
            },
        }
        merged_dict = {}
        all_keys = self.json_export_format.retrieve_all_keys(test_dict)

        # On simule le fait que le champ_2 soit le parent key de tout le dict d'entrée "test_dict".
        # La clé doit apparaître dans l'arborescence de chaque champ imbriquée.
        self.json_export_format.process_keys(all_keys, test_dict, merged_dict, "champ_2")

        expected_dict = {
            "champ_2": "valeur",
            "champ_3": {
                "cle_dict_imbrique_2": "champ_2/champ_3/cle_dict_imbrique_2",
                "cle_dict_imbrique_2_FR": "valeur2",
                "cle_dict_imbrique_2_CN": "valeur24996",
                "cle_dict_imbrique_3": "champ_2/champ_3/cle_dict_imbrique_3",
                "cle_dict_imbrique_3_FR": [
                    "element_liste_imbriqueFR",
                    "element_autre_listeFR",
                ],
                "cle_dict_imbrique_3_CN": [
                    "element_liste_imbrique",
                    "element_autre_liste",
                ],
                "cle_dict_imbrique_1": "champ_2/champ_3/cle_dict_imbrique_1",
                "cle_dict_imbrique_1_FR": "valeur1",
                "cle_dict_imbrique_1_CN": "valeur1489",
            },
        }
        self.assertDictEqual(expected_dict, merged_dict)

    def test_index_json_export_route(self):
        # Fonction appelé par le controller qui gère l'export au format json (bouton "Action" > "Exporter")
        self.authenticate("admin", "admin")
        csrf = self.helper_get_csrf_token()

        url = "/web/export/json"
        payload = {
            "csrf_token": csrf,
            "data": json.dumps(self.data_dict),
        }

        response = self.url_open(url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(self.basic_expect_dict, response.json()[0])

    def test_formats_export_formats(self):
        # On vérifie que la pop-up d'export ajoute bien la coche json dans les options de format de sortie.
        self.authenticate("admin", "admin")
        url = "/web/export/formats"
        payload = {"jsonrpc": "2.0", "method": "call", "params": {}, "id": 1}

        response = self.url_open(
            url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        result_format = response.json().get("result")
        self.assertIn(
            {"label": "JSON", "tag": "json"},
            result_format,
            "Le nouveau format json doit être disponible enexport",
        )

    def test_json_export_on_none_ordinary_table(self):
        fields = [field["name"] for field in self.data_dict["fields"]]
        model = self.env[self.data_dict["model"]]
        with patch("odoo.models.BaseModel._is_an_ordinary_table", return_value=False):
            with patch.object(controller_module, "request", self.mock_request):
                result_json = self.json_export_format.perform_json_export(
                    self.data_dict["domain"], fields, self.data_dict["ids"], model
                )

        res_dict = json.loads(result_json)
        self.basic_expect_dict.pop("id")
        self.assertDictEqual(
            res_dict[0],
            self.basic_expect_dict,
            "Seul l'id ne doit pas être récupérer, "
            "si la table associé au modèle ne correspond pas à une table classique."
            "Toutes les autres informations doivent être récupérés normalement.",
        )

    def test_property_extension(self):
        self.assertEqual(self.json_export_format.extension, ".json")

    def test_property_content_type(self):
        self.assertEqual(self.json_export_format.content_type, "text/json;charset=utf8")
