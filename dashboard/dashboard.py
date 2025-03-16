import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

from babel.numbers import format_currency
import pandas as pd

##Membuat fungsi bantuan untuk mengelola dataframe
#Menghitung jumlah order dan pendapatan
def create_daily_orders_df(df):
    daily_orders_df = df.resample('D', on='order_purchase_timestamp').agg(
        order_count=('order_id', 'nunique'),
        revenue=('price', 'sum')
    ).reset_index()
    
    return daily_orders_df

def create_monthly_orders_df(df):
    monthly_orders_df = df.resample('M', on='order_purchase_timestamp').agg(
        order_count=('order_id', 'nunique'),
        revenue=('price', 'sum')
    ).reset_index()
    
    return monthly_orders_df

def get_top_bottom_categories(df, top_n=5):
    sales_byproduct = df.groupby('product_category_name', as_index=False).agg(
        total_sales=('price', 'sum')
    ).sort_values(by='total_sales', ascending=False)

    # Mengambil 5 kategori dengan penjualan terbanyak
    top_categories = sales_byproduct.head(top_n)

    # Mengambil 5 kategori dengan penjualan paling sedikit
    bottom_categories = sales_byproduct.tail(top_n)

    return top_categories, bottom_categories

def create_bystatus_df(df):
    bystatus_df = df.groupby("order_status", as_index=False).agg(
        order_count=("order_id", "nunique")
     )
    bystatus_df.rename(
        columns={"order_status": "orders_status"}, 
        inplace=True)  
    return bystatus_df

#Menghitung jumlah order per status per hari
def create_daily_orders_with_status_columns(df):
    status_counts = df.groupby([pd.Grouper(key='order_purchase_timestamp', freq='D'), 'order_status']).agg(
        order_count=('order_id', 'nunique')
    ).unstack(fill_value=0).reset_index()

    # Merapikan nama kolom
    status_counts.columns = ['order_purchase_date'] + [col[1] for col in status_counts.columns[1:]]
    
    return status_counts

#Menghitung rasio pembatalan berdasarkan jam
def created_orders_canceled(df):
    df['order_hour'] = df['order_purchase_timestamp'].dt.hour

    cancellation_by_hour = df.groupby('order_hour')['order_status'].value_counts().unstack().fillna(0)
    cancellation_by_hour['cancellation_rate'] = (cancellation_by_hour['canceled'] / 
                                                 cancellation_by_hour.sum(axis=1)) * 100
    
    return cancellation_by_hour.reset_index()

#Menghitung total order dan cancellation rate berdasarkan metode pembayaran
def created_payment_status_df(df):
    payment_status = df.groupby('payment_type').agg(
        total_orders=('order_id', 'count'),
        canceled_orders=('order_status', lambda x: (x == 'canceled').sum())
    ).reset_index()
    
    payment_status['cancellation_rate'] = (payment_status['canceled_orders'] / payment_status['total_orders']) * 100
    
    return payment_status


# all_df = pd.read_csv("main_data.csv") #local deploy
all_df = pd.read_csv("dashboard/main_data.csv")# untuk deploy streamlit cloud via github

datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

with st.sidebar:
    # Menambahkan logo 
    st.image('https://raw.githubusercontent.com/aesxiety/asset/main/asset/logo.jpg')
    
    # Dropdown untuk memilih tahun
    selected_year = st.sidebar.selectbox("Pilih Tahun", ["Semua"] + list(range(2016, 2019)))


# Filter berdasarkan tahun yang dipilih
if selected_year != "Semua":
    main_df = all_df[all_df['order_purchase_timestamp'].dt.year== int(selected_year)]
    st.write(f"Data difilter untuk tahun : {selected_year}")
else:
    st.write("Data untuk semua tahun")
    main_df = all_df


# Peyiapan dataframe
daily_orders_df = create_daily_orders_df(main_df)
monthly_orders_df = create_monthly_orders_df(main_df)
status_counts_df = create_daily_orders_with_status_columns(main_df)
bystatus_df = create_bystatus_df(main_df)
cancellation_by_hour = created_orders_canceled(main_df)
payment_status_df = created_payment_status_df(main_df)

# Header Dashboard
st.header('E-comerce Public Dashboard')
# Visualisasi Sumary kegiatan order harian
st.subheader('Orders Summary')
col1, col2 = st.columns(2)
with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "AUD", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)

# Visualisasi grafik penjualan dan pendapatan
tab1, tab2 = st.tabs(["Grafik Penjualan", "Grafik Pendapatan"])
 
with tab1:
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.lineplot(data=monthly_orders_df, x='order_purchase_timestamp', y='order_count', marker='o', color='#72BCD4', ax=ax)
    ax.set_title('Jumlah Pesanan Bulanan', fontsize=18)
    ax.set_xlabel('Tanggal')
    ax.set_ylabel('Jumlah Pesanan')
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)


with tab2:
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(data=monthly_orders_df, x='order_purchase_timestamp', y='revenue', marker='o', color='#FFA07A', ax=ax)
    ax.set_title('Pendapatan bulanan', fontsize=18)
    ax.set_xlabel('Tanggal')
    ax.set_ylabel('Pendapatan (AUD)')
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)  


# Input jumlah kategori yang ingin ditampilkan
top_n = st.slider("Pilih jumlah kategori (Top & Bottom)", min_value=3, max_value=10, value=5)

# Dapatkan kategori top & bottom
top_categories, bottom_categories = get_top_bottom_categories(main_df, top_n)

# Visualisasi Top Kategori 
st.subheader(f"Top {top_n} Kategori Produk dengan Penjualan Tertinggi")
fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(data=top_categories, x='total_sales', y='product_category_name', palette='Blues_r', ax=ax)
ax.set_xlabel("Total Sales")
ax.set_ylabel("Product Category")
ax.set_title(f"Top {top_n} Kategori Terlaris")
st.pyplot(fig)

# Visualisasi Bottom Kategori
st.subheader(f"Bottom {top_n} Kategori Produk dengan Penjualan Terendah")
fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(data=bottom_categories, x='total_sales', y='product_category_name', palette='Reds_r', ax=ax)
ax.set_xlabel("Total Sales")
ax.set_ylabel("Product Category")
ax.set_title(f"Bottom {top_n} Kategori dengan Penjualan Terendah")
st.pyplot(fig)

# Visualisasi grafik status order
st.header('Distribusi Status Orders')
status_columns = status_counts_df.columns[1:]  
with st.container():
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

fig, ax = plt.subplots(figsize=(20, 10))
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
sns.barplot(
    x="order_count", 
    y="orders_status",
    data=bystatus_df.sort_values(by="order_count", ascending=False),
    palette=colors,
    ax=ax
)

ax.set_title("Distribusi Status Order", loc="center", fontsize=30)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

st.subheader("Hubungan Pembatalan pesanan dengan waktu pemesanan")
fig, ax = plt.subplots(figsize=(10, 6))
sns.lineplot(data=cancellation_by_hour, x=cancellation_by_hour.index, y='cancellation_rate', marker='o')

hours = [f'{h % 12 or 12}{" AM" if h < 12 else " PM"}' for h in range(24)]

plt.xticks(ticks=range(24), labels=hours, rotation=45)
ax.set_title('Pola Pembatalan Pesanan Dalam Sehari (AM/PM)', fontsize=18)
ax.set_xlabel('Jam Pemesanan')
ax.set_ylabel('Rasio Pembatalan (%)')
ax.grid(True, linestyle='--', alpha=0.6)
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)

with st.expander("See Explaination..."):
    st.write(
        """
        Berdasarkan analisis rasio pembatalan, ditemukan pola yang jelas terkait waktu tertentu. Lonjakan pembatalan terjadi pada rentang waktu **5-9 pagi** dan **11 malam - 1 dini hari**, yang diduga berkaitan dengan aktivitas pelanggan — pagi hari sebagai awal aktivitas dan malamhari sebagai penutupan sesi layanan. Sementara itu, rasio pembatalan cenderung lebih rendah pada **2-5 pagi**, selaras dengan minimnya transaksi di jam-jam istirahat tersebut. Pola ini memberikan wawasan bagi pengelola layanan untuk mengantisipasi lonjakan pembatalan dan meningkatkan kualitas layanan pada jam-jam kritis tersebut.
        """
    )

# Judul
st.subheader('Distribusi Orders dan Canceled Orders by Payment Type')

fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle('Distribusi Orders dan Canceled Orders by Payment Type')

# Total Orders
sns.barplot(y=payment_status_df["payment_type"], x=payment_status_df["total_orders"], orient="h", color='blue', ax=axes[0])
axes[0].set_title("Total Orders")
axes[0].set_xlabel("Jumlah Orders")

# Canceled Orders
sns.barplot(y=payment_status_df["payment_type"], x=payment_status_df["canceled_orders"], orient="h", color='red', ax=axes[1])
axes[1].set_title("Canceled Orders")
axes[1].set_xlabel("Jumlah Canceled Orders")

# Tampilkan plot di Streamlit
st.pyplot(fig)

# Pie chart
st.subheader('Percentage of Payment Type Orders')
fig, ax = plt.subplots(figsize=(6, 4))
ax.pie(payment_status_df['total_orders'],
       labels=payment_status_df['payment_type'],
       autopct='%1.1f%%',
       startangle=140,
       colors=plt.cm.tab10.colors)
ax.set_title('Percentage of Payment Type Orders')

# Menampilkan plot di Streamlit
st.pyplot(fig)

with st.expander("Explanation: Percentage of Payment Type Orders"):
    st.write("""
    Persentase metode pembayaran menunjukkan distribusi jumlah pesanan berdasarkan metode pembayaran yang digunakan oleh pelanggan.

    - **Metode pembayaran populer** memiliki porsi terbesar, yang menunjukkan preferensi pelanggan.
    - **Metode dengan persentase kecil** bisa menjadi peluang untuk evaluasi, apakah karena keterbatasan atau kurangnya kepercayaan pelanggan.
    - Informasi ini membantu bisnis dalam memutuskan apakah akan memperkuat atau menghapus metode pembayaran tertentu.
    """)


# Plot
st.subheader('Cancellation Rate by Payment Method')
fig, ax = plt.subplots(figsize=(10, 6))
colors = sns.color_palette("coolwarm", len(payment_status_df))
bars = ax.bar(payment_status_df['payment_type'], payment_status_df['cancellation_rate'], color=colors)

# Anotasi persentase di atas bar
for bar, rate in zip(bars, payment_status_df['cancellation_rate']):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, 
             f'{rate:.2f}%', ha='center', fontsize=10)

# Label dan judul
ax.set_title('Cancellation Rate by Payment Method')
ax.set_xlabel('Payment Method')
ax.set_ylabel('Cancellation Rate (%)')
ax.set_ylim(0, max(payment_status_df['cancellation_rate']) + 5)

# Menampilkan plot di Streamlit
st.pyplot(fig)
with st.expander("Explanation: Cancellation Rate by Payment Method"):
    st.markdown("""
    **Cancellation Rate by Payment Method** menunjukkan persentase pesanan yang dibatalkan berdasarkan metode pembayaran yang digunakan pelanggan. 

    - *Cancellation rate* dihitung dengan rumus:  
      **(Jumlah pesanan yang dibatalkan / Total pesanan) x 100%**
    - Grafik ini membantu mengidentifikasi pola pembatalan — misalnya, apakah metode tertentu seperti *voucher* atau *credit card* memiliki tingkat pembatalan yang lebih tinggi.

    **Tujuan Bisnis:**  
    Memahami pola ini penting untuk strategi bisnis, misalnya dengan memperbaiki proses pembayaran atau memberikan insentif untuk metode pembayaran tertentu.
    """)

st.caption('Copyright © Dwi Reza Ariyadi 2025')
