import { Link } from "react-router-dom";

import { MarketingIcon, type MarketingIconName } from "./MarketingIcon";
import { VenueDashboardPreview, WorkerPhonePreview } from "./ProductPreview";
import "./AudiencePages.css";

type Feature = { icon: MarketingIconName; title: string; copy: string };

const WORKER_FEATURES: Feature[] = [
  { icon: "location", title: "Nearby by default", copy: "See local hospitality shifts with the essential details upfront." },
  { icon: "clock", title: "Built around your time", copy: "Choose the shifts that fit your lectures, plans and existing work." },
  { icon: "message", title: "Keep it in one place", copy: "Applications, confirmations and venue messages stay connected." },
];

const EMPLOYER_FEATURES: Feature[] = [
  { icon: "calendar", title: "Post in minutes", copy: "Create a clear shift with the role, rate, place and timing." },
  { icon: "people", title: "Review with context", copy: "Compare applications and worker profiles before confirming." },
  { icon: "briefcase", title: "Run the week calmly", copy: "Keep coverage, applications and repeatable templates together." },
];

function FeatureGrid({ features }: { features: Feature[] }) {
  return (
    <div className="audience-feature-grid">
      {features.map((feature) => (
        <article key={feature.title}>
          <span><MarketingIcon name={feature.icon} size={23} /></span>
          <h3>{feature.title}</h3>
          <p>{feature.copy}</p>
        </article>
      ))}
    </div>
  );
}

export function WorkerLandingPage() {
  return (
    <>
      <section className="audience-hero worker-audience">
        <div className="audience-hero-copy">
          <span className="public-eyebrow"><i /> For hospitality workers</span>
          <h1>Work around<br /><em>your life.</em></h1>
          <p>Find clear, local shifts and choose the ones that make sense for your week.</p>
          <div className="audience-hero-actions">
            <Link className="public-button dark" to="/download">Get the worker app</Link>
            <a className="public-button light" href="#worker-flow">How it works</a>
          </div>
        </div>
        <div className="audience-preview worker-preview"><WorkerPhonePreview /></div>
      </section>

      <section className="audience-details" id="worker-flow">
        <div className="audience-section-copy">
          <span className="public-kicker">Designed for clarity</span>
          <h2>Everything you need.<br />Nothing you don’t.</h2>
          <p>The worker experience is shaped around quick decisions and a simple shift journey.</p>
        </div>
        <FeatureGrid features={WORKER_FEATURES} />
      </section>

      <AudienceCta
        kicker="Launching in Bath"
        title="Your next good shift could be closer than you think."
        copy="The worker app is currently in private testing ahead of the Bath pilot."
        label="View app access"
        to="/download"
      />
    </>
  );
}

export function EmployerLandingPage() {
  return (
    <>
      <section className="audience-hero employer-audience">
        <div className="audience-hero-copy">
          <span className="public-eyebrow"><i /> For hospitality venues</span>
          <h1>Fill the gap.<br /><em>Keep service moving.</em></h1>
          <p>Post a shift, review local applicants and organise coverage from one focused venue workspace.</p>
          <div className="audience-hero-actions">
            <Link className="public-button green" to="/register">Create venue account</Link>
            <Link className="public-button light" to="/login">Log in</Link>
          </div>
        </div>
        <div className="audience-preview employer-preview"><VenueDashboardPreview /></div>
      </section>

      <section className="audience-details">
        <div className="audience-section-copy">
          <span className="public-kicker">Venue operations</span>
          <h2>Built for the moment<br />the rota changes.</h2>
          <p>A structured flow for urgent gaps, planned events and the busy weekends you can see coming.</p>
        </div>
        <FeatureGrid features={EMPLOYER_FEATURES} />
      </section>

      <AudienceCta
        kicker="Early venue access"
        title="Give your team a better way to find extra hands."
        copy="Create a venue account and explore the operator dashboard today."
        label="Post your first shift"
        to="/register"
      />
    </>
  );
}

export function DownloadPage() {
  return (
    <section className="simple-public-page download-page">
      <div className="simple-public-copy">
        <span className="public-eyebrow"><i /> Worker app</span>
        <h1>Shifts in your pocket.</h1>
        <p>The Venue OS worker app is in private testing. Public App Store and Google Play links will appear here when the Bath pilot opens.</p>
        <div className="store-button-row">
          <span className="store-placeholder"><small>Coming soon to the</small><strong>App Store</strong></span>
          <span className="store-placeholder"><small>Coming soon to</small><strong>Google Play</strong></span>
        </div>
        <Link className="public-text-link dark-link" to="/for-workers">See the worker experience <MarketingIcon name="arrow" size={18} /></Link>
      </div>
      <div className="simple-phone-wrap"><WorkerPhonePreview compact /></div>
    </section>
  );
}

export function SafetyPage() {
  return (
    <>
      <section className="safety-hero">
        <span className="safety-icon"><MarketingIcon name="shield" size={32} /></span>
        <span className="public-kicker">Trust &amp; safety</span>
        <h1>Better shifts start with better information.</h1>
        <p>This page provides a visual framework for the trust, conduct and support content that will be finalised before public launch.</p>
      </section>
      <section className="safety-grid">
        <article><strong>01</strong><h2>Clear expectations</h2><p>Role, rate, timing and location are visible before a worker applies.</p></article>
        <article><strong>02</strong><h2>Accountable histories</h2><p>Completed work contributes to a more useful reliability picture over time.</p></article>
        <article><strong>03</strong><h2>Connected communication</h2><p>Shift messages remain attached to the relevant application and booking.</p></article>
      </section>
    </>
  );
}

function AudienceCta({ kicker, title, copy, label, to }: { kicker: string; title: string; copy: string; label: string; to: string }) {
  return (
    <section className="audience-cta">
      <div><span className="public-kicker light">{kicker}</span><h2>{title}</h2><p>{copy}</p></div>
      <Link className="public-button light" to={to}>{label} <MarketingIcon name="arrow" size={18} /></Link>
    </section>
  );
}
