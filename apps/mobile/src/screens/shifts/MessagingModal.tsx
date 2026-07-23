import { Modal, Pressable, StyleSheet, Text, View } from "react-native";

import { MessageThread } from "../../components/MessageThread";
import { useAuth } from "../../contexts/AuthContext";
import { COLORS } from "../../theme/colors";
import type { Application, Booking } from "../../types";

type MessagingModalProps = {
  application: Application | null;
  booking: Booking | null;
  onClose: () => void;
};

export function MessagingModal({ application, booking, onClose }: MessagingModalProps) {
  const { user } = useAuth();
  const visible = application !== null || booking !== null;
  const shiftId = application?.shift_id ?? booking?.shift_id;

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet">
      <View style={styles.container}>
        <View style={styles.header}>
          <View>
            <Text style={styles.title}>Messages</Text>
            <Text style={styles.subtitle}>
              {application
                ? `Application ${application.application_id.slice(0, 8)}`
                : booking
                ? `Booking ${booking.booking_id.slice(0, 8)}`
                : ""}
            </Text>
          </View>
          <Pressable style={styles.closeButton} onPress={onClose}>
            <Text style={styles.closeText}>Close</Text>
          </Pressable>
        </View>

        {shiftId && (
          <MessageThread
            shiftId={shiftId}
            applicationId={application?.application_id}
            bookingId={booking?.booking_id}
            currentUserRole="worker"
          />
        )}
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.canvas,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 18,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: COLORS.surface,
  },
  title: {
    color: COLORS.ink,
    fontSize: 20,
    fontWeight: "900",
  },
  subtitle: {
    color: COLORS.inkMuted,
    marginTop: 2,
  },
  closeButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  closeText: {
    color: COLORS.primary,
    fontWeight: "900",
  },
});
