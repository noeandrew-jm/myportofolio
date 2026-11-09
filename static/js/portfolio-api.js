/**
 * Shared transport for session-authenticated portfolio mutations.
 * Page controllers own forms and DOM updates; this module owns the HTTP contract.
 */
(() => {
    'use strict';

    const resourceIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

    function hasResourceId(value) {
        return value !== null && typeof value === 'object' && resourceIdPattern.test(value.id);
    }

    function serverMessage(payload) {
        if (!payload || typeof payload !== 'object') return '';
        return typeof payload.detail === 'string' ? payload.detail
            : typeof payload.message === 'string' ? payload.message : '';
    }

    function validationMessages(payload) {
        if (!payload || typeof payload !== 'object') return [];
        return Object.values(payload).flat().filter(value => typeof value === 'string');
    }

    /**
     * Return a validated resource, or null for a successful deletion.
     * A 2xx login page, malformed JSON, or wrong status must never clear a form.
     * POST star toggles are not idempotent, so failures are deliberately not retried.
     */
    async function write(url, {method, payload, csrfToken, expectedStatus, messages}) {
        const response = await fetch(url, {
            method,
            credentials: 'same-origin',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                // Session cookies authenticate the user; this separate token
                // proves the modifying request originated from our page.
                'X-CSRFToken': csrfToken,
            },
            body: payload === undefined ? undefined : JSON.stringify(payload),
        }).catch(() => { throw new Error(messages.network); });

        // HTTP 204 has no JSON body. Attempting response.json() here would turn
        // a completed deletion into an apparent failure and invite a repeat.
        if (method === 'DELETE' && response.status === 204) return null;
        const result = await response.json().catch(() => null);
        if (!response.ok) {
            const message = validationMessages(result).join(' ') || messages.http(response.status);
            const error = new Error(message);
            error.status = response.status;
            error.payload = result;
            throw error;
        }
        if (method === 'DELETE' || response.status !== expectedStatus || !hasResourceId(result)) {
            throw new Error(messages.invalid);
        }
        return result;
    }

    window.PortfolioAPI = Object.freeze({write, hasResourceId, serverMessage});
})();
