import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { useToast } from "../../components/Toast";
import { useAuth } from "../../contexts/AuthContext";
import { deleteJson, fetchJson, postJson, postPublicJson } from "../../lib/api";
import { Group } from "./SettingsRows";

type Report = { report_id: string; status: string };
type Export = { generated_at: string; data: unknown };

export function AccountPane() {
  const { user, logout } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [confirming, setConfirming] = useState<"export" | "delete" | null>(null);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const reports = useQuery({ queryKey: ["reports", "me"], queryFn: () => fetchJson<Report[]>("/reports/me") });

  const run = async (task: () => Promise<void>) => {
    setBusy(true);
    try {
      await task();
    } catch (error) {
      toast({ type: "error", message: (error as Error).message });
    } finally {
      setBusy(false);
    }
  };

  const sendResetLink = () =>
    run(async () => {
      await postPublicJson("/auth/forgot-password", { email: user?.email });
      toast({ type: "success", message: `Reset link sent to ${user?.email}.` });
    });

  const signOutEverywhere = () =>
    run(async () => {
      await postJson("/auth/logout-all");
      logout();
      navigate("/login");
    });

  const exportData = () =>
    run(async () => {
      const result = await postJson<Export>("/auth/account-export", { password });
      const blob = new Blob([JSON.stringify(result.data, null, 2)], { type: "application/json" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `venue-os-export-${result.generated_at.slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(link.href);
      setConfirming(null);
      setPassword("");
    });

  const deleteAccount = () =>
    run(async () => {
      if (!window.confirm("Delete this venue account? Open shifts are cancelled and booked workers notified.")) return;
      await deleteJson("/auth/account", { password, confirmation: "DELETE" });
      logout();
      navigate("/login");
    });

  const confirmControl = (kind: "export" | "delete", label: string, action: () => void, danger?: boolean) =>
    confirming === kind ? (
      <span className="st-inline">
        <input className="st-input" type="password" placeholder="Your password" value={password} autoFocus onChange={(event) => setPassword(event.target.value)} />
        <button type="button" className={`st-btn ${danger ? "danger" : "primary"}`} disabled={busy || !password} onClick={action}>{label}</button>
        <button type="button" className="st-btn" onClick={() => { setConfirming(null); setPassword(""); }}>Cancel</button>
      </span>
    ) : (
      <button type="button" className={`st-btn ${danger ? "danger" : ""}`} disabled={busy} onClick={() => setConfirming(kind)}>{label}…</button>
    );

  const filed = reports.data ?? [];
  const open = filed.filter((report) => report.status !== "resolved").length;

  return (
    <>
      <Group
        title="Sign-in"
        rows={[
          { key: "email", label: "Email", hint: user?.email, control: <span className="st-readonly">Verified</span> },
          { key: "password", label: "Password", hint: "We email a link that expires in an hour", control: <button type="button" className="st-btn" disabled={busy} onClick={sendResetLink}>Send reset link</button> },
          { key: "sso", label: "Google & Apple", hint: "Sign in with one tap from the sign-in page", control: <span className="st-readonly">Available at sign-in</span> },
          { key: "devices", label: "Devices", hint: "Signs out every browser and phone, including this one", control: <button type="button" className="st-btn" disabled={busy} onClick={signOutEverywhere}>Sign out everywhere</button> },
        ]}
      />
      <Group
        title="Your data"
        hint="Both actions ask for your password."
        rows={[
          { key: "export", label: "Download your data", hint: "Shifts, bookings, applications, messages and ratings as JSON", stack: confirming === "export", control: confirmControl("export", "Download", exportData) },
          { key: "reports", label: "Reports you've filed", hint: filed.length ? `${filed.length} filed · ${open} under review` : "None", control: <span className="st-readonly">{filed.length}</span> },
          { key: "legal", label: "Legal", control: <span className="st-inline"><Link className="st-btn" to="/terms">Terms</Link><Link className="st-btn" to="/privacy">Privacy</Link><Link className="st-btn" to="/cookies">Cookies</Link></span> },
        ]}
      />
      <Group
        title="Danger"
        rows={[
          { key: "delete", label: "Delete this venue account", hint: "Cancels open shifts, notifies booked workers, removes your data", stack: confirming === "delete", control: confirmControl("delete", "Delete account", deleteAccount, true) },
        ]}
      />
    </>
  );
}
