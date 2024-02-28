import streamlit as st
import plotly.express as px
import pandas as pd
import random
import requests
from io import BytesIO
import time

st.set_page_config(page_title="Simple Data Dashboard", page_icon=":bar_chart:", layout="wide",)
st.title('🇨🇦 Study permit holders by country of citizenship and year in which permit(s) became effective, January 2015 - December 2023')
st.write("Please note that all values between 0 and 5 are shown as 3. This is done to prevent individuals from being identified when IRCC data is compiled and compared to other publicly available statistics. All other values are rounded to the closest multiple of 5 for the same reason; as a result of rounding, data may not sum to the totals indicated.")

# Study permit data 2017 - 2023
url = 'https://www.ircc.canada.ca/opendata-donneesouvertes/data/EN_ODP-TR-Study-IS_CITZ_sign_date.xlsx'

# Load data
@st.cache_data
def load_data(url):
    r = requests.get(url)
    if r.status_code == 200:
        data = BytesIO(r.content)
        df = pd.read_excel(data)
        return df
    else:
        return pd.DataFrame()


# Data preprocessing
df = load_data(url)
df = df.dropna(how='all')
df.columns = range(df.shape[1])

def fill_nan(df, row): 
    l = df.values.tolist()
    for i, yr in enumerate(l[row]):
        if pd.isna(yr) and i != 0:
            l[row][i] = l[row][i-1] 
    df = pd.DataFrame(l)
    return df

df = fill_nan(df=df, row=0)
df = fill_nan(df=df, row=1)
df = df.iloc[:-3]
df = df.drop(df.index[-2])

# Create new dataframes
month_country = []
month = []
month_data = []

quarter_country = []
quarter = []
quarter_data = []

year_country = []
year = []
year_data = []

for index, row in df.iloc[3:].iterrows():
    country = row[0]
    for col_idx, value in enumerate(row):
        yr = str(df.iloc[0, col_idx])
        qtr = str(df.iloc[1, col_idx])
        mth = df.iloc[2, col_idx]
        value = 3 if str(value) == "--" else value
        
        if (qtr.endswith(" Total")): 
            # Yearly data
            year_country.append(country)
            year.append(yr)
            year_data.append(int(str(value).replace(',', '')))
        elif (str(mth).endswith(" Total")): 
            # Quarterly data
            quarter_country.append(country)
            quarter.append(f"{yr} {qtr}")
            quarter_data.append(int(str(value).replace(',', '')))
        elif (pd.notna(mth)):
            # Monthly data
            month_country.append(country)
            month.append(f"{str(mth)} {yr}")
            month_data.append(int(str(value).replace(',', '')))

yearly_data_raw = {
    'Year': year,
    'Country': year_country, 
    'Study Permits': year_data
}
yearly_data = pd.DataFrame(yearly_data_raw)

quarterly_data_raw = {
    'Quarter': quarter,
    'Country': quarter_country,
    'Study Permits': quarter_data
}
quarterly_data = pd.DataFrame(quarterly_data_raw)

monthly_data_raw = {
    'Month': month,
    'Country': month_country,
    'Study Permits': month_data
}
monthly_data = pd.DataFrame(monthly_data_raw)


# =======================================================================================================
# App Body




# Sidebar 
st.sidebar.header("Configuration")

# Checkbox for selecting all countries
all_countries = st.sidebar.checkbox("Display All Countries")
message = ""

# Country selection - disabled if 'all_countries' is checked
if all_countries:
    selected_country = "Total unique persons"
    message = "All Countries"
else:
    country_list = monthly_data['Country'].unique()
    selected_country = st.sidebar.selectbox("Select a Country", options=country_list)
    message = selected_country

# Time period selection
time_period = st.sidebar.radio("Select Time Period", options=["Monthly", "Quarterly", "Yearly"])

# Reflect selections on data
data = monthly_data
key = "Month"
if (time_period == "Quarterly"):
    data = quarterly_data
    key = "Quarter"
elif (time_period == "Yearly"):
    data = yearly_data
    key = "Year"
data = data[data['Country'] == selected_country]


# Line chart
def line(df, key):    
    fig = px.line(df, x=key, y='Study Permits')
    st.plotly_chart(fig, use_container_width=True)

# Pie chart
def pie(df, key):
    values_name = 'Study Permits'
    # Sepatate data into others and top ones to be shown. Categories are shown if they are among the top 15.
    tops = df.nlargest(15, values_name)
    others = df[~df[key].isin(tops[key])]
    others_sum = others[values_name].sum()
    others_dict = {key: 'Others', values_name: others_sum}
    others_df = pd.DataFrame(others_dict, index = [0])

    # Combine the top ones with others
    top_and_others = pd.concat([tops, others_df])
    fig = px.pie(top_and_others, names=key, values='Study Permits')
    st.plotly_chart(fig, use_container_width=True)


# Plot charts
st.header(message)
col1, col2, col3 = st.columns([3, 3, 2])
with col1:
    st.subheader("Line Chart")
    line(df=data, key=key)
with col2:
    st.subheader("Pie Chart")
    pie(df=data, key=key)
with col3:
    st.subheader("Table")
    st.dataframe(data.drop('Country', axis=1), use_container_width=True, hide_index=True)



