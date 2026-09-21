// Native cards remain readable and horizontally scrollable without JavaScript.
// Repeated visual groups make the leftward movement seamless even for one item.
document.querySelectorAll('[data-showcase]').forEach(section => {
    const viewport = section.querySelector('.showcase-viewport');
    const track = section.querySelector('.showcase-track');
    const original = section.querySelector('.showcase-group');
    const cards = [...original.querySelectorAll('.showcase-card')];
    if (!cards.length) {
        section.classList.add('showcase--empty');
        viewport.removeAttribute('tabindex');
        return;
    }
    const preference = matchMedia('(prefers-reduced-motion: reduce)');
    const actions = [...original.querySelectorAll('a, button')].filter(el => !el.closest('[popover]'));
    let groupWidth = 0;
    let position = 0;
    let lastTime = 0;
    let touching = false;
    let keyboardFocus = false;
    let visible = true;

    function copyGroup() {
        const copy = original.cloneNode(true);
        copy.classList.add('showcase-copy');
        copy.setAttribute('aria-hidden', 'true');
        // Only original cards own dialogs, forms, IDs and keyboard destinations.
        copy.querySelectorAll('[popover], form').forEach(el => el.remove());
        copy.querySelectorAll('[id]').forEach(el => el.removeAttribute('id'));
        const copyActions = [...copy.querySelectorAll('a, button')];
        copyActions.forEach((el, index) => {
            const visual = document.createElement('span');
            visual.className = el.className;
            visual.innerHTML = el.innerHTML;
            visual.dataset.copyAction = String(index);
            el.replaceWith(visual);
        });
        copy.querySelectorAll('[tabindex]').forEach(el => el.removeAttribute('tabindex'));
        copy.addEventListener('click', event => {
            const action = event.target.closest('[data-copy-action]');
            if (action) actions[Number(action.dataset.copyAction)]?.click();
        });
        return copy;
    }

    function measure() {
        track.querySelectorAll('.showcase-copy').forEach(el => el.remove());
        groupWidth = original.getBoundingClientRect().width;
        if (!groupWidth || preference.matches) {
            position = viewport.scrollLeft = 0;
            return;
        }
        const count = Math.ceil(viewport.clientWidth / groupWidth) + 1;
        for (let i = 0; i < count; i++) track.append(copyGroup());
        position = viewport.scrollLeft % groupWidth;
        viewport.scrollLeft = position;
    }

    function paused() {
        return preference.matches || !visible || document.hidden || touching ||
            viewport.matches(':hover') || keyboardFocus || !!section.querySelector(':popover-open');
    }

    function tick(time) {
        const delta = lastTime ? Math.min(time - lastTime, 64) : 0;
        lastTime = time;
        if (!paused() && groupWidth) {
            // Keep subpixel progress separately: scrollLeft can round on some browsers.
            position = (position + delta * 0.028) % groupWidth;
            viewport.scrollLeft = position;
        } else {
            position = viewport.scrollLeft;
        }
        requestAnimationFrame(tick);
    }

    viewport.addEventListener('pointerdown', () => { touching = true; keyboardFocus = false; });
    window.addEventListener('pointerup', () => { touching = false; position = viewport.scrollLeft; });
    window.addEventListener('pointercancel', () => { touching = false; });
    viewport.addEventListener('wheel', () => { position = viewport.scrollLeft; }, { passive: true });
    section.addEventListener('keydown', event => {
        keyboardFocus = true;
        if (event.target === viewport && ['ArrowLeft', 'ArrowRight'].includes(event.key)) {
            event.preventDefault();
            viewport.scrollBy({ left: (event.key === 'ArrowLeft' ? -1 : 1) * (cards[0].offsetWidth + 26), behavior: 'auto' });
            position = viewport.scrollLeft;
        }
    });
    section.addEventListener('focusin', event => {
        if (event.target.matches(':focus-visible')) keyboardFocus = true;
    });
    section.addEventListener('focusout', event => {
        if (!section.contains(event.relatedTarget)) keyboardFocus = false;
    });
    const resize = new ResizeObserver(measure);
    resize.observe(viewport);
    const observer = new IntersectionObserver(entries => { visible = entries[0].isIntersecting; });
    observer.observe(section);
    preference.addEventListener('change', measure);
    measure();
    requestAnimationFrame(tick);
});
