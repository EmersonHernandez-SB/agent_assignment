# User Roles and Permissions

## Built-in Roles

EmerClinic has three built-in roles assigned to every user.

### Admin
- Full access to all features including settings, billing, and team management.
- Can add, edit, and deactivate other users.
- Can view all patient records regardless of assigned provider.
- Receives all system notifications and billing emails.
- Recommended for: clinic owner, office manager.

### Provider
- Access to their own patient records, appointment calendar, and medical notes.
- Can view patient demographics and insurance info.
- Cannot access billing settings, subscription management, or other providers' records.
- Recommended for: doctors, dentists, hygienists, nurse practitioners.

### Front Desk
- Can schedule, cancel, and reschedule appointments for all providers.
- Can view and edit patient demographics.
- Can generate and send invoices.
- Cannot view medical records, clinical notes, or billing settings.
- Recommended for: receptionists, scheduling coordinators.

## Custom Roles (Premium only)

Admins can create custom roles with granular permissions.

1. Go to **Settings → Team → Roles → Create New Role**.
2. Name the role (e.g., "Billing Specialist", "Medical Records Clerk").
3. Toggle individual permissions on or off:
   - View/edit patient records
   - View/edit medical records
   - Manage scheduling
   - Export data
   - Manage billing
   - View reports
   - Manage team
4. Click **Save Role**.
5. Assign the role to users under **Settings → Team → Users**.

## Adding a New User

1. Go to **Settings → Team → Users → Add User**.
2. Enter their name, email address, and select their role.
3. Click **Send Invite**.
4. The user will receive an email invitation to set up their password and log in.
5. They appear as "Invite Pending" until they complete setup.

## Deactivating a User

1. Go to **Settings → Team → Users**.
2. Click the user's name.
3. Click **Deactivate User**.
4. Their account is immediately locked. Their records and activity history are preserved.

## Password and Security Policies

Admins can enforce the following under **Settings → Security**:
- Minimum password length (default: 8 characters)
- Require 2FA for all users
- Session timeout (default: 8 hours of inactivity)
- IP allowlist (restrict logins to specific IP addresses or ranges)
