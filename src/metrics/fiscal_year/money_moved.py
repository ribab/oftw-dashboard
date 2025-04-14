#!/usr/bin/env python3
# %%
# Cumulative Money Moved Line Chart
# This notebook creates a line chart showing cumulative money moved with a .8M target line and trendline projection.

import pandas as pd
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from components.kpi_card import create_kpi_card

MONEY_MOVED_TARGET = 1800000
MONEY_MOVED_COUNTERFACTUAL_TARGET = 1260000


def create_money_moved_kpi_card(data_frame, counterfactual=False):
    """
    Create a KPI card for money moved in the current fiscal year.
    
    Args:
        data_frame (pd.DataFrame): DataFrame containing payment data
        counterfactual (bool): Whether to calculate counterfactual money moved
        
    Returns:
        dash component: A KPI card showing money moved metrics
    """
    # Import the KPI card component
    
    # Set target based on counterfactual flag
    if counterfactual:
        target = MONEY_MOVED_COUNTERFACTUAL_TARGET
    else:
        target = MONEY_MOVED_TARGET
    
    # Convert "date" to datetime objects
    data_frame = data_frame.copy()
    data_frame["date"] = pd.to_datetime(data_frame["date"])

    # Determine the last date in the dataset
    last_date = data_frame["date"].max()

    # Determine the fiscal year start (last July 1st before the last date)
    fiscal_year_start = pd.Timestamp(last_date.year, 7, 1)
    if fiscal_year_start > last_date:
        fiscal_year_start = pd.Timestamp(last_date.year - 1, 7, 1)
        
    # Determine the fiscal year end (June 30th of the following year)
    fiscal_year_end = pd.Timestamp(fiscal_year_start.year + 1, 6, 30)

    # Filter the DataFrame to include only data from the current fiscal year
    fiscal_year_data = data_frame[data_frame["date"] >= fiscal_year_start].copy()

    # Exclude internal funds
    fiscal_year_data = fiscal_year_data[~fiscal_year_data["portfolio"].isin(["One for the World Discretionary Fund", "One for the World Operating Costs"])]
    
    # Calculate Money Moved (MM)
    if counterfactual:
        fiscal_year_data['money_moved'] = fiscal_year_data['counterfactuality'] * fiscal_year_data['usd_amount']
    else:
        fiscal_year_data['money_moved'] = fiscal_year_data['usd_amount']
        
    # Group by day and sum the money moved
    daily_money_moved = fiscal_year_data.groupby(pd.Grouper(key="date", freq="D"))["money_moved"].sum().reset_index()

    # Calculate cumulative sum of money moved
    daily_money_moved["cumulative_money_moved"] = daily_money_moved["money_moved"].cumsum()
    
    # Get current total money moved
    total_money_moved = daily_money_moved["cumulative_money_moved"].iloc[-1] if not daily_money_moved.empty else 0
    
    # Fit a linear trend line
    z = np.polyfit(daily_money_moved["date"].map(pd.Timestamp.toordinal), daily_money_moved["cumulative_money_moved"], 1)
    p = np.poly1d(z)

    # Calculate trendline values for start and end of fiscal year
    trendline_dates = [fiscal_year_start, fiscal_year_end]
    trendline_data = p(pd.to_datetime(trendline_dates).map(pd.Timestamp.toordinal))
    
    # Calculate the projected end-of-year value and delta from target
    projected_eoy_value = trendline_data[-1]
    delta_value = projected_eoy_value - target
    delta_percent = (delta_value / target) * 100
    
    # Format the value for display
    formatted_value = f"${total_money_moved:,.0f}"
    
    # Set target value
    formatted_target = f"${target:,.0f}"
    
    # Format delta
    formatted_delta = f"{abs(delta_percent):.1f}%"
    
    # Determine if on target
    is_on_target = delta_value >= 0
    
    # Create comparison text
    comparison_text = "ahead of target" if is_on_target else "behind target"
    
    # Create title based on counterfactual flag
    title = "Counterfactual Money Moved" if counterfactual else "Money Moved"
    subtitle = f"Fiscal Year to Date"
    
    # Create the KPI card
    card = create_kpi_card(
        title=title,
        subtitle=subtitle,
        value=formatted_value,
        is_on_target=is_on_target,
        on_target_msg=f"above target of {formatted_target}",
        off_target_msg=f"below target of {formatted_target}",
        additional_metrics=[
            f"Target: {formatted_target}",
        ]
    )
    
    return card



def money_moved_chart(data_frame, counterfactual=False, breakdown_by=None):
    if counterfactual:
        target = MONEY_MOVED_COUNTERFACTUAL_TARGET
        target_label = "Target: 1.26M"
    else:
        target = MONEY_MOVED_TARGET
        target_label = "Target: 1.8M"

    # Convert "date" to datetime objects
    data_frame["date"] = pd.to_datetime(data_frame["date"])

    # Determine the last date in the dataset
    last_date = data_frame["date"].max()

    # Determine the fiscal year start (last July 1st before the last date)
    fiscal_year_start = pd.Timestamp(last_date.year, 7, 1)
    if fiscal_year_start > last_date:
        fiscal_year_start = pd.Timestamp(last_date.year - 1, 7, 1)

    # Determine the fiscal year end (June 30th of the following year)
    fiscal_year_end = pd.Timestamp(fiscal_year_start.year + 1, 6, 30)

    # Filter the DataFrame to include only data from the current fiscal year
    fiscal_year_data = data_frame[data_frame["date"] >= fiscal_year_start].copy()

    # Exclude internal funds
    fiscal_year_data = fiscal_year_data[~fiscal_year_data["portfolio"].isin(["One for the World Discretionary Fund", "One for the World Operating Costs"])]
    
    # Calculate Money Moved (MM)
    if counterfactual:
        fiscal_year_data['money_moved'] = fiscal_year_data['counterfactuality'] * fiscal_year_data['usd_amount']
    else:
        fiscal_year_data['money_moved'] = fiscal_year_data['usd_amount']

    # Create the figure
    fig = go.Figure()
    
    # Handle breakdown options
    if breakdown_by is None:
        # No breakdown - just show cumulative total
        daily_donations = fiscal_year_data.groupby(pd.Grouper(key="date", freq="D"))["money_moved"].sum().reset_index()
        daily_donations["cumulative_money_moved"] = daily_donations["money_moved"].cumsum()
        
        # Add cumulative donations trace
        fig.add_trace(
            go.Scatter(
                x=daily_donations["date"], 
                y=daily_donations["cumulative_money_moved"], 
                mode="lines", 
                name="Cumulative Donations",
                fill='tozeroy'
            )
        )
    else:
        # Apply breakdown by the specified column
        if breakdown_by == 'payment_platform':
            # For platform breakdown
            breakdown_column = 'payment_platform'  # Using correct column name from metadata
            # Ensure platform is filled
            fiscal_year_data[breakdown_column] = fiscal_year_data[breakdown_column].fillna('off platform')
        elif breakdown_by == 'donor_chapter':
            # For source breakdown (chapter types)
            breakdown_column = 'donor_chapter'  # Using correct column name from metadata
            fiscal_year_data[breakdown_column] = fiscal_year_data[breakdown_column].fillna('none')
        elif breakdown_by == 'chapter_type':
            # For source breakdown (chapter types)
            breakdown_column = 'chapter_type'  # Using correct column name from metadata
            fiscal_year_data[breakdown_column] = fiscal_year_data[breakdown_column].fillna('none')
        elif breakdown_by == 'currency':
            # For currency breakdown
            breakdown_column = 'currency'  # Using correct column name from metadata
            fiscal_year_data[breakdown_column] = fiscal_year_data[breakdown_column].fillna('none')
        elif breakdown_by == 'portfolio':
            breakdown_column = 'portfolio'
            fiscal_year_data[breakdown_column] = fiscal_year_data[breakdown_column].fillna('none')
        else:
            assert False, f"Breakdown by {breakdown_by} not supported"
        # Group by date and breakdown column
        grouped = fiscal_year_data.groupby([pd.Grouper(key="date", freq="D"), breakdown_column])["money_moved"].sum().reset_index()
        
        # Create a pivot table for the stacked area chart
        pivot_df = grouped.pivot(index='date', columns=breakdown_column, values='money_moved').fillna(0)
        
        # Calculate cumulative sums for each category
        for column in pivot_df.columns:
            pivot_df[column] = pivot_df[column].cumsum()
        
        # Add traces for each category
        for column in pivot_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=pivot_df.index,
                    y=pivot_df[column],
                    mode='lines',
                    name=str(column),
                    stackgroup='one'  # This creates the stacked area chart
                )
            )

    # Fit a linear trend line on the total cumulative money moved
    daily_total = fiscal_year_data.groupby(pd.Grouper(key="date", freq="D"))["money_moved"].sum().reset_index()
    daily_total["cumulative_money_moved"] = daily_total["money_moved"].cumsum()
    
    z = np.polyfit(daily_total["date"].map(pd.Timestamp.toordinal), daily_total["cumulative_money_moved"], 1)
    p = np.poly1d(z)

    # Calculate trendline values for start and end of fiscal year
    trendline_dates = [fiscal_year_start, fiscal_year_end]
    trendline_data = p(pd.to_datetime(trendline_dates).map(pd.Timestamp.toordinal))

    # Add trendline trace
    fig.add_trace(
        go.Scatter(
            x=trendline_dates,
            y=trendline_data,
            mode="lines",
            name="Trendline",
            line=dict(color="gray"),
            hovertemplate="Trending to %{y:$,.0f}<extra></extra>"
        )
    )

    # Add horizontal line for the target at fiscal year end
    fig.add_trace(
        go.Scatter(
            x=[fiscal_year_start, fiscal_year_end],
            y=[target, target],
            mode="lines",
            name=target_label,
            line=dict(color="gray", width=2, dash="dash")
        )
    )

    # Add annotation for the target line
    fig.add_annotation(
        x=fiscal_year_end,
        y=target,
        text=target_label,
        xref="x",
        yref="y",
        xanchor="right",
        yanchor="bottom",
        showarrow=False,
        xshift=-10
    )

    # Create title based on breakdown and counterfactual status
    # Get the fiscal year as a string (e.g., "2023-2024")
    fiscal_year_str = f"{fiscal_year_start.year}-{fiscal_year_end.year}"
    
    title = f"Cumulative Money Moved - Fiscal Year {fiscal_year_str}"
    if counterfactual:
        title = f"Counterfactual Money Moved - Fiscal Year {fiscal_year_str}"
    if breakdown_by:
        title += f" (by {breakdown_by.replace('_', ' ').title()})"

    # Update layout for better presentation
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Cumulative USD Amount",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        yaxis=dict(
            tickformat="$,.0f"
        )
    )

    return fig

def money_moved_bar_chart(data_frame, breakdown_by=None, counterfactual=False):
    """
    Create a bar chart showing cumulative money moved for the current fiscal year,
    broken down by the specified category.
    
    Args:
        data_frame (pd.DataFrame): DataFrame containing payment data
        breakdown_by (str): Column to break down the data by (payment_platform, donor_chapter, etc.)
        counterfactual (bool): Whether to calculate counterfactual money moved
        
    Returns:
        plotly.graph_objects.Figure: A bar chart showing money moved metrics
    """
    assert breakdown_by is not None, "Breakdown by must be specified"
    # Convert "date" to datetime objects
    data_frame = data_frame.copy()
    data_frame["date"] = pd.to_datetime(data_frame["date"])

    # Determine the last date in the dataset
    last_date = data_frame["date"].max()

    # Determine the fiscal year start (last July 1st before the last date)
    fiscal_year_start = pd.Timestamp(last_date.year, 7, 1)
    if fiscal_year_start > last_date:
        fiscal_year_start = pd.Timestamp(last_date.year - 1, 7, 1)
        
    # Determine the fiscal year end (June 30th of the following year)
    fiscal_year_end = pd.Timestamp(fiscal_year_start.year + 1, 6, 30)

    # Filter the DataFrame to include only data from the current fiscal year
    fiscal_year_data = data_frame[data_frame["date"] >= fiscal_year_start].copy()

    # Exclude internal funds
    fiscal_year_data = fiscal_year_data[
        ~fiscal_year_data["portfolio"].isin(["One for the World Discretionary Fund", "One for the World Operating Costs"])
    ]

    # Apply counterfactual calculation if requested
    if counterfactual:
        fiscal_year_data["money_moved"] = fiscal_year_data["usd_amount"] * fiscal_year_data["counterfactuality"]
    else:
        fiscal_year_data["money_moved"] = fiscal_year_data["usd_amount"]

    # Create figure
    fig = go.Figure()

    # Validate breakdown_by parameter
    if breakdown_by is None:
        # If no breakdown, just show total
        total_money_moved = fiscal_year_data["money_moved"].sum()
        fig.add_trace(
            go.Bar(
                x=["Total"],
                y=[total_money_moved],
                text=[f"${total_money_moved:,.0f}"],
                textposition="auto"
            )
        )
    else:
        # Apply breakdown by the specified column
        if breakdown_by == 'payment_platform':
            breakdown_column = 'payment_platform'
            fiscal_year_data[breakdown_column] = fiscal_year_data[breakdown_column].fillna('off platform')
        elif breakdown_by == 'donor_chapter':
            breakdown_column = 'donor_chapter'
            fiscal_year_data[breakdown_column] = fiscal_year_data[breakdown_column].fillna('none')
        elif breakdown_by == 'chapter_type':
            breakdown_column = 'chapter_type'
            fiscal_year_data[breakdown_column] = fiscal_year_data[breakdown_column].fillna('none')
        elif breakdown_by == 'currency':
            breakdown_column = 'currency'
            fiscal_year_data[breakdown_column] = fiscal_year_data[breakdown_column].fillna('none')
        elif breakdown_by == 'portfolio':
            breakdown_column = 'portfolio'
            fiscal_year_data[breakdown_column] = fiscal_year_data[breakdown_column].fillna('none')
        elif breakdown_by == 'month':
            # Create month column
            fiscal_year_data['month'] = fiscal_year_data['date'].dt.strftime('%Y-%m')
            breakdown_column = 'month_display'
            
            # Generate all months in the fiscal year
            all_months = []
            current_date = fiscal_year_start
            while current_date <= fiscal_year_end:
                all_months.append({
                    'month': current_date.strftime('%Y-%m'),
                    'month_display': current_date.strftime('%b %Y')
                })
                # Move to next month
                if current_date.month == 12:
                    current_date = pd.Timestamp(current_date.year + 1, 1, 1)
                else:
                    current_date = pd.Timestamp(current_date.year, current_date.month + 1, 1)
        else:
            assert False, f"Breakdown by {breakdown_by} not supported"
        
        
        # Sort appropriately based on breakdown type
        if breakdown_by == 'month':
            # Group by breakdown column and sum money moved
            grouped = fiscal_year_data.groupby('month')["money_moved"].sum().reset_index()
            # Create a DataFrame with all months
            all_months_df = pd.DataFrame(all_months)
            
            # Merge with the grouped data to ensure all months are included
            grouped = pd.merge(all_months_df, grouped, on='month', how='left')
            
            # Fill NaN values with 0
            grouped['money_moved'] = grouped['money_moved'].fillna(0)
            
            # Sort by month chronologically
            grouped = grouped.sort_values('month')
        else:
            # Group by breakdown column and sum money moved
            grouped = fiscal_year_data.groupby(breakdown_column)["money_moved"].sum().reset_index()
            # Sort by money moved in descending order for other breakdowns
            grouped = grouped.sort_values("money_moved", ascending=False)
        
        # Add bar trace
        fig.add_trace(
            go.Bar(
                x=grouped[breakdown_column],
                y=grouped["money_moved"],
                text=[f"${val:,.0f}" for val in grouped["money_moved"]],
                textposition="auto"
            )
        )

    # Create title based on breakdown and counterfactual status
    # Get the fiscal year as a string (e.g., "2023-2024")
    fiscal_year_str = f"{fiscal_year_start.year}-{fiscal_year_end.year}"
    
    title = f"Cumulative Money Moved - Fiscal Year {fiscal_year_str}"
    if counterfactual:
        title = f"Counterfactual Money Moved - Fiscal Year {fiscal_year_str}"
    if breakdown_by:
        title += f" (by {breakdown_by.replace('_', ' ').title()})"

    # Update layout for better presentation
    fig.update_layout(
        title=title,
        xaxis_title=breakdown_by.replace('_', ' ').title() if breakdown_by else "",
        yaxis_title="Cumulative USD Amount",
        template="plotly_white",
        yaxis=dict(
            tickformat="$,.0f"
        ),
        xaxis=dict(
            showticklabels=True if breakdown_by == 'month' else None,
            type='category'
        )
    )

    return fig


if __name__ == "__main__":
    import pickle
    from utils.datasource import *
    # get path to this script
    # path to payments json
    # get data
    payments_df = load_payments()
    # run the chart
    fig = money_moved_chart(payments_df)
    # Set dark theme
    fig.update_layout(template="plotly_dark")
    fig.show()

    # with counterfactual
    fig = money_moved_chart(payments_df, counterfactual=True)
    fig.update_layout(template="plotly_dark")
    fig.show()

    # Plot with different breakdown options
    
    # Import the merged data for breakdowns that need pledge information
    
    # Get the merged dataframe for breakdowns that need pledge information
    merged_df = load_merged_payments_and_pledges()
    
    # By platform
    fig = money_moved_chart(merged_df, breakdown_by="payment_platform")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By source (chapter types)
    fig = money_moved_chart(merged_df, breakdown_by="donor_chapter")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By recurring vs one-time
    fig = money_moved_chart(merged_df, breakdown_by="chapter_type")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By portfolio
    fig = money_moved_chart(merged_df, breakdown_by="portfolio")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By currency
    fig = money_moved_chart(merged_df, breakdown_by="currency")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # Counterfactual versions with breakdowns
    # By payment platform
    fig = money_moved_chart(merged_df, counterfactual=True, breakdown_by="payment_platform")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By donor chapter
    fig = money_moved_chart(merged_df, counterfactual=True, breakdown_by="donor_chapter")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By donation type
    fig = money_moved_chart(merged_df, counterfactual=True, breakdown_by="chapter_type")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By portfolio
    fig = money_moved_chart(merged_df, counterfactual=True, breakdown_by="portfolio")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By currency
    fig = money_moved_chart(merged_df, counterfactual=True, breakdown_by="currency")
    fig.update_layout(template="plotly_dark")
    fig.show()

# %%

    # By payment platform
    fig = money_moved_bar_chart(merged_df, breakdown_by="payment_platform")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By donor chapter
    fig = money_moved_bar_chart(merged_df, breakdown_by="donor_chapter")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By chapter type
    fig = money_moved_bar_chart(merged_df, breakdown_by="chapter_type")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By portfolio
    fig = money_moved_bar_chart(merged_df, breakdown_by="portfolio")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By currency
    fig = money_moved_bar_chart(merged_df, breakdown_by="currency")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By month
    fig = money_moved_bar_chart(merged_df, breakdown_by="month")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By payment platform
    fig = money_moved_bar_chart(merged_df, counterfactual=True, breakdown_by="payment_platform")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By donor chapter
    fig = money_moved_bar_chart(merged_df, counterfactual=True, breakdown_by="donor_chapter")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By chapter type
    fig = money_moved_bar_chart(merged_df, counterfactual=True, breakdown_by="chapter_type")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By portfolio
    fig = money_moved_bar_chart(merged_df, counterfactual=True, breakdown_by="portfolio")
    fig.update_layout(template="plotly_dark")
    fig.show()
    
    # By currency
    fig = money_moved_bar_chart(merged_df, counterfactual=True, breakdown_by="currency")
    fig.update_layout(template="plotly_dark")
    fig.show()

    # By month
    fig = money_moved_bar_chart(merged_df, counterfactual=True, breakdown_by="month")
    fig.update_layout(template="plotly_dark")
    fig.show()

# %%
