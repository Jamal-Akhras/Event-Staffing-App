import { Link } from "react-router-dom";
import "./LegalLinks.css";

type Props = {
  className?: string;
};

export function LegalLinks({ className = "" }: Props) {
  return (
    <nav className={`legal-links ${className}`.trim()} aria-label="Legal">
      <Link to="/terms">Terms</Link>
      <Link to="/privacy">Privacy</Link>
      <Link to="/cookies">Cookies</Link>
    </nav>
  );
}
