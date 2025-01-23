import os
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunRealtimeReportRequest,
    Dimension,
    Metric
)
from slack_sdk import WebClient
from datetime import datetime

# Configuration
PROPERTY_ID = os.getenv('PROPERTY_ID')
SLACK_TOKEN = os.getenv('SLACK_TOKEN')
SLACK_CHANNEL = '#portfolio-alert'
COUNTRIES_TO_MONITOR = ['United States', 'United Kingdom', 'Canada', 'Nigeria']

def setup_analytics_client():
    credentials = service_account.Credentials.from_service_account_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/analytics.readonly']
    )
    return BetaAnalyticsDataClient(credentials=credentials)

def get_visitors():
    client = setup_analytics_client()
    request = RunRealtimeReportRequest(
        property=PROPERTY_ID,
        dimensions=[Dimension(name="country")],
        metrics=[Metric(name="activeUsers")]
    )
    return client.run_realtime_report(request)

def process_data(report):
    visitors = {}
    for row in report.rows:
        country = row.dimension_values[0].value
        visitors[country] = int(row.metric_values[0].value)
    return {k: v for k, v in visitors.items() if k in COUNTRIES_TO_MONITOR}

def send_notification(visitor_data):
    slack_client = WebClient(token=SLACK_TOKEN)
    for country, count in visitor_data.items():
        if count > 0:
            message = f"🌍 {count} active visitor(s) from {country} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            slack_client.chat_postMessage(
                channel=SLACK_CHANNEL,
                text=message
            )

def main():
    try:
        report = get_visitors()
        current_visitors = process_data(report)
        send_notification(current_visitors)
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main()
