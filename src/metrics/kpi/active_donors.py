#!/usr/bin/env python3
# Active Donors KPI Card
# This file creates a KPI card showing the total number of active donors
# %%
import sys
from pathlib import Path
import pandas as pd
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from components.kpi_card import create_kpi_card

def calculate_all_active_donors(data_frame):
    """
    Calculate the total number of active donors based on pledge data
    
    Args:
        data_frame: DataFrame containing pledge data
        
    Returns:
        Integer representing the total number of active donors
    """
    # Convert date columns to datetime objects
    data_frame['pledge_created_at'] = pd.to_datetime(data_frame['pledge_created_at'])
    data_frame['pledge_starts_at'] = pd.to_datetime(data_frame['pledge_starts_at'])
    data_frame['pledge_ended_at'] = pd.to_datetime(data_frame['pledge_ended_at'])

    # Get current date
    now = pd.Timestamp.now()

    # Filter for active pledges
    active_pledges = data_frame[
        (data_frame['pledge_starts_at'] <= now) & 
        ((data_frame['pledge_ended_at'].isna()) | (data_frame['pledge_ended_at'] > now))
    ]

    # Count unique donors with active pledges
    active_donors = active_pledges['donor_id'].nunique()

    return active_donors

def kpi_card(pledges_df):
    """
    Create a KPI card showing the total number of active donors
    
    Args:
        pledges_df: DataFrame containing pledge data
        
    Returns:
        A KPI card component showing active donors count and target
    """
    # Calculate active donors
    active_donors = calculate_all_active_donors(pledges_df)
    
    # Create the KPI card
    return create_kpi_card(
        title="Active Donors",
        subtitle="Currently contributing donors",
        value="{:,}".format(active_donors),
        is_on_target=active_donors >= 1200,
        on_target_msg="above target of 1,200",
        off_target_msg="below target of 1,200",
        additional_metrics=["One-time and recurring"]
    )

if __name__ == "__main__":
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    
    # Import the load_pledges function from utils.datasource
    from src.utils.datasource import load_pledges
    
    # Load the pledges data
    print("Loading pledges data...")
    pledges_df = load_pledges()
    
    # Create and display the KPI card using Vizro
    import vizro.models as vm
    from vizro import Vizro
    from vizro.models.types import capture
    
    @capture("figure")
    def example_card(data_frame):
        return kpi_card(data_frame)
    
    # Create a test page with the KPI card
    page = vm.Page(
        title="Active Donors KPI Test",
        components=[
            vm.Figure(
                id="active-donors-kpi",
                figure=example_card(pledges_df)
            )
        ]
    )
    
    # Create and run the dashboard
    dashboard = vm.Dashboard(pages=[page])
    
    # Find an available port and run
    from utils.developer_tools import find_available_port
    port = find_available_port()
    Vizro().build(dashboard).run(port=port) 
# %%
