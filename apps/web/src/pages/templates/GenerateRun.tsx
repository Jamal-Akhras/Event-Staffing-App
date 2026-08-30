import { useState } from "react";

import { formatMoney } from "../../lib/format";
import type { Template } from "../../types/templates";
import { crossesClockChange, matchingDays, type GenerateRequest } from "./useTemplates";

const WEEK = [
  ["M", "Monday"],
  ["T", "Tuesday"],
  ["W", "Wednesday"],
  ["T", "Thursday"],
  ["F", "Friday"],
  ["S", "Saturday"],
  ["S", "Sunday"],
];

function today() {
  return new Date().toISOString().slice(0, 10);
}

function inDays(count: number) {
  const date = new Date();
  date.setDate(date.getDate() + count);
  return date.toISOString().slice(0, 10);
}

type GenerateRunProps = {
  templates: Template[];
  templateId: string;
  currency: string;
  busy: boolean;
  onTemplateChange: (templateId: string) => void;
  onGenerate: (request: GenerateRequest) => void;
};

export function GenerateRun({ templates, templateId, currency, busy, onTemplateChange, onGenerate }: GenerateRunProps) {
  const [startDate, setStartDate] = useState(today);
  const [endDate, setEndDate] = useState(() => inDays(28));
  const [startTime, setStartTime] = useState("18:00");
  const [days, setDays] = useState<number[]>([]);

  const template = templates.find((item) => item.template_id === templateId) ?? templates[0];
  if (!template) return null;

  const count = days.length === 0 ? 0 : matchingDays(startDate, endDate, days);
  const seats = count * template.workers_needed;
  const wages = seats * template.duration_hours * Number(template.pay_rate);
  const warnClockChange = count > 0 && crossesClockChange(startDate, endDate);
  const ready = count > 0 && !busy;

  const toggle = (day: number) =>
    setDays((current) => (current.includes(day) ? current.filter((value) => value !== day) : [...current, day]));

  return (
    <section className="tp-run">
      <div>
        <span className="tp-kicker">Bulk posting</span>
        <h2>Generate a run of shifts</h2>
        <p>Pick a template and a stretch of dates, and every matching day is posted at once.</p>

        <div className="tp-fields">
          <label className="tp-field tp-field-wide">
            <span>Template</span>
            <select value={template.template_id} onChange={(event) => onTemplateChange(event.target.value)}>
              {templates.map((item) => (
                <option key={item.template_id} value={item.template_id}>
                  {item.name} · {item.role} × {item.workers_needed}
                </option>
              ))}
            </select>
          </label>
          <label className="tp-field">
            <span>From</span>
            <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
          </label>
          <label className="tp-field">
            <span>To</span>
            <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
          </label>
          <label className="tp-field">
            <span>Start time</span>
            <input type="time" value={startTime} onChange={(event) => setStartTime(event.target.value)} />
          </label>
          <div className="tp-field">
            <span>Days</span>
            <div className="tp-days">
              {WEEK.map(([short, full], index) => (
                <button
                  key={full}
                  type="button"
                  aria-label={full}
                  aria-pressed={days.includes(index)}
                  className={days.includes(index) ? "on" : ""}
                  onClick={() => toggle(index)}
                >
                  {short}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="tp-preview">
        <span className="tp-kicker">This will create</span>
        {count === 0 ? (
          <>
            <b>Nothing yet</b>
            <p>Choose the days of the week you want this template posted on.</p>
          </>
        ) : (
          <>
            <b>
              {count} {count === 1 ? "shift" : "shifts"}
              <br />
              {seats} {seats === 1 ? "seat" : "seats"}
            </b>
            <p>
              {template.duration_hours} hours from {startTime}, about {formatMoney(wages, currency)} in wages at{" "}
              {formatMoney(template.pay_rate, currency)}/hr.
            </p>
          </>
        )}
        {warnClockChange && (
          <p className="tp-warn">
            This range crosses the clock change, so later shifts would be an hour out. Generate them in two runs.
          </p>
        )}
        <button
          type="button"
          className="btn tp-go"
          disabled={!ready}
          onClick={() => onGenerate({ templateId: template.template_id, startDate, endDate, startTime, daysOfWeek: days })}
        >
          {busy ? "Posting…" : count === 0 ? "Pick some days" : `Generate ${count} ${count === 1 ? "shift" : "shifts"}`}
        </button>
      </div>
    </section>
  );
}
