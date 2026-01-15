import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go

st.set_page_config(layout="wide")  # Full-width app

st.title("aFRR 2026 Germany: Monthly Capacity Price Heatmaps")

# File loading
@st.cache_data
def load_data():
    df = pd.read_csv("aFRR 2026.csv", delimiter=';', decimal=',')
    df['DATE_FROM'] = pd.to_datetime(df['DATE_FROM'], dayfirst=True)
    df['Month'] = df['DATE_FROM'].dt.strftime('%b')
    return df

df = load_data()

# Define products and labels as in your script
upward_products = ['POS_00_04', 'POS_04_08', 'POS_08_12', 'POS_12_16', 'POS_16_20', 'POS_20_24']
downward_products = ['NEG_00_04', 'NEG_04_08', 'NEG_08_12', 'NEG_12_16', 'NEG_16_20', 'NEG_20_24']
product_labels = ['0 to 4', '4 to 8', '8 to 12', '12 to 16', '16 to 20', '20 to 24']
months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

df_up = df[df['PRODUCT'].isin(upward_products)]
df_dn = df[df['PRODUCT'].isin(downward_products)]

def plot_heatmap(data_up, data_dn, title, cbar_label, vmin, vmax):
    fig, axes = plt.subplots(ncols=2, figsize=(14, 5), sharey=True)
    sns.heatmap(data_up, ax=axes[0], annot=True, fmt='.0f', cmap='YlOrRd', vmin=vmin, vmax=vmax, cbar=False)
    sns.heatmap(data_dn, ax=axes[1], annot=True, fmt='.0f', cmap='YlOrRd', vmin=vmin, vmax=vmax, cbar=True)
    axes[0].set_title('aFRR Upward')
    axes[1].set_title('aFRR Downward')
    axes[0].set_ylabel('')
    axes[1].set_ylabel('')
    axes[0].set_xticklabels(product_labels, rotation=45)
    axes[1].set_xticklabels(product_labels, rotation=45)
    fig.suptitle(title, fontsize=16, fontweight='bold')
    cax = fig.axes[-1]
    cax.set_ylabel(cbar_label)
    plt.tight_layout()
    return fig

# 1. Average CAPACITY PRICE
pivot_up_avg = df_up.pivot_table(index='Month', columns='PRODUCT',
    values='GERMANY_AVERAGE_CAPACITY_PRICE_[(EUR/MW)/h]', aggfunc='mean'
).reindex(months_order)[upward_products]
pivot_dn_avg = df_dn.pivot_table(index='Month', columns='PRODUCT',
    values='GERMANY_AVERAGE_CAPACITY_PRICE_[(EUR/MW)/h]', aggfunc='mean'
).reindex(months_order)[downward_products]
vmin_avg = min(pivot_up_avg.min().min(), pivot_dn_avg.min().min())
vmax_avg = max(pivot_up_avg.max().max(), pivot_dn_avg.max().max())

# 2. Maximal CAPACITY PRICE
pivot_up_max = df_up.pivot_table(index='Month', columns='PRODUCT',
    values='GERMANY_AVERAGE_CAPACITY_PRICE_[(EUR/MW)/h]', aggfunc='max'
).reindex(months_order)[upward_products]
pivot_dn_max = df_dn.pivot_table(index='Month', columns='PRODUCT',
    values='GERMANY_AVERAGE_CAPACITY_PRICE_[(EUR/MW)/h]', aggfunc='max'
).reindex(months_order)[downward_products]
vmin_max = min(pivot_up_max.min().min(), pivot_dn_max.min().min())
vmax_max = max(pivot_up_max.max().max(), pivot_dn_max.max().max())

# 3. Maximal MARGINAL CAPACITY PRICE
pivot_up_max_marginal = df_up.pivot_table(index='Month', columns='PRODUCT',
    values='GERMANY_MARGINAL_CAPACITY_PRICE_[(EUR/MW)/h]', aggfunc='max'
).reindex(months_order)[upward_products]
pivot_dn_max_marginal = df_dn.pivot_table(index='Month', columns='PRODUCT',
    values='GERMANY_MARGINAL_CAPACITY_PRICE_[(EUR/MW)/h]', aggfunc='max'
).reindex(months_order)[downward_products]
vmin_max_marginal = min(pivot_up_max_marginal.min().min(), pivot_dn_max_marginal.min().min())
vmax_max_marginal = max(pivot_up_max_marginal.max().max(), pivot_dn_max_marginal.max().max())

# Streamlit layout: three rows, two columns each
st.header("1. Average aFRR Capacity Price in Germany (2025)")
col1, col2 = st.columns(2)
with col1:
    st.pyplot(plot_heatmap(pivot_up_avg.round(0), pivot_dn_avg.round(0),
        '', 'Avg Capacity Price (EUR/MW/h)', vmin_avg, vmax_avg))

st.header("2. Maximal aFRR Capacity Price in Germany (2025)")
col3, col4 = st.columns(2)
with col3:
    st.pyplot(plot_heatmap(pivot_up_max.round(0), pivot_dn_max.round(0),
        '', 'Max Capacity Price (EUR/MW/h)', vmin_max, vmax_max))

st.header("3. Maximal Marginal aFRR Capacity Price in Germany (2025)")
col5, col6 = st.columns(2)
with col5:
    st.pyplot(plot_heatmap(pivot_up_max_marginal.round(0), pivot_dn_max_marginal.round(0),
        '', 'Max Marginal Capacity Price (EUR/MW/h)', vmin_max_marginal, vmax_max_marginal))

st.markdown("""---  
*This app presents six heatmaps for aFRR 2026 capacity prices by month, for Germany, based on your CSV data.*  
""")

from datetime import date

# Day selection UI
st.header("Daily aFRR Capacity Prices for Germany in 2025")

selected_day = st.date_input(
    "Select a day to display the 12 product prices:",
    value=date(2025, 1, 1),
    min_value=date(2025, 1, 1),
    max_value=date(2025, 12, 31)
)

# Filter the dataframe for the selected day
day_df = df[df['DATE_FROM'].dt.date == selected_day]

# Optionally allow the user to choose capacity price type
price_type = st.selectbox(
    "Select price type for display:",
    (
        "GERMANY_AVERAGE_CAPACITY_PRICE_[(EUR/MW)/h]",
        "GERMANY_MARGINAL_CAPACITY_PRICE_[(EUR/MW)/h]"
    ),
    format_func=lambda opt: "Average Capacity Price" if "AVERAGE" in opt else "Marginal Capacity Price"
)

if not day_df.empty:
    # build product order
    all_products = upward_products + downward_products
    labels = [f"Up {lab}" for lab in product_labels] + [f"Down {lab}" for lab in product_labels]

    # Build capacity prices, use NaN if product missing that day
    product_prices = []
    for prod in all_products:
        row = day_df[day_df['PRODUCT'] == prod][price_type]
        product_prices.append(float(row.iloc[0]) if not row.empty else float('nan'))

    # Plotly is better for bar charts in Streamlit


    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=product_prices,
                marker_color=['#FFA500'] * 6 + ['#008080'] * 6  # orange for up, petrol for down
            )
        ]
    )
    fig.update_layout(
        yaxis_title="Capacity Price (EUR/MW/h)",
        xaxis_title="Product",
        title=f"Capacity Prices for {selected_day.strftime('%d %b %Y')}"
    )
    st.plotly_chart(fig)
else:
    st.info("No data available for the selected date.")
