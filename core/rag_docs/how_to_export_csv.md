# How to Export Patient Data as CSV

EmerClinic allows you to export patient records, appointments, and billing data in CSV format. This is available on both Basic and Premium plans.

## Export Patient Records

1. From the main menu, go to **Patients → Patient List**.
2. Use the search/filter bar to narrow down results (optional).
3. Click the **Export** button in the top-right corner.
4. Select **Export as CSV**.
5. Choose which fields to include:
   - Patient ID, First Name, Last Name
   - Date of Birth, Gender
   - Contact Info (phone, email, address)
   - Insurance Policy Number
   - Last Visit Date
6. Click **Download**. The file will be saved to your default downloads folder.

> **Note:** Patient exports are limited to 5,000 records per file. For larger exports, use date filters to split into multiple files.

## Export Appointments

1. Go to **Scheduling → Appointments**.
2. Set your desired date range using the date picker.
3. Optionally filter by provider or appointment status.
4. Click **Export → Export as CSV**.
5. The CSV includes: Appointment ID, Patient Name, Provider, Date/Time, Status, Reason for Visit.

## Export Invoices and Billing Data

1. Go to **Settings → Billing → Invoices**.
2. Filter by date range or payment status if needed.
3. Click **Export → Export as CSV**.
4. Fields included: Invoice ID, Patient Name, Amount, Status, Issue Date, Due Date, Payment Date.

## Export Medical Records (Premium only)

1. Go to **Patients → select a patient → Medical Records**.
2. Click **Export Records → CSV**.
3. For HIPAA compliance, exported files containing medical records are password-protected. The password is sent to the account admin's email.

## Troubleshooting Export Issues

- **Export button is greyed out:** You may not have the required permissions. Ask your admin to grant you "Export" access under **Settings → Team → Permissions**.
- **CSV opens with garbled text:** Open the file in Excel using **Data → From Text/CSV** and select UTF-8 encoding.
- **Large exports time out:** Break the export into smaller date ranges (e.g., 3 months at a time).
- **Missing fields in the export:** Ensure the fields were not hidden in your column settings. Go to **Export Settings** to add them back.
