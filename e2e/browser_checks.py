"""Selenium authentication, authorization, CSRF, and AJAX project scenarios."""

import os
from pathlib import Path
import secrets
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
        self.driver.delete_all_cookies()
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
            self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f'.project-form [name="{name}"]'))).send_keys(value)

    def click(self, selector):
        element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", element)
        element.click()

    def wait_for_titles(self, expected):
        self.wait.until(lambda driver: [
            element.text for element in driver.find_elements(By.CSS_SELECTOR, "#project-cards > .showcase-card .showcase-title")
        ] == expected)

    def search(self, query):
        self.driver.execute_script("""
            const field = document.getElementById('search-input');
            field.value = arguments[0];
            field.dispatchEvent(new Event('input', {bubbles: true}));
        """, query)

    def assert_same_document(self):
        self.assertTrue(self.driver.execute_script("return window.ajaxDocumentMarker === 'unchanged';"))

    def test_ajax_read_search_states_and_legacy_xss(self):
        Project.objects.all().delete()
        alpha = Project.objects.create(title="Alpha portfolio", description="Alpha description", tech_stack="Django")
        beta = Project.objects.create(title="Beta dashboard", description="Beta description", tech_stack="Python")
        self.open_page("show_projects")
        self.wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "#project-cards > .showcase-card")) == 2)
        self.assertFalse(self.driver.find_elements(By.ID, "add-project-modal"))
        self.assertFalse(self.driver.find_elements(By.CSS_SELECTOR, "#project-cards .star-form"))
        self.assertEqual(len(self.driver.find_elements(By.CSS_SELECTOR, "#project-cards a.button-star")), 2)

        # Track real AJAX calls and hold their response to inspect loading.
        self.driver.execute_script("""
            window.ajaxDocumentMarker = 'unchanged';
            window.originalFetch = window.fetch;
            window.projectReads = [];
            window.fetch = (url, options) => {
                const parsed = new URL(url, location.href);
                if (parsed.pathname === arguments[0]) {
                    window.projectReads.push(parsed.searchParams.get('title'));
                    if (window.failProjectRead === 'http') return Promise.resolve(new Response('', {status: 503}));
                    if (window.failProjectRead === 'network') return Promise.reject(new TypeError('Failed to fetch'));
                    if (window.failProjectRead === 'invalid-json') return Promise.resolve(new Response('invalid JSON'));
                    if (window.failProjectRead === 'invalid-list') return Promise.resolve(new Response('{}'));
                    if (window.holdProjectRead) return new Promise(resolve => {
                        window.releaseProjectRead = () => resolve(window.originalFetch(url, options));
                    });
                }
                return window.originalFetch(url, options);
            };
            window.holdProjectRead = true;
            const field = document.getElementById('search-input');
            for (const query of ['A', 'Al', '  aLpHa  ']) {
                field.value = query;
                field.dispatchEvent(new Event('input', {bubbles: true}));
            }
        """, reverse("main:get_projects_json"))
        self.wait.until(lambda driver: driver.execute_script("return typeof window.releaseProjectRead === 'function';"))
        self.assertTrue(self.driver.find_element(By.ID, "loading").is_displayed())
        self.assertEqual(self.driver.find_element(By.ID, "grid").get_attribute("aria-busy"), "true")
        self.assertFalse(self.driver.find_element(By.ID, "grid").is_displayed())
        self.assertEqual(self.driver.execute_script("return window.projectReads;"), ["aLpHa"])
        self.driver.execute_script("window.holdProjectRead = false; window.releaseProjectRead();")
        self.wait_for_titles([alpha.title])
        self.assert_same_document()

        self.search("No result")
        self.wait.until(EC.visibility_of_element_located((By.ID, "empty")))
        self.assertEqual(self.driver.find_elements(By.CSS_SELECTOR, "#project-cards > .showcase-card"), [])
        self.assertEqual(
            self.driver.find_element(By.ID, "empty").text,
            'Tidak ada proyek yang cocok dengan pencarian "No result".',
        )
        for failure in ("http", "network", "invalid-json", "invalid-list"):
            with self.subTest(failure=failure):
                self.driver.execute_script("window.failProjectRead = arguments[0];", failure)
                self.search("Beta")
                self.wait.until(EC.visibility_of_element_located((By.ID, "error")))
                for state in ("loading", "empty", "grid"):
                    self.assertFalse(self.driver.find_element(By.ID, state).is_displayed())
                self.driver.execute_script("window.failProjectRead = false;")
                self.click("#retry-projects")
                self.wait_for_titles([beta.title])
                self.assertEqual(self.driver.find_element(By.ID, "grid").get_attribute("aria-busy"), "false")
                self.assert_same_document()

        # Insert legacy content directly: form sanitization cannot protect old
        # records, so the client must render text and reject dangerous URL schemes.
        legacy_title = '<img src="x" onerror="window.projectXss=true">'
        legacy = Project.objects.create(
            title=legacy_title,
            description='<svg onload="window.projectXss=true">Legacy text</svg>',
            tech_stack='<b onclick="window.projectXss=true">Python</b>',
            project_url="javascript:window.projectXss=true",
            project_image_url="javascript:window.projectXss=true",
        )
        self.click("#reset-search")
        self.wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "#project-cards > .showcase-card")) == 3)
        card = self.driver.find_element(By.CSS_SELECTOR, f'#project-cards [data-project-id="{legacy.pk}"]')
        self.assertEqual(card.find_element(By.CLASS_NAME, "showcase-title").text, legacy_title)
        self.assertEqual(card.find_element(By.CLASS_NAME, "showcase-description").text, legacy.description)
        self.assertEqual(card.find_element(By.CLASS_NAME, "content-item-label").get_attribute("textContent"), legacy.tech_stack)
        self.assertFalse(card.find_elements(By.CSS_SELECTOR, "img, svg, [onerror], [onload], [onclick], [href^='javascript:']"))
        self.assertIsNone(self.driver.execute_script("return window.projectXss;"))
        self.assert_same_document()
        Project.objects.all().delete()
        self.search("")
        self.wait.until(EC.visibility_of_element_located((By.ID, "empty")))
        self.assertIn("Belum ada proyek", self.driver.find_element(By.ID, "empty").text)
        print("[PASS] AJAX read, debounce, loading/empty/error/retry, dan legacy XSS", flush=True)

    def test_ajax_search_debounce_and_composition(self):
        Project.objects.all().delete()
        alpha = Project.objects.create(title="Alpha portfolio", description="First result", tech_stack="Django")
        beta = Project.objects.create(title="Beta dashboard", description="Final query result", tech_stack="Python")
        self.open_page("show_projects")
        self.wait_for_titles([alpha.title, beta.title])
        self.driver.execute_script("""
            window.ajaxDocumentMarker = 'unchanged';
            window.originalFetch = window.fetch;
            window.projectReads = [];
            window.projectReadTimes = [];
            window.fetch = (url, options) => {
                const parsed = new URL(url, location.href);
                if (parsed.pathname === arguments[0]) {
                    window.projectReads.push(parsed.searchParams.get('title'));
                    window.projectReadTimes.push(performance.now());
                }
                return window.originalFetch(url, options);
            };
        """, reverse("main:get_projects_json"))
        # Each keystroke resets the timer: even after 500 ms overall, no request
        # should be sent until the last input has been idle for 300 ms.
        reads_before_idle = self.driver.execute_async_script("""
            const done = arguments[0];
            const field = document.getElementById('search-input');
            const queries = ['B', 'Be', 'Beta'];
            function typeNext(index) {
                field.value = queries[index];
                window.lastSearchInputAt = performance.now();
                field.dispatchEvent(new Event('input', {bubbles: true}));
                if (index < queries.length - 1) setTimeout(() => typeNext(index + 1), 150);
                else setTimeout(() => done([...window.projectReads]), 200);
            }
            typeNext(0);
        """)
        self.assertEqual(reads_before_idle, [])
        self.wait_for_titles([beta.title])
        self.assertEqual(self.driver.execute_script("return window.projectReads;"), ["Beta"])
        # Allow small differences in browser timer precision.
        self.assertGreaterEqual(self.driver.execute_script(
            "return window.projectReadTimes[0] - window.lastSearchInputAt;"
        ), 290)
        self.assert_same_document()

        # Starting IME composition cancels a pending search. Intermediate text
        # and Enter to confirm a character must not issue an AJAX request.
        reads_during_composition = self.driver.execute_async_script("""
            const done = arguments[0];
            window.projectReads = [];
            const field = document.getElementById('search-input');
            field.value = 'Alpha';
            field.dispatchEvent(new Event('input', {bubbles: true}));
            field.dispatchEvent(new CompositionEvent('compositionstart', {bubbles: true}));
            field.value = 'Al';
            field.dispatchEvent(new InputEvent('input', {bubbles: true, isComposing: true}));
            field.value = 'Alp';
            field.dispatchEvent(new Event('input', {bubbles: true}));
            document.getElementById('project-search-form').requestSubmit();
            setTimeout(() => done([...window.projectReads]), 400);
        """)
        self.assertEqual(reads_during_composition, [])
        self.driver.execute_script("""
            const field = document.getElementById('search-input');
            field.value = 'Alpha';
            field.dispatchEvent(new CompositionEvent('compositionend', {bubbles: true}));
            field.dispatchEvent(new InputEvent('input', {bubbles: true, isComposing: false}));
        """)
        self.wait_for_titles([alpha.title])
        self.assertEqual(self.driver.execute_script("return window.projectReads;"), ["Alpha"])
        self.assert_same_document()
        print("[PASS] Debounce dari input terakhir, satu request, dan komposisi IME tanpa reload", flush=True)

    def test_ajax_initial_query_enter_and_out_of_order_responses(self):
        Project.objects.all().delete()
        alpha = Project.objects.create(title="Alpha portfolio", description="Initial filter", tech_stack="Django")
        Project.objects.create(title="Beta dashboard", description="Older response", tech_stack="Python")
        gamma = Project.objects.create(title="Gamma app", description="Latest response", tech_stack="JavaScript")
        self.driver.get(self.live_server_url + reverse("main:show_projects") + "?title=Alpha")
        self.wait_for_titles([alpha.title])
        self.assertEqual(self.driver.find_element(By.ID, "search-input").get_attribute("value"), "Alpha")
        self.assertTrue(self.driver.find_element(By.ID, "reset-search").is_displayed())

        # Ignore abort deliberately and hold JSON bodies after the real HTTP
        # request. An old response must never replace a newer search result.
        self.driver.execute_script("""
            window.ajaxDocumentMarker = 'unchanged';
            window.originalFetch = window.fetch;
            window.projectReads = [];
            window.projectBodies = {};
            window.fetch = async (url, options) => {
                const parsed = new URL(url, location.href);
                if (parsed.pathname !== arguments[0]) return window.originalFetch(url, options);
                const query = parsed.searchParams.get('title');
                window.projectReads.push(query);
                const response = await window.originalFetch(url, {...options, signal: undefined});
                const payload = await response.json();
                return {
                    ok: response.ok,
                    status: response.status,
                    json: () => new Promise(resolve => {
                        window.projectBodies[query] = () => resolve(payload);
                    }),
                };
            };
            document.getElementById('project-search-form').addEventListener('submit', () => {
                window.readsAtEnter = [...window.projectReads];
            });
            document.getElementById('search-input').value = '';
        """, reverse("main:get_projects_json"))
        self.driver.find_element(By.ID, "search-input").send_keys("Beta", Keys.ENTER)
        self.assertEqual(self.driver.execute_script("return window.readsAtEnter;"), ["Beta"])
        self.wait.until(lambda driver: driver.execute_script("return typeof window.projectBodies.Beta === 'function';"))
        # Cross the debounce interval: Enter must cancel its pending request.
        reads = self.driver.execute_async_script("""
            const done = arguments[0];
            setTimeout(() => done(window.projectReads), 400);
        """)
        self.assertEqual(reads, ["Beta"])

        self.search("Gamma")
        self.wait.until(lambda driver: driver.execute_script("return typeof window.projectBodies.Gamma === 'function';"))
        self.driver.execute_script("window.projectBodies.Gamma();")
        self.wait_for_titles([gamma.title])
        self.driver.execute_async_script("""
            const done = arguments[0];
            window.projectBodies.Beta();
            setTimeout(done, 0);
        """)
        self.wait_for_titles([gamma.title])
        self.assertEqual(self.driver.execute_script("return window.projectReads;"), ["Beta", "Gamma"])
        self.assertEqual(self.driver.execute_script("return new URL(location.href).searchParams.get('title');"), "Gamma")
        self.assertFalse(self.driver.find_element(By.ID, "error").is_displayed())
        self.assert_same_document()
        print("[PASS] Query URL awal, Enter tanpa debounce ganda, dan respons pencarian terlambat", flush=True)

    def test_ajax_create_failures_preserve_input_and_active_filter(self):
        Project.objects.all().delete()
        alpha = Project.objects.create(title="Alpha portfolio", description="Visible filtered card", tech_stack="Django")
        self.open_page("login")
        self.submit_login("admin_test", self.admin_password)
        self.open_page("show_projects")
        self.wait_for_titles([alpha.title])
        self.search("Alpha")
        self.wait.until(EC.url_contains("?title=Alpha"))
        self.wait_for_titles([alpha.title])
        self.driver.execute_script("""
            window.ajaxDocumentMarker = 'unchanged';
            window.originalFetch = window.fetch;
            window.projectReads = [];
            window.fetch = (url, options) => {
                const parsed = new URL(url, location.href);
                if (parsed.pathname === arguments[0]) {
                    window.projectReads.push(parsed.searchParams.get('title'));
                }
                if (parsed.pathname === arguments[1] && options?.method === 'POST') {
                    if (window.postFailure === 'network') {
                        return Promise.reject(new TypeError('Simulated disconnected network'));
                    }
                    if (window.postFailure === 'html_error' || window.postFailure === 'html_success') {
                        return Promise.resolve(new Response('<html><body>Sign in again</body></html>', {
                            status: window.postFailure === 'html_error' ? 503 : 200,
                            headers: {'Content-Type': 'text/html'},
                        }));
                    }
                }
                return window.originalFetch(url, options);
            };
        """, reverse("main:get_projects_json"), reverse("main:create_project_ajax"))
        self.click(".project-add-button")
        self.fill_project("Beta outside active filter")
        for mode, message in (
            ("network", "Tidak dapat terhubung"),
            ("html_error", "503"),
            ("html_success", "Respons server tidak valid"),
        ):
            with self.subTest(response=mode):
                self.driver.execute_script("window.postFailure = arguments[0];", mode)
                self.submit_project()
                self.wait.until(EC.text_to_be_present_in_element((By.ID, "toast-message"), message))
                self.assertIn("Gagal", self.driver.find_element(By.ID, "toast-title").text)
                self.assertTrue(self.driver.find_element(By.ID, "project-form").is_displayed())
                self.assertEqual(self.driver.find_element(By.ID, "id_title").get_attribute("value"), "Beta outside active filter")
                self.assertEqual(self.driver.find_element(By.ID, "id_description").get_attribute("value"), "Data sementara untuk pengujian browser.")
                self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, '#project-form button[type="submit"]').is_enabled())
                self.assertTrue(self.driver.find_element(By.ID, "id_title").is_enabled())
                self.assertIsNone(self.driver.find_element(By.ID, "project-form").get_attribute("aria-busy"))
                self.assertEqual(Project.objects.count(), 1)
                self.assert_same_document()

        self.driver.execute_script("window.postFailure = null;")
        self.submit_project()
        self.wait.until(EC.invisibility_of_element_located((By.ID, "add-project-modal")))
        self.wait_for_titles([alpha.title])
        self.wait.until(lambda driver: driver.execute_script("return window.projectReads.length === 1;"))
        self.assertEqual(self.driver.execute_script("return window.projectReads;"), ["Alpha"])
        self.assertEqual(self.driver.find_element(By.ID, "search-input").get_attribute("value"), "Alpha")
        self.assertEqual(self.driver.execute_script("return new URL(location.href).searchParams.get('title');"), "Alpha")
        self.assertEqual(Project.objects.count(), 2)
        self.assertTrue(Project.objects.filter(title="Beta outside active filter").exists())
        self.assertEqual(self.driver.find_element(By.ID, "toast-title").text, "Berhasil")
        self.assertEqual(self.driver.find_element(By.ID, "id_title").get_attribute("value"), "")
        self.assert_same_document()
        print("[PASS] AJAX gagal jaringan/HTML mempertahankan input, sukses mempertahankan filter", flush=True)

    def test_ajax_create_validation_csrf_toast_and_existing_actions(self):
        Project.objects.all().delete()
        self.open_page("login")
        self.submit_login("admin_test", self.admin_password)
        self.open_page("show_projects")
        self.wait.until(EC.visibility_of_element_located((By.ID, "empty")))
        self.driver.execute_script("window.ajaxDocumentMarker = 'unchanged';")
        self.click(".project-add-button")
        self.wait.until(EC.visibility_of_element_located((By.ID, "project-form")))
        self.fill_project("   ")
        self.submit_project()
        self.wait.until(EC.visibility_of_element_located((By.ID, "id_title_error")))
        self.assertEqual(Project.objects.count(), 0)
        self.assertTrue(self.driver.find_element(By.ID, "project-form").is_displayed())
        self.assertTrue(self.driver.find_element(By.ID, "toast-component").is_displayed())
        self.assertIn("Gagal", self.driver.find_element(By.ID, "toast-title").text)
        self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, '#project-form [name="description"]').get_attribute("value"), "Data sementara untuk pengujian browser.")
        self.assert_same_document()

        title_field = self.driver.find_element(By.CSS_SELECTOR, '#project-form [name="title"]')
        title_field.clear()
        title_field.send_keys("Browser AJAX project")
        # An expired/mismatched CSRF token produces HTML 403; it still must show
        # feedback, preserve input, and re-enable the submit button.
        self.driver.execute_script("""
            const token = document.querySelector('#project-form [name=csrfmiddlewaretoken]');
            window.validProjectCsrf = token.value;
            token.value = 'invalid';
        """)
        self.submit_project()
        self.wait.until(EC.text_to_be_present_in_element((By.ID, "toast-message"), "403"))
        self.assertEqual(Project.objects.count(), 0)
        self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, '#project-form button[type="submit"]').is_enabled())
        self.driver.execute_script("document.querySelector('#project-form [name=csrfmiddlewaretoken]').value = window.validProjectCsrf;")

        # Delay the POST response to exercise duplicate submission protection.
        self.driver.execute_script("""
            window.originalFetch = window.fetch;
            window.projectPosts = 0;
            window.fetch = (url, options) => {
                if (options?.method === 'POST') {
                    window.projectPosts++;
                    return new Promise(resolve => {window.releaseProjectPost = () => resolve(window.originalFetch(url, options));});
                }
                return window.originalFetch(url, options);
            };
        """)
        self.submit_project()
        self.wait.until(lambda driver: driver.execute_script("return typeof window.releaseProjectPost === 'function';"))
        self.assertFalse(self.driver.find_element(By.CSS_SELECTOR, '#project-form button[type="submit"]').is_enabled())
        for field in self.driver.find_elements(By.CSS_SELECTOR, '#project-form input:not([type="hidden"]), #project-form textarea'):
            self.assertFalse(field.is_enabled())
        self.driver.execute_script("document.getElementById('project-form').dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}));")
        self.assertEqual(self.driver.execute_script("return window.projectPosts;"), 1)
        self.driver.execute_script("window.releaseProjectPost(); window.fetch = window.originalFetch;")
        self.wait_for_titles(["Browser AJAX project"])
        self.wait.until(EC.invisibility_of_element_located((By.ID, "add-project-modal")))
        self.assertEqual(Project.objects.count(), 1)
        self.assert_same_document()
        self.assertEqual(self.driver.find_element(By.ID, "toast-title").text, "Berhasil")
        self.assertEqual(title_field.get_attribute("value"), "")
        self.assertTrue(title_field.is_enabled())

        # Toast uses text rather than interpreting user-controlled HTML.
        self.driver.execute_script("window.showToast(arguments[0], arguments[1], 'error', 10000);", '<img src=x onerror="window.toastXss=true">', "<svg onload='window.toastXss=true'>message</svg>")
        self.assertFalse(self.driver.find_elements(By.CSS_SELECTOR, "#toast-component img, #toast-component svg"))
        self.assertIsNone(self.driver.execute_script("return window.toastXss;"))
        self.click("#toast-component .toast-close")

        project = Project.objects.get()
        self.click("#project-cards .star-form button")
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#project-cards .button-star[aria-pressed="true"]')))
        self.assertEqual(project.starred_by.count(), 1)
        self.click("#project-cards .project-title-link")
        self.wait.until(EC.url_to_be(self.live_server_url + reverse("main:project_detail", args=[project.pk])))
        self.assertIn(project.title, self.driver.find_element(By.TAG_NAME, "main").get_attribute("textContent"))
        self.open_page("show_projects")
        self.wait_for_titles([project.title])
        self.click(f'#project-cards [popovertarget="delete-project-{project.pk}"]')
        self.wait.until(EC.visibility_of_element_located((By.ID, f"delete-project-{project.pk}")))
        self.click(f'#delete-project-{project.pk} button[autofocus]')
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())
        self.click(f'#project-cards [popovertarget="delete-project-{project.pk}"]')
        self.click(f'#delete-project-{project.pk} button[type="submit"]')
        self.wait.until(EC.visibility_of_element_located((By.ID, "empty")))
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())
        print("[PASS] Modal AJAX, validasi/CSRF, toast, anti-duplikasi, star/detail/delete", flush=True)

    def test_ajax_editor_permissions_and_edit_navigation(self):
        Project.objects.all().delete()
        project = Project.objects.create(title="Editor browser project", description="Edit permissions", tech_stack="Django")
        editor = get_user_model().objects.create_user(username="editor_test", password=self.user_password)
        editor.groups.add(Group.objects.get_or_create(name="Editor")[0])
        self.open_page("login")
        self.submit_login(editor.username, self.user_password)
        self.open_page("show_projects")
        self.wait_for_titles([project.title])
        self.assertFalse(self.driver.find_elements(By.ID, "add-project-modal"))
        self.assertFalse(self.driver.find_elements(By.CSS_SELECTOR, "#project-cards [data-delete-project]"))
        self.click("#project-cards [data-edit-project]")
        self.wait.until(EC.url_to_be(self.live_server_url + reverse("main:update_project", args=[project.pk])))
        title = self.driver.find_element(By.NAME, "title")
        title.clear()
        title.send_keys("Edited through browser")
        self.submit_project()
        self.wait_for_titles(["Edited through browser"])
        project.refresh_from_db()
        self.assertEqual(project.title, "Edited through browser")
        self.assertEqual(Project.objects.count(), 1)
        print("[PASS] Kartu AJAX mempertahankan izin dan navigasi Editor", flush=True)

    def test_mobile_modal_focus_layout_and_carousel_proxies(self):
        Project.objects.all().delete()
        first = Project.objects.create(title="First mobile project", description="Mobile layout", tech_stack="Django")
        second = Project.objects.create(title="Second mobile project", description="Copied card actions", tech_stack="Python")
        self.open_page("login")
        self.submit_login("admin_test", self.admin_password)
        uses_cdp = self.driver.capabilities.get("browserName", "").lower() in ("chrome", "msedge")
        try:
            self.driver.set_window_size(390, 844)
            if uses_cdp:
                self.driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
                    "width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": False,
                })
            self.open_page("show_projects")
            self.wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "#project-cards > .showcase-card")) == 2)
            self.assertLessEqual(self.driver.execute_script("return window.innerWidth;"), 390)
            self.assertTrue(self.driver.execute_script("return document.documentElement.scrollWidth <= window.innerWidth + 1;"))
            self.click(".project-add-button")
            self.wait.until(lambda driver: driver.execute_script("return document.activeElement.id === 'id_title';"))
            self.assertTrue(self.driver.execute_script("return document.querySelector('main').inert;"))
            self.assertTrue(self.driver.execute_script("""
                const panel = document.querySelector('.project-form-modal__content');
                const rect = panel.getBoundingClientRect();
                return rect.left >= -1 && rect.right <= innerWidth + 1 &&
                    rect.top >= -1 && rect.bottom <= innerHeight + 1 &&
                    panel.scrollWidth <= panel.clientWidth + 1;
            """))

            self.driver.execute_script("window.showToast('Validasi proyek', arguments[0], 'error', 0);", "Periksa kolom formulir. " + "x" * 150)
            self.wait.until(lambda driver: driver.execute_script("return getComputedStyle(document.getElementById('toast-component')).opacity === '1';"))
            self.assertTrue(self.driver.execute_script("""
                const toast = document.getElementById('toast-component');
                const rect = toast.getBoundingClientRect();
                return rect.left >= 0 && rect.right <= innerWidth && rect.top >= 0 && rect.bottom <= innerHeight &&
                    toast.scrollWidth <= toast.clientWidth + 1 && document.documentElement.scrollWidth <= innerWidth + 1;
            """))
            screenshot = Path(tempfile.gettempdir()) / "tutorial05-mobile-modal.png"
            self.driver.save_screenshot(str(screenshot))
            print(f"[SCREENSHOT] {screenshot}", flush=True)
            self.click("#toast-component .toast-close")
            self.wait.until(lambda driver: driver.execute_script("return !document.getElementById('toast-component').matches(':popover-open');"))
            self.assertTrue(self.driver.execute_script("return document.getElementById('add-project-modal').matches(':popover-open');"))

            # Real Tab/Shift+Tab key events exercise both ends of the dialog.
            self.driver.execute_script("document.querySelector('#project-form button[type=submit]').focus();")
            self.driver.switch_to.active_element.send_keys(Keys.TAB)
            self.assertTrue(self.driver.execute_script("return document.activeElement.matches('.project-form-modal__close');"))
            ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.TAB).key_up(Keys.SHIFT).perform()
            self.assertTrue(self.driver.execute_script("return document.activeElement.matches('#project-form button[type=submit]');"))
            self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
            self.wait.until(EC.invisibility_of_element_located((By.ID, "add-project-modal")))
            self.wait.until(lambda driver: driver.execute_script("return document.activeElement.matches('.project-add-button');"))
            self.assertFalse(self.driver.execute_script("return document.querySelector('main').inert;"))
        finally:
            if uses_cdp:
                self.driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
            self.driver.set_window_size(1440, 1000)

        self.click(".project-add-button")
        self.wait.until(lambda driver: driver.execute_script("return document.activeElement.id === 'id_title';"))
        self.assertEqual(self.driver.execute_script("return document.querySelector('.project-form-modal__content').scrollTop;"), 0)
        screenshot = Path(tempfile.gettempdir()) / "tutorial05-desktop-modal.png"
        self.driver.save_screenshot(str(screenshot))
        print(f"[SCREENSHOT] {screenshot}", flush=True)
        self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
        self.wait.until(EC.invisibility_of_element_located((By.ID, "add-project-modal")))

        # Copied cards proxy to original actions. The second card catches index
        # drift caused by counting buttons inside removed delete dialogs.
        if not self.driver.execute_script("return matchMedia('(prefers-reduced-motion: reduce)').matches;"):
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "showcase-copy")))
            self.assertFalse(self.driver.find_elements(By.CSS_SELECTOR, ".showcase-copy [id], .showcase-copy form, .showcase-copy [popover], .showcase-copy input, .showcase-copy a, .showcase-copy button"))
            self.driver.find_element(By.CLASS_NAME, "showcase-viewport").send_keys(Keys.ARROW_RIGHT)
            self.click(f'.showcase-copy [data-project-id="{second.pk}"] .button-star')
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f'#project-cards [data-project-id="{second.pk}"] .button-star[aria-pressed="true"]')))
            self.assertEqual(first.starred_by.count(), 0)
            self.assertEqual(second.starred_by.count(), 1)
            self.driver.find_element(By.CLASS_NAME, "showcase-viewport").send_keys(Keys.ARROW_RIGHT)
            self.click(f'.showcase-copy [data-project-id="{second.pk}"] .button-danger')
            self.wait.until(EC.visibility_of_element_located((By.ID, f"delete-project-{second.pk}")))
            self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, f'#delete-project-{second.pk} [data-delete-title]').text, second.title)
            self.assertFalse(self.driver.find_element(By.ID, f"delete-project-{first.pk}").is_displayed())
            self.click(f'#delete-project-{second.pk} button[autofocus]')
            self.assertEqual(Project.objects.count(), 2)
        print("[PASS] Mobile modal/layout, focus trap/Escape, toast, dan aksi salinan carousel", flush=True)

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
