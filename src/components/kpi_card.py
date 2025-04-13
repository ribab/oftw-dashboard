#!/usr/bin/env python3
# KPI Card Component
# Reusable component for creating KPI cards with consistent styling
# %%

import pandas as pd
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go


def create_kpi_card(title, subtitle, value, target_value, is_on_target,
                    target_label="Target", comparison_text=None, additional_metrics=None):
    """
    Create a reusable KPI card with consistent styling
    
    Args:
        title: Main title of the KPI card
        subtitle: Subtitle or description text
        value: The main KPI value to display
        target_value: The target value for comparison
        is_on_target: Boolean indicating if the KPI is meeting target
        target_label: Label for the target section (default: "Target")
        comparison_text: Custom text for comparison (e.g., "less attrition than target")
        additional_metrics: Optional list of dicts with {label, value} for additional metrics
        
    Returns:
        A Dash Bootstrap card component
    """
    # Determine status styling
    status_color = "success" if is_on_target else "danger"
    
    # Default comparison text if none provided
    if comparison_text is None:
        comparison_text = "better than target" if is_on_target else "worse than target"
    
    # Create the card
    card = dbc.Card(
        [
            dbc.CardBody(
                [
                    # Title and subtitle
                    html.H3(title, className="card-title mb-0 text-center"),
                    html.P(subtitle, className="text-muted small mb-0 text-center"),
                    
                    # Main KPI value (large percentage)
                    dbc.Row(
                        [
                            dbc.Col(
                                html.H1(
                                    value, 
                                    className="text-center display-2 fw-bold"
                                ),
                                width=12,
                                className="text-center"
                            ),
                        ],
                    ),
                    
                    # Info text (e.g. "5093 cancelled / 11911 total")
                    dbc.Row(
                        html.Div(
                            [
                                html.Div(m)
                                for m in additional_metrics
                            ] if isinstance(additional_metrics, list) else additional_metrics,
                            className="text-muted small mb-0 text-center d-flex flex-column"
                        ),
                        className="text-center"
                    ) if additional_metrics else html.Div(),
                    
                    # Status text (e.g. "24.8% more attrition than target")
                    dbc.Row(
                        dbc.Col(
                            html.P(
                                f"{comparison_text}",
                                className=f"text-center text-{status_color}"
                            ),
                            width=12,
                            className="text-center"
                        ),
                        className="text-center"
                    ),
                ],
                className="d-flex flex-column justify-content-center align-items-center"
            )
        ],
        className="h-100 shadow-sm",
        style={"overflow": "hidden", "border-radius": "10px", "color": "white"}
    )
    
    return card

# Example usage in a Jupyter notebook
if __name__ == "__main__":
    import pandas as pd
    import dash_bootstrap_components as dbc
    from dash import html
    import vizro.models as vm
    from vizro import Vizro
    from vizro.models.types import capture
    import socket

    # add project root to sys.path
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.developer_tools import find_available_port

    @capture("figure")
    def example_card(data_frame):
        return create_kpi_card(
            title="Example KPI Metric",
            subtitle="Sample metric description",
            value="75.5%",
            target_value="80.0%",
            is_on_target=False,
            comparison_text="below target",
            additional_metrics=["755 / 1000 total"]
        )

    Vizro._reset()
    
    # Create a Vizro dashboard with the KPI card
    page = vm.Page(
        id="kpi-example-page",
        title="KPI Card Example",
        components=[
            vm.Figure(
                id="example-kpi-card",
                figure=example_card(pd.DataFrame())
            )
        ]
    )
    
    dashboard = vm.Dashboard(pages=[page])
    
    # run the dashboard
    Vizro().build(dashboard).run(port=find_available_port())

# %%
