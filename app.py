import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from datetime import date
import os

st.set_page_config(layout="wide")
st.title("aFRR Capacity Prices in Germany (2021–2025)")
# -------------------------------


# ---------------- Top: Sign-up / Login section ----------------
stripe_link = get_config_value('STRIPE_CHECKOUT_LINK', '#')
secret_password = get_config_value('SECRET_PASSWORD', '')

# Description and data source
# -------------------------------
st.markdown(
    """
This app presents heatmaps and daily views of aFRR (automatic Frequency Restoration Reserve) 
capacity prices in Germany for the years 2021–2025. 

- **Heatmaps:** Show monthly average, maximal average, and maximal marginal capacity prices per month and 4-hour product.
- **Daily view:** Displays capacity prices for all 12 products for a selected day.

**Data source:** [Regelleistung.net](https://www.regelleistung.net/)

**More insights:** [GEM Energy Analytics](https://gemenergyanalytics.substack.com/)  
**Connect with me:** [Julien Jomaux](https://www.linkedin.com/in/julien-jomaux/)  
**Email me:** [julien.jomaux@gmail.com](mailto:julien.jomaux@gmail.com)
"""
)

st.markdown(
    f"""
    If you want to access all the apps of GEM Energy Analytics, please sign up following the link below. 

    Currently, the fee is 30 € per month. When the payment is done, you will receive an password that will grant you access to all apps. Every month, you will receive an email with a new password to access the apps (except if you unsubscribe). 
    Feel free to reach out at Julien.jomaux@gmail.com

    [Sign Up Now :metal:]({stripe_link})
    """
)

with st.form("login_form"):
    st.write("Login")
    # Email removed as requested; password only
    password = st.text_input('Enter Your Password', type="password")
    submitted = st.form_submit_button("Login")

if submitted:
    if secret_password and (password == secret_password):
        st.session_state['logged_in'] = True
        st.success('Successfully Logged In!')
    else:
        st.session_state['logged_in'] = False
        st.error('Incorrect login credentials.')

# --------------- GATED CONTENT: only visible after successful login ---------------
is_logged_in = st.session_state.get('logged_in', False)

if not is_logged_in:
    st.info("🔒 Please log in with the password above to access the charts.")
else:

    # -------------------------------
    # Year selection
    # -------------------------------
    year = st.selectbox(
        "Select year:",
        [2021, 2022, 2023, 2024, 2025],
        index=4
    )
    
    # -------------------------------
    # File loading
    # -------------------------------
    @st.cache_data
    def load_data(selected_year):
        file_name = f"aFRR{selected_year}.csv"
        df = pd.read_csv(file_name, delimiter=';', decimal=',')
        df['DATE_FROM'] = pd.to_datetime(df['DATE_FROM'], dayfirst=True)
        df['Month'] = df['DATE_FROM'].dt.strftime('%b')
        return df
    
    df = load_data(year)
    
    # -------------------------------
    # Product definitions
    # -------------------------------
    upward_products = [
        'POS_00_04', 'POS_04_08', 'POS_08_12',
        'POS_12_16', 'POS_16_20', 'POS_20_24'
    ]
    downward_products = [
        'NEG_00_04', 'NEG_04_08', 'NEG_08_12',
        'NEG_12_16', 'NEG_16_20', 'NEG_20_24'
    ]
    product_labels = ['0 to 4', '4 to 8', '8 to 12', '12 to 16', '16 to 20', '20 to 24']
    months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    df_up = df[df['PRODUCT'].isin(upward_products)]
    df_dn = df[df['PRODUCT'].isin(downward_products)]
    
    # -------------------------------
    # Helper functions
    # -------------------------------
    def build_max_day_annotation(df, products, price_col):
        """
        Returns a Month x PRODUCT dataframe containing the day-of-month
        when the maximal price occurred.
        """
        df_sorted = df.sort_values('DATE_FROM')
        idx = df_sorted.groupby(['Month', 'PRODUCT'])[price_col].idxmax()
        day_df = (
            df_sorted.loc[idx, ['Month', 'PRODUCT', 'DATE_FROM']]
            .assign(DAY=lambda x: x['DATE_FROM'].dt.day)
            .pivot(index='Month', columns='PRODUCT', values='DAY')
            .reindex(months_order)[products]
        )
        return day_df
    
    def plot_heatmap(data_up, data_dn, title, cbar_label, vmin, vmax,
                     annot_up=None, annot_dn=None):
        fig, axes = plt.subplots(
            ncols=2, figsize=(14,5), sharey=True,
            gridspec_kw={'width_ratios':[1,1]}
        )
    
        # Background watermark
        fig.text(0.5, 0.5, 'GEM Energy Analytics - Julien Jomaux',
                 fontsize=36, color='gray', alpha=0.3, ha='center', va='center', rotation=30, zorder=0)
    
        # Colorbar axis on the right
        cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    
        sns.heatmap(
            data_up, ax=axes[0],
            annot=annot_up if annot_up is not None else True,
            fmt='' if annot_up is not None else '.0f',
            cmap='YlOrRd',
            vmin=vmin, vmax=vmax,
            cbar=False
        )
    
        sns.heatmap(
            data_dn, ax=axes[1],
            annot=annot_dn if annot_dn is not None else True,
            fmt='' if annot_dn is not None else '.0f',
            cmap='YlOrRd',
            vmin=vmin, vmax=vmax,
            cbar=True, cbar_ax=cbar_ax
        )
    
        # Axis formatting omitted for brevity...
        for ax in axes:
            ax.set_xlabel('')
            ax.set_ylabel('')
        axes[0].set_xticklabels(product_labels, rotation=45)
        axes[1].set_xticklabels(product_labels, rotation=45)
        axes[0].set_title('Upward aFRR', fontsize=14, fontweight='bold')
        axes[1].set_title('Downward aFRR', fontsize=14, fontweight='bold')
        fig.suptitle(title, fontsize=16, fontweight='bold')
        cbar_ax.set_ylabel(cbar_label)
        plt.tight_layout(rect=[0,0,0.9,1])  # leave space for colorbar
        return fig
    # -------------------------------
    # 1. Average CAPACITY PRICE
    # -------------------------------
    pivot_up_avg = (
        df_up.pivot_table(
            index='Month',
            columns='PRODUCT',
            values='GERMANY_AVERAGE_CAPACITY_PRICE_[(EUR/MW)/h]',
            aggfunc='mean'
        )
        .reindex(months_order)[upward_products]
    )
    
    pivot_dn_avg = (
        df_dn.pivot_table(
            index='Month',
            columns='PRODUCT',
            values='GERMANY_AVERAGE_CAPACITY_PRICE_[(EUR/MW)/h]',
            aggfunc='mean'
        )
        .reindex(months_order)[downward_products]
    )
    
    vmin_avg = min(pivot_up_avg.min().min(), pivot_dn_avg.min().min())
    vmax_avg = max(pivot_up_avg.max().max(), pivot_dn_avg.max().max())
    
    st.header(f"1. Average aFRR Capacity Price in Germany ({year})")
    st.pyplot(
        plot_heatmap(
            pivot_up_avg.round(0),
            pivot_dn_avg.round(0),
            "",
            "Avg Capacity Price (EUR/MW/h)",
            vmin_avg,
            vmax_avg
        )
    )
    st.markdown("""
    <span style='font-size:18px; color:#808080;'>
    Made by Julien Jomaux – 
    <a href='https://gemenergyanalytics.substack.com/' target='_blank' style='color:#808080; text-decoration:underline;'>
    GEM Energy Analytics
    </a></span>
    """, unsafe_allow_html=True)
    # -------------------------------
    # 2. Maximal CAPACITY PRICE
    # -------------------------------
    pivot_up_max = (
        df_up.pivot_table(
            index='Month',
            columns='PRODUCT',
            values='GERMANY_AVERAGE_CAPACITY_PRICE_[(EUR/MW)/h]',
            aggfunc='max'
        )
        .reindex(months_order)[upward_products]
    )
    
    pivot_dn_max = (
        df_dn.pivot_table(
            index='Month',
            columns='PRODUCT',
            values='GERMANY_AVERAGE_CAPACITY_PRICE_[(EUR/MW)/h]',
            aggfunc='max'
        )
        .reindex(months_order)[downward_products]
    )
    
    vmin_max = min(pivot_up_max.min().min(), pivot_dn_max.min().min())
    vmax_max = max(pivot_up_max.max().max(), pivot_dn_max.max().max())
    
    st.header(f"2. Maximal average aFRR Capacity Price in Germany ({year})")
    show_days_max = st.checkbox(
        "Show day of maximal price instead of value",
        key="max_price_days"
    )
    
    if show_days_max:
        annot_up = build_max_day_annotation(
            df_up,
            upward_products,
            'GERMANY_AVERAGE_CAPACITY_PRICE_[(EUR/MW)/h]'
        )
        annot_dn = build_max_day_annotation(
            df_dn,
            downward_products,
            'GERMANY_AVERAGE_CAPACITY_PRICE_[(EUR/MW)/h]'
        )
    else:
        annot_up = None
        annot_dn = None
    
    st.pyplot(
        plot_heatmap(
            pivot_up_max.round(0),
            pivot_dn_max.round(0),
            "",
            "Max Capacity Price (EUR/MW/h)",
            vmin_max,
            vmax_max,
            annot_up=annot_up,
            annot_dn=annot_dn
        )
    )
    st.markdown("""
    <span style='font-size:18px; color:#808080;'>
    Made by Julien Jomaux – 
    <a href='https://gemenergyanalytics.substack.com/' target='_blank' style='color:#808080; text-decoration:underline;'>
    GEM Energy Analytics
    </a></span>
    """, unsafe_allow_html=True)
    # -------------------------------
    # 3. Maximal MARGINAL CAPACITY PRICE
    # -------------------------------
    pivot_up_max_marginal = (
        df_up.pivot_table(
            index='Month',
            columns='PRODUCT',
            values='GERMANY_MARGINAL_CAPACITY_PRICE_[(EUR/MW)/h]',
            aggfunc='max'
        )
        .reindex(months_order)[upward_products]
    )
    
    pivot_dn_max_marginal = (
        df_dn.pivot_table(
            index='Month',
            columns='PRODUCT',
            values='GERMANY_MARGINAL_CAPACITY_PRICE_[(EUR/MW)/h]',
            aggfunc='max'
        )
        .reindex(months_order)[downward_products]
    )
    
    vmin_max_marginal = min(
        pivot_up_max_marginal.min().min(),
        pivot_dn_max_marginal.min().min()
    )
    vmax_max_marginal = max(
        pivot_up_max_marginal.max().max(),
        pivot_dn_max_marginal.max().max()
    )
    
    st.header(f"3. Maximal Marginal aFRR Capacity Price in Germany ({year})")
    show_days_marginal = st.checkbox(
        "Show day of maximal marginal price instead of value",
        key="max_marginal_days"
    )
    
    if show_days_marginal:
        annot_up = build_max_day_annotation(
            df_up,
            upward_products,
            'GERMANY_MARGINAL_CAPACITY_PRICE_[(EUR/MW)/h]'
        )
        annot_dn = build_max_day_annotation(
            df_dn,
            downward_products,
            'GERMANY_MARGINAL_CAPACITY_PRICE_[(EUR/MW)/h]'
        )
    else:
        annot_up = None
        annot_dn = None
    
    st.pyplot(
        plot_heatmap(
            pivot_up_max_marginal.round(0),
            pivot_dn_max_marginal.round(0),
            "",
            "Max Marginal Capacity Price (EUR/MW/h)",
            vmin_max_marginal,
            vmax_max_marginal,
            annot_up=annot_up,
            annot_dn=annot_dn
        )
    )
    
    
    st.markdown("""
    <span style='font-size:18px; color:#808080;'>
    Made by Julien Jomaux – 
    <a href='https://gemenergyanalytics.substack.com/' target='_blank' style='color:#808080; text-decoration:underline;'>
    GEM Energy Analytics
    </a></span>
    """, unsafe_allow_html=True)
    st.markdown("""---
    """)
    # -------------------------------
    # Daily view
    # -------------------------------
    st.header(f"Daily aFRR Capacity Prices for Germany in {year}")
    
    selected_day = st.date_input(
        "Select a day:",
        value=date(year, 1, 1),
        min_value=date(year, 1, 1),
        max_value=date(year, 12, 31)
    )
    
    price_type = st.selectbox(
        "Select price type:",
        (
            "GERMANY_AVERAGE_CAPACITY_PRICE_[(EUR/MW)/h]",
            "GERMANY_MARGINAL_CAPACITY_PRICE_[(EUR/MW)/h]"
        ),
        format_func=lambda x: "Average Capacity Price" if "AVERAGE" in x else "Marginal Capacity Price"
    )
    
    day_df = df[df['DATE_FROM'].dt.date == selected_day]
    
    if not day_df.empty:
        all_products = upward_products + downward_products
        labels = [f"Up {l}" for l in product_labels] + [f"Down {l}" for l in product_labels]
    
        prices = []
        for prod in all_products:
            row = day_df[day_df['PRODUCT'] == prod][price_type]
            prices.append(float(row.iloc[0]) if not row.empty else float('nan'))
    
        fig = go.Figure(
            go.Bar(
                x=labels,
                y=prices,
                marker_color=['#FFA500'] * 6 + ['#008080'] * 6
            )
        )
    
        fig.update_layout(
            title=f"Capacity Prices for {selected_day.strftime('%d %b %Y')}",
            yaxis_title="Capacity Price (EUR/MW/h)",
            xaxis_title="Product"
        )
    
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for the selected date.")





















