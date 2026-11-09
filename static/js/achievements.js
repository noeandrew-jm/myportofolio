(() => {
    'use strict';
    const app = document.getElementById('achievements-app');
    if (!app) return;
    const byId = id => document.getElementById(id);
    const searchForm = byId('achievement-search-form');
    const searchInput = searchForm.elements.title;
    const reset = byId('reset-achievement-search');
    const grid = byId('achievement-grid');
    const cards = byId('achievement-cards');
    const modal = byId('achievement-modal');
    const form = byId('achievement-form');
    const deleteModal = byId('delete-achievement-modal');
    const deleteForm = byId('delete-achievement-form');
    const fields = ['title', 'description', 'award', 'thumbnail', 'display_order'];
    const placeholder = '00000000-0000-0000-0000-000000000000';
    const api = window.PortfolioAPI;
    const pending = new Set();
    let records = new Map();
    let controller, timer, composing = false, submitting = false, deleting = false;
    const route = (name, id) => app.dataset[name].replace(placeholder, id);
    const toast = (title, message, type) => window.showToast?.(title, message, type, 5000);
    const element = (tag, className, text) => {
        const node = document.createElement(tag);
        node.className = className;
        // API strings include legacy database values: never parse them as HTML.
        if (text !== undefined) node.textContent = text;
        return node;
    };
    const button = (className, text) => {
        const node = element('button', className, text);
        node.type = 'button';
        return node;
    };
    function thumbnailUrl(value) {
        if (typeof value !== 'string' || !value || /[\\\u0000-\u001f\u007f]/.test(value)) return '';
        try {
            const local = value.startsWith('/static/');
            const url = local ? new URL(value, location.origin) : new URL(value);
            if (local) {
                const decoded = decodeURIComponent(url.pathname);
                return url.origin === location.origin && decoded.startsWith('/static/')
                    && !decoded.split('/').includes('..') && !decoded.includes('\\') ? url.href : '';
            }
            return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
        } catch { return ''; }
    }
    function setState(state) {
        for (const name of ['loading', 'error', 'empty', 'grid']) byId(`achievement-${name}`).hidden = name !== state;
        grid.setAttribute('aria-busy', String(state === 'loading'));
    }
    function setBusy(id, busy) {
        cards.querySelectorAll('[data-achievement-id]').forEach(card => {
            if (card.dataset.achievementId === id) card.querySelectorAll('button').forEach(control => { control.disabled = busy; });
        });
    }
    function buildCard(record) {
        if (!api.hasResourceId(record)) throw new Error('Data prestasi tidak valid.');
        const card = element('article', 'showcase-card');
        card.dataset.achievementId = record.id;
        const title = element('h2', 'showcase-title');
        const link = element('a', 'project-title-link', record.title ?? '');
        link.href = route('detailUrl', record.id);
        title.append(link);
        card.append(title);
        const src = thumbnailUrl(record.thumbnail);
        if (src) {
            const image = element('img', 'showcase-image');
            image.src = src; image.alt = String(record.title ?? ''); image.loading = 'lazy';
            card.append(image);
        } else {
            const initial = element('span', 'showcase-monogram', Array.from(String(record.title ?? ''))[0] || '?');
            initial.setAttribute('aria-hidden', 'true'); card.append(initial);
        }
        card.append(element('p', 'showcase-description', record.description ?? ''));
        if (record.award) {
            const caption = element('div', 'showcase-caption');
            caption.append(element('p', 'content-item-label', record.award)); card.append(caption);
        }
        const actions = element('div', 'project-card-actions');
        if (app.dataset.canEdit === 'true') {
            const edit = element('a', 'button button-secondary', 'Edit Prestasi');
            edit.href = route('editUrl', record.id); edit.dataset.editAchievement = record.id;
            actions.append(edit);
        }
        const count = Number.isSafeInteger(record.star_count) && record.star_count >= 0 ? record.star_count : 0;
        const counter = element('span', 'star-count', String(count));
        counter.setAttribute('aria-label', `${count} star`);
        if (app.dataset.authenticated === 'true') {
            const starForm = element('form', 'star-form');
            starForm.dataset.starAchievement = record.id;
            const star = button(`button button-star${record.is_starred ? ' is-starred' : ''}`, `★ ${record.is_starred ? 'Unstar' : 'Star'} `);
            star.type = 'submit'; star.setAttribute('aria-pressed', String(record.is_starred === true));
            star.setAttribute('aria-label', `${record.is_starred ? 'Batalkan star untuk' : 'Beri star untuk'} ${record.title}`);
            star.append(counter); starForm.append(star); actions.append(starForm);
        } else {
            const login = element('a', 'button button-star', '★ Login untuk star ');
            login.href = `${app.dataset.loginUrl}?next=${encodeURIComponent(location.pathname + location.search)}`;
            login.append(counter); actions.append(login);
        }
        if (app.dataset.canCreate === 'true') {
            const remove = button('button button-danger', 'Hapus Prestasi');
            remove.dataset.deleteAchievement = record.id; actions.append(remove);
        }
        actions.querySelectorAll('button').forEach(control => { control.disabled = pending.has(record.id); });
        card.append(actions);
        return card;
    }
    async function load() {
        clearTimeout(timer); controller?.abort();
        const current = new AbortController(); controller = current;
        const query = searchInput.value.trim();
        const page = new URL(location.href);
        if (query) page.searchParams.set('title', query); else page.searchParams.delete('title');
        history.replaceState(null, '', page); reset.hidden = !query;
        setState('loading');
        try {
            const url = new URL(app.dataset.endpoint, location.origin);
            if (query) url.searchParams.set('title', query);
            const response = await fetch(url, {credentials: 'same-origin', cache: 'no-store', headers: {Accept: 'application/json'}, signal: current.signal});
            if (!response.ok) throw new Error(`Gagal memuat prestasi (status ${response.status}). Silakan coba lagi.`);
            const data = await response.json();
            // Abort saves network work; the identity check also rejects an old
            // response that finished parsing just as a newer search started.
            if (current.signal.aborted || controller !== current) return;
            if (!Array.isArray(data)) throw new Error('Data prestasi dari server tidak valid.');
            const fragment = document.createDocumentFragment();
            data.forEach(record => fragment.append(buildCard(record)));
            records = new Map(data.map(record => [record.id, record]));
            cards.replaceChildren(fragment);
            byId('achievement-empty-message').textContent = query ? `Tidak ada prestasi yang cocok dengan pencarian "${query}".` : 'Belum ada prestasi yang ditambahkan.';
            setState(data.length ? 'grid' : 'empty');
            grid.dispatchEvent(new Event('showcase:refresh'));
        } catch (error) {
            if (current.signal.aborted || controller !== current) return;
            byId('achievement-load-error').textContent = error.message || 'Gagal memuat prestasi. Periksa koneksi Anda.';
            setState('error');
        }
    }
    function schedule() {
        // Invalidate old results when typing starts, before the debounce fires.
        clearTimeout(timer); controller?.abort(); reset.hidden = !searchInput.value.trim();
        if (!composing) timer = setTimeout(load, 300);
    }
    searchInput.addEventListener('input', schedule);
    searchInput.addEventListener('compositionstart', () => { composing = true; clearTimeout(timer); controller?.abort(); });
    searchInput.addEventListener('compositionend', () => { composing = false; schedule(); });
    searchForm.addEventListener('submit', event => { event.preventDefault(); if (!composing) load(); });
    reset.addEventListener('click', () => { searchInput.value = ''; searchInput.focus(); load(); });
    byId('retry-achievements').addEventListener('click', load);

    function write(url, method, payload, expectedStatus = 200) {
        return api.write(url, {
            method, payload, expectedStatus,
            csrfToken: byId('achievement-csrf-token')?.querySelector('input').value || '',
            messages: {
                network: 'Tidak dapat terhubung ke server. Periksa daftar prestasi sebelum mencoba kembali.',
                invalid: 'Respons server tidak valid. Periksa daftar prestasi sebelum mencoba kembali.',
                http: status => `Permintaan gagal (status ${status}).`,
            },
        });
    }
    cards.addEventListener('submit', async event => {
        const starForm = event.target.closest('[data-star-achievement]');
        if (!starForm) return;
        event.preventDefault();
        const id = starForm.dataset.starAchievement;
        if (pending.has(id)) return;
        pending.add(id); setBusy(id, true);
        try {
            await write(route('starUrl', id), 'POST');
            toast('Berhasil', 'Star berhasil diperbarui.', 'success'); await load();
        } catch (error) { toast('Gagal memperbarui star', error.message, 'error'); }
        finally { pending.delete(id); setBusy(id, false); }
    });
    function clearErrors() {
        form.querySelectorAll('[data-field-errors], #achievement-form-errors').forEach(node => { node.textContent = ''; node.hidden = true; });
        form.querySelectorAll('[aria-invalid]').forEach(node => node.removeAttribute('aria-invalid'));
    }
    function openForm(record, opener) {
        if (submitting || deleting || !modal?.showPopover) return false;
        clearErrors(); form.reset(); form.dataset.achievementId = record?.id || '';
        if (record) fields.forEach(name => { form.elements.namedItem(name).value = record[name] ?? ''; });
        byId('achievement-modal-title').textContent = record ? 'Edit Prestasi' : 'Tambah Prestasi';
        modal.returnFocus = opener; modal.showPopover(); return true;
    }
    app.querySelector('[data-create-achievement]')?.addEventListener('click', event => {
        if (submitting || deleting || openForm(null, event.currentTarget)) event.preventDefault();
    });
    cards.addEventListener('click', event => {
        const edit = event.target.closest('[data-edit-achievement]');
        const remove = event.target.closest('[data-delete-achievement]');
        const id = edit?.dataset.editAchievement || remove?.dataset.deleteAchievement;
        if (!id) return;
        if (pending.has(id) || submitting || deleting) { event.preventDefault(); return; }
        const record = records.get(id);
        if (!record) return;
        if (edit && openForm(record, edit)) event.preventDefault();
        if (remove) {
            if (!deleteModal?.showPopover) { location.assign(route('detailUrl', id)); return; }
            deleteForm.dataset.achievementId = id;
            byId('delete-achievement-name').textContent = record.title;
            byId('achievement-delete-error').hidden = true;
            deleteModal.returnFocus = remove; deleteModal.showPopover();
        }
    });
    form?.addEventListener('submit', async event => {
        event.preventDefault(); if (submitting) return;
        submitting = true; clearErrors();
        const id = form.dataset.achievementId;
        const payload = Object.fromEntries(fields.map(name => [name, form.elements.namedItem(name).value]));
        const controls = [...form.querySelectorAll('input:not([type="hidden"]), textarea, select, button')];
        controls.forEach(control => { control.disabled = true; }); form.setAttribute('aria-busy', 'true');
        try {
            await write(id ? route('apiDetailUrl', id) : app.dataset.endpoint, id ? 'PATCH' : 'POST', payload, id ? 200 : 201);
            form.reset(); modal.hidePopover();
            toast('Berhasil', id ? 'Prestasi berhasil diperbarui.' : 'Prestasi baru berhasil ditambahkan.', 'success'); await load();
        } catch (error) {
            controls.forEach(control => { control.disabled = false; });
            for (const [name, errors] of Object.entries(error.payload || {})) {
                const control = form.elements.namedItem(name);
                const container = control && byId(`${control.id}_error`);
                if (!container) continue;
                container.textContent = (Array.isArray(errors) ? errors : [errors]).filter(value => typeof value === 'string').join(' ');
                container.hidden = false; control.setAttribute('aria-invalid', 'true');
            }
            byId('achievement-form-errors').textContent = error.message;
            byId('achievement-form-errors').hidden = false;
            form.querySelector('[aria-invalid="true"]')?.focus();
            toast('Gagal menyimpan prestasi', error.message, 'error');
        } finally {
            submitting = false; controls.forEach(control => { control.disabled = false; }); form.removeAttribute('aria-busy');
        }
    });
    deleteForm?.addEventListener('submit', async event => {
        event.preventDefault();
        const id = deleteForm.dataset.achievementId;
        if (deleting || !api.hasResourceId({id}) || pending.has(id)) return;
        deleting = true; pending.add(id); setBusy(id, true);
        const submit = deleteForm.querySelector('[type="submit"]'); submit.disabled = true;
        byId('achievement-delete-error').hidden = true;
        try {
            await write(route('apiDetailUrl', id), 'DELETE'); deleteModal.hidePopover();
            toast('Berhasil', 'Prestasi berhasil dihapus.', 'success'); await load();
        } catch (error) {
            byId('achievement-delete-error').textContent = error.message; byId('achievement-delete-error').hidden = false;
            toast('Gagal menghapus prestasi', error.message, 'error');
        } finally { deleting = false; pending.delete(id); setBusy(id, false); submit.disabled = false; }
    });
    form?.querySelectorAll('[data-field-errors]').forEach(container => {
        const control = form.elements.namedItem(container.dataset.fieldErrors);
        control.setAttribute('aria-describedby', [control.getAttribute('aria-describedby'), container.id].filter(Boolean).join(' '));
    });
    // Popovers keep the existing visual style; trap focus and suspend the page
    // while each dialog is open, restoring the originating control afterward.
    [modal, deleteModal].filter(Boolean).forEach(dialog => {
        const previous = new Map();
        dialog.addEventListener('toggle', event => {
            const open = event.newState === 'open';
            document.documentElement.classList.toggle('project-modal-open', open);
            if (open) {
                document.querySelectorAll('body > header, body > main, body > footer, body > .site-messages').forEach(node => { previous.set(node, node.inert); node.inert = true; });
                (dialog === modal ? form.elements.title : deleteForm.querySelector('[autofocus]')).focus({preventScroll: true});
                dialog.querySelector('[class$="modal__content"]').scrollTop = 0;
            } else {
                previous.forEach((inert, node) => { node.inert = inert; }); previous.clear();
                if (dialog.returnFocus?.isConnected) dialog.returnFocus.focus({preventScroll: true});
            }
        });
        dialog.addEventListener('keydown', event => {
            if (event.key !== 'Tab') return;
            const controls = [...dialog.querySelectorAll('button, input, textarea, select, a[href]')].filter(node => !node.disabled && node.tabIndex >= 0 && node.getClientRects().length);
            const first = controls[0], last = controls[controls.length - 1];
            if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
            else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
        });
    });
    load();
})();
