import { Link } from "react-router-dom";

import { MarketingIcon, type MarketingIconName } from "./MarketingIcon";
import { PremiumHeroVisual } from "./PremiumHeroVisual";
import { VenueDashboardPreview } from "./ProductPreview";
import { useLandingReveal } from "./useLandingReveal";
import "./HomePage.css";

const FLOW_STEPS: Array<{ number: string; title: string; copy: string; icon: MarketingIconName }> = [
  { number: "01", title: "Post what you need", copy: "Add the role, rate, place and time from the venue dashboard.", icon: "calendar" },
  { number: "02", title: "Meet the right people", copy: "Local workers discover the shift and apply with their profile.", icon: "people" },
  { number: "03", title: "Build your go-to team", copy: "Confirm, message and keep every shift organised in one place.", icon: "spark" },
];

export function HomePage() {
  const homeRef = useLandingReveal();

  return (
    <div className="public-home" ref={homeRef}>
      <section className="public-hero">
        <div className="public-hero-copy">
          <span className="public-eyebrow"><i /> Starting with hospitality in Bath</span>
          <h1>The right people,<br /><em>right when it matters.</em></h1>
          <p>Pick up flexible hospitality shifts around your life, or find trusted local staff when your venue needs an extra pair of hands.</p>
          <div className="public-hero-actions">
            <Link className="public-button green" to="/for-workers">
              Find shifts <MarketingIcon name="arrow" size={18} />
            </Link>
            <Link className="public-button light" to="/for-employers">Find staff</Link>
          </div>
          <div className="public-proof-line">
            <span><MarketingIcon name="check" size={15} /> Clear shift details</span>
            <span><MarketingIcon name="check" size={15} /> Local opportunities</span>
            <span><MarketingIcon name="check" size={15} /> Free for workers</span>
          </div>
        </div>

        <PremiumHeroVisual />
      </section>

      <div className="public-motion-rail" aria-hidden="true">
        <div className="motion-rail-track">
          {[0, 1].map((group) => (
            <div className="motion-rail-group" key={group}>
              <span>Bartenders</span><i />
              <span>Floor teams</span><i />
              <span>Events</span><i />
              <span>Hosts</span><i />
              <span>Bath hospitality</span><i />
            </div>
          ))}
        </div>
      </div>

      <section className="public-flow-section" id="how-it-works">
        <div className="public-section-heading" data-reveal>
          <span className="public-kicker">One simple flow</span>
          <h2>From staffing gap to<br />confirmed shift.</h2>
          <p>Built to keep the important parts clear for both sides.</p>
        </div>
        <div className="public-flow-grid">
          {FLOW_STEPS.map((step) => (
            <article key={step.number} className="public-flow-card" data-reveal>
              <div className="flow-card-top"><span>{step.number}</span><MarketingIcon name={step.icon} size={24} /></div>
              <h3>{step.title}</h3>
              <p>{step.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="public-product-section">
        <div className="product-copy" data-reveal>
          <span className="public-kicker light">For venue teams</span>
          <h2>Your staffing operation,<br />without the scramble.</h2>
          <p>Post shifts, review applications, message workers and see upcoming coverage from one calm workspace.</p>
          <ul>
            <li><MarketingIcon name="check" size={16} /> See what needs attention first</li>
            <li><MarketingIcon name="check" size={16} /> Reuse shift templates</li>
            <li><MarketingIcon name="check" size={16} /> Keep applications and messages together</li>
          </ul>
          <Link className="public-text-link" to="/for-employers">Explore the venue platform <MarketingIcon name="arrow" size={18} /></Link>
        </div>
        <div className="product-dashboard-wrap" data-reveal><VenueDashboardPreview /></div>
      </section>

      <section className="public-audience-section">
        <div className="audience-card worker" data-reveal>
          <span className="audience-icon"><MarketingIcon name="briefcase" size={24} /></span>
          <div>
            <span className="public-kicker">For workers</span>
            <h2>Work that fits your week.</h2>
            <p>Discover nearby shifts with the essentials upfront: pay, location, hours and venue.</p>
          </div>
          <Link to="/for-workers">See how it works <MarketingIcon name="arrow" size={18} /></Link>
        </div>
        <div className="audience-card employer" data-reveal>
          <span className="audience-icon"><MarketingIcon name="people" size={24} /></span>
          <div>
            <span className="public-kicker light">For venues</span>
            <h2>Extra hands, minus the chaos.</h2>
            <p>Turn an uncovered service, event or busy weekend into a clear, trackable shift.</p>
          </div>
          <Link to="/for-employers">Meet the venue platform <MarketingIcon name="arrow" size={18} /></Link>
        </div>
      </section>

      <section className="public-final-cta" data-reveal>
        <span className="public-kicker">The Bath launch</span>
        <h2>Great shifts start with<br />great local people.</h2>
        <p>We’re building the first Venue OS community with Bath’s hospitality workers and independent venues.</p>
        <div>
          <Link className="public-button dark" to="/download">Get worker access</Link>
          <Link className="public-button light" to="/register">Create a venue account</Link>
        </div>
      </section>
    </div>
  );
}
