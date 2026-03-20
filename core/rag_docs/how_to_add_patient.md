# How to Add a New Patient

## Adding a Patient Manually

1. From the main menu, go to **Patients → Add New Patient**.
2. Fill in the required fields:
   - First Name, Last Name
   - Date of Birth
   - Gender
   - Primary phone number
3. Fill in the optional fields as available:
   - Email address
   - Home address
   - Emergency contact name and phone
   - Insurance policy number (links to an existing policy in the system)
4. Click **Save Patient**. The patient is now active and can be scheduled.

## Bulk Import Patients via CSV (Premium only)

1. Go to **Patients → Import Patients**.
2. Download the EmerClinic CSV template by clicking **Download Template**.
3. Fill in the template with your patient data. Do not change the column headers.
4. Required columns: `first_name`, `last_name`, `date_of_birth`, `phone`
5. Optional columns: `email`, `address`, `insurance_policy_number`, `gender`
6. Save the file as `.csv` (UTF-8 encoding).
7. Click **Upload CSV** and select your file.
8. EmerClinic will validate the file and show a preview. Rows with errors are highlighted in red with an explanation.
9. Fix any errors and re-upload, or click **Import Valid Rows** to skip errored rows and import the rest.
10. A confirmation email is sent to the admin with the import summary.

## Editing Patient Information

1. Go to **Patients → Patient List**.
2. Search for the patient by name or ID.
3. Click their name to open the patient profile.
4. Click **Edit** in the top-right corner.
5. Make your changes and click **Save**.

## Deactivating a Patient

Deactivating a patient removes them from scheduling views but preserves all their records.

1. Open the patient profile.
2. Click **Actions → Deactivate Patient**.
3. Confirm the action.

To reactivate, go to **Patients → Inactive Patients**, find the patient, and click **Reactivate**.

## Notes

- Patient IDs are assigned automatically by EmerClinic and cannot be changed.
- Duplicate detection: if a patient with the same name and date of birth already exists, EmerClinic will warn you before saving.
