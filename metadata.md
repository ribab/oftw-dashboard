# One for the World Data Dictionary

## Pledges Dataset

| Column | Description | Notes |
|--------|-------------|--------|
| donor_id | Unique identifier of each donor | |
| pledge_id | Unique identifier of each pledge | A donor might have made several pledges over time. A change in amount or frequency of pledges creates a 'new' pledge. |
| donor_chapter | The channel where a donor first signed their pledge | There is no difference between n/a and empty cells. Both are unknown. |
| chapter_type | Categories of donor_chapter | For example, UG is Undergraduate |
| pledge_status | self-explanatory | Pledges might get cancelled or change. Many metrics will want to focus on 'active' or 'pledged' (future) pledges |
| pledge_created_at | self-explanatory | |
| pledge_starts_at | self-explanatory | |
| pledge_ended_at | self-explanatory | |
| contribution_amount | Amount of money the donor pledged | |
| currency | Currency to be used for pledged payments | Many metrics on the wishlist will want these converted to USD |
| frequency | Frequency of pledged payments | |
| payment_platform | The Platform that processed the payment | |

## Payments Dataset

| Column | Description | Notes |
|--------|-------------|--------|
| id | Payment ID | |
| donor_id | Unique identifier of each donor | |
| payment_platform | The Platform that processed the payment | |
| portfolio | Where the donor chose to donate to | OFTW recommends currently 4 top charities, so choosing "OFTW Top Picks" will distribute your donation 25% to each. However, donors can customise their donation and choose just one of OFTW's recommended charities to give 100% of their donation to ("OFTW Top Pick: NameOfOrganization"). "Entire OFTW Portfolio" was promoted by OFTW in prior years but some people are still on it. It includes more charities than just the top 4 recommended ones. |
| amount | Amount of money donated | |
| currency | Currency in which the payment was made | |
| date | Date of payment | |
| counterfactuality | How likely it is that this is a donation that wouldn't have happened otherwise (if OFTW didn't exist) | 0-1 where 0 is 0% counterfactual, and the donation would likely have happened even if OFTW didn't exist. 1 for a 100% original donation that wouldn't have happened without OFTW. The closer the number is to 1 the more impactful OFTW is. |
| pledge_id | Unique identifier of each pledge | A donor might have made several pledges over time. A change in amount or frequency of pledges creates a 'new' pledge. | 