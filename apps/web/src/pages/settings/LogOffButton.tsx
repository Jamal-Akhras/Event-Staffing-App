import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useToast } from "../../components/Toast";
import { useAuth } from "../../contexts/AuthContext";

export function LogOffButton() {
  const navigate = useNavigate();
  const { logOff } = useAuth();
  const { toast } = useToast();
  const [loggingOff, setLoggingOff] = useState(false);

  const handleLogOff = async () => {
    setLoggingOff(true);
    try {
      await logOff();
      navigate("/", { replace: true });
    } catch (error) {
      toast({ type: "error", message: (error as Error).message });
      setLoggingOff(false);
    }
  };

  return (
    <button type="button" className="st-btn" disabled={loggingOff} onClick={handleLogOff}>
      {loggingOff ? "Logging off…" : "Log off"}
    </button>
  );
}
