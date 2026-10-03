(() => {
    "use strict";

    const toast = document.getElementById("toast-component");
    const titleElement = document.getElementById("toast-title");
    const messageElement = document.getElementById("toast-message");
    let dismissTimer;
    let hideTimer;
    let showFrame;

    function clearTimers() {
        window.clearTimeout(dismissTimer);
        window.clearTimeout(hideTimer);
        window.cancelAnimationFrame(showFrame);
    }

    function hideToast() {
        if (!toast) return;
        clearTimers();
        toast.classList.remove("toast-show");
        toast.classList.add("toast-hidden");
        hideTimer = window.setTimeout(() => {
            if (typeof toast.hidePopover === "function" && toast.matches(":popover-open")) {
                toast.hidePopover();
            }
            toast.classList.remove("toast-fallback-open");
        }, 220);
    }

    window.showToast = function showToast(title, message, type = "normal", duration = 3000) {
        if (!toast || !titleElement || !messageElement) return;
        clearTimers();
        toast.classList.remove("toast-success", "toast-error", "toast-normal");
        toast.classList.add(type === "success" ? "toast-success" : type === "error" ? "toast-error" : "toast-normal");

        // Keep toast interactions inside an open dialog's light-dismiss boundary.
        // It still uses the top layer, so it is not clipped by the dialog panel.
        const dialog = typeof toast.showPopover === "function"
            ? document.querySelector('[role="dialog"]:popover-open')
            : null;
        const parent = dialog || document.body;
        if (toast.parentElement !== parent) parent.append(toast);

        // Reopen an existing toast so it is above any newly opened popover.
        if (typeof toast.showPopover === "function") {
            if (toast.matches(":popover-open")) toast.hidePopover();
            toast.showPopover();
        } else {
            toast.classList.add("toast-fallback-open");
        }

        // Server messages must be displayed as text, never interpreted as HTML.
        titleElement.textContent = String(title ?? "");
        messageElement.textContent = String(message ?? "");
        showFrame = window.requestAnimationFrame(() => {
            toast.classList.remove("toast-hidden");
            toast.classList.add("toast-show");
        });

        const timeout = Number.isFinite(Number(duration)) ? Math.max(0, Number(duration)) : 3000;
        if (timeout > 0) dismissTimer = window.setTimeout(hideToast, timeout);
    };

    toast?.querySelector(".toast-close")?.addEventListener("click", hideToast);

    // Django already escapes these messages in the fallback HTML. Read them
    // back as text so full-page form submissions receive the same safe toast.
    const validationErrors = [...document.querySelectorAll('[data-toast-validation] .form-error')]
        .map(element => element.textContent.trim()).filter(Boolean);
    if (validationErrors.length) {
        window.showToast("Gagal menyimpan proyek", validationErrors.join("\n"), "error", 5000);
    } else {
        const messages = [...document.querySelectorAll('[data-toast-message]')];
        if (messages.length) {
            const hasType = (message, type) => message.dataset.toastType.split(/\s+/).includes(type);
            const type = messages.some(message => hasType(message, "error")) ? "error"
                : messages.every(message => hasType(message, "success")) ? "success" : "normal";
            const title = type === "error" ? "Terjadi kesalahan" : type === "success" ? "Berhasil" : "Notifikasi";
            window.showToast(title, messages.map(message => message.textContent.trim()).join("\n"), type, 5000);
        }
    }
})();
