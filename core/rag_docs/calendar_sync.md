# Calendar Sync

EmerClinic supports two-way calendar sync with **Google Calendar** and **Microsoft Outlook**. This feature is available on the **Premium plan** only.

## What Gets Synced

- New appointments created in EmerClinic appear in the provider's connected calendar.
- Cancellations and reschedules in EmerClinic are reflected in the external calendar.
- Events created in Google/Outlook are **not** imported into EmerClinic (one-way sync from EmerClinic outward).

## Setting Up Google Calendar Sync

1. Go to **Settings → Integrations → Calendar Sync**.
2. Click **Connect Google Calendar**.
3. You will be redirected to Google's authorization page. Sign in with the Google account you want to sync to.
4. Grant EmerClinic the requested permissions (read/write access to calendar events).
5. Select which Google Calendar to sync to (if the account has multiple calendars).
6. Click **Save**. Sync is now active.

## Setting Up Outlook Calendar Sync

1. Go to **Settings → Integrations → Calendar Sync**.
2. Click **Connect Outlook Calendar**.
3. Sign in with your Microsoft account when prompted.
4. Grant the requested permissions.
5. Select the target calendar.
6. Click **Save**.

## Per-Provider Calendar Sync

Each provider can connect their own calendar independently.

1. Ask the provider to go to **My Profile → Calendar Sync**.
2. They follow the same Google or Outlook steps above.
3. Only their own appointments are synced to their personal calendar.

## Troubleshooting Calendar Sync

**Appointments not showing in Google/Outlook:**
- Check that the sync is still authorized: go to **Settings → Integrations → Calendar Sync** and verify the status shows "Connected".
- If it shows "Disconnected" or "Error", click **Reconnect** and reauthorize.
- Google and Outlook tokens expire every 60 days. You will receive an email reminder to reconnect.

**Duplicate events in calendar:**
- This can happen if the same provider connected the same calendar twice. Go to **Settings → Integrations → Calendar Sync**, disconnect, and reconnect once.

**Can't connect — authorization error:**
- Make sure you are not using a work Google/Microsoft account that has third-party app restrictions enforced by your IT department.
- Contact your IT admin to whitelist EmerClinic's OAuth app, or use a personal account.

## Disconnecting Calendar Sync

1. Go to **Settings → Integrations → Calendar Sync**.
2. Click **Disconnect** next to the calendar you want to remove.
3. Future appointments will no longer sync. Previously synced events remain in the external calendar but will not be updated.
