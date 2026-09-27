"""Selenium login, session, authorization, and CSRF tutorial scenarios."""

import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from main.models import Project


class AuthenticationBrowserTests(StaticLiveServerTestCase):
    host = "127.0.0.1"

    @classmethod
    def setUpClass(cls):
        if settings.SETTINGS_MODULE != "e2e.settings":
            raise RuntimeError("Jalankan pengujian browser melalui python test_e2e.py.")
        super().setUpClass()
        browser = os.environ.get("E2E_BROWSER", "chrome")
        options_type, driver_type = {
            "chrome": (webdriver.ChromeOptions, webdriver.Chrome),
            "edge": (webdriver.EdgeOptions, webdriver.Edge),
            "firefox": (webdriver.FirefoxOptions, webdriver.Firefox),
        }[browser]
        options = options_type()
        options.page_load_strategy = "eager"
        if os.environ.get("E2E_HEADLESS") == "1":
            options.add_argument("-headless" if browser == "firefox" else "--headless=new")
        try:
            cls.driver = driver_type(options=options)
        except WebDriverException as exc:
            raise RuntimeError(
                f"Browser {browser} belum dapat dijalankan. Pastikan browser terpasang "
                "dan Selenium Manager dapat mengunduh driver, atau coba --browser edge."
            ) from exc
        cls.addClassCleanup(cls.driver.quit)
        cls.driver.set_window_size(1440, 1000)
        cls.driver.set_page_load_timeout(30)

    def setUp(self):
        # No passwords are embedded in source or printed to the terminal.
        self.user_password = os.getenv("E2E_USER_PASSWORD") or secrets.token_urlsafe(32)
        self.admin_password = os.getenv("E2E_ADMIN_PASSWORD") or secrets.token_urlsafe(32)
        user_model = get_user_model()
        user_model.objects.create_user(username="burhan_test", password=self.user_password)
        user_model.objects.create_superuser(username="admin_test", password=self.admin_password)
        self.wait = WebDriverWait(self.driver, 15)

    def open_page(self, route):
        self.driver.get(self.live_server_url + reverse(f"main:{route}"))

    def submit_login(self, username, password):
        self.wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, ".project-form button[type='submit']").click()
        self.wait.until(EC.url_to_be(self.live_server_url + reverse("main:show_main")))
        self.wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, "nav-user"), username))

    def logout_and_check(self):
        self.open_page("logout")
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f'a[href="{reverse("main:login")}"]')))
        self.assertIsNone(self.driver.get_cookie(settings.SESSION_COOKIE_NAME))
        self.assertIsNone(self.driver.get_cookie("last_login"))
        self.assertFalse(self.driver.find_elements(By.CLASS_NAME, "nav-user"))

    def fill_project(self, title):
        for name, value in {
            "title": title,
            "description": "Data sementara untuk pengujian browser.",
            "tech_stack": "Django, Selenium",
        }.items():
            self.wait.until(EC.visibility_of_element_located((By.NAME, name))).send_keys(value)

    def submit_project(self):
        button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".project-form button[type='submit']"))
        )
        # The site's smooth scrolling can leave the button outside the viewport
        # while WebDriver attempts its click. Finish scrolling before clicking.
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", button
        )
        button.click()

    def test_authentication_and_csrf_workflow(self):
        # 1. Login form publishes both the hidden token and CSRF cookie.
        self.open_page("login")
        token = self.wait.until(EC.presence_of_element_located((By.NAME, "csrfmiddlewaretoken")))
        self.assertTrue(token.get_attribute("value"))
        self.assertTrue(self.driver.get_cookie(settings.CSRF_COOKIE_NAME)["value"])
        print("[PASS] CSRF token dan cookie terverifikasi", flush=True)

        # 2. Real browser login establishes the session and last-login display.
        self.submit_login("burhan_test", self.user_password)
        self.assertTrue(self.driver.get_cookie(settings.SESSION_COOKIE_NAME)["value"])
        last_login = self.driver.get_cookie("last_login")
        self.assertTrue(last_login["value"])
        displayed_login = self.driver.find_element(
            By.XPATH, "//dt[normalize-space()='Sesi Terakhir Login']/following-sibling::dd"
        )
        self.assertEqual(displayed_login.text, last_login["value"].strip('"'))
        print("[PASS] Login user biasa dan cookie sesi berhasil", flush=True)

        # 3. Knowing the URL is insufficient for a non-superuser.
        self.open_page("create_project")
        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Forbidden"))
        self.assertIn("403", self.driver.title)
        self.assertFalse(self.driver.find_elements(By.CLASS_NAME, "project-form"))
        print("[PASS] Otorisasi user biasa dibatasi (403)", flush=True)

        # 4. A superuser reaches the form; the session alone cannot bypass CSRF.
        self.logout_and_check()
        self.open_page("login")
        self.submit_login("admin_test", self.admin_password)
        self.open_page("create_project")
        self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "project-form")))
        print("[PASS] Akses superuser ke form proyek berhasil", flush=True)
        initial_count = Project.objects.count()
        self.fill_project("E2E rejected CSRF project")
        self.driver.execute_script("document.querySelector('[name=csrfmiddlewaretoken]').remove();")
        self.submit_project()
        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "CSRF verification failed"))
        self.assertIn("403", self.driver.title)
        self.assertEqual(Project.objects.count(), initial_count)
        print("[PASS] POST tanpa token CSRF ditolak; data tidak berubah", flush=True)

        # Control request: the same authenticated user can submit a valid token.
        self.open_page("create_project")
        title = "E2E temporary browser project"
        self.fill_project(title)
        self.submit_project()
        self.wait.until(EC.url_to_be(self.live_server_url + reverse("main:show_projects")))
        self.wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, "showcase-title"), title))
        self.assertEqual(Project.objects.count(), initial_count + 1)
        self.assertTrue(Project.objects.filter(title=title).exists())
        print("[PASS] POST dengan token CSRF sah berhasil dan proyek tampil", flush=True)

        # 5. Both session cookies disappear and protected access requires login.
        self.logout_and_check()
        self.open_page("create_project")
        self.wait.until(EC.url_contains(reverse("main:login") + "?next="))
        print("[PASS] Logout dan pembersihan cookie berhasil", flush=True)
