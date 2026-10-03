/* Native canvas adaptation of the CursorDotTrail behavior supplied by the owner.
 * Reference: https://framer.com/m/CursorDotTrail-ZDqFAE.js@iLyzK205nNCuHNDP5Nsc
 * Uses local assets; Framer's editor/runtime is not needed on Django pages.
 */
(() => {
    'use strict';

    if (document.querySelector('.cursor-trail')) return;
    const pointerPreference = window.matchMedia('(hover: hover) and (pointer: fine)');
    const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const settings = {
        size: 12,
        hoverSize: 40,
        borderWidth: 2,
        spring: 0.15,
        friction: 0.5,
        trailDuration: 200,
        transitionSpeed: 0.15,
        color: '255, 255, 255',
        invertedColor: '8, 8, 8',
    };
    const canvas = document.createElement('canvas');
    canvas.className = 'cursor-trail';
    canvas.setAttribute('aria-hidden', 'true');
    canvas.hidden = true;
    const context = canvas.getContext('2d');
    if (!context) return;
    document.body.append(canvas);

    let enabled = false;
    let frame = 0;
    let lastTime = 0;
    let width = 0;
    let height = 0;
    let points = [];
    const target = { x: 0, y: 0 };
    const ball = { x: 0, y: 0 };
    const velocity = { x: 0, y: 0 };
    const visual = { radius: settings.size / 2, fill: 1, stroke: 0, underline: 0, lineOpacity: 0 };

    function hide() {
        window.cancelAnimationFrame(frame);
        frame = 0;
        canvas.hidden = true;
        points = [];
        velocity.x = velocity.y = 0;
        context.clearRect(0, 0, width, height);
    }

    function resize() {
        hide();
        if (!enabled) return;
        width = window.innerWidth;
        height = window.innerHeight;
        const ratio = Math.min(2, Math.max(1, window.devicePixelRatio || 1));
        canvas.width = Math.round(width * ratio);
        canvas.height = Math.round(height * ratio);
        context.setTransform(ratio, 0, 0, ratio, 0, 0);
    }

    function updatePreference() {
        enabled = pointerPreference.matches && !motionPreference.matches;
        resize();
    }

    function wake() {
        if (enabled && !canvas.hidden && !frame && !document.hidden) {
            lastTime = performance.now();
            frame = window.requestAnimationFrame(draw);
        }
    }

    function modeElement(element, mode) {
        return element?.closest(`[data-cursor-trail~="${mode}"], [aria-label~="trail{${mode}}"], [data-framer-name~="trail{${mode}}"]`);
    }

    function draw(now) {
        frame = 0;
        if (!enabled || canvas.hidden || document.hidden) return;
        const element = document.elementFromPoint(target.x, target.y);
        if (modeElement(element, 'hide')) {
            hide();
            return;
        }
        const color = modeElement(element, 'invert-color') ? settings.invertedColor : settings.color;
        const rgba = opacity => `rgba(${color}, ${opacity})`;
        const workCard = element?.closest('[data-cursor-trail~="work-card"], [aria-label~="work-card"]');
        const link = workCard ? null : modeElement(element, 'link');
        const linkRect = link?.getBoundingClientRect();
        const ring = !workCard && !link && element?.closest('a, button, [role~="button"]');
        const hideDot = element?.closest('[data-cursor-trail~="hide-dot"], [aria-label~="button"]');
        const desired = {
            radius: (ring || link ? settings.hoverSize : settings.size) / 2,
            fill: ring || link ? 0 : 1,
            stroke: ring ? 1 : 0,
            underline: linkRect?.width || 0,
            lineOpacity: link ? 1 : 0,
        };
        const destination = linkRect
            ? { x: linkRect.left + linkRect.width / 2, y: linkRect.bottom + 1 }
            : target;
        const step = Math.max(0.25, Math.min(2, (now - lastTime) / (1000 / 60)));
        lastTime = now;
        const previousX = ball.x;
        const previousY = ball.y;
        const damping = Math.pow(settings.friction, step);
        velocity.x = (velocity.x + (destination.x - ball.x) * settings.spring * step) * damping;
        velocity.y = (velocity.y + (destination.y - ball.y) * settings.spring * step) * damping;
        ball.x += velocity.x * step;
        ball.y += velocity.y * step;
        const moving = Math.hypot(destination.x - ball.x, destination.y - ball.y)
            + Math.hypot(velocity.x, velocity.y) > 0.15;
        if (!moving) {
            ball.x = destination.x;
            ball.y = destination.y;
            velocity.x = velocity.y = 0;
        }
        if (Math.hypot(ball.x - previousX, ball.y - previousY) > 0.05) {
            points.push({ x: ball.x, y: ball.y, time: now });
        }
        points = points.filter(point => now - point.time < settings.trailDuration);

        const transition = 1 - Math.pow(1 - settings.transitionSpeed, step);
        let transitioning = false;
        for (const property of Object.keys(visual)) {
            visual[property] += (desired[property] - visual[property]) * transition;
            if (Math.abs(desired[property] - visual[property]) > 0.01) transitioning = true;
            else visual[property] = desired[property];
        }

        context.clearRect(0, 0, width, height);
        context.lineCap = context.lineJoin = 'round';
        if (points.length > 1) {
            const oldest = points[0];
            const newest = points[points.length - 1];
            const gradient = context.createLinearGradient(oldest.x, oldest.y, newest.x, newest.y);
            gradient.addColorStop(0, rgba(Math.max(0, 1 - (now - oldest.time) / settings.trailDuration) * 0.3));
            gradient.addColorStop(1, rgba(1));
            context.beginPath();
            context.moveTo(oldest.x, oldest.y);
            for (const point of points.slice(1)) context.lineTo(point.x, point.y);
            context.strokeStyle = gradient;
            context.lineWidth = Math.max(2, settings.size / 4);
            context.stroke();
        }
        if (!hideDot) {
            if (linkRect && visual.lineOpacity > 0.01) {
                const startX = linkRect.left + (linkRect.width - visual.underline) / 2;
                context.beginPath();
                context.moveTo(startX, linkRect.bottom + 1);
                context.lineTo(startX + visual.underline, linkRect.bottom + 1);
                context.strokeStyle = rgba(visual.lineOpacity);
                context.lineWidth = Math.max(1, settings.borderWidth - 1);
                context.stroke();
            } else {
                context.beginPath();
                context.arc(ball.x, ball.y, visual.radius, 0, Math.PI * 2);
                if (visual.fill > 0.01) {
                    context.fillStyle = rgba(visual.fill);
                    context.fill();
                }
                if (visual.stroke > 0.01) {
                    context.strokeStyle = rgba(visual.stroke);
                    context.lineWidth = settings.borderWidth;
                    context.stroke();
                }
            }
        }
        // Keep the settled dot, but stop repainting once the short trail expires.
        if (moving || transitioning || points.length) frame = window.requestAnimationFrame(draw);
    }

    document.addEventListener('pointermove', event => {
        if (event.pointerType !== 'mouse') {
            hide();
            return;
        }
        if (!enabled) return;
        target.x = event.clientX;
        target.y = event.clientY;
        if (canvas.hidden) {
            ball.x = target.x;
            ball.y = target.y;
            visual.radius = settings.size / 2;
            visual.fill = 1;
            visual.stroke = visual.underline = visual.lineOpacity = 0;
            canvas.hidden = false;
        }
        wake();
    }, { passive: true });
    document.addEventListener('pointerout', event => {
        if (!event.relatedTarget) hide();
    }, { passive: true });
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) hide();
    });
    window.addEventListener('scroll', wake, { passive: true, capture: true });
    window.addEventListener('resize', resize, { passive: true });
    window.addEventListener('blur', hide);
    window.addEventListener('pagehide', hide);
    pointerPreference.addEventListener('change', updatePreference);
    motionPreference.addEventListener('change', updatePreference);
    updatePreference();
})();
