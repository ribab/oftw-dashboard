#!/usr/bin/env python3
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import vizro.models as vm
import vizro.plotly.express as px
from vizro import Vizro
from vizro.models.types import capture

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import data source
from utils.datasource import load_pledges, load_payments, load_merged_payments_and_pledges

# Import components
from components.kpi_card import create_kpi_card
from components.ai_graph_generator import AIGraphGenerator

# Import fiscal year metrics
import metrics.fiscal_year.money_moved

# Import kpi metrics
import metrics.kpi.arr
import metrics.kpi.attrition_rate_avg
import metrics.kpi.attrition_rate_all_time
import metrics.kpi.active_donors

# Import monthly metrics
import metrics.monthly.pledges
import metrics.monthly.all_active_donors
import metrics.monthly.active_recurring_donors
import metrics.monthly.monthly_donations
import metrics.monthly.arr
import metrics.monthly.attrition

# Import bar chart metrics
import metrics.bar_charts.chapter_arr
import metrics.bar_charts.channel_arr

Vizro._reset()

def create_home_page(payments_df, pledges_df, merged_df):
    """Create the home page with KPI cards and monthly metrics"""
    # Load data

    from vizro.managers import data_manager

    def calculate_fiscal_year(date):
        if date.month < 7:
            return f"{date.year - 1}-{date.year}"
        else:
            return f"{date.year}-{date.year + 1}"
    
    def get_payments_df(fiscal_year=None):
        df = payments_df
        if fiscal_year is None:
            fiscal_year = calculate_fiscal_year(datetime.now())
        # Fix: Use proper date string format for pd.Timestamp
        last_date_in_fiscal_year = f"{fiscal_year.split('-')[1]}-06-30"
        df = df[df['date'] <= last_date_in_fiscal_year]
        df['fiscal_year'] = fiscal_year
        return df

    def get_pledges_df(fiscal_year=None):
        df = pledges_df
        if fiscal_year is None:
            fiscal_year = calculate_fiscal_year(datetime.now())
        df['fiscal_year'] = fiscal_year
        return df

    def get_merged_df(fiscal_year=None):
        df = merged_df
        if fiscal_year is None:
            fiscal_year = calculate_fiscal_year(datetime.now())
        # Fix: Use proper date string format for pd.Timestamp
        last_date_in_fiscal_year = f"{fiscal_year.split('-')[1]}-06-30"
        df = df[df['date'] <= last_date_in_fiscal_year]
        df['fiscal_year'] = fiscal_year
        return df

    # Register the data with the data manager
    data_manager["home_page_payments"] = get_payments_df
    data_manager["home_page_pledges"] = get_pledges_df
    data_manager["home_page_merged"] = get_merged_df
    
    # Create KPI cards grid
    kpi_cards = [
        vm.Figure(
            id="money_moved_kpi",
            figure=capture('figure')(lambda data_frame: metrics.kpi.money_moved.kpi_card(data_frame))("home_page_payments")
        ),
        vm.Figure(
            id="arr_kpi",
            figure=capture('figure')(lambda data_frame: metrics.kpi.arr.create_arr_kpi_card(data_frame))("home_page_pledges")
        ),
        vm.Figure(
            id="future_arr_kpi",
            figure=capture('figure')(lambda data_frame: metrics.kpi.arr.create_future_arr_kpi_card(data_frame))("home_page_pledges")
        ),
        vm.Figure(
            id="active_arr_kpi",
            figure=capture('figure')(lambda data_frame: metrics.kpi.arr.create_active_arr_kpi_card(data_frame))("home_page_pledges")
        ),
        vm.Figure(
            id="attrition_kpi",
            figure=capture('figure')(lambda data_frame: metrics.kpi.attrition_rate_avg.create_total_attrition_kpi_card(data_frame, start_date=None, end_date=None))("home_page_pledges")
        ),
        vm.Figure(
            id="active_donors_kpi",
            figure=capture('figure')(lambda data_frame: metrics.kpi.active_donors.kpi_card(data_frame))("home_page_pledges")
        ),
        # vm.Figure(
        #     id="active_donors_kpi",
        #     figure=create_kpi_card(
        #         title="Active Donors",
        #         subtitle="Currently contributing donors",
        #         value="{:,}".format(metrics.monthly.all_active_donors.calculate_all_active_donors(pledges_df)),
        #         target_value="1,200",
        #         is_on_target=metrics.monthly.all_active_donors.calculate_all_active_donors(pledges_df) >= 1200,
        #         additional_metrics=["One-time and recurring"]
        #     )
        # )
    ]
    fiscal_year_metrics = vm.Tabs(
        tabs=[
            vm.Container(
                title="Money Moved",
                components=[
                    vm.Graph(
                        id="money_moved_fiscal_year",
                        figure=capture('graph')(lambda data_frame: metrics.fiscal_year.money_moved.money_moved_chart(data_frame, counterfactual=False))("home_page_payments")
                    ),
                ]
            ),
            vm.Container(
                title="Money Moved Counterfactual",
                components=[
                    vm.Graph(
                        id="money_moved_fiscal_year_counterfactual",
                        figure=capture('graph')(lambda data_frame: metrics.fiscal_year.money_moved.money_moved_chart(data_frame, counterfactual=True))("home_page_payments")
                    ),
                ]
            ),
            vm.Container(
                title="By Payment Platform",
                components=[
                    vm.Graph(
                        id="money_moved_platform",
                        figure=capture('graph')(lambda data_frame: metrics.fiscal_year.money_moved.money_moved_bar_chart(data_frame, breakdown_by="payment_platform", counterfactual=False))("home_page_merged")
                    ),
                ]
            ),
            vm.Container(
                title="By Payment Platform (Counterfactual)",
                components=[
                    vm.Graph(
                        id="money_moved_platform_counterfactual",
                        figure=capture('graph')(lambda data_frame: metrics.fiscal_year.money_moved.money_moved_bar_chart(data_frame, breakdown_by="payment_platform", counterfactual=True))("home_page_merged")
                    ),
                ]
            ),
            vm.Container(
                title="By Donor Chapter",
                components=[
                    vm.Graph(
                        id="money_moved_donor_chapter",
                        figure=capture('graph')(lambda data_frame: metrics.fiscal_year.money_moved.money_moved_bar_chart(data_frame, breakdown_by="donor_chapter", counterfactual=False))("home_page_merged")
                    ),
                ]
            ),
            vm.Container(
                title="By Donor Chapter (Counterfactual)",
                components=[
                    vm.Graph(
                        id="money_moved_donor_chapter_counterfactual",
                        figure=capture('graph')(lambda data_frame: metrics.fiscal_year.money_moved.money_moved_bar_chart(data_frame, breakdown_by="donor_chapter", counterfactual=True))("home_page_merged")
                    ),
                ]
            ),
            vm.Container(
                title="By Chapter Type",
                components=[
                    vm.Graph(
                        id="money_moved_chapter_type",
                        figure=capture('graph')(lambda data_frame: metrics.fiscal_year.money_moved.money_moved_bar_chart(data_frame, breakdown_by="chapter_type", counterfactual=False))("home_page_merged")
                    ),
                ]
            ),
            vm.Container(
                title="By Chapter Type (Counterfactual)",
                components=[
                    vm.Graph(
                        id="money_moved_chapter_type_counterfactual",
                        figure=capture('graph')(lambda data_frame: metrics.fiscal_year.money_moved.money_moved_bar_chart(data_frame, breakdown_by="chapter_type", counterfactual=True))("home_page_merged")
                    ),
                ]
            ),
            vm.Container(
                title="By Currency",
                components=[
                    vm.Graph(
                        id="money_moved_currency",
                        figure=capture('graph')(lambda data_frame: metrics.fiscal_year.money_moved.money_moved_bar_chart(data_frame, breakdown_by="currency", counterfactual=False))("home_page_merged")
                    ),
                ]
            ),
            vm.Container(
                title="By Currency (Counterfactual)",
                components=[
                    vm.Graph(
                        id="money_moved_currency_counterfactual",
                        figure=capture('graph')(lambda data_frame: metrics.fiscal_year.money_moved.money_moved_bar_chart(data_frame, breakdown_by="currency", counterfactual=True))("home_page_merged")
                    ),
                ]
            ),
            vm.Container(
                title="By Portfolio",
                components=[
                    vm.Graph(
                        id="money_moved_portfolio",
                        figure=capture('graph')(lambda data_frame: metrics.fiscal_year.money_moved.money_moved_bar_chart(data_frame, breakdown_by="portfolio", counterfactual=False))("home_page_merged")
                    ),
                ]
            ),
            vm.Container(
                title="By Portfolio (Counterfactual)",
                components=[
                    vm.Graph(
                        id="money_moved_portfolio_counterfactual",
                        figure=capture('graph')(lambda data_frame: metrics.fiscal_year.money_moved.money_moved_bar_chart(data_frame, breakdown_by="portfolio", counterfactual=True))("home_page_merged")
                    ),
                ]
            ),
        ]
    )
    
    # Create the home page
    return vm.Page(
        title="Fiscal Year Metrics",
        layout=vm.Grid(
            grid=[[0, 1, 2],
                  [3, 4, 5],  # KPI cards on top, monthly metrics below
                  [6, 6, 6],
                  [6, 6, 6]],  # KPI cards on top, monthly metrics below
            row_min_height='250px'
        ),
        components=[*kpi_cards, fiscal_year_metrics],
        controls=[
            vm.Parameter(
                targets=[
                    "money_moved_kpi.data_frame.fiscal_year",
                    "arr_kpi.data_frame.fiscal_year",
                    "future_arr_kpi.data_frame.fiscal_year",
                    "active_arr_kpi.data_frame.fiscal_year",
                    "attrition_kpi.data_frame.fiscal_year",
                    "active_donors_kpi.data_frame.fiscal_year",
                    "money_moved_fiscal_year.data_frame.fiscal_year",
                    "money_moved_fiscal_year_counterfactual.data_frame.fiscal_year",
                    "money_moved_platform.data_frame.fiscal_year",
                    "money_moved_platform_counterfactual.data_frame.fiscal_year",
                    "money_moved_donor_chapter.data_frame.fiscal_year",
                    "money_moved_donor_chapter_counterfactual.data_frame.fiscal_year",
                    "money_moved_chapter_type.data_frame.fiscal_year",
                    "money_moved_chapter_type_counterfactual.data_frame.fiscal_year",
                    "money_moved_currency.data_frame.fiscal_year",
                    "money_moved_currency_counterfactual.data_frame.fiscal_year",
                    "money_moved_portfolio.data_frame.fiscal_year",
                    "money_moved_portfolio_counterfactual.data_frame.fiscal_year",
                ],
                # value=calculate_fiscal_year(datetime.now()),
                selector=vm.Dropdown(
                    options=[
                        calculate_fiscal_year(datetime(year, 7, 1))
                        for year in reversed(range(
                            min(pd.to_datetime(payments_df['date']).dt.year),
                            max(pd.to_datetime(payments_df['date']).dt.year)
                        ))
                    ],
                    multi=False
                )
            )
        ]

        # controls=[
        #     vm.Filter(
        #         column="date",
        #         targets=["monthly_donations", "monthly_donations_breakdown", "monthly_pledges", "chapter_arr", "active_recurring_donors"],
        #         selector=vm.DatePicker(
        #             title="Select Month",
        #             value=datetime.now().strftime("%Y-%m")
        #         )
        #     ),
        #     vm.Filter(
        #         column="chapter_type",
        #         targets=["chapter_arr"],
        #         selector=vm.Dropdown(
        #             title="Chapter Type",
        #             multi=True
        #         )
        #     ),
        #     vm.Filter(
        #         column="payment_platform",
        #         targets=["monthly_donations", "monthly_donations_breakdown"],
        #         selector=vm.Dropdown(
        #             title="Payment Platform",
        #             multi=True
        #         )
        #     )
        # ]
    )

def create_channel_chapter_page(pledges_df):
    """Both channel and chapter are the same thing according to metadata.md"""
    from vizro.managers import data_manager
    
    def get_pledges_df():
        return pledges_df

    # Register the pledges data with the data manager
    data_manager["channel_chapter_pledges"] = get_pledges_df

    @capture('graph')
    def active_and_pledged_donors_chart(data_frame):
        return metrics.bar_charts.chapter_arr.custom_chart(data_frame, start_column='pledge_created_at', end_column='pledge_ended_at')
    
    @capture('graph')
    def active_donors_chart(data_frame):
        return metrics.bar_charts.chapter_arr.custom_chart(data_frame, start_column='pledge_starts_at', end_column='pledge_ended_at')
    
    @capture('graph')
    def pledged_donors_chart(data_frame):
        return metrics.bar_charts.chapter_arr.custom_chart(data_frame, start_column='pledge_created_at', end_column='pledge_starts_at')
    
    # Create the page components using the registered data
    
    return vm.Page(
        title="Annual Recurring Revenue by Chapter",
        layout=vm.Grid(
            grid=[
                [0], [1], [1], [1], [1], [1], [1], [1],
            ],
            row_gap='0px'
        ),
        components=[
            vm.Text(text="""
                Both channel and chapter are the same thing according to the [project metadata](https://docs.google.com/spreadsheets/d/1XSlvYfBxqAPvdXLCG7hnVzjCCjAtQ5CpGUebhU-8sPg/edit?usp=sharing).
                    
                Hold left-click and drag the mouse on the graph to zoom-in.
            """),
            vm.Tabs(tabs=[
                vm.Container(
                    title="Active + Pledged Donors",
                    components=[
                        vm.Graph(
                            id="active_and_pledged_donors_chart",
                            figure=active_and_pledged_donors_chart("channel_chapter_pledges"),
                        ),
                    ]
                ),
                vm.Container(
                    title="Active Donors",
                    components=[
                        vm.Graph(
                            id="active_donors_chart",
                            figure=active_donors_chart("channel_chapter_pledges"),
                        ),
                    ]
                ),
                vm.Container(
                    title="Pledged Donors",
                    components=[
                        vm.Graph(
                            id="pledged_donors_chart",
                            figure=pledged_donors_chart("channel_chapter_pledges"),
                        ),
                    ]
                ),
            ])
        ],
        controls=[
            vm.Filter(
                column="chapter_type",
                targets=["active_and_pledged_donors_chart", "active_donors_chart", "pledged_donors_chart"],
                selector=vm.Dropdown(
                    title="Chapter Type",
                    options=sorted(pledges_df['chapter_type'].unique()),
                    multi=True,
                    value=['ALL']
                )
            ),
        ]
    )

def create_monthly_metrics_page(payments_df, pledges_df, merged_df):
    """Create the monthly metrics page"""
    import metrics.monthly.active_recurring_donors
    import metrics.monthly.all_active_donors
    import metrics.monthly.arr
    import metrics.monthly.attrition
    import metrics.monthly.monthly_donations
    import metrics.monthly.pledges

    from vizro.managers import data_manager

    def calculate_fiscal_year(date):
        if date.month < 7:
            return f"{date.year - 1}-{date.year}"
        else:
            return f"{date.year}-{date.year + 1}"
    
    def get_payments_df():
        df = payments_df
        return df

    def get_pledges_df():
        df = pledges_df
        return df

    def get_merged_df():
        df = merged_df
        return df

    # Register the data with the data manager
    data_manager["monthly_metrics_payments"] = get_payments_df
    data_manager["monthly_metrics_pledges"] = get_pledges_df
    data_manager["monthly_metrics_merged"] = get_merged_df
    
    return vm.Page(
        title="Monthly Metrics",
        layout=vm.Grid(
            grid=[
                [0], [1], [1], [2], [2], [3], [3], [4], [4], [5], [5], [5], [5]
            ],
            # row_gap='',
            row_min_height='200px'
        ),
        components=[
            vm.Text(text="""
                Table of contents:
                - [Donors with Active Pledges Per Month](#active_recurring_donors_chart)
                - [All Active Donors at Month End](#all_active_donors_chart)
                - [Attrition Rate](#attrition_rate_chart)
                - [Monthly Donations](#monthly_donations_chart)
                - [Active + Pledged Donors](#pledges_chart)
                - [Active Donors](#active_pledges_chart)
                - [Pledged Donors](#future_pledges_chart)
                - [Annual Recurring Revenue](#arr_chart)
            """),
            # active recurring donors
            vm.Graph(
                id="active_recurring_donors_chart",
                figure=capture('graph')(lambda data_frame: metrics.monthly.active_recurring_donors.custom_chart(data_frame))("monthly_metrics_pledges")
            ),
            # all active donors
            vm.Graph(
                id="all_active_donors_chart",
                figure=capture('graph')(lambda data_frame: metrics.monthly.all_active_donors.custom_chart(data_frame))("monthly_metrics_pledges")
            ),
            # attrition rate
            vm.Graph(
                id="attrition_rate_chart",
                figure=capture('graph')(lambda data_frame: metrics.monthly.attrition.attrition_chart(data_frame))("monthly_metrics_pledges")
            ),
            # monthly donations
            vm.Graph(
                id="monthly_donations_chart",
                figure=capture('graph')(lambda data_frame: metrics.monthly.monthly_donations.custom_chart(data_frame))("monthly_metrics_payments")
            ),
            # arr and pledges
            vm.Tabs(tabs=[
                vm.Container(
                    title="Active + Pledged Donors",
                    components=[
                        vm.Graph(
                            id="pledges_chart",
                            figure=capture('graph')(lambda data_frame: metrics.monthly.pledges.pledges_chart(data_frame))("monthly_metrics_pledges")
                        ),
                        vm.Graph(
                            id="arr_chart",
                            figure=capture('graph')(lambda data_frame: metrics.monthly.arr.custom_chart(data_frame, start_column='pledge_created_at', end_column='pledge_ended_at'))("monthly_metrics_pledges")
                        )
                    ]
                ),
                vm.Container(
                    title="Active Donors",
                    components=[
                        vm.Graph(
                            id="active_pledges_chart",
                            figure=capture('graph')(lambda data_frame: metrics.monthly.pledges.active_pledges_chart(data_frame))("monthly_metrics_pledges")
                        ),
                        vm.Graph(
                            id="active_arr_chart",
                            figure=capture('graph')(lambda data_frame: metrics.monthly.arr.custom_chart(data_frame, start_column='pledge_starts_at', end_column='pledge_ended_at'))("monthly_metrics_pledges")
                        )
                    ]
                ),
                vm.Container(
                    title="Pledged Donors",
                    components=[
                        vm.Graph(
                            id="future_pledges_chart",
                            figure=capture('graph')(lambda data_frame: metrics.monthly.pledges.future_pledges_chart(data_frame))("monthly_metrics_pledges")
                        ),
                        vm.Graph(
                            id="future_arr_chart",
                            figure=capture('graph')(lambda data_frame: metrics.monthly.arr.custom_chart(data_frame, start_column='pledge_created_at', end_column='pledge_starts_at'))("monthly_metrics_pledges")
                        )
                    ]
                )
            ])
        ]
    )

def create_ai_page(payments_df, pledges_df, merged_df):
    """Create the AI graph generator page"""
    return vm.Page(
        title="AI Graph Generator - use for quick insights (May be inaccurate)",
        components=[
            AIGraphGenerator(
                id="graph_container",
                data_frames={
                    "Pledges": pledges_df,
                    "Payments": payments_df,
                    "Merged": merged_df
                }
            )
        ]
    )

if __name__ == "__main__":
    payments_df = load_payments()
    pledges_df = load_pledges()
    merged_df = load_merged_payments_and_pledges()

    # Create the dashboard
    dashboard = vm.Dashboard(
        pages=[
            create_home_page(payments_df, pledges_df, merged_df),
            create_monthly_metrics_page(payments_df, pledges_df, merged_df),
            create_channel_chapter_page(pledges_df),
            create_ai_page(payments_df, pledges_df, merged_df),
        ],
        title="One for the World Analytics"
    )
    
    # Build and run the dashboard
    app = Vizro().build(dashboard)
    
    # Run the app
    app.run(debug=True, port=10000, host='0.0.0.0')
