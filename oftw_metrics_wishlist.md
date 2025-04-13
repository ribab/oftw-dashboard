# One for the World Metrics Wishlist

## Objectives and Key Results

### Money Movement Metrics

| Metric | Target for 2025 | Notes | Description |
|--------|----------------|--------|-------------|
| Money Moved (monthly + total FYTD) | $1.8M | Our fiscal year runs July 1-June 30, so last fiscal year was July 1, 2023 - June 30 2024 | Tracks actual donations flowing through OFTW, measured both monthly and fiscal year-to-date. Excludes internal funds like Discretionary Fund and Operating Costs. |
| Counterfactual MM | $1.26M | The payments dataset also has a column 'counterfactuality' which will be between 0-1, to determine how 'counterfactual' the payment is. Which is, how likely it is that this is money that would not have otherwise been donated. Also exclude "One for the World Discretionary Fund" and "One for the World Operating Costs" from the portfolio column. Calculate the MM by multiplying the counterfactual column by the amount column. | A sophisticated impact measure that estimates donation "additionality" using a 0-1 score to calculate how much of each donation would not have happened without OFTW's influence. |
| Active Annualized Run Rate (By Channel) | $1.2M | Pledges dataset, converting to USD, active pledges are ones with pledge_status 'Active donor'. The ARR is the total donations per year, so convert monthly and quarterly to how much they would be over the whole year | Projects annual donation volume based on current active donations, normalizing different frequencies (monthly/quarterly) to annual amounts. Broken down by donation channels. |
| Pledge Attrition Rate | 18% | Pledges dataset: what proportion are being cancelled (pledge_status Payment failure or Churned donor). Calculate attrition rate as you see fit. | Measures the rate of pledge losses, including both payment failures and voluntary donor churn. Key metric for understanding donor retention. |
| Total number of active donors | 1,200 | Pledges dataset, only include 'one-time' donor and 'Active donor' under pledge_status, count number of unique donor_ids | Counts unique individuals currently contributing, including both one-time donors and active recurring donors. |
| Total number of active pledges (paying now) | 850 | Pledges dataset, only include 'Active donor' under pledge_status, count number of unique donor_ids | Specifically counts recurring pledges currently active, excluding one-time donors. |
| Chapter ARR (current and unstarted, by chapter type) | $670,000 | Pledges dataset, by chapter and chapter type, converted to USD | Breaks down annual run rate by different chapters, including both currently active and committed future pledges. Segmented by chapter type. |

## Money Moved Details

### Core Metrics

| Metric | Target | Notes | Description |
|--------|---------|--------|-------------|
| Money Moved (monthly + total YTD) | $1.8M | In the payments dataset, excluding "One for the World Discretionary Fund" and "One for the World Operating Costs" from the portfolio column | Primary metric tracking actual donation flow, excluding internal operational funds. Measured both monthly and year-to-date. |
| Counterfactual MM | $1.26M | Calculate the MM by multiplying the counterfactual column by the amount column | Impact-adjusted donation metric that accounts for OFTW's direct influence on giving behavior. |

### Additional Breakdowns
- By platform (Benevity, Donational, off platform)
- By Source (chapter types, etc)
- By month
- Reoccuring v. One-Time

## Pledge Performance

### Monthly Tracking Metrics

| Metric | Target | Notes | Description |
|--------|---------|--------|-------------|
| ALL pledges (active + future pledges) | 1,850 | Pledges dataset, 'pledge_status' column Pledged donor and Active donor | Total pledge count combining both currently active donations and committed future pledges. |
| Future pledges | 1,000 | Pledges dataset, 'pledge_status' column equals 'Pledged donor' | Count of committed but not yet active pledges, indicating future growth pipeline. |
| Active Pledges | 850 | Pledges dataset, 'pledge_status' column equals 'Active donor' | Number of currently active recurring pledges in the system. |
| ALL ARR | $1.8M | Future ARR + Active ARR | Combined annual run rate including both active and future committed pledges. |
| Future ARR | $600,000 | Pledges dataset, 'pledge_status' equals 'Pledged donor', converted to USD | Projected annual value of committed future pledges, converted to USD. |
| Active ARR | $1.2M | Pledges dataset, 'pledge_status' equals 'Active donor', converted to USD | Current annual run rate from active pledges only, in USD. |
| Monthly Attrition | 18% | Pledges dataset, what proportion has the status changed to Payment failure or Churned donor | Monthly rate of pledge losses, tracking transitions to payment failure or churned status. |

_Note: All of the above metrics should also be broken down by channel/chapter on a monthly basis (TBD)_ 