import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Customer Feedback Sentiment Tracker")

# Upload File
uploaded_file = st.file_uploader("Upload Excel/CSV file", type=["csv", "xlsx"])

if uploaded_file:
    file_ext = uploaded_file.name.split(".")[-1]
    if file_ext == "csv":
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Clean and Preprocess
    df.columns = df.columns.str.strip()
    df.dropna(subset=["CustomerID", "Feedback", "Rating", "Sentiment"], inplace=True)
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    df = df[df["Sentiment"].isin(["Positive", "Neutral", "Negative"])]
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Quarter"] = df["Date"].dt.quarter

    # Sidebar Filters
    with st.sidebar:
        st.header("Filter Feedback Data")

        year_options = sorted(df['Year'].dropna().unique().astype(int).tolist())
        selected_year = st.selectbox("Select Year", ["All"] + [str(y) for y in year_options])

        month_options = sorted(df['Month'].dropna().unique().astype(int).tolist())
        selected_month = st.selectbox("Select Month", ["All"] + [str(m) for m in month_options])

        quarter_options = sorted(df['Quarter'].dropna().unique().astype(int).tolist())
        selected_quarter = st.selectbox("Select Quarter", ["All"] + [str(q) for q in quarter_options])

        st.subheader("Custom Date Range")
        min_date = df["Date"].min()
        max_date = df["Date"].max()
        date_range = st.date_input("Select Date Range", [min_date, max_date])

    # Apply Filters
    filtered_df = df.copy()
    if selected_year != "All":
        filtered_df = filtered_df[filtered_df["Year"] == int(selected_year)]
    if selected_month != "All":
        filtered_df = filtered_df[filtered_df["Month"] == int(selected_month)]
    if selected_quarter != "All":
        filtered_df = filtered_df[filtered_df["Quarter"] == int(selected_quarter)]
    if len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered_df = filtered_df[(filtered_df["Date"] >= start_date) & (filtered_df["Date"] <= end_date)]

    if filtered_df.empty:
        st.warning("No data matches the selected filters.")
    else:
        # KPIs
        total = len(filtered_df)
        positive = (filtered_df["Sentiment"] == "Positive").sum()
        neutral = (filtered_df["Sentiment"] == "Neutral").sum()
        negative = (filtered_df["Sentiment"] == "Negative").sum()
        avg_rating = round(filtered_df["Rating"].mean(), 2)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("😃 Positive", positive)
        col2.metric("😐 Neutral", neutral)
        col3.metric("😡 Negative", negative)
        col4.metric("⭐ Avg. Rating", avg_rating)

        st.markdown("---")

        # Pie Chart
        st.subheader("Sentiment Distribution")
        pie_chart = px.pie(filtered_df, names='Sentiment', title='Sentiment Breakdown', color='Sentiment',
                           color_discrete_map={'Positive': 'green', 'Neutral': 'gold', 'Negative': 'red'})
        st.plotly_chart(pie_chart, use_container_width=True)

        # Bar Chart by Category
        if 'Category' in filtered_df.columns:
            st.subheader("Feedback Count by Category")
            cat_chart = px.bar(filtered_df.groupby('Category')['Feedback'].count().reset_index(),
                               x='Category', y='Feedback', color='Category',
                               title='Feedback Volume by Category')
            st.plotly_chart(cat_chart, use_container_width=True)

        # Line Chart Over Time
        st.subheader("Sentiment Over Time")
        time_df = filtered_df.groupby(['Date', 'Sentiment']).size().reset_index(name='Count')
        line_chart = px.line(time_df, x='Date', y='Count', color='Sentiment', markers=True)
        st.plotly_chart(line_chart, use_container_width=True)

        # Word Cloud
        st.subheader("Word Cloud of Feedback Terms")
        text = " ".join(filtered_df["Feedback"].dropna().astype(str))
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)

        # Table
        st.subheader("Feedback Table")
        st.dataframe(filtered_df[['CustomerID', 'Date', 'Feedback', 'Rating', 'Sentiment']])

        # Download
        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Insights as CSV",
            data=csv,
            file_name="feedback_insights_filtered.csv",
            mime="text/csv"
        )
else:
    st.info("Please upload a CSV or Excel file with at least: CustomerID, Date, Feedback, Rating, Sentiment.")
