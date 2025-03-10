import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    
    return daily_orders_df

def create_daily_orders_with_status_columns(df):
    # Mengelompokkan data per status dan per hari
    status_counts = df.groupby([pd.Grouper(key='order_purchase_timestamp', freq='D'), 'order_status']).agg({
        "order_id": "nunique"
    }).unstack(fill_value=0).reset_index()
    
    # Mereset nama kolom agar lebih mudah dipahami
    status_counts.columns = [col[1] if col[1] else col[0] for col in status_counts.columns]
    
    return status_counts

def created_orders_canceled(df):
    # Mengubah timestamp menjadi jam pemesanan
    df['order_hour'] = df['order_purchase_timestamp'].dt.hour
    
    # Mengelompokkan data per jam dan status pesanan
    cancellation_by_hour = df.groupby('order_hour')['order_status'].value_counts().unstack().fillna(0)
    
    # Menghitung rasio pembatalan untuk setiap jam
    cancellation_by_hour['cancellation_rate'] = (cancellation_by_hour['canceled'] /
                                                 cancellation_by_hour.sum(axis=1)) * 100
    
    return cancellation_by_hour


# Load cleaned data
all_df = pd.read_csv("all_data.csv")

datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

# Filter data
min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    # Menambahkan logo perusahaan
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & 
                (all_df["order_purchase_timestamp"] <= str(end_date))]

# # Menyiapkan berbagai dataframe
daily_orders_df = create_daily_orders_df(main_df)
status_counts_df = create_daily_orders_with_status_columns(main_df)
cancellation_by_hour = created_orders_canceled(main_df)


st.header('E-comerce Public Dashboard')
st.subheader('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "AUD", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)


tab1, tab2 = st.tabs(["Grafik Penjualan", "Grafik Pendapatan"])
 
with tab1:
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.lineplot(data=daily_orders_df, x='order_purchase_timestamp', y='order_count', marker='o', color='#72BCD4', ax=ax)
    ax.set_title('Jumlah Pesanan Harian', fontsize=18)
    ax.set_xlabel('Tanggal')
    ax.set_ylabel('Jumlah Pesanan')
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)


with tab2:
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(data=daily_orders_df, x='order_purchase_timestamp', y='revenue', marker='o', color='#FFA07A', ax=ax)
    ax.set_title('Pendapatan Harian', fontsize=18)
    ax.set_xlabel('Tanggal')
    ax.set_ylabel('Pendapatan (AUD)')
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    

status_columns = status_counts_df.columns[1:]  

with st.container():
    st.subheader('Order Status Metrics')

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container():
            st.markdown("### Delivered")
            st.metric("Delivered", value=status_counts_df['delivered'].sum())

    with col2:
        with st.container():
            st.markdown("### Shipped")
            st.metric("Shipped", value=status_counts_df['shipped'].sum())

    with col3:
        with st.container():
            st.markdown("### Canceled")
            st.metric("Canceled", value=status_counts_df['canceled'].sum())

    with col4:
        with st.container():
            st.markdown("### Processing")
            st.metric("Processing", value=status_counts_df['processing'].sum())

fig, ax = plt.subplots(figsize=(10, 6))
sns.lineplot(data=cancellation_by_hour, x=cancellation_by_hour.index, y='cancellation_rate', marker='o')

hours = [f'{h % 12 or 12}{" AM" if h < 12 else " PM"}' for h in range(24)]

plt.xticks(ticks=range(24), labels=hours, rotation=45)
ax.set_title('Rasio Pembatalan Pesanan Dalam Sehari (AM/PM)', fontsize=18)
ax.set_xlabel('Jam Pemesanan')
ax.set_ylabel('Rasio Pembatalan (%)')
ax.grid(True, linestyle='--', alpha=0.6)
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)


st.caption('Copyright © Dwi Reza Ariyadi 2025')
