# HIPAA Compliance and Data Security

## Is EmerClinic HIPAA Compliant?

Yes. EmerClinic is designed to meet HIPAA requirements for covered entities (dental and medical clinics). We sign a **Business Associate Agreement (BAA)** with all clinic accounts.

To request your BAA:
1. Go to **Settings → Account → Legal Documents**.
2. Click **Request BAA**.
3. A signed copy will be emailed to the account admin within 1 business day.

## How Patient Data is Protected

- **Encryption at rest:** All patient data is encrypted using AES-256.
- **Encryption in transit:** All data transmitted between your browser and EmerClinic servers uses TLS 1.2 or higher.
- **Access controls:** Role-based permissions ensure staff only see the data relevant to their role.
- **Audit logs:** All access to patient records is logged and available to admins under **Settings → Security → Audit Log**.
- **Data centers:** EmerClinic runs on AWS infrastructure located in the United States (us-east-1 and us-west-2 regions).

## User Roles and Permissions

EmerClinic has three built-in roles:

| Role        | Access Level                                                              |
|-------------|---------------------------------------------------------------------------|
| Admin       | Full access: settings, billing, all patient data, team management         |
| Provider    | Patient records, scheduling, medical notes for their own patients         |
| Front Desk  | Scheduling, patient demographics, invoices — no medical records access    |

Custom roles can be created on the Premium plan under **Settings → Team → Roles**.

## Two-Factor Authentication (2FA)

EmerClinic supports 2FA via authenticator app (Google Authenticator, Authy) or SMS.

To enable 2FA:
1. Go to **My Profile → Security → Two-Factor Authentication**.
2. Click **Enable 2FA**.
3. Scan the QR code with your authenticator app or enter the manual key.
4. Enter the 6-digit code to confirm.

Admins can enforce 2FA for all users under **Settings → Security → Require 2FA**.

## Data Retention and Deletion

- Active accounts: data retained indefinitely.
- Cancelled accounts: data retained for 90 days, then permanently deleted.
- Medical records: retained for a minimum of 7 years to comply with medical record retention laws, even after account cancellation, unless a deletion request is submitted in writing.
- To request early deletion: contact privacy@emerclinic.com with your account ID and a signed deletion authorization form.

## Breach Notification

In the event of a data breach affecting patient data, EmerClinic will:
1. Notify affected clinic accounts within 60 days of discovery (as required by HIPAA).
2. Provide a detailed breach report.
3. Offer guidance on patient notification requirements.

## Data Backups

- EmerClinic performs automated backups every 6 hours.
- Backups are retained for 30 days.
- In the event of data loss, point-in-time recovery is available. Contact support to initiate a restore.
