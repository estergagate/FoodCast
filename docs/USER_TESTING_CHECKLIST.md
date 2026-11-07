# FoodCast User Testing Checklist

Tester:
Date:
Browser:
Device:
Screen size:

Use the following result values:

- Pass — the feature worked correctly
- Fail — the feature did not work correctly
- Not tested — the test was not performed

## 1. Registration and Account

| No. | Test | Expected result | Actual result | Status |
|---|---|---|---|---|
| 1.1 | Open the registration page | The registration form opens correctly | | |
| 1.2 | Submit empty fields | The system asks the user to complete the required fields | | |
| 1.3 | Enter an invalid email | The system asks for a valid email address | | |
| 1.4 | Enter weak or unmatched passwords | The system explains the password requirement | | |
| 1.5 | Enter an existing username | The system says the username is already taken | | |
| 1.6 | Register with valid information | A verification code is sent to the email | | |
| 1.7 | Enter an incorrect verification code | The account is not created | | |
| 1.8 | Enter the correct verification code | The account is created successfully | | |
| 1.9 | Sign in with the new account | A sign-in verification code is sent | | |
| 1.10 | Complete sign-in verification | The business Home page opens | | |

## 2. Products

| No. | Test | Expected result | Actual result | Status |
|---|---|---|---|---|
| 2.1 | Add a valid product | The product appears in the product list | | |
| 2.2 | Add a product with an empty name | The system asks for a product name | | |
| 2.3 | Add the same product twice | The system prevents the duplicate product | | |
| 2.4 | Search for a product | Only matching products are displayed | | |
| 2.5 | Edit one product | The product information is updated | | |
| 2.6 | Select and edit several products | Every selected product appears on the edit page | | |
| 2.7 | Select and delete several products | The selected products are removed | | |
| 2.8 | Export products | The spreadsheet downloads successfully | | |

## 3. Sales

| No. | Test | Expected result | Actual result | Status |
|---|---|---|---|---|
| 3.1 | Record a valid sale | The sale appears in the sales list | | |
| 3.2 | Record a sale without selecting a product | The system asks the user to select a product | | |
| 3.3 | Enter a negative quantity | The system rejects the quantity | | |
| 3.4 | Enter a future date | The system rejects the future sales date | | |
| 3.5 | Record more sales than available stock | The system explains that stock is insufficient | | |
| 3.6 | Edit one sales record | The updated values appear correctly | | |
| 3.7 | Edit several selected sales records | Every selected sale appears on the edit page | | |
| 3.8 | Delete several selected sales records | The selected sales are removed | | |
| 3.9 | Search for a sales record | Matching records are displayed | | |
| 3.10 | Filter sales by date | Only records inside the selected dates appear | | |
| 3.11 | Export sales | The spreadsheet downloads successfully | | |

## 4. Stock

| No. | Test | Expected result | Actual result | Status |
|---|---|---|---|---|
| 4.1 | Add stock to a product | Available stock increases | | |
| 4.2 | Record damaged or wasted stock | Available stock decreases | | |
| 4.3 | Enter a negative or zero quantity | The system rejects the invalid quantity | | |
| 4.4 | Remove more than the available stock | The system prevents negative stock | | |
| 4.5 | Record a sale | The sold quantity is deducted from stock | | |
| 4.6 | Edit a sale quantity | Stock is adjusted using the changed quantity | | |
| 4.7 | Delete a sale | The deleted sale quantity is returned to stock | | |
| 4.8 | Search the stock list | Matching products are displayed | | |

## 5. Sales Forecast

| No. | Test | Expected result | Actual result | Status |
|---|---|---|---|---|
| 5.1 | Generate a forecast without products | The system asks the user to add products | | |
| 5.2 | Generate a forecast without sales | The system asks the user to record sales | | |
| 5.3 | Product has fewer than 7 recorded days | The system says there is not enough history | | |
| 5.4 | Product has 7–89 recorded days | The day-of-week method is used | | |
| 5.5 | Product has at least 90 recorded days | Random Forest Regression is used | | |
| 5.6 | Generate a next-day forecast | One estimated day is displayed | | |
| 5.7 | Generate a 7-day forecast | Seven estimated days are displayed | | |
| 5.8 | Generate a 30-day forecast | Thirty estimated days are displayed | | |
| 5.9 | Click Generate forecast | A loading message appears while processing | | |
| 5.10 | Review the forecast chart | Past sales and estimated demand are displayed | | |
| 5.11 | Review the forecast test | MAE, RMSE, percentage error and reliability appear | | |
| 5.12 | View on a small screen | The page remains usable without overlapping content | | |

## 6. Decision Support

| No. | Test | Expected result | Actual result | Status |
|---|---|---|---|---|
| 6.1 | Estimated demand is higher than stock | The system recommends preparing more items | | |
| 6.2 | Stock is enough for estimated demand | The system says that stock is enough | | |
| 6.3 | A product has low stock | A low-stock recommendation appears | | |
| 6.4 | Recent sales have a best seller | The best-selling product is identified | | |
| 6.5 | Waste is recorded | The system recommends reviewing wasted stock | | |
| 6.6 | Recent sales records are incomplete | The system asks the user to complete daily records | | |
| 6.7 | Weather information is available | Weather advice appears separately from the sales estimate | | |
| 6.8 | Open Business Tips | Recommendations use the business’s products, sales and stock | | |

## 7. General Use

| No. | Test | Expected result | Actual result | Status |
|---|---|---|---|---|
| 7.1 | Open every sidebar page | Every link opens the correct page | | |
| 7.2 | Open the Help Center | The Help Center opens correctly | | |
| 7.3 | Search the Help Center | Matching instructions are displayed | | |
| 7.4 | Switch between light and dark mode | The theme changes without unreadable content | | |
| 7.5 | Collapse and open the sidebar | The sidebar changes size correctly | | |
| 7.6 | Edit the business profile | The updated information is saved | | |
| 7.7 | Change the account email | The new email is verified before being saved | | |
| 7.8 | Change the password | The new password works during the next sign-in | | |
| 7.9 | Sign out | The session ends and the sign-in page opens | | |
| 7.10 | Use the Back button after signing out | Protected business pages remain unavailable | | |

# Test Summary

Total tests:
Passed:
Failed:
Not tested:

Overall result:

## Problems Found

| Test number | Problem | Steps that caused it | Screenshot or error | Fix status |
|---|---|---|---|---|

## Tester Comments

Write any parts that were confusing, difficult to find or difficult to understand.

## Final Decision

- [ ] The system is ready for demonstration.
- [ ] The system needs minor fixes.
- [ ] The system needs major fixes.

Tester signature:
Date: