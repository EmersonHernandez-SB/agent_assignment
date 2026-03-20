# Insurance and Coverage Management

## Overview

EmerClinic allows you to store patient insurance policies and verify coverage details directly within the platform. Insurance management is available on the **Premium plan** only.

## Adding an Insurance Policy to a Patient

1. Open the patient's profile (**Patients → Patient List → select patient**).
2. Click the **Insurance** tab.
3. Click **Add Insurance Policy**.
4. Fill in the required fields:
   - Insurance Provider Name (e.g., Delta Dental, Aetna, BlueCross)
   - Policy Number
   - Group Number (if applicable)
   - Policy Holder Name (if different from patient)
   - Effective Date and Expiration Date
5. Optionally add coverage details:
   - Annual deductible
   - Co-pay amount
   - Covered procedures (e.g., cleanings, X-rays, fillings, crowns)
6. Click **Save Policy**.

## Checking Coverage for a Procedure

1. Open the patient's profile and go to the **Insurance** tab.
2. Click **Check Coverage**.
3. Select the procedure type from the dropdown (e.g., Routine Cleaning, Root Canal, Crown).
4. EmerClinic will display:
   - Whether the procedure is covered under the patient's plan
   - The estimated patient responsibility after insurance
   - Remaining deductible for the current year
   - Any waiting period restrictions

> **Note:** Coverage data is based on the information entered manually. EmerClinic does not connect directly to insurance company systems for real-time eligibility verification.

## Updating or Renewing a Policy

1. Open the patient's Insurance tab.
2. Click **Edit** next to the active policy.
3. Update the relevant fields (e.g., new expiration date, new policy number).
4. Click **Save**.

## Removing an Insurance Policy

1. Open the patient's Insurance tab.
2. Click **Actions → Deactivate Policy** next to the policy.
3. Deactivated policies are hidden from the active view but preserved in the patient's history.

## Insurance Reports

Go to **Reports → Insurance** to see:
- Claims by insurance provider
- Outstanding balances by payer
- Procedures billed by coverage type

These reports help identify which insurance providers are generating the most revenue and where claim denials are occurring.

## Common Questions

**Can EmerClinic submit claims directly to insurance companies?**
Not currently. EmerClinic generates a claim summary that you can submit manually or through your clearinghouse. Direct claim submission is on the product roadmap.

**What if the patient has two insurance policies (dual coverage)?**
You can add multiple policies per patient. Set one as "Primary" and one as "Secondary". EmerClinic will apply the primary first when calculating patient responsibility.
