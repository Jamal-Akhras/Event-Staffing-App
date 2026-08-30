import type { ReactNode } from "react";

import "./PageHeader.css";

type PageSearch = {
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
};

type PageHeaderProps = {
  title: string;
  lead: string;
  emphasis?: string;
  search?: PageSearch;
  actions?: ReactNode;
};

export function PageHeader({ title, lead, emphasis, search, actions }: PageHeaderProps) {
  return (
    <header className="pg-head">
      <div className="pg-head-copy">
        <h1>{title}</h1>
        <p>
          {lead}
          {emphasis ? <em> {emphasis}</em> : null}
        </p>
      </div>
      <div className="pg-head-tools">
        {search && (
          <label className="pg-search">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="M20 20l-3.5-3.5" />
            </svg>
            <input
              value={search.value}
              placeholder={search.placeholder}
              onChange={(event) => search.onChange(event.target.value)}
            />
            {search.value && (
              <button type="button" aria-label="Clear search" onClick={() => search.onChange("")}>
                ×
              </button>
            )}
          </label>
        )}
        {actions}
      </div>
    </header>
  );
}
