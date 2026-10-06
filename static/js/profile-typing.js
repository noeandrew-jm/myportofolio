(() => {
    'use strict';

    const target = document.getElementById('profile-role-typing');
    if (!target || typeof window.Typed !== 'function') return;

    const roles = [
        'a Full Stack Developer',
        'Well - known Performer',
        'An Experienced MC',
        'Leader',
    ];
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let animation;

    const start = () => {
        animation?.destroy();
        animation = undefined;
        target.textContent = roles[0];
        if (reducedMotion.matches) return;

        target.textContent = '';
        animation = new window.Typed(target, {
            strings: roles,
            typeSpeed: 65,
            backSpeed: 35,
            startDelay: 250,
            backDelay: 1400,
            smartBackspace: false,
            shuffle: false,
            loop: true,
            showCursor: true,
            cursorChar: '|',
            autoInsertCss: false,
            contentType: null,
        });
    };

    start();
    reducedMotion.addEventListener('change', start);
})();
