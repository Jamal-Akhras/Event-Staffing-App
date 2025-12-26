import { StatusBar } from "expo-status-bar";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaProvider, useSafeAreaInsets } from "react-native-safe-area-context";

type Booking = {
  booking_id: string;
  shift_id: string;
  worker_id: string;
  operator_id: string;
  start_time: string;
  end_time: string;
  state: string;
  allowed_transitions: string[];
  checked_in_at?: string | null;
  checked_out_at?: string | null;
  confirmed_at?: string | null;
};

type Shift = {
  shift_id: string;
  operator_id: string;
  role: string;
  location: string;
  start_time: string;
  end_time: string;
  pay_rate: number;
  notes?: string | null;
  status: string;
};

type Application = {
  application_id: string;
  shift_id: string;
  worker_id: string;
  operator_id: string;
  start_time: string;
  end_time: string;
  status: string;
  message?: string | null;
  booking_id?: string | null;
  created_at: string;
  decided_at?: string | null;
};

type WorkerProfile = {
  worker_id: string;
  display_name: string;
  role: string;
  city: string;
  experience_years: number;
  reliability_score: number;
  badges: string[];
  bio?: string | null;
  languages: string[];
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  emergency_contact?: string | null;
  pay_rate?: number | null;
  notes?: string | null;
  updated_at: string;
};

type ProfileForm = {
  worker_id: string;
  display_name: string;
  role: string;
  city: string;
  experience_years: string;
  bio: string;
  languages: string;
  email: string;
  phone: string;
  address: string;
  emergency_contact: string;
  pay_rate: string;
  notes: string;
};

type TabKey = "browse" | "shifts" | "profile";

type ShiftTab = "upcoming" | "previous" | "applications";

const workerHeaders = {
  "X-Actor-Role": "worker",
  "Content-Type": "application/json",
};

const TAB_BAR_HEIGHT = 64;
const COLORS = {
  ink: "#0f1720",
  inkMuted: "#6b7785",
  surface: "#ffffff",
  canvas: "#f4f0ea",
  border: "#e1e6ec",
  primary: "#0e5a3a",
  primaryDeep: "#123a2a",
  primarySoft: "#2f8f5f",
  warning: "#d97706",
  error: "#b83b32",
  onPrimary: "#f7efe8",
};

function AppContent() {
  const insets = useSafeAreaInsets();
  const defaultBase =
    process.env.EXPO_PUBLIC_API_BASE ?? "http://192.168.10.131:8000";
  const [apiBase, setApiBase] = useState(defaultBase);
  const [health, setHealth] = useState<string>("Unknown");
  const [error, setError] = useState<string | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [selected, setSelected] = useState<Booking | null>(null);
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [shiftError, setShiftError] = useState<string | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [applicationsError, setApplicationsError] = useState<string | null>(null);
  const [applicationStatus, setApplicationStatus] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("browse");
  const [shiftTab, setShiftTab] = useState<ShiftTab>("upcoming");
  const [selectedShift, setSelectedShift] = useState<Shift | null>(null);
  const [showApply, setShowApply] = useState(false);
  const [applicationMessage, setApplicationMessage] = useState("");
  const [profileForm, setProfileForm] = useState<ProfileForm>({
    worker_id: "worker-1",
    display_name: "",
    role: "",
    city: "",
    experience_years: "0",
    bio: "",
    languages: "",
    email: "",
    phone: "",
    address: "",
    emergency_contact: "",
    pay_rate: "",
    notes: "",
  });
  const [profileMeta, setProfileMeta] = useState<WorkerProfile | null>(null);
  const [profileStatus, setProfileStatus] = useState<string | null>(null);
  const pollInFlight = useRef(false);

  useEffect(() => {
    if (!apiBase) {
      setHealth("Missing API base");
      setError("Set API base URL to continue.");
      return;
    }
    const controller = new AbortController();
    fetch(`${apiBase}/health`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return response.json();
      })
      .then(() => {
        setHealth("Healthy");
        setError(null);
      })
      .catch((err) => {
        setHealth("Unavailable");
        setError(err.message);
      });

    return () => controller.abort();
  }, [apiBase]);

  const loadBookings = async () => {
    if (!apiBase) {
      return;
    }
    try {
      const response = await fetch(
        `${apiBase}/bookings?worker_id=${encodeURIComponent(profileForm.worker_id)}`,
        {
          headers: workerHeaders,
        }
      );
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const data = (await response.json()) as Booking[];
      setBookings(data);
      setBookingError(null);
      if (!selected && data.length > 0) {
        setSelected(data[0]);
      }
    } catch (err) {
      setBookingError((err as Error).message);
    }
  };

  const loadShifts = async () => {
    if (!apiBase) {
      return;
    }
    try {
      const response = await fetch(`${apiBase}/shifts`, {
        headers: workerHeaders,
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const data = (await response.json()) as Shift[];
      setShifts(data);
      setShiftError(null);
    } catch (err) {
      setShifts([]);
      setShiftError((err as Error).message);
    }
  };

  const loadApplications = async () => {
    if (!apiBase || !profileForm.worker_id) {
      return;
    }
    try {
      const response = await fetch(
        `${apiBase}/applications?worker_id=${encodeURIComponent(profileForm.worker_id)}`,
        {
          headers: workerHeaders,
        }
      );
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const data = (await response.json()) as Application[];
      setApplications(data);
      setApplicationsError(null);
    } catch (err) {
      setApplications([]);
      setApplicationsError((err as Error).message);
    }
  };

  const loadProfile = async () => {
    if (!apiBase || !profileForm.worker_id) {
      return;
    }
    try {
      const response = await fetch(`${apiBase}/workers/${profileForm.worker_id}`, {
        headers: workerHeaders,
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const data = (await response.json()) as WorkerProfile;
      setProfileMeta(data);
      setProfileForm({
        worker_id: data.worker_id,
        display_name: data.display_name,
        role: data.role,
        city: data.city,
        experience_years: String(data.experience_years),
        bio: data.bio ?? "",
        languages: data.languages.join(", "),
        email: data.email ?? "",
        phone: data.phone ?? "",
        address: data.address ?? "",
        emergency_contact: data.emergency_contact ?? "",
        pay_rate: data.pay_rate ? String(data.pay_rate) : "",
        notes: data.notes ?? "",
      });
      setProfileStatus(null);
    } catch {
      setProfileMeta(null);
    }
  };

  const pollAll = async () => {
    if (!apiBase || pollInFlight.current) {
      return;
    }
    pollInFlight.current = true;
    try {
      await Promise.all([loadBookings(), loadShifts(), loadApplications()]);
    } finally {
      pollInFlight.current = false;
    }
  };

  useEffect(() => {
    pollAll();
    loadProfile();
  }, [apiBase, profileForm.worker_id]);

  useEffect(() => {
    if (!apiBase) {
      return;
    }
    const interval = setInterval(() => {
      pollAll();
    }, 15000);
    return () => clearInterval(interval);
  }, [apiBase, profileForm.worker_id]);

  const transition = async (action: "check-in" | "check-out") => {
    if (!apiBase || !selected) {
      return;
    }
    setBookingError(null);
    try {  
      const response = await fetch(
        `${apiBase}/bookings/${selected.booking_id}/${action}`,
        {
          method: "POST",
          headers: workerHeaders,
          body: JSON.stringify({ now: new Date().toISOString() }),
        }
      );
      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload?.detail ?? `API error: ${response.status}`);
      }
      const data = (await response.json()) as Booking;
      setSelected(data);
      await loadBookings();
    } catch (err) {
      setBookingError((err as Error).message);
    }
  };

  const applyForShift = async () => {
    if (!apiBase || !selectedShift) {
      return;
    }
    setApplicationStatus(null);
    try {
      const payload = {
        shift_id: selectedShift.shift_id,
        worker_id: profileForm.worker_id,
        message: applicationMessage || null,
        now: new Date().toISOString(),
      };
      const response = await fetch(`${apiBase}/applications`, {
        method: "POST",
        headers: workerHeaders,
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const errorPayload = await response.json();
        throw new Error(errorPayload?.detail ?? `API error: ${response.status}`);
      }
      setApplicationStatus("Application sent.");
      setApplicationMessage("");
      setShowApply(false);
      await loadApplications();
    } catch (err) {
      setApplicationStatus((err as Error).message);
    }
  };

  const saveProfile = async () => {
    if (!apiBase || !profileForm.worker_id) {
      return;
    }
    setProfileStatus(null);
    const languages = profileForm.languages
      .split(",")
      .map((value) => value.trim())
      .filter((value) => value.length > 0);
    const payload = {
      display_name: profileForm.display_name,
      role: profileForm.role,
      city: profileForm.city,
      experience_years: Number(profileForm.experience_years || 0),
      bio: profileForm.bio || null,
      languages,
      email: profileForm.email || null,
      phone: profileForm.phone || null,
      address: profileForm.address || null,
      emergency_contact: profileForm.emergency_contact || null,
      pay_rate: profileForm.pay_rate ? Number(profileForm.pay_rate) : null,
      notes: profileForm.notes || null,
      now: new Date().toISOString(),
    };
    try {
      const response = await fetch(`${apiBase}/workers/${profileForm.worker_id}`, {
        method: "PUT",
        headers: workerHeaders,
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const errorPayload = await response.json();
        throw new Error(errorPayload?.detail ?? `API error: ${response.status}`);
      }
      const data = (await response.json()) as WorkerProfile;
      setProfileMeta(data);
      setProfileStatus("Profile saved.");
    } catch (err) {
      setProfileStatus((err as Error).message);
    }
  };

  const canTransition = (state: string) =>
    selected?.allowed_transitions?.includes(state) ?? false;

  const formatDateTime = (value?: string | null) => {
    if (!value) {
      return "N/A";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString();
  };

  const checkInWindow = () => {
    if (!selected) {
      return "N/A";
    }
    const start = new Date(selected.start_time);
    if (Number.isNaN(start.getTime())) {
      return "N/A";
    }
    const open = new Date(start.getTime() - 30 * 60 * 1000);
    const close = new Date(start.getTime() + 15 * 60 * 1000);
    return `${open.toLocaleTimeString()} - ${close.toLocaleTimeString()}`;
  };

  const openShifts = useMemo(
    () => shifts.filter((shift) => shift.status === "open"),
    [shifts]
  );

  const upcomingBookings = useMemo(() => {
    const now = Date.now();
    return bookings.filter((booking) => {
      const end = new Date(booking.end_time).getTime();
      return (
        end >= now &&
        booking.state !== "cancelled_by_worker" &&
        booking.state !== "cancelled_by_operator"
      );
    });
  }, [bookings]);

  const previousBookings = useMemo(() => {
    const now = Date.now();
    return bookings.filter((booking) => {
      const end = new Date(booking.end_time).getTime();
      return (
        end < now ||
        booking.state === "no_show" ||
        booking.state.startsWith("cancelled")
      );
    });
  }, [bookings]);

  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar style="dark" />
      <View style={[styles.topBar, { paddingTop: insets.top + 8 }]}>
        <Text style={styles.topTitle}>Shift Companion</Text>
        <Text style={styles.topSubtitle}>{health}</Text>
      </View>

      <ScrollView
        contentContainerStyle={[
          styles.container,
          { paddingBottom: TAB_BAR_HEIGHT + 24 + insets.bottom },
        ]}
      >
        {activeTab === "browse" && (
          <>
            <Text style={styles.sectionTitle}>Available shifts</Text>
            <Text style={styles.sectionHint}>
              Filters for role and location are coming soon.
            </Text>
            {shiftError && <Text style={styles.cardError}>{shiftError}</Text>}
            {openShifts.length === 0 && (
              <Text style={styles.cardHint}>No open shifts yet.</Text>
            )}
            {openShifts.map((shift) => (
              <Pressable
                key={shift.shift_id}
                style={styles.listItem}
                onPress={() => {
                  setSelectedShift(shift);
                  setShowApply(true);
                }}
              >
                <Text style={styles.listItemTitle}>{shift.role}</Text>
                <Text style={styles.listItemMeta}>{shift.location}</Text>
                <Text style={styles.listItemMeta}>${shift.pay_rate.toFixed(2)}</Text>
                <Text style={styles.listItemMeta}>{formatDateTime(shift.start_time)}</Text>
              </Pressable>
            ))}
            {showApply && selectedShift && (
              <View style={styles.sheet}>
                <Text style={styles.cardTitle}>Shift details</Text>
                <Text style={styles.cardHint}>{selectedShift.role}</Text>
                <Text style={styles.cardHint}>{selectedShift.location}</Text>
                <Text style={styles.cardHint}>{formatDateTime(selectedShift.start_time)}</Text>
                <Text style={styles.cardHint}>{formatDateTime(selectedShift.end_time)}</Text>
                {selectedShift.notes && (
                  <Text style={styles.cardHint}>{selectedShift.notes}</Text>
                )}
                <TextInput
                  placeholder="Message to venue"
                  value={applicationMessage}
                  onChangeText={(value) => setApplicationMessage(value)}
                  style={styles.input}
                />
                <View style={styles.actions}>
                  <Pressable style={styles.button} onPress={applyForShift}>
                    <Text style={styles.buttonText}>Apply</Text>
                  </Pressable>
                  <Pressable
                    style={[styles.button, styles.buttonSecondary]}
                    onPress={() => setShowApply(false)}
                  >
                    <Text style={styles.buttonText}>Close</Text>
                  </Pressable>
                </View>
                {applicationStatus && <Text style={styles.cardHint}>{applicationStatus}</Text>}
              </View>
            )}
          </>
        )}

        {activeTab === "shifts" && (
          <>
            <View style={styles.shiftTabs}>
              <Pressable
                style={[styles.shiftTab, shiftTab === "upcoming" && styles.shiftTabActive]}
                onPress={() => setShiftTab("upcoming")}
              >
                <Text
                  style={[
                    styles.shiftTabText,
                    shiftTab === "upcoming" && styles.shiftTabTextActive,
                  ]}
                >
                  Upcoming
                </Text>
              </Pressable>
              <Pressable
                style={[styles.shiftTab, shiftTab === "previous" && styles.shiftTabActive]}
                onPress={() => setShiftTab("previous")}
              >
                <Text
                  style={[
                    styles.shiftTabText,
                    shiftTab === "previous" && styles.shiftTabTextActive,
                  ]}
                >
                  Previous
                </Text>
              </Pressable>
              <Pressable
                style={[styles.shiftTab, shiftTab === "applications" && styles.shiftTabActive]}
                onPress={() => setShiftTab("applications")}
              >
                <Text
                  style={[
                    styles.shiftTabText,
                    shiftTab === "applications" && styles.shiftTabTextActive,
                  ]}
                >
                  Applications
                </Text>
              </Pressable>
            </View>
            {shiftTab === "upcoming" && (
              <>
                {upcomingBookings.length === 0 && (
                  <Text style={styles.cardHint}>No upcoming shifts.</Text>
                )}
                {upcomingBookings.map((booking) => (
                  <Pressable
                    key={booking.booking_id}
                    style={styles.listItem}
                    onPress={() => setSelected(booking)}
                  >
                    <Text style={styles.listItemTitle}>{booking.shift_id}</Text>
                    <Text style={styles.listItemMeta}>{booking.state}</Text>
                    <Text style={styles.listItemMeta}>{formatDateTime(booking.start_time)}</Text>
                  </Pressable>
                ))}
              </>
            )}
            {shiftTab === "previous" && (
              <>
                {previousBookings.length === 0 && (
                  <Text style={styles.cardHint}>No previous shifts.</Text>
                )}
                {previousBookings.map((booking) => (
                  <Pressable
                    key={booking.booking_id}
                    style={styles.listItem}
                    onPress={() => setSelected(booking)}
                  >
                    <Text style={styles.listItemTitle}>{booking.shift_id}</Text>
                    <Text style={styles.listItemMeta}>{booking.state}</Text>
                    <Text style={styles.listItemMeta}>{formatDateTime(booking.end_time)}</Text>
                  </Pressable>
                ))}
              </>
            )}
            {shiftTab === "applications" && (
              <>
                {applicationsError && (
                  <Text style={styles.cardError}>{applicationsError}</Text>
                )}
                {applications.length === 0 && (
                  <Text style={styles.cardHint}>No applications yet.</Text>
                )}
                {applications.map((application) => (
                  <View key={application.application_id} style={styles.listItem}>
                    <Text style={styles.listItemTitle}>{application.shift_id}</Text>
                    <Text style={styles.listItemMeta}>{application.status}</Text>
                    {application.message && (
                      <Text style={styles.listItemMeta}>{application.message}</Text>
                    )}
                  </View>
                ))}
              </>
            )}

            <View style={styles.card}>
              <Text style={styles.cardTitle}>Selected shift</Text>
              {!selected && <Text style={styles.cardValue}>No shift loaded yet</Text>}
              {selected && (
                <>
                  <Text style={styles.cardValue}>{selected.state}</Text>
                  <Text style={styles.cardHint}>{selected.shift_id}</Text>
                  <Text style={styles.cardHint}>{formatDateTime(selected.start_time)}</Text>
                  <Text style={styles.cardHint}>{formatDateTime(selected.end_time)}</Text>
                  <Text style={styles.cardHint}>Check-in window: {checkInWindow()}</Text>
                </>
              )}
              {bookingError && <Text style={styles.cardError}>{bookingError}</Text>}
              <View style={styles.actions}>
                <Pressable
                  style={[
                    styles.button,
                    !canTransition("checked_in") && styles.buttonDisabled,
                  ]}
                  onPress={() => transition("check-in")}
                  disabled={!canTransition("checked_in")}
                >
                  <Text style={styles.buttonText}>Check in</Text>
                </Pressable>
                <Pressable
                  style={[
                    styles.button,
                    !canTransition("checked_out") && styles.buttonDisabled,
                  ]}
                  onPress={() => transition("check-out")}
                  disabled={!canTransition("checked_out")}
                >
                  <Text style={styles.buttonText}>Check out</Text>
                </Pressable>
              </View>
            </View>
          </>
        )}

        {activeTab === "profile" && (
          <>
            <Text style={styles.sectionTitle}>Profile</Text>
            <Text style={styles.sectionHint}>Public info is shared with venues.</Text>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Worker identity</Text>
              <TextInput
                placeholder="Worker ID"
                value={profileForm.worker_id}
                onChangeText={(value) =>
                  setProfileForm({ ...profileForm, worker_id: value })
                }
                style={styles.input}
              />
              <TextInput
                placeholder="Display name"
                value={profileForm.display_name}
                onChangeText={(value) =>
                  setProfileForm({ ...profileForm, display_name: value })
                }
                style={styles.input}
              />
              <TextInput
                placeholder="Role"
                value={profileForm.role}
                onChangeText={(value) =>
                  setProfileForm({ ...profileForm, role: value })
                }
                style={styles.input}
              />
              <TextInput
                placeholder="City"
                value={profileForm.city}
                onChangeText={(value) =>
                  setProfileForm({ ...profileForm, city: value })
                }
                style={styles.input}
              />
              <TextInput
                placeholder="Experience years"
                value={profileForm.experience_years}
                onChangeText={(value) =>
                  setProfileForm({ ...profileForm, experience_years: value })
                }
                style={styles.input}
                keyboardType="numeric"
              />
              <TextInput
                placeholder="Languages (comma-separated)"
                value={profileForm.languages}
                onChangeText={(value) =>
                  setProfileForm({ ...profileForm, languages: value })
                }
                style={styles.input}
              />
              <TextInput
                placeholder="Bio"
                value={profileForm.bio}
                onChangeText={(value) => setProfileForm({ ...profileForm, bio: value })}
                style={styles.input}
              />
              {profileMeta && (
                <Text style={styles.cardHint}>
                  Reliability score: {profileMeta.reliability_score.toFixed(2)}
                </Text>
              )}
            </View>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Private info</Text>
              <TextInput
                placeholder="Email"
                value={profileForm.email}
                onChangeText={(value) => setProfileForm({ ...profileForm, email: value })}
                style={styles.input}
              />
              <TextInput
                placeholder="Phone"
                value={profileForm.phone}
                onChangeText={(value) => setProfileForm({ ...profileForm, phone: value })}
                style={styles.input}
              />
              <TextInput
                placeholder="Address"
                value={profileForm.address}
                onChangeText={(value) => setProfileForm({ ...profileForm, address: value })}
                style={styles.input}
              />
              <TextInput
                placeholder="Emergency contact"
                value={profileForm.emergency_contact}
                onChangeText={(value) =>
                  setProfileForm({ ...profileForm, emergency_contact: value })
                }
                style={styles.input}
              />
              <TextInput
                placeholder="Preferred pay rate"
                value={profileForm.pay_rate}
                onChangeText={(value) =>
                  setProfileForm({ ...profileForm, pay_rate: value })
                }
                style={styles.input}
                keyboardType="numeric"
              />
              <TextInput
                placeholder="Private notes"
                value={profileForm.notes}
                onChangeText={(value) => setProfileForm({ ...profileForm, notes: value })}
                style={styles.input}
              />
              <Pressable style={styles.button} onPress={saveProfile}>
                <Text style={styles.buttonText}>Save profile</Text>
              </Pressable>
              {profileStatus && <Text style={styles.cardHint}>{profileStatus}</Text>}
            </View>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>API Status</Text>
              <Text style={styles.cardValue}>{health}</Text>
              {error && <Text style={styles.cardError}>{error}</Text>}
              <Text style={styles.cardLabel}>API Base URL</Text>
              <TextInput
                placeholder="https://api.example.com"
                value={apiBase}
                onChangeText={setApiBase}
                style={styles.input}
                autoCapitalize="none"
              />
            </View>
          </>
        )}
      </ScrollView>

      <View style={[styles.tabBar, { paddingBottom: insets.bottom }]}>
        <Pressable
          style={[styles.tabButton, activeTab === "browse" && styles.tabButtonActive]}
          onPress={() => setActiveTab("browse")}
        >
          <Text style={styles.tabText}>Browse</Text>
        </Pressable>
        <Pressable
          style={[styles.tabButton, activeTab === "shifts" && styles.tabButtonActive]}
          onPress={() => setActiveTab("shifts")}
        >
          <Text style={styles.tabText}>Shifts</Text>
        </Pressable>
        <Pressable
          style={[styles.tabButton, activeTab === "profile" && styles.tabButtonActive]}
          onPress={() => setActiveTab("profile")}
        >
          <Text style={styles.tabText}>Profile</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <AppContent />
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: COLORS.canvas,
  },
  container: {
    padding: 24,
    paddingBottom: 120,
    gap: 18,
  },
  topBar: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  topTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: COLORS.ink,
  },
  topSubtitle: {
    fontSize: 12,
    color: COLORS.inkMuted,
  },
  tabBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: "row",
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    backgroundColor: COLORS.surface,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: "center",
  },
  tabButtonActive: {
    borderTopWidth: 2,
    borderTopColor: COLORS.primary,
  },
  tabText: {
    fontWeight: "600",
    color: COLORS.ink,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: COLORS.ink,
  },
  sectionHint: {
    fontSize: 12,
    color: COLORS.inkMuted,
  },
  shiftTabs: {
    flexDirection: "row",
    gap: 12,
  },
  shiftTab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: COLORS.surface,
    alignItems: "center",
  },
  shiftTabActive: {
    backgroundColor: COLORS.primary,
  },
  shiftTabText: {
    fontWeight: "600",
    color: COLORS.ink,
  },
  shiftTabTextActive: {
    color: COLORS.onPrimary,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 18,
    padding: 18,
    shadowColor: COLORS.ink,
    shadowOpacity: 0.08,
    shadowRadius: 10,
    elevation: 2,
    gap: 10,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: COLORS.ink,
  },
  cardValue: {
    fontSize: 20,
    fontWeight: "700",
    color: COLORS.ink,
  },
  cardError: {
    color: COLORS.error,
    fontSize: 12,
  },
  cardLabel: {
    fontSize: 12,
    color: COLORS.primary,
    marginTop: 8,
  },
  cardHint: {
    fontSize: 12,
    color: COLORS.inkMuted,
  },
  input: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 10,
    fontSize: 14,
  },
  actions: {
    flexDirection: "row",
    gap: 12,
  },
  button: {
    backgroundColor: COLORS.primary,
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 12,
  },
  buttonSecondary: {
    backgroundColor: COLORS.primaryDeep,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    color: COLORS.onPrimary,
    fontWeight: "600",
  },
  listItem: {
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginTop: 8,
    backgroundColor: COLORS.surface,
  },
  listItemTitle: {
    fontWeight: "600",
    color: COLORS.ink,
  },
  listItemMeta: {
    fontSize: 12,
    color: COLORS.inkMuted,
  },
  sheet: {
    backgroundColor: COLORS.surface,
    borderRadius: 18,
    padding: 18,
    gap: 10,
    marginTop: 12,
  },
});
