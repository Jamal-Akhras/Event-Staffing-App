import { ProfileField } from "./ProfileField";
import type { ProfileForm } from "./profileForm";

type ProfileFieldsProps = {
  form: ProfileForm;
  onChange: (form: ProfileForm) => void;
};

export function PublicProfileFields({ form, onChange }: ProfileFieldsProps) {
  return (
    <>
      <ProfileField
        placeholder="Worker ID"
        value={form.worker_id}
        onChangeText={(worker_id) => onChange({ ...form, worker_id })}
      />
      <ProfileField
        placeholder="Display name"
        value={form.display_name}
        onChangeText={(display_name) => onChange({ ...form, display_name })}
      />
      <ProfileField
        placeholder="Role"
        value={form.role}
        onChangeText={(role) => onChange({ ...form, role })}
      />
      <ProfileField
        placeholder="Experience years"
        value={form.experience_years}
        keyboardType="numeric"
        onChangeText={(experience_years) => onChange({ ...form, experience_years })}
      />
      <ProfileField
        placeholder="Languages, comma-separated"
        value={form.languages}
        onChangeText={(languages) => onChange({ ...form, languages })}
      />
      <ProfileField
        placeholder="Bio"
        value={form.bio}
        multiline
        onChangeText={(bio) => onChange({ ...form, bio })}
      />
    </>
  );
}

export function PrivateProfileFields({ form, onChange }: ProfileFieldsProps) {
  return (
    <>
      <ProfileField
        placeholder="Email"
        value={form.email}
        keyboardType="email-address"
        onChangeText={(email) => onChange({ ...form, email })}
      />
      <ProfileField
        placeholder="Phone"
        value={form.phone}
        keyboardType="phone-pad"
        onChangeText={(phone) => onChange({ ...form, phone })}
      />
      <ProfileField
        placeholder="Address"
        value={form.address}
        onChangeText={(address) => onChange({ ...form, address })}
      />
      <ProfileField
        placeholder="Emergency contact"
        value={form.emergency_contact}
        onChangeText={(emergency_contact) => onChange({ ...form, emergency_contact })}
      />
      <ProfileField
        placeholder="Preferred pay rate"
        value={form.pay_rate}
        keyboardType="numeric"
        onChangeText={(pay_rate) => onChange({ ...form, pay_rate })}
      />
      <ProfileField
        placeholder="Private notes"
        value={form.notes}
        multiline
        onChangeText={(notes) => onChange({ ...form, notes })}
      />
    </>
  );
}
