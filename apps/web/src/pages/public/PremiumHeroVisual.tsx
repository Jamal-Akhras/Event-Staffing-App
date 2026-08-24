import { useEffect, useRef } from "react";

import { MarketingIcon } from "./MarketingIcon";
import { WorkerPhonePreview } from "./ProductPreview";

export function PremiumHeroVisual() {
  const stageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stage = stageRef.current;
    if (
      !stage
      || window.matchMedia("(prefers-reduced-motion: reduce)").matches
      || !window.matchMedia("(pointer: fine)").matches
    ) return;
    let frame = 0;

    const update = (event: PointerEvent) => {
      const bounds = stage.getBoundingClientRect();
      const x = ((event.clientX - bounds.left) / bounds.width - 0.5) * 2;
      const y = ((event.clientY - bounds.top) / bounds.height - 0.5) * 2;
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => setPosition(stage, x, y));
    };
    const reset = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => setPosition(stage, 0, 0));
    };

    stage.addEventListener("pointermove", update);
    stage.addEventListener("pointerleave", reset);
    return () => {
      cancelAnimationFrame(frame);
      stage.removeEventListener("pointermove", update);
      stage.removeEventListener("pointerleave", reset);
    };
  }, []);

  return (
    <div className="public-hero-visual" ref={stageRef}>
      <div className="hero-aurora" />
      <div className="hero-grain" />
      <div className="hero-orbit hero-orbit-one"><i /></div>
      <div className="hero-orbit hero-orbit-two"><i /></div>
      <div className="hero-phone-stage">
        <div className="hero-phone-float"><WorkerPhonePreview /></div>
      </div>
      <div className="floating-match-card">
        <span className="floating-match-icon"><MarketingIcon name="check" size={19} /></span>
        <div><strong>Application sent</strong><small>The venue can now review your profile</small></div>
      </div>
      <div className="floating-shift-count"><strong>24</strong><span>local shifts<br />this week</span></div>
      <div className="floating-live-card">
        <span className="live-pulse" />
        <div><small>New in Bath</small><strong>Friday bar shift · £15/hr</strong></div>
      </div>
      <span className="hero-stage-label">Bath · 51.38° N</span>
    </div>
  );
}

function setPosition(stage: HTMLDivElement, x: number, y: number) {
  stage.style.setProperty("--phone-x", `${(x * 12).toFixed(2)}px`);
  stage.style.setProperty("--phone-y", `${(y * 9).toFixed(2)}px`);
  stage.style.setProperty("--phone-rx", `${(-y * 2.4).toFixed(2)}deg`);
  stage.style.setProperty("--phone-ry", `${(x * 3.2).toFixed(2)}deg`);
  stage.style.setProperty("--card-x", `${(-x * 8).toFixed(2)}px`);
  stage.style.setProperty("--card-y", `${(-y * 6).toFixed(2)}px`);
  stage.style.setProperty("--counter-x", `${(x * 5.6).toFixed(2)}px`);
  stage.style.setProperty("--counter-y", `${(y * 4.2).toFixed(2)}px`);
  stage.style.setProperty("--glow-x", `${(50 + x * 8).toFixed(2)}%`);
  stage.style.setProperty("--glow-y", `${(46 + y * 8).toFixed(2)}%`);
}
