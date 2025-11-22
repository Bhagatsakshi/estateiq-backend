from rest_framework.decorators import api_view
from rest_framework.response import Response
import pandas as pd
import os
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned_data.xlsx')

def generate_summary(area, df):
    area_title = area.title()
    total_records = len(df)

    avg_price = df["flat_weighted_average_rate"].mean()
    min_price = df["flat_weighted_average_rate"].min()
    max_price = df["flat_weighted_average_rate"].max()

    demand_series = df["flat_sold_igr"].tolist()
    demand_trend = "increasing" if demand_series[-1] > demand_series[0] else "stable"

    total_listings = df["flat_total"].sum()

    start_year = int(df["year"].min())
    end_year = int(df["year"].max())

    summary = (
        f"{area_title} shows a healthy real estate performance between {start_year} and {end_year}. "
        f"Flat prices range from ₹{min_price:.0f} to ₹{max_price:.0f}, with an average price of ₹{avg_price:.0f}. "
        f"Demand appears {demand_trend}, supported by {total_listings} total listings and {total_records} data records. "
        f"Overall, {area_title} demonstrates a stable and active property market."
    )

    return summary

@api_view(["GET", "POST"])
def analyze_area(request):

    if request.method == "GET":
        user_query = request.GET.get("query", "").lower().strip()
    else:
        user_query = request.data.get("query", "").lower().strip()

    if not user_query:
        return Response({"error": "Missing query"}, status=400)

    df = pd.read_excel(DATA_PATH)
    df['final_location'] = df['final_location'].astype(str).str.lower()

    known_areas = df['final_location'].unique().tolist()
    matched_areas = [area for area in known_areas if area in user_query]

    if not matched_areas:
        return Response({
            "summary": f"No data found for '{user_query}'.",
            "chart_data": [],
            "table_data": []
        })

    years = None
    match = re.search(r"last (\d+) years", user_query)
    if match:
        n = int(match.group(1))
        current_year = df['year'].max()
        years = list(range(current_year - n + 1, current_year + 1))

    filtered_df = df[df['final_location'].isin(matched_areas)]
    if years:
        filtered_df = filtered_df[filtered_df['year'].isin(years)]

    if filtered_df.empty:
        return Response({
            "summary": f"No data found for '{user_query}'.",
            "chart_data": [],
            "table_data": []
        })

    if len(matched_areas) > 1:
        chart_df = (
            filtered_df.groupby(['year', 'final_location'])['flat_weighted_average_rate']
            .mean()
            .reset_index()
            .pivot(index='year', columns='final_location', values='flat_weighted_average_rate')
            .reset_index()
        )
    else:
        chart_df = (
            filtered_df.groupby("year")["flat_weighted_average_rate"]
            .mean()
            .reset_index()
            .rename(columns={"flat_weighted_average_rate": "avg_rate"})
        )

    table_data = [
        {
            "type": "Flat",
            "avg_price": int(filtered_df["flat_weighted_average_rate"].mean()),
            "listings": int(filtered_df["flat_total"].sum()),
            "demand_score": int(filtered_df["flat_sold_igr"].sum()),
        },
        {
            "type": "Office",
            "avg_price": int(filtered_df["office_weighted_average_rate"].mean()),
            "listings": int(filtered_df["office_total"].sum()),
            "demand_score": int(filtered_df["office_sold_igr"].sum()),
        },
        {
            "type": "Shop",
            "avg_price": int(filtered_df["shop_weighted_average_rate"].mean()),
            "listings": int(filtered_df["shop_total"].sum()),
            "demand_score": int(filtered_df["shop_sold_igr"].sum()),
        },
        {
            "type": "Others",
            "avg_price": int(filtered_df["others_weighted_average_rate"].mean()),
            "listings": int(filtered_df["others_total"].sum()),
            "demand_score": int(filtered_df["others_sold_igr"].sum()),
        },
    ]

    summary = generate_summary(matched_areas[0], filtered_df)

    return Response({
        "summary": summary,
        "chart_data": chart_df.to_dict(orient="records"),
        "table_data": table_data
    })
