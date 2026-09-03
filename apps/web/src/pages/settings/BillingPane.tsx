import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useToast } from "../../components/Toast";
import { fetchJson, postJson } from "../../lib/api";
import { formatMoney } from "../../lib/format";
import { useVenue } from "../../lib/useVenue";
import type { BillingSummary, Waiver } from "../../types/billing";
import { Group, Tag } from "./SettingsRows";
import "./BillingPane.css";

function currentMonth() {
  return new Date().toISOString().slice(0, 7);
}

function shiftMonth(month: string, delta: number) {
  const [year, index] = month.split("-").map(Number);
  const date = new Date(Date.UTC(year, index - 1 + delta, 1));
  return date.toISOString().slice(0, 7);
}

function monthLabel(month: string) {
  const [year, index] = month.split("-").map(Number);
  return new Date(Date.UTC(year, index - 1, 1)).toLocaleDateString("en-GB", { month: "long", year: "numeric", timeZone: "UTC" });
}

function longDate(value: string) {
  return new Date(value).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function waiverHint(waiver: Waiver) {
  const until = longDate(waiver.fee_waived_until);
  const remaining = Math.max(waiver.shift_cap - waiver.shifts_used, 0);
  return waiver.active
    ? `${waiver.label} · no platform fee until ${until} or ${remaining} more completed shift${remaining === 1 ? "" : "s"}`
    : `${waiver.label} ended · ${waiver.shifts_used} of ${waiver.shift_cap} shifts used, until ${until}`;
}

export function BillingPane() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const venue = useVenue();
  const currency = venue.data?.currency ?? "GBP";
  const [month, setMonth] = useState(currentMonth);
  const [code, setCode] = useState("");
  const summary = useQuery({
    queryKey: ["billing", month],
    queryFn: () => fetchJson<BillingSummary>(`/billing/summary?month=${month}`),
  });
  const redeem = useMutation({
    mutationFn: (value: string) => postJson<Waiver>("/billing/partner-codes/redeem", { code: value }),
    onSuccess: async (waiver) => {
      await queryClient.invalidateQueries({ queryKey: ["billing"] });
      setCode("");
      toast({ type: "success", message: `${waiver.label} applied.` });
    },
    onError: (error: Error) => toast({ type: "error", message: error.message }),
  });

  if (summary.error) return <p className="st-error">{(summary.error as Error).message}</p>;
  if (!summary.data) return <p className="st-muted">Loading billing…</p>;
  const data = summary.data;
  const money = (value: string) => formatMoney(value, currency);

  return (
    <>
      <Group
        title="Plan"
        hint="What you pay us. Wages are always paid by you, directly to the worker."
        rows={[
          {
            key: "plan",
            label: data.plan === "founding_partner" ? "Founding partner" : "Standard",
            hint: data.waiver ? waiverHint(data.waiver) : `${data.fee_percent}% of wages on each completed shift`,
            control: <Tag tone="live">{data.plan === "founding_partner" ? "Fee waived" : `${data.fee_percent}% fee`}</Tag>,
          },
          data.waiver
            ? { key: "code", label: "Partner code", hint: "Applied to this venue", control: <span className="st-readonly bl-code">{data.waiver.code}</span> }
            : {
                key: "code",
                label: "Partner code",
                hint: "Founding partners: paste the code we gave you",
                control: (
                  <span className="st-inline">
                    <input className="st-input" value={code} placeholder="BATH-XXXX-XXXX" onChange={(event) => setCode(event.target.value.toUpperCase())} />
                    <button type="button" className="st-btn primary" disabled={redeem.isPending || code.trim().length < 4} onClick={() => redeem.mutate(code)}>
                      {redeem.isPending ? "Applying…" : "Apply"}
                    </button>
                  </span>
                ),
              },
          {
            key: "all-time",
            label: "Completed shifts",
            hint: "All time, across every worker",
            control: <span className="st-readonly">{data.completed_shifts_all_time}</span>,
          },
        ]}
      />
      <Group
        title="Statement"
        hint="Wages are information — you pay workers directly. The platform fee is the only amount owed to Venue OS."
        rows={[
          {
            key: "statement",
            label: monthLabel(month),
            hint: data.lines.length ? "Corrections are shown as their own lines against the original shift" : "No completed shifts this month",
            stack: true,
            control: (
              <div className="bl-statement">
                <div className="bl-nav">
                  <button type="button" className="st-btn" onClick={() => setMonth(shiftMonth(month, -1))}>‹ {monthLabel(shiftMonth(month, -1))}</button>
                  <button type="button" className="st-btn" onClick={() => setMonth(currentMonth())}>This month</button>
                  <button type="button" className="st-btn" disabled={month >= currentMonth()} onClick={() => setMonth(shiftMonth(month, 1))}>{monthLabel(shiftMonth(month, 1))} ›</button>
                </div>
                <div className="bl-due">
                  <span>
                    <b>Owed to Venue OS · {monthLabel(month)}</b>
                    <em>Platform fees only. Wages below are paid by you, directly to your workers.</em>
                  </span>
                  <strong>{money(data.amount_due)}</strong>
                </div>
                {data.lines.length > 0 && (
                  <table className="bl-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Worker</th>
                        <th>Role</th>
                        <th className="r">Hours</th>
                        <th className="r">Wages · paid by you</th>
                        <th className="r">Fee · owed to us</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.lines.map((line) => (
                        <tr key={line.line_id} className={line.line_kind === "correction" ? "bl-correction" : undefined}>
                          <td>{longDate(line.start_time)}</td>
                          <td>{line.line_kind === "correction" ? `Correction · ${line.worker_name}` : line.worker_name}</td>
                          <td>{line.reason ?? line.role}</td>
                          <td className="r">{line.hours}</td>
                          <td className="r">{money(line.wages)}</td>
                          <td className="r">{line.waived ? <span className="bl-waived">waived</span> : money(line.fee)}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr>
                        <td colSpan={3}>Totals</td>
                        <td />
                        <td className="r">{money(data.wages_total)}</td>
                        <td className="r bl-due-cell">{money(data.fee_total)}</td>
                      </tr>
                    </tfoot>
                  </table>
                )}
              </div>
            ),
          },
        ]}
      />
      <Group
        title="Payment"
        hint="Platform fees are invoiced monthly on the 1st. Nothing is charged until a payment method is on file."
        soon
        rows={[
          { key: "card", label: "Payment method", hint: "Card or direct debit", control: <button type="button" className="st-btn">Add card</button> },
          { key: "invoices", label: "Invoices", hint: "Monthly, on the 1st", control: <span className="st-readonly">None yet</span> },
          { key: "business", label: "Business details", hint: "Appears on invoices", stack: true, control: <span className="st-inline"><input className="st-input" placeholder="Registered company name" /><input className="st-input short" placeholder="VAT no." /></span> },
        ]}
      />
    </>
  );
}
