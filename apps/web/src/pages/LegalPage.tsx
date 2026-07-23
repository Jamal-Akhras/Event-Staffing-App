import { Link } from "react-router-dom";
import { LegalLinks } from "../components/LegalLinks";
import "./LegalPage.css";

type LegalKind = "terms" | "privacy" | "cookies";

type LegalSection = {
  heading: string;
  body: string[];
};

type LegalContent = {
  eyebrow: string;
  title: string;
  updated: string;
  summary: string;
  sections: LegalSection[];
};

const entity = "[LEGAL ENTITY NAME]";
const contact = "[PRIVACY CONTACT EMAIL]";
const address = "[REGISTERED ADDRESS]";

const LEGAL_CONTENT: Record<LegalKind, LegalContent> = {
  terms: {
    eyebrow: "Legal",
    title: "Terms of Service",
    updated: "May 25, 2026",
    summary: `These draft terms govern use of Venue OS by venues, operators, and workers. Replace placeholders with ${entity} details before client use.`,
    sections: [
      {
        heading: "1. Who we are",
        body: [
          `Venue OS is operated by ${entity}, ${address}. These terms apply when you access the web dashboard, worker mobile app, API, or related services.`,
          `Contact: [SUPPORT EMAIL]. Legal notices: ${contact}.`,
        ],
      },
      {
        heading: "2. Marketplace role",
        body: [
          "Venue OS helps operators post shifts and workers apply for event staffing work. Unless a signed contract says otherwise, Venue OS is a software provider and not the employer, agency, payroll provider, or tax adviser for either party.",
          "Operators remain responsible for lawful hiring, worker checks, site safety, pay, tax, employment status, insurance, and local venue obligations.",
        ],
      },
      {
        heading: "3. Accounts and acceptable use",
        body: [
          "You must provide accurate account information, protect login credentials, and tell us promptly if an account is compromised.",
          "You must not misuse the platform, scrape data, reverse engineer the service, upload unlawful content, harass users, or attempt to bypass security controls.",
        ],
      },
      {
        heading: "4. Shifts, applications, bookings, and ratings",
        body: [
          "Operators are responsible for the accuracy of shift details, pay rates, location, working hours, and cancellation terms. Workers are responsible for applying only to shifts they can reasonably attend.",
          "Reliability scores, ratings, messages, and booking states are operational tools. They should be reviewed with human judgment and corrected if they are inaccurate.",
        ],
      },
      {
        heading: "5. Fees, payments, and availability",
        body: [
          "Payment processing is not yet enabled in this MVP. Any fees, payment terms, refund terms, or payout timing must be documented in a signed order form or updated production terms before launch.",
          "We aim to keep the service available, but we do not guarantee uninterrupted access. Planned maintenance and urgent security work may affect availability.",
        ],
      },
      {
        heading: "6. Liability and termination",
        body: [
          "To the fullest extent permitted by law, the service is provided as is and we exclude implied warranties. Nothing in these terms excludes liability that cannot legally be excluded.",
          "We may suspend or terminate access for security risk, non-payment, unlawful use, or serious breach of these terms.",
        ],
      },
    ],
  },
  privacy: {
    eyebrow: "Privacy",
    title: "Privacy Policy",
    updated: "May 25, 2026",
    summary: "This draft explains how Venue OS handles personal data under UK GDPR, the Data Protection Act 2018, and UAE Federal Decree-Law No. 45 of 2021 where applicable.",
    sections: [
      {
        heading: "1. Controller and contacts",
        body: [
          `${entity}, ${address}, is the controller for account, marketplace, support, and website data unless a signed agreement states otherwise.`,
          `Privacy contact: ${contact}. Data protection officer or representative, if appointed: [DPO OR REPRESENTATIVE CONTACT].`,
        ],
      },
      {
        heading: "2. Personal data we collect",
        body: [
          "Account data: name, email, phone, role, venue, country, login metadata, and authentication records.",
          "Marketplace data: shift details, applications, bookings, messages, ratings, check-in/out timestamps, reliability signals, worker profile information, and uploaded venue or profile images.",
          "Technical data: device, browser, IP address, API logs, cookie identifiers, error reports, and security audit records.",
        ],
      },
      {
        heading: "3. Why we use data",
        body: [
          "We use data to create accounts, match workers with shifts, manage bookings, support messaging, show earnings and operational history, prevent abuse, secure the platform, comply with law, and improve reliability.",
          "Typical lawful bases include contract performance, legitimate interests, legal obligations, and consent where required for optional cookies or marketing.",
        ],
      },
      {
        heading: "4. Sharing, transfers, and subprocessors",
        body: [
          "We share data with operators and workers as needed to run shifts, with hosting and infrastructure providers, and with professional advisers or authorities where legally required.",
          "Personal data may be processed in the UK, UAE, EEA, United States, or other countries used by our subprocessors. Our current subprocessor list and transfer safeguards: [SUBPROCESSOR LIST URL] (draft at docs/legal/subprocessors.md).",
        ],
      },
      {
        heading: "5. Retention and security",
        body: [
          "We keep account and booking records while the account is active and as long as needed for legal, tax, audit, dispute, safety, and fraud-prevention purposes. Define exact retention periods before production launch.",
          "We use technical and organisational controls including authentication, access controls, encrypted transport, environment separation, backups, logging, and least-privilege operations.",
        ],
      },
      {
        heading: "6. Your rights",
        body: [
          "Depending on location, you may request access, correction, deletion, restriction, objection, portability, withdrawal of consent, or review of automated decisions.",
          `UK users can contact the Information Commissioner's Office. UAE users may have rights under the UAE PDPL. Contact ${contact} first so we can investigate quickly.`,
        ],
      },
    ],
  },
  cookies: {
    eyebrow: "Cookies",
    title: "Cookie Policy",
    updated: "May 25, 2026",
    summary: "This draft explains the cookies and similar technologies used by Venue OS. Replace placeholders after the production analytics and marketing stack is confirmed.",
    sections: [
      {
        heading: "1. What cookies are",
        body: [
          "Cookies and similar technologies store small pieces of information on a browser or device. They can keep users signed in, remember choices, measure service performance, and help protect accounts.",
        ],
      },
      {
        heading: "2. Cookies we use",
        body: [
          "Strictly necessary: authentication, session continuity, security, load balancing, and saved preferences required to provide the service.",
          "Error reporting: Sentry (sentry.io) may set short-lived identifiers in browser storage so we can group errors and avoid duplicate reports. It is enabled only when an environment variable is set; we treat it as strictly necessary because it helps us fix outages.",
          "Analytics: product usage and page performance. Not currently enabled in this MVP. Add provider names here if enabled: [ANALYTICS PROVIDERS].",
          "Marketing: not currently enabled in this MVP. Add consent tooling before using advertising or retargeting cookies.",
        ],
      },
      {
        heading: "3. Managing choices",
        body: [
          "You can block or delete cookies in your browser settings. Some strictly necessary cookies are required for login and secure account access.",
          "If optional analytics or marketing cookies are enabled later, add a consent banner and preference center before collecting them.",
        ],
      },
      {
        heading: "4. Mobile app storage",
        body: [
          "The mobile app may store authentication tokens, account state, and user preferences on the device so the app can function reliably.",
          "Removing the app or signing out may clear local app storage, but server-side records may remain under the Privacy Policy retention rules.",
        ],
      },
    ],
  },
};

function LegalPage({ kind }: { kind: LegalKind }) {
  const content = LEGAL_CONTENT[kind];
  return (
    <main className="legal-page">
      <header className="legal-hero">
        <div className="legal-hero-nav">
          <Link to="/login" className="legal-brand" aria-label="Back to Venue OS login">
            <span className="legal-brand-mark">V</span>
            <span>Venue OS</span>
          </Link>
          <div className="legal-hero-cta">
            <Link to="/login" className="legal-hero-link">Sign in</Link>
            <Link to="/register" className="legal-hero-link primary">Sign up</Link>
          </div>
        </div>
        <p className="legal-eyebrow">{content.eyebrow}</p>
        <h1>{content.title}</h1>
        <p className="legal-summary">{content.summary}</p>
        <p className="legal-updated">Last updated: {content.updated}. Draft for legal review.</p>
      </header>
      <article className="legal-card">
        {content.sections.map((section) => (
          <section key={section.heading}>
            <h2>{section.heading}</h2>
            {section.body.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
          </section>
        ))}
      </article>
      <LegalLinks className="legal-footer-links" />
    </main>
  );
}

export function TermsPage() {
  return <LegalPage kind="terms" />;
}

export function PrivacyPage() {
  return <LegalPage kind="privacy" />;
}

export function CookiesPage() {
  return <LegalPage kind="cookies" />;
}
