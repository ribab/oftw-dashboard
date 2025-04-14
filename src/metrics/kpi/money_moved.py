from vizro.models.types import capture
import pandas as pd
import numpy as np
from datetime import datetime
import calendar
from vizro.models.types import capture
from components.kpi_card import create_kpi_card
import pandas as pd
import numpy as np

# def kpi_card(df, fiscal_year=None, counterfactual=False):
def kpi_card(data_frame):
    """
    Create a KPI card showing money moved for the current fiscal year.
    
    Args:
        df (pd.DataFrame): DataFrame containing payment data
        fiscal_year (str, optional): Fiscal year in format "YYYY-YYYY". Defaults to current fiscal year.
        counterfactual (bool): Whether to calculate counterfactual money moved
        
    Returns:
        dash component: A KPI card showing money moved metrics
    """
    df = data_frame.copy()
    df['date'] = pd.to_datetime(df['date'])
    last_date = df["date"].max()
    fiscal_year = None
    counterfactual = False

    if fiscal_year is None:
        start_date = None
        end_date = None
    else:
        start_date = pd.Timestamp(fiscal_year.split('-')[0].strip(), 7, 1)
    
    # Set default dates if not provided
    if start_date is None:
        # Determine the fiscal year start (last July 1st before the last date)
        start_date = pd.Timestamp(last_date.year, 7, 1)
        if start_date > last_date:
            start_date = pd.Timestamp(last_date.year - 1, 7, 1)
            
    if end_date is None:
        # Determine the fiscal year end (June 30th of the following year)
        end_date = pd.Timestamp(start_date.year + 1, 6, 30)
    
    # Filter the DataFrame to include only data from the specified period
    period_data = df[df["date"] >= start_date].copy()
    
    # Exclude internal funds
    period_data = period_data[~period_data["portfolio"].isin(["One for the World Discretionary Fund", "One for the World Operating Costs"])]
    
    # Calculate Money Moved
    if counterfactual:
        period_data['money_moved'] = period_data['counterfactuality'] * period_data['usd_amount']
        target = 1_260_000  # Counterfactual target
    else:
        period_data['money_moved'] = period_data['usd_amount']
        target = 1_800_000  # Regular target
    
    # Group by day and sum the money moved
    daily_money_moved = period_data.groupby(pd.Grouper(key="date", freq="D"))["money_moved"].sum().reset_index()
    
    # Calculate cumulative sum of money moved
    daily_money_moved["cumulative_money_moved"] = daily_money_moved["money_moved"].cumsum()
    
    # Get current total money moved
    total_money_moved = daily_money_moved["cumulative_money_moved"].iloc[-1] if not daily_money_moved.empty else 0
    
    # Fit a linear trend line
    z = np.polyfit(daily_money_moved["date"].map(pd.Timestamp.toordinal), daily_money_moved["cumulative_money_moved"], 1)
    p = np.poly1d(z)
    
    # Calculate trendline values for start and end of period
    trendline_dates = [start_date, end_date]
    trendline_data = p(pd.to_datetime(trendline_dates).map(pd.Timestamp.toordinal))
    
    # Calculate the projected end-of-year value and delta from target
    projected_eoy_value = trendline_data[-1]
    delta_value = projected_eoy_value - target
    delta_percent = (delta_value / target) * 100
    
    # Format the value for display
    formatted_value = f"${total_money_moved:,.0f}"
    
    # Set target value
    formatted_target = f"${target/1e6:.1f}M"
    
    # Format delta
    formatted_delta = f"{abs(delta_percent):.1f}%"
    
    # Determine if on target
    is_on_target = delta_value >= 0
    
    # Create comparison text
    comparison_text = "ahead of target" if is_on_target else "behind target"
    
    # Create title and subtitle
    title = "Counterfactual Money Moved" if counterfactual else "Money Moved"
    subtitle = f"Fiscal Year to Date"
    
    # Create the KPI card
    card = create_kpi_card(
        title=title,
        subtitle=subtitle,
        value=formatted_value,
        is_on_target=is_on_target,
        on_target_msg=f"above {formatted_target} target",
        off_target_msg=f"below {formatted_target} target",
        additional_metrics=[
            f"Target: {formatted_target}",
        ]
    )
    
    return card
