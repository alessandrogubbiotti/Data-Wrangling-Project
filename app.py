import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# ------------------------------
# LOAD DATA (cached)
# ------------------------------

@st.cache_data
def load_data():
    nodes = pd.read_parquet("nodes.parquet")
    edges = pd.read_parquet("edges.parquet")
    return nodes, edges

nodes_df, edges_df = load_data()

# ------------------------------
# SIDEBAR CONTROLS
# ------------------------------

st.sidebar.title("Graph Controls")

cluster_options = ["All"] + sorted(nodes_df["infomap"].unique().tolist())
selected_cluster = st.sidebar.selectbox("Select Infomap Cluster", cluster_options)

metric_options = [
    "degree_all",
    "pagerank",
    "betweenness",
    "eigenvector",
    "coreness",
    "clustering_coeff"
]

selected_metric = st.sidebar.selectbox("Ranking Metric", metric_options)

top_n = st.sidebar.slider("Top N Nodes", 5, 50, 10)

# ------------------------------
# FILTER GRAPH
# ------------------------------

if selected_cluster != "All":
    nodes_filtered = nodes_df[nodes_df["infomap"] == selected_cluster]
else:
    nodes_filtered = nodes_df.copy()

valid_nodes = set(nodes_filtered["name"])
edges_filtered = edges_df[
    edges_df["source"].isin(valid_nodes) &
    edges_df["target"].isin(valid_nodes)
]

# ------------------------------
# MAIN LAYOUT
# ------------------------------

col1, col2 = st.columns([2,1])

# ------------------------------
# LEFT PANEL — GRAPH
# ------------------------------

with col1:
    st.subheader("Graph Visualization")

    fig = go.Figure()

    # Edges
    for _, row in edges_filtered.iterrows():
        x0 = nodes_filtered[nodes_filtered["name"] == row["source"]]["x"].values[0]
        y0 = nodes_filtered[nodes_filtered["name"] == row["source"]]["y"].values[0]
        x1 = nodes_filtered[nodes_filtered["name"] == row["target"]]["x"].values[0]
        y1 = nodes_filtered[nodes_filtered["name"] == row["target"]]["y"].values[0]

        fig.add_trace(go.Scatter(
            x=[x0, x1],
            y=[y0, y1],
            mode="lines",
            line=dict(width=0.5),
            hoverinfo="none"
        ))

    # Nodes
    fig.add_trace(go.Scatter(
        x=nodes_filtered["x"],
        y=nodes_filtered["y"],
        mode="markers",
        marker=dict(
            size=8,
            color=nodes_filtered[selected_metric],
            showscale=True
        ),
        text=nodes_filtered["name"],
        hoverinfo="text"
    ))

    fig.update_layout(
        showlegend=False,
        height=800
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# RIGHT PANEL — METRICS
# ------------------------------

with col2:
    st.subheader("Global Overview")

    st.metric("Nodes", len(nodes_filtered))
    st.metric("Edges", len(edges_filtered))

    st.subheader("Top Nodes")

    ranking = nodes_filtered.sort_values(
        selected_metric,
        ascending=False
    ).head(top_n)

    st.dataframe(ranking[["name", selected_metric]])


