(() => {
    'use strict';

    const app = document.getElementById('projects-app');
    if (!app) return;

    const searchForm = document.getElementById('project-search-form');
    const searchInput = document.getElementById('search-input');
    const resetButton = document.getElementById('reset-search');
    const grid = document.getElementById('grid');
    const cards = document.getElementById('project-cards');
    const cardTemplate = document.getElementById('project-card-template');
    const projectForm = document.getElementById('project-form');
    const modal = document.getElementById('add-project-modal');
    const placeholderId = '00000000-0000-0000-0000-000000000000';
    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    let projectsController;
    let searchTimer;
    let submitting = false;

    function displayPageSection(state) {
        for (const name of ['loading', 'error', 'empty', 'grid']) {
            document.getElementById(name).classList.toggle('hide', name !== state);
        }
        grid.setAttribute('aria-busy', String(state === 'loading'));
    }

    // textContent protects text/attributes; URL schemes need a separate allowlist,
    // including for legacy records that did not pass through today's ModelForm.
    function safeWebUrl(value) {
        if (!value) return null;
        try {
            const url = new URL(value);
            return ['http:', 'https:'].includes(url.protocol) ? url.href : null;
        } catch {
            return null;
        }
    }

    function buildProjectCardElement(item) {
        if (!uuidPattern.test(item.pk) || !item.fields) throw new Error('Invalid project data');
        const project = item.fields;
        const article = cardTemplate.content.firstElementChild.cloneNode(true);
        const route = name => app.dataset[name].replace(placeholderId, item.pk);
        const title = String(project.title ?? '');
        article.dataset.projectId = item.pk;
        const titleLink = article.querySelector('.project-title-link');
        titleLink.textContent = title;
        titleLink.href = route('detailUrl');
        article.querySelector('.showcase-description').textContent = project.description ?? '';
        article.querySelector('.content-item-label').textContent = project.tech_stack ?? '';

        const monogram = article.querySelector('.showcase-monogram');
        monogram.textContent = Array.from(title)[0] || '?';
        const imageUrl = safeWebUrl(project.project_image_url);
        if (imageUrl) {
            const image = document.createElement('img');
            image.src = imageUrl;
            image.alt = `Gambar ${title}`;
            image.className = 'showcase-image';
            image.loading = 'lazy';
            monogram.replaceWith(image);
        }
        const projectLink = article.querySelector('[data-project-link]');
        const projectUrl = safeWebUrl(project.project_url);
        if (projectUrl) projectLink.href = projectUrl;
        else projectLink.remove();

        const editLink = article.querySelector('[data-edit-project]');
        if (editLink) {
            editLink.href = route('editUrl');
            editLink.setAttribute('aria-label', `Edit ${title}`);
        }
        const starButton = article.querySelector('.button-star');
        const count = Number.isSafeInteger(project.star_count) && project.star_count >= 0 ? project.star_count : 0;
        const countElement = article.querySelector('.star-count');
        countElement.textContent = String(count);
        countElement.setAttribute('aria-label', `${count} star`);
        const next = window.location.pathname + window.location.search;
        const starForm = article.querySelector('.star-form');
        if (starForm) {
            const starred = project.is_starred === true;
            starForm.action = route('starUrl');
            starForm.elements.next.value = next;
            starButton.classList.toggle('is-starred', starred);
            starButton.setAttribute('aria-pressed', String(starred));
            starButton.title = `${starred ? 'Batalkan star untuk' : 'Beri star untuk'} ${title}`;
            starButton.querySelector('[data-star-label]').textContent = starred ? 'Unstar' : 'Star';
        } else {
            starButton.href = `${app.dataset.loginUrl}?next=${encodeURIComponent(next)}`;
            starButton.title = `Login untuk memberi star pada ${title}`;
        }

        const deleteButton = article.querySelector('[data-delete-project]');
        if (deleteButton) {
            const deleteModal = article.querySelector('.project-delete-modal');
            const modalId = `delete-project-${item.pk}`;
            deleteModal.id = modalId;
            deleteModal.querySelector('h2').id = `${modalId}-title`;
            deleteModal.setAttribute('aria-labelledby', `${modalId}-title`);
            deleteButton.setAttribute('popovertarget', modalId);
            deleteButton.setAttribute('aria-label', `Hapus ${title}`);
            deleteModal.querySelectorAll('[popovertargetaction]').forEach(button => {
                button.setAttribute('popovertarget', modalId);
            });
            deleteModal.querySelector('[data-delete-title]').textContent = title;
            deleteModal.querySelector('form').action = route('deleteUrl');
        }
        return article;
    }

    function updateSearchUrl(query) {
        const url = new URL(window.location.href);
        if (query) url.searchParams.set('title', query);
        else url.searchParams.delete('title');
        window.history.replaceState(null, '', url);
        resetButton.classList.toggle('hide', !query);
    }

    async function fetchProjects(query = '') {
        projectsController?.abort();
        const controller = new AbortController();
        projectsController = controller;
        updateSearchUrl(query);
        displayPageSection('loading');
        try {
            const url = new URL(app.dataset.projectsEndpoint, window.location.origin);
            if (query) url.searchParams.set('title', query);
            const response = await fetch(url, {
                headers: { Accept: 'application/json' },
                credentials: 'same-origin',
                cache: 'no-store',
                signal: controller.signal,
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const projects = await response.json();
            if (controller.signal.aborted || projectsController !== controller) return;
            if (!Array.isArray(projects)) throw new Error('Invalid project list');
            // Build the whole fragment before replacing the current cards.
            const fragment = document.createDocumentFragment();
            projects.forEach(project => fragment.append(buildProjectCardElement(project)));
            cards.replaceChildren(fragment);
            displayPageSection(projects.length ? 'grid' : 'empty');
            grid.dispatchEvent(new Event('showcase:refresh'));
        } catch (error) {
            if (controller.signal.aborted || projectsController !== controller) return;
            displayPageSection('error');
        }
    }

    function searchProjects() {
        clearTimeout(searchTimer);
        return fetchProjects(searchInput.value.trim());
    }

    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimer);
        // Invalidate an older result immediately, even during the debounce delay.
        projectsController?.abort();
        resetButton.classList.toggle('hide', !searchInput.value);
        searchTimer = setTimeout(searchProjects, 300);
    });
    searchForm.addEventListener('submit', event => {
        event.preventDefault();
        searchProjects();
    });
    resetButton.addEventListener('click', () => {
        searchInput.value = '';
        searchInput.focus();
        searchProjects();
    });
    document.getElementById('retry-projects').addEventListener('click', searchProjects);

    function clearFormErrors() {
        projectForm.querySelectorAll('[data-field-errors], #project-form-errors').forEach(element => {
            element.textContent = '';
            element.hidden = true;
        });
        projectForm.querySelectorAll('[aria-invalid]').forEach(field => field.removeAttribute('aria-invalid'));
    }

    function showFormErrors(errors) {
        const messages = [];
        for (const [name, fieldErrors] of Object.entries(errors || {})) {
            const text = fieldErrors.map(error => String(error.message)).join(' ');
            messages.push(text);
            const field = projectForm.elements.namedItem(name);
            const container = field ? document.getElementById(`${field.id}_error`) : document.getElementById('project-form-errors');
            if (container) {
                container.textContent = text;
                container.hidden = false;
            }
            if (field) field.setAttribute('aria-invalid', 'true');
        }
        projectForm.querySelector('[aria-invalid="true"]')?.focus();
        return messages.join(' ');
    }

    async function addProject(event) {
        event.preventDefault();
        if (submitting) return;
        submitting = true;
        clearFormErrors();
        const formData = new FormData(projectForm);
        const editableFields = [...projectForm.querySelectorAll('input:not([type="hidden"]), textarea, select')]
            .filter(field => !field.disabled);
        editableFields.forEach(field => { field.disabled = true; });
        const submitButton = projectForm.querySelector('button[type="submit"]');
        const originalLabel = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = 'Menyimpan...';
        projectForm.setAttribute('aria-busy', 'true');
        try {
            const response = await fetch(app.dataset.createEndpoint, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    Accept: 'application/json',
                    'X-CSRFToken': projectForm.elements.csrfmiddlewaretoken.value,
                },
                body: formData,
            });
            const payload = await response.json().catch(() => null);
            const result = payload && typeof payload === 'object' ? payload : {};
            editableFields.forEach(field => { field.disabled = false; });
            if (response.ok) {
                // An HTML login page or intermediary response may still use 200.
                // Only the create endpoint's confirmed result can clear input.
                if (response.status !== 201 || !uuidPattern.test(result.pk)) {
                    window.showToast('Gagal menambahkan proyek', 'Respons server tidak valid. Periksa daftar proyek sebelum mencoba kembali.', 'error', 5000);
                    return;
                }
                projectForm.reset();
                if (modal.matches(':popover-open')) modal.hidePopover();
                window.showToast('Berhasil', 'Proyek baru berhasil ditambahkan!', 'success');
                await searchProjects();
            } else {
                const message = result.errors ? showFormErrors(result.errors) : result.message;
                window.showToast('Gagal menambahkan proyek', message || `Terjadi kesalahan (status ${response.status}). Silakan coba lagi.`, 'error', 5000);
            }
        } catch {
            window.showToast('Gagal menambahkan proyek', 'Tidak dapat terhubung ke server. Periksa daftar proyek sebelum mencoba kembali.', 'error', 5000);
        } finally {
            submitting = false;
            editableFields.forEach(field => { field.disabled = false; });
            submitButton.disabled = false;
            submitButton.textContent = originalLabel;
            projectForm.removeAttribute('aria-busy');
        }
    }

    if (projectForm) {
        projectForm.addEventListener('submit', addProject);
        projectForm.querySelectorAll('[data-field-errors]').forEach(container => {
            const field = projectForm.elements.namedItem(container.dataset.fieldErrors);
            if (field) {
                const descriptions = [field.getAttribute('aria-describedby'), container.id].filter(Boolean);
                field.setAttribute('aria-describedby', descriptions.join(' '));
            }
        });
        const backgroundState = new Map();
        modal.addEventListener('toggle', event => {
            const open = event.newState === 'open';
            document.documentElement.classList.toggle('project-modal-open', open);
            if (open) {
                document.querySelectorAll('body > header, body > main, body > footer, body > .site-messages').forEach(element => {
                    backgroundState.set(element, element.inert);
                    element.inert = true;
                });
                projectForm.elements.title.focus({ preventScroll: true });
                modal.querySelector('.project-form-modal__content').scrollTop = 0;
            } else {
                backgroundState.forEach((inert, element) => { element.inert = inert; });
                backgroundState.clear();
                app.querySelector('.project-add-button').focus();
            }
        });
        modal.addEventListener('keydown', event => {
            if (event.key !== 'Tab') return;
            const focusable = [...modal.querySelectorAll('button, input, textarea, a[href]')]
                .filter(element => !element.disabled && element.tabIndex >= 0 && element.getClientRects().length);
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        });
    }

    fetchProjects(searchInput.value.trim());
})();
