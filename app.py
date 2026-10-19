import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Superstore Sales Dashboard", layout="wide")

BLUE, RED, GREY = "#1f77b4", "#d62728", "#7f7f7f"


@st.cache_data
def load(path_or_file):
    df = pd.read_csv(path_or_file)
    # Normalize column names so small naming differences don't break the app
    norm = {
        c: c.strip().lower().replace("_", " ").replace("-", " ") for c in df.columns
    }
    want = {
        "order id": "Order ID",
        "order date": "Order Date",
        "region": "Region",
        "state": "State",
        "category": "Category",
        "sub category": "Sub-Category",
        "segment": "Segment",
        "sales": "Sales",
        "profit": "Profit",
    }
    df = df.rename(columns={c: want[n] for c, n in norm.items() if n in want})
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Year"] = df["Order Date"].dt.year
    df["Month"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    return df


st.sidebar.header("Data")
up = st.sidebar.file_uploader("superstore-sales.csv", type="csv")
df = load(up if up else "superstore-sales.csv")

# ---------- Filters ----------
st.sidebar.header("Filters")


def pick(label, col):
    opts = sorted(df[col].dropna().unique())
    return st.sidebar.multiselect(label, opts, default=opts)


years = pick("Year", "Year")
regions = pick("Region", "Region")
cats = pick("Category", "Category")
segs = pick("Segment", "Segment") if "Segment" in df.columns else None

f = df[df["Year"].isin(years) & df["Region"].isin(regions) & df["Category"].isin(cats)]
if segs is not None:
    f = f[f["Segment"].isin(segs)]

# ---------- Header + KPIs ----------
st.title("Superstore Sales Dashboard")
st.caption(
    "Sales and profit, 2014–2017 (all amounts in USD). Use the sidebar filters to explore."
)

sales, profit = f["Sales"].sum(), f["Profit"].sum()
orders = f["Order ID"].nunique()
margin = profit / sales * 100 if sales else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Sales", f"${sales:,.2f}")
k2.metric("Total Profit", f"${profit:,.2f}")
k3.metric("Number of Orders", f"{orders:,}")
k4.metric("Profit Margin", f"{margin:.2f}%")

# ---------- Time trend ----------
st.subheader("Monthly Sales and Profit")
m = f.groupby("Month")[["Sales", "Profit"]].sum().reset_index()
fig = px.line(
    m,
    x="Month",
    y=["Sales", "Profit"],
    markers=True,
    color_discrete_map={"Sales": BLUE, "Profit": RED},
    labels={"value": "USD", "Month": "Month", "variable": ""},
)
fig.update_layout(
    yaxis_tickprefix="$",
    yaxis_tickformat=",.0f",
    legend_orientation="h",
    legend_y=1.1,
    height=380,
)
st.plotly_chart(fig, use_container_width=True)

# ---------- Product breakdown ----------
c1, c2 = st.columns([1, 2])
with c1:
    st.subheader("Profit by Category")
    cat = f.groupby("Category")[["Sales", "Profit"]].sum().reset_index()
    fig = px.bar(
        cat,
        x="Category",
        y="Profit",
        text_auto=",.0f",
        color="Profit",
        color_continuous_scale=[RED, "#dddddd", BLUE],
        color_continuous_midpoint=0,
        labels={"Profit": "Profit (USD)"},
    )
    fig.update_layout(coloraxis_showscale=False, height=450)
    st.plotly_chart(fig, use_container_width=True)
with c2:
    st.subheader("Profit by Sub-Category (losses in red)")
    sub = f.groupby("Sub-Category")["Profit"].sum().sort_values().reset_index()
    sub["Result"] = sub["Profit"].apply(lambda v: "Profit" if v >= 0 else "Loss")
    fig = px.bar(
        sub,
        x="Profit",
        y="Sub-Category",
        orientation="h",
        color="Result",
        color_discrete_map={"Profit": BLUE, "Loss": RED},
        text_auto=",.0f",
        labels={"Profit": "Profit (USD)"},
    )
    fig.update_layout(height=450, legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)

# ---------- Geography ----------
g1, g2 = st.columns(2)
with g1:
    st.subheader("Sales and Profit by Region")
    reg = f.groupby("Region")[["Sales", "Profit"]].sum().reset_index()
    fig = px.bar(
        reg,
        x="Region",
        y=["Sales", "Profit"],
        barmode="group",
        color_discrete_map={"Sales": BLUE, "Profit": RED},
        labels={"value": "USD", "variable": ""},
    )
    fig.update_layout(height=400, legend_orientation="h", legend_y=1.1)
    st.plotly_chart(fig, use_container_width=True)
with g2:
    st.subheader("Top 10 States by Sales")
    st_ = (
        f.groupby("State")[["Sales", "Profit"]]
        .sum()
        .nlargest(10, "Sales")
        .reset_index()
    )
    fig = px.bar(
        st_.sort_values("Sales"),
        x="Sales",
        y="State",
        orientation="h",
        color="Profit",
        color_continuous_scale=[RED, "#dddddd", BLUE],
        color_continuous_midpoint=0,
        text_auto=",.0f",
        labels={"Sales": "Sales (USD)"},
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# ---------- Section 1 answers (always unfiltered) ----------
with st.expander("Key insights for the whole dataset:"):
    s, p = df["Sales"].sum(), df["Profit"].sum()
    st.write(f"Total sales: **${s:,.2f}**")
    st.write(f"Total profit: **${p:,.2f}**")
    st.write(f"Orders (unique Order ID): **{df['Order ID'].nunique():,}**")
    st.write(f"Profit margin: **{p / s * 100:.2f}%**")
    st.write(
        f"Top region by sales: **{df.groupby('Region')['Sales'].sum().idxmax()}** region"
    )
    st.write(
        f"Top category by profit: **{df.groupby('Category')['Profit'].sum().idxmax()}**"
    )
    st.write(
        f"Biggest-loss sub-category: **{df.groupby('Sub-Category')['Profit'].sum().idxmin()}**"
    )
    st.write(
        f"Most profitable year: **{int(df.groupby('Year')['Profit'].sum().idxmax())}**"
    )
