import { useEffect, useRef, useState } from "react";
import "./LocationAutocomplete.css";

type Suggestion = { place_id: number; display_name: string };

type Props = {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
};

export function LocationAutocomplete({ value, onChange, placeholder }: Props) {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [open, setOpen] = useState(false);
  const [locating, setLocating] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => { setQuery(value); }, [value]);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (query.length < 3) { setSuggestions([]); setOpen(false); return; }
    timerRef.current = setTimeout(async () => {
      try {
        const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=5&addressdetails=1`;
        const res = await fetch(url, { headers: { "Accept-Language": "en" } });
        const data: Suggestion[] = await res.json();
        setSuggestions(data);
        setOpen(data.length > 0);
      } catch { /* network error — fail silently */ }
    }, 350);
  }, [query]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function select(s: Suggestion) {
    setQuery(s.display_name);
    onChange(s.display_name);
    setSuggestions([]);
    setOpen(false);
  }

  function useCurrentLocation() {
    if (!navigator.geolocation) return;
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        try {
          const url = `https://nominatim.openstreetmap.org/reverse?lat=${coords.latitude}&lon=${coords.longitude}&format=json`;
          const res = await fetch(url, { headers: { "Accept-Language": "en" } });
          const data = await res.json();
          const name: string = data.display_name ?? "";
          setQuery(name);
          onChange(name);
        } finally {
          setLocating(false);
        }
      },
      () => setLocating(false),
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  return (
    <div className="loc-wrap" ref={wrapRef}>
      <div className="loc-input-wrap">
        <span className="loc-search-icon">⊙</span>
        <input
          type="text"
          className="loc-input"
          value={query}
          onChange={(e) => { setQuery(e.target.value); onChange(e.target.value); }}
          onFocus={() => suggestions.length > 0 && setOpen(true)}
          placeholder={placeholder ?? "Search address…"}
          autoComplete="off"
        />
        {query.length > 0 && (
          <button className="loc-clear" onMouseDown={(e) => { e.preventDefault(); setQuery(""); onChange(""); setSuggestions([]); }} title="Clear">✕</button>
        )}
        {open && suggestions.length > 0 && (
          <ul className="loc-dropdown">
            {suggestions.map((s) => (
              <li key={s.place_id} className="loc-suggestion" onMouseDown={() => select(s)}>
                <span className="loc-pin">📍</span>
                <span className="loc-name">{s.display_name}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <button type="button" className="loc-gps-btn" onClick={useCurrentLocation} disabled={locating}>
        <span>◎</span>
        {locating ? "Detecting location…" : "Use my current location"}
      </button>
    </div>
  );
}
