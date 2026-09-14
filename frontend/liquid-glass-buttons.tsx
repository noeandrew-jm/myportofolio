import { useLayoutEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import LiquidGlass from "./vendor/liquid-glass-react/src/index";

const restingPointer = { position: { x: 0, y: 0 }, offset: { x: 0, y: 0 } };

// React owns only an aria-hidden decorative layer. Django owns the native link,
// its accessible label, focus state and destination, even if JavaScript fails.
function GlassButtonEffect({ button }: { button: HTMLElement }) {
  const [size, setSize] = useState({ width: button.offsetWidth, height: button.offsetHeight });
  const [pointer, setPointer] = useState(restingPointer);
  const [reducedMotion, setReducedMotion] = useState(false);
  const frame = useRef(0);

  useLayoutEffect(() => {
    const measure = () => {
      const width = button.offsetWidth;
      const height = button.offsetHeight;
      setSize(current => current.width === width && current.height === height
        ? current : { width, height });
    };
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(measure);
    observer?.observe(button);
    window.addEventListener("resize", measure);
    measure();
    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [button]);

  useLayoutEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const syncPreference = () => setReducedMotion(preference.matches);
    syncPreference();
    preference.addEventListener("change", syncPreference);
    return () => preference.removeEventListener("change", syncPreference);
  }, []);

  useLayoutEffect(() => {
    const reset = () => {
      cancelAnimationFrame(frame.current);
      setPointer(restingPointer);
      button.style.removeProperty("--glass-x");
      button.style.removeProperty("--glass-y");
    };
    const move = (event: PointerEvent) => {
      if (reducedMotion || event.pointerType === "touch") return;
      const rect = button.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const x = (event.clientX - rect.left) / rect.width;
      const y = (event.clientY - rect.top) / rect.height;
      cancelAnimationFrame(frame.current);
      frame.current = requestAnimationFrame(() => {
        button.style.setProperty("--glass-x", `${x * 100}%`);
        button.style.setProperty("--glass-y", `${y * 100}%`);
        setPointer({
          position: { x: event.clientX, y: event.clientY },
          offset: { x: (x - 0.5) * 100, y: (y - 0.5) * 100 },
        });
      });
    };
    reset();
    button.addEventListener("pointermove", move);
    button.addEventListener("pointerleave", reset);
    button.addEventListener("pointercancel", reset);
    button.addEventListener("blur", reset);
    return () => {
      cancelAnimationFrame(frame.current);
      button.removeEventListener("pointermove", move);
      button.removeEventListener("pointerleave", reset);
      button.removeEventListener("pointercancel", reset);
      button.removeEventListener("blur", reset);
    };
  }, [button, reducedMotion]);

  return (
    <LiquidGlass
      className="liquid-glass-layer"
      mode="standard"
      overLight
      displacementScale={48}
      blurAmount={0.065}
      saturation={135}
      aberrationIntensity={1.6}
      elasticity={reducedMotion ? 0 : 0.22}
      cornerRadius={999}
      padding="0"
      globalMousePos={pointer.position}
      mouseOffset={pointer.offset}
      style={{ position: "absolute", left: "50%", top: "50%" }}
    >
      <span style={{ display: "block", width: size.width, height: size.height }} />
    </LiquidGlass>
  );
}

document.querySelectorAll<HTMLElement>(".glass-button").forEach((button, index) => {
  const effect = document.createElement("div");
  effect.className = "glass-button__effect";
  effect.setAttribute("aria-hidden", "true");
  button.prepend(effect);
  createRoot(effect, { identifierPrefix: `glass-${index}-` }).render(<GlassButtonEffect button={button} />);
});
