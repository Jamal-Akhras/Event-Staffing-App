export type BrowseNotificationParams = {
  shift_id?: string;
  notification_key?: string;
};

export type ShiftsNotificationParams = {
  notification_key?: string;
  application_id?: string;
  booking_id?: string;
  open?: "messages";
};

export type ApplicationsNotificationParams = {
  application_id?: string;
  open?: "messages";
};

export type ProfileStackParamList = {
  ProfileHome: undefined;
  ProfileDetails: undefined;
  NotificationSettings: undefined;
  PrivacySettings: undefined;
  Certifications: undefined;
  AccountSettings: undefined;
};

export type RootTabParamList = {
  Browse: BrowseNotificationParams | undefined;
  Shifts: ShiftsNotificationParams | undefined;
  Applications: ApplicationsNotificationParams | undefined;
  Alerts: undefined;
  Earnings: undefined;
  Profile: undefined;
};
