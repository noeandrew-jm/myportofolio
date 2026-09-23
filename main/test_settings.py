import os
from pathlib import Path
import runpy
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase


SETTINGS_PATH = Path(__file__).resolve().parent.parent / "portofolio" / "settings.py"


class DatabaseSettingsTests(SimpleTestCase):
    def production_environment(self, **overrides):
        environment = {
            "PRODUCTION": "True",
            "DB_NAME": "portfolio",
            "DB_USER": "portfolio_owner",
            "DB_PASSWORD": " password <with> symbols! ",
            "DB_HOST": "database.example.test",
            "DB_PORT": "5432",
            "SCHEMA": "portfolio_schema",
        }
        environment.update(overrides)
        return environment

    def load_settings(self, environment):
        # Exercise the real settings file while keeping the developer's .env,
        # process environment, and database connections out of these tests.
        with patch.dict(os.environ, environment, clear=True), patch("dotenv.load_dotenv"):
            return runpy.run_path(str(SETTINGS_PATH))

    def test_production_database_uses_validated_values_and_preserves_password(self):
        environment = self.production_environment(PRODUCTION="  tRuE  ", DB_PORT=" 5432 ")

        settings = self.load_settings(environment)
        database = settings["DATABASES"]["default"]

        self.assertTrue(settings["PRODUCTION"])
        self.assertFalse(settings["DEBUG"])
        self.assertEqual(database["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(database["NAME"], environment["DB_NAME"])
        self.assertEqual(database["USER"], environment["DB_USER"])
        self.assertEqual(database["PASSWORD"], environment["DB_PASSWORD"])
        self.assertEqual(database["HOST"], environment["DB_HOST"])
        self.assertEqual(database["PORT"], 5432)
        self.assertIsInstance(database["PORT"], int)
        self.assertEqual(database["OPTIONS"]["options"], "-c search_path=portfolio_schema")

    def test_missing_port_and_schema_use_defaults(self):
        environment = self.production_environment()
        del environment["DB_PORT"]
        del environment["SCHEMA"]

        database = self.load_settings(environment)["DATABASES"]["default"]

        self.assertEqual(database["PORT"], 5432)
        self.assertEqual(database["OPTIONS"]["options"], "-c search_path=public")

    def test_port_accepts_valid_boundaries(self):
        for port in ("1", "65535"):
            with self.subTest(port=port):
                database = self.load_settings(self.production_environment(DB_PORT=port))["DATABASES"]["default"]
                self.assertEqual(database["PORT"], int(port))

    def test_invalid_ports_fail_early_with_actionable_guidance(self):
        for port in ("<5432>", "", " ", "postgres", "0", "-1", "65536", "5432.0", "+5432", "５４３２"):
            with self.subTest(port=port):
                with self.assertRaises(ImproperlyConfigured) as error:
                    self.load_settings(self.production_environment(DB_PORT=port))

                self.assertIn("DB_PORT", str(error.exception))
                self.assertIn("5432", str(error.exception))

    def test_invalid_port_error_does_not_disclose_raw_value_or_password(self):
        environment = self.production_environment(DB_PORT="private-input-that-is-not-a-port")

        with self.assertRaises(ImproperlyConfigured) as error:
            self.load_settings(environment)

        self.assertNotIn(environment["DB_PORT"], str(error.exception))
        self.assertNotIn(environment["DB_PASSWORD"], str(error.exception))

    def test_production_requires_database_connection_values(self):
        for name in ("DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST"):
            for missing in (True, False):
                with self.subTest(name=name, missing=missing):
                    environment = self.production_environment()
                    if missing:
                        del environment[name]
                    else:
                        environment[name] = ""

                    with self.assertRaises(ImproperlyConfigured) as error:
                        self.load_settings(environment)

                    self.assertIn(name, str(error.exception))

    def test_placeholder_connection_values_fail_without_disclosing_contents(self):
        for name in ("DB_NAME", "DB_USER", "DB_HOST", "SCHEMA"):
            with self.subTest(name=name):
                environment = self.production_environment(**{name: "<private-placeholder>"})

                with self.assertRaises(ImproperlyConfigured) as error:
                    self.load_settings(environment)

                self.assertIn(name, str(error.exception))
                self.assertNotIn("private-placeholder", str(error.exception))
                self.assertNotIn(environment["DB_PASSWORD"], str(error.exception))

    def test_angle_brackets_are_allowed_in_passwords(self):
        environment = self.production_environment(DB_PASSWORD="<valid-password>")

        database = self.load_settings(environment)["DATABASES"]["default"]

        self.assertEqual(database["PASSWORD"], "<valid-password>")

    def test_local_mode_does_not_require_or_validate_postgres_settings(self):
        for production in (None, "False", " false "):
            with self.subTest(production=production):
                environment = {"DB_PORT": "<5432>"}
                if production is not None:
                    environment["PRODUCTION"] = production

                settings = self.load_settings(environment)

                self.assertFalse(settings["PRODUCTION"])
                self.assertTrue(settings["DEBUG"])
                self.assertEqual(settings["DATABASES"]["default"]["ENGINE"], "django.db.backends.sqlite3")
                self.assertEqual(settings["DATABASES"]["default"]["NAME"], SETTINGS_PATH.parent.parent / "db.sqlite3")
