export type BrowseNotificationParams = {
  shift_id?: string;
  notification_key?: string;
};

export type ShiftsNotificationParams = {
  focus?: "upcoming" | "previous" | "applications";
  notification_key?: string;
  application_id?: string;
  booking_id?: string;
  open?: "messages";
};

export type RootTabParamList = {
  Browse: BrowseNotificationParams | undefined;
  Shifts: ShiftsNotificationParams | undefined;
  Alerts: undefined;
  Earnings: undefined;
  Profile: undefined;
};
