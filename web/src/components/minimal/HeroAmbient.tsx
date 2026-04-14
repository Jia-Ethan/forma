import { useEffect, type RefObject } from "react";

type HeroAmbientProps = {
  containerRef: RefObject<HTMLElement | null>;
};

const DEFAULT_POINTER_X = "50%";
const DEFAULT_POINTER_Y = "42%";

function resetAmbientPosition(node: HTMLElement) {
  node.style.setProperty("--ambient-pointer-x", DEFAULT_POINTER_X);
  node.style.setProperty("--ambient-pointer-y", DEFAULT_POINTER_Y);
  node.style.setProperty("--ambient-shift-x", "0px");
  node.style.setProperty("--ambient-shift-y", "0px");
}

export function HeroAmbient({ containerRef }: HeroAmbientProps) {
  useEffect(() => {
    const node = containerRef.current;
    if (!node || typeof window === "undefined") return;

    resetAmbientPosition(node);

    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches ?? false;
    const supportsHover = window.matchMedia?.("(hover: hover)")?.matches ?? false;
    if (reduceMotion || !supportsHover) {
      return;
    }

    let rafId = 0;
    let nextShiftX = "0px";
    let nextShiftY = "0px";
    let nextPointerX = DEFAULT_POINTER_X;
    let nextPointerY = DEFAULT_POINTER_Y;

    const flush = () => {
      rafId = 0;
      node.style.setProperty("--ambient-pointer-x", nextPointerX);
      node.style.setProperty("--ambient-pointer-y", nextPointerY);
      node.style.setProperty("--ambient-shift-x", nextShiftX);
      node.style.setProperty("--ambient-shift-y", nextShiftY);
    };

    const scheduleFlush = () => {
      if (rafId) return;
      rafId = window.requestAnimationFrame(flush);
    };

    const handlePointerMove = (event: PointerEvent) => {
      const rect = node.getBoundingClientRect();
      if (!rect.width || !rect.height) return;

      const relativeX = (event.clientX - rect.left) / rect.width;
      const relativeY = (event.clientY - rect.top) / rect.height;
      const normalizedX = relativeX - 0.5;
      const normalizedY = relativeY - 0.5;

      nextPointerX = `${Math.max(0, Math.min(100, relativeX * 100)).toFixed(2)}%`;
      nextPointerY = `${Math.max(0, Math.min(100, relativeY * 100)).toFixed(2)}%`;
      nextShiftX = `${(normalizedX * 18).toFixed(2)}px`;
      nextShiftY = `${(normalizedY * 14).toFixed(2)}px`;
      scheduleFlush();
    };

    const handlePointerLeave = () => {
      nextPointerX = DEFAULT_POINTER_X;
      nextPointerY = DEFAULT_POINTER_Y;
      nextShiftX = "0px";
      nextShiftY = "0px";
      scheduleFlush();
    };

    node.addEventListener("pointermove", handlePointerMove);
    node.addEventListener("pointerleave", handlePointerLeave);

    return () => {
      node.removeEventListener("pointermove", handlePointerMove);
      node.removeEventListener("pointerleave", handlePointerLeave);
      if (rafId) window.cancelAnimationFrame(rafId);
      resetAmbientPosition(node);
    };
  }, [containerRef]);

  return (
    <div className="hero-ambient" aria-hidden="true">
      <div className="hero-ambient__layer hero-ambient__layer--wash" />
      <div className="hero-ambient__layer hero-ambient__layer--drift" />
      <div className="hero-ambient__layer hero-ambient__layer--halo" />
      <div className="hero-ambient__grain" />
    </div>
  );
}
