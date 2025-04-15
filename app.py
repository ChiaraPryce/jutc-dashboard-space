#!/usr/bin/env python
# coding: utf-8

# In[49]:


import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gradio as gr
from matplotlib.ticker import MaxNLocator


try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # __file__ not defined in interactive sessions
    BASE_DIR = os.getcwd()

routes_path = os.path.join(BASE_DIR, "JUTC Depot Routes.xlsx")
fuel_path   = os.path.join(BASE_DIR, "JUTC Fuel Types 2 .xlsx")


routes_data = pd.read_excel(routes_path)
fuel_data   = pd.read_excel(fuel_path)

#CSS
custom_css = """
body, .gradio-container {
  background-color: #F5F5F5 !important;
  color: #333333 !important;
  font-family: "Arial", sans-serif !important;
}
/* Header */
.header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0;
  color: #001f3f;
}
/* KPI cards */
.metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
}
.metric-card {
  background-color: #FFFFFF;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  padding: 16px;
  flex: 1 1 140px;
  min-width: 140px;
  text-align: center;
}
.metric-card .label {
  font-size: 0.9rem;
  color: #666666;
  margin: 0;
}
.metric-card .value {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 4px 0 0;
  color: #001f3f;
}
/* Grid for charts */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  margin: 16px 0;
}
/* Chart card */
.chart-card {
  background-color: #FFFFFF;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  padding: 12px;
  min-height: 360px;
  display: flex;
  flex-direction: column;
}
/* Plot inside card */
.chart-card .gradio-plot {
  flex: 1 1 auto;
  width: 100% !important;
  height: 100% !important;
}
.chart-card canvas,
.chart-card svg {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain;
}
/* Tabs */
.gradio-accordion .accordion-header,
.gradio-tabs .tab-item {
  font-weight: 600 !important;
  color: #001f3f !important;
}
.gradio-tabs .tab-item.selected {
  border-bottom: 3px solid #FF851B !important;
  color: #FF851B !important;
}
/* Buttons */
button {
  border-radius: 4px !important;
  padding: 8px 16px !important;
  font-weight: 600 !important;
  background-color: #E0E0E0 !important;
  color: #333333 !important;
}
button:hover {
  background-color: #FFDC00 !important;
  color: #001f3f !important;
}
"""

# ——————————————————————————————
# PART 1: DEPOT ROUTES DATA CLEANING & METRICS
# ——————————————————————————————
routes_data.columns = (
    routes_data.columns
      .str.strip()
      .str.lower()
      .str.replace(r"\s+", " ", regex=True)
)
routes_data['fare'] = (
    routes_data['fare structure']
      .replace({r"\$": "", ",": ""}, regex=True)
      .pipe(pd.to_numeric, errors="coerce")
)

most_expensive    = routes_data.loc[routes_data['fare'].idxmax()]
shortest_distance = routes_data.loc[routes_data['distance (km)'].idxmin()]
longest_distance  = routes_data.loc[routes_data['distance (km)'].idxmax()]
most_buses        = routes_data.loc[routes_data['buses available'].idxmax()]
least_buses       = routes_data.loc[routes_data['buses available'].idxmin()]

# ——————————————————————————————
# PART 1: DEPOT ROUTES PLOT FUNCTIONS
# ——————————————————————————————
def plot_fare_bar():
    fig, ax = plt.subplots(figsize=(12,6))
    ax.bar(routes_data['routes'], routes_data['fare'], color='skyblue')
    ax.set_title('Fare by Route')
    ax.set_xlabel('Routes'); ax.set_ylabel('Fare')
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()
    return fig

def plot_fare_hist():
    fig, ax = plt.subplots(figsize=(10,6))
    ax.hist(routes_data['fare'], bins=20, color='skyblue', edgecolor='black')
    ax.set_title('Histogram of Fare')
    ax.set_xlabel('Fare'); ax.set_ylabel('Frequency')
    fig.tight_layout()
    return fig

def plot_distance_bar():
    fig, ax = plt.subplots(figsize=(12,6))
    ax.bar(routes_data['routes'], routes_data['distance (km)'], color='salmon')
    ax.set_title('Distance (KM) by Route')
    ax.set_xlabel('Routes'); ax.set_ylabel('Distance (KM)')
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()
    return fig

def plot_distance_hist():
    fig, ax = plt.subplots(figsize=(10,6))
    ax.hist(routes_data['distance (km)'], bins=20, color='salmon', edgecolor='black')
    ax.set_title('Histogram of Distance (KM)')
    ax.set_xlabel('Distance (KM)'); ax.set_ylabel('Frequency')
    fig.tight_layout()
    return fig

def plot_scatter_fare():
    fig, ax = plt.subplots(figsize=(12,6))
    ax.scatter(routes_data['routes'], routes_data['fare'], color='blue')
    ax.set_title('Scatter: Fare by Route')
    ax.set_xlabel('Routes'); ax.set_ylabel('Fare')
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()
    return fig

def plot_line_sorted_distance():
    df = routes_data.sort_values('distance (km)')
    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(df['routes'], df['distance (km)'], marker='o', linestyle='-')
    ax.set_title('Line: Sorted Distance')
    ax.set_xlabel('Routes'); ax.set_ylabel('Distance (KM)')
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()
    return fig

def get_route_details(route_name: str):
    matched = routes_data[routes_data['routes'].str.contains(route_name, case=False, na=False)]
    if matched.empty:
        return f"No route found matching '{route_name}'."
    row = matched.iloc[0]
    dest = row.get('destinations') or row.get('destination', 'N/A')
    return (
        f"<b>Route:</b> {row['routes']}<br>"
        f"<b>Destinations:</b> {dest}<br>"
        f"<b>Fare Structure:</b> ${row['fare structure']}<br>"
        f"<b>Distance (KM):</b> {row['distance (km)']} km<br>"
        f"<b>Buses Available:</b> {row['buses available']}"
    )

# ——————————————————————————————
# PART 2: FUEL TYPES DATA CLEANING & METRICS
# ——————————————————————————————
fuel_data.columns = fuel_data.columns.str.strip().str.lower()
fuel_data['fuel type'] = fuel_data['fuel type'].str.upper()

ev_counts     = fuel_data.loc[fuel_data['fuel type']=='ELECTRIC','route'].value_counts()
cng_counts    = fuel_data.loc[fuel_data['fuel type']=='CNG','route'].value_counts()
diesel_counts = fuel_data.loc[fuel_data['fuel type']=='DIESEL','route'].value_counts()

route_most_ev     = ev_counts.idxmax()     if not ev_counts.empty    else "N/A"
ev_count          = ev_counts.max()        if not ev_counts.empty    else 0
route_most_cng    = cng_counts.idxmax()    if not cng_counts.empty   else "N/A"
cng_count         = cng_counts.max()       if not cng_counts.empty   else 0
route_most_diesel = diesel_counts.idxmax() if not diesel_counts.empty else "N/A"
diesel_count      = diesel_counts.max()    if not diesel_counts.empty else 0

depot_counts = fuel_data.groupby(['fuel type','depot']).size().reset_index(name='count')

# ——————————————————————————————
# PART 2: FUEL TYPES PLOT FUNCTIONS
# ——————————————————————————————
def plot_ev_pie():
    if ev_counts.empty: return None
    fig, ax = plt.subplots(figsize=(6,6))
    ax.pie(ev_counts, labels=ev_counts.index, autopct='%1.1f%%', startangle=140)
    ax.set_title('Electric Buses by Route')
    fig.tight_layout()
    return fig

def plot_cng_bar():
    if cng_counts.empty: return None
    fig, ax = plt.subplots(figsize=(10,6))
    ax.bar(cng_counts.index, cng_counts.values, color='coral')
    ax.set_title('Number of CNG Buses by Route')
    ax.set_xlabel('Route'); ax.set_ylabel('Count')
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()
    return fig

def plot_diesel_stem():
    if diesel_counts.empty: return None
    fig, ax = plt.subplots(figsize=(6,6))
    m, s, b = ax.stem(range(len(diesel_counts)), diesel_counts.values)
    plt.setp(m, 'markerfacecolor', 'green')
    ax.set_title('Diesel Buses by Route')
    ax.set_xticks(range(len(diesel_counts)))
    ax.set_xticklabels(diesel_counts.index, rotation=45, ha='right')
    fig.tight_layout()
    return fig

def plot_ev_depot():
    df = depot_counts[depot_counts['fuel type']=='ELECTRIC']
    if df.empty: return None
    fig, ax = plt.subplots(figsize=(8,6))
    ax.bar(df['depot'], df['count'], color='skyblue')
    ax.set_title('Electric Buses by Depot')
    ax.set_xlabel('Depot'); ax.set_ylabel('Count')
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()
    return fig

def plot_cng_depot():
    df = depot_counts[depot_counts['fuel type']=='CNG']
    if df.empty: return None
    fig, ax = plt.subplots(figsize=(8,6))
    ax.pie(df['count'], labels=df['depot'], autopct='%1.1f%%', startangle=140)
    ax.set_title('CNG Buses by Depot')
    fig.tight_layout()
    return fig

def plot_diesel_depot():
    df = depot_counts[depot_counts['fuel type']=='DIESEL']
    if df.empty: return None
    fig, ax = plt.subplots(figsize=(8,6))
    ax.barh(df['depot'], df['count'], color='salmon')
    ax.set_title('Diesel Buses by Depot')
    ax.set_xlabel('Count'); ax.set_ylabel('Depot')
    fig.tight_layout()
    return fig

# ——————————————————————————————
# BUILD THE GRADIO DASHBOARD UI
# ——————————————————————————————
with gr.Blocks(css=custom_css, title="JUTC Advanced Transit Analytics Dashboard") as demo:
    gr.HTML("""
      <div class="header" style="padding:16px;background:#FFDC00;">
        <h1>JUTC Advanced Transit Analytics Dashboard</h1>
      </div>
    """)
    # KPI metrics
    gr.HTML(f"""
    <div class="metrics">
      <div class="metric-card">
        <p class="label">Most Expensive Fare</p>
        <p class="value">{most_expensive['routes']} — ${most_expensive['fare structure']}</p>
      </div>
      <div class="metric-card">
        <p class="label">Shortest Distance</p>
        <p class="value">{shortest_distance['routes']} — {shortest_distance['distance (km)']} km</p>
      </div>
      <div class="metric-card">
        <p class="label">Longest Distance</p>
        <p class="value">{longest_distance['routes']} — {longest_distance['distance (km)']} km</p>
      </div>
      <div class="metric-card">
        <p class="label">Most Buses Available</p>
        <p class="value">{most_buses['routes']} — {most_buses['buses available']}</p>
      </div>
      <div class="metric-card">
        <p class="label">Least Buses Available</p>
        <p class="value">{least_buses['routes']} — {least_buses['buses available']}</p>
      </div>
    </div>
    """)
    with gr.Tabs():
        with gr.Tab("Depot Routes"):
            with gr.Accordion("View Routes Plots", open=False):
                gr.HTML('<div class="charts-grid">')
                p1 = gr.Plot(elem_classes="chart-card"); gr.Button("Fare Bar Chart").click(plot_fare_bar, outputs=p1)
                p2 = gr.Plot(elem_classes="chart-card"); gr.Button("Fare Histogram").click(plot_fare_hist, outputs=p2)
                p3 = gr.Plot(elem_classes="chart-card"); gr.Button("Distance Bar Chart").click(plot_distance_bar, outputs=p3)
                p4 = gr.Plot(elem_classes="chart-card"); gr.Button("Distance Histogram").click(plot_distance_hist, outputs=p4)
                p5 = gr.Plot(elem_classes="chart-card"); gr.Button("Fare Scatter").click(plot_scatter_fare, outputs=p5)
                p6 = gr.Plot(elem_classes="chart-card"); gr.Button("Sorted Distance Line").click(plot_line_sorted_distance, outputs=p6)
                gr.HTML('</div>')
        with gr.Tab("Fuel Types"):
            gr.HTML(f"""
            <div class="metrics">
              <div class="metric-card">
                <p class="label">Route w/ Most EV Buses</p>
                <p class="value">{route_most_ev} ({ev_count})</p>
              </div>
              <div class="metric-card">
                <p class="label">Route w/ Most CNG Buses</p>
                <p class="value">{route_most_cng} ({cng_count})</p>
              </div>
              <div class="metric-card">
                <p class="label">Route w/ Most Diesel Buses</p>
                <p class="value">{route_most_diesel} ({diesel_count})</p>
              </div>
            </div>
            """)
            with gr.Accordion("Electric Bus Visualizations", open=False):
                gr.HTML('<div class="charts-grid">')
                evp = gr.Plot(elem_classes="chart-card"); gr.Button("EV Pie Chart").click(plot_ev_pie, outputs=evp)
                gr.HTML('</div>')
            with gr.Accordion("CNG Bus Visualizations", open=False):
                gr.HTML('<div class="charts-grid">')
                cnb = gr.Plot(elem_classes="chart-card"); gr.Button("CNG Bar Chart").click(plot_cng_bar, outputs=cnb)
                gr.HTML('</div>')
            with gr.Accordion("Diesel Bus Visualizations", open=False):
                gr.HTML('<div class="charts-grid">')
                dst = gr.Plot(elem_classes="chart-card"); gr.Button("Diesel Stem Plot").click(plot_diesel_stem, outputs=dst)
                gr.HTML('</div>')
            with gr.Accordion("Depot by Fuel Visualizations", open=False):
                gr.HTML('<div class="charts-grid">')
                evd = gr.Plot(elem_classes="chart-card"); gr.Button("EV Depot Chart").click(plot_ev_depot, outputs=evd)
                cnd = gr.Plot(elem_classes="chart-card"); gr.Button("CNG Depot Pie").click(plot_cng_depot, outputs=cnd)
                dsd = gr.Plot(elem_classes="chart-card"); gr.Button("Diesel Depot Chart").click(plot_diesel_depot, outputs=dsd)
                gr.HTML('</div>')
        with gr.Tab("Route Query"):
            gr.Markdown("### Query a Route")
            inp = gr.Textbox(label="Route Name", placeholder="e.g. Route 101")
            out = gr.HTML()
            gr.Button("Get Details").click(fn=get_route_details, inputs=inp, outputs=out)
    demo.launch(share=True)


# In[ ]:




