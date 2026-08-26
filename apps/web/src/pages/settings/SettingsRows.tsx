import { createContext, useContext, type ReactNode } from "react";

import "./SettingsControls.css";
import "./SettingsMedia.css";

export const SearchContext = createContext("");

export type SettingRow = {
  key: string;
  label: string;
  hint?: string;
  control: ReactNode;
  stack?: boolean;
};

type GroupProps = {
  title: string;
  hint?: string;
  rows: SettingRow[];
  soon?: boolean;
};

export function Group({ title, hint, rows, soon }: GroupProps) {
  const query = useContext(SearchContext).trim().toLowerCase();
  const visible = query
    ? rows.filter((row) => [title, row.label, row.hint].some((text) => text?.toLowerCase().includes(query)))
    : rows;
  if (!visible.length) return null;
  const Box = soon ? "fieldset" : "div";
  return (
    <section className={`st-group ${soon ? "soon" : ""}`}>
      <div className="st-group-head">
        <h2>{title}{soon && <Tag tone="soon">Coming soon</Tag>}</h2>
        {hint && <p>{hint}</p>}
      </div>
      <Box className="st-box" disabled={soon || undefined}>
        {visible.map((row) => (
          <div key={row.key} className={`st-row ${row.stack ? "stack" : ""}`}>
            <div className="st-row-text">
              <b>{row.label}</b>
              {row.hint && <span>{row.hint}</span>}
            </div>
            <div className="st-row-control">{row.control}</div>
          </div>
        ))}
      </Box>
    </section>
  );
}

export function Tag({ tone, children }: { tone: "live" | "soon"; children: ReactNode }) {
  return <span className={`st-tag ${tone}`}>{children}</span>;
}

type SwitchProps = {
  checked: boolean;
  disabled?: boolean;
  label: string;
  onChange: () => void;
};

export function Switch({ checked, disabled, label, onChange }: SwitchProps) {
  return (
    <label className="st-switch">
      <input type="checkbox" checked={checked} disabled={disabled} aria-label={label} onChange={onChange} />
      <span />
    </label>
  );
}
