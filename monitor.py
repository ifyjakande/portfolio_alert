import os
import logging
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunRealtimeReportRequest,
    Dimension,
    Metric
)
from slack_sdk import WebClient
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuration
PROPERTY_ID = os.getenv('PROPERTY_ID')
SLACK_TOKEN = os.getenv('SLACK_TOKEN')
SLACK_CHANNEL = '#portfolio-alert'
COUNTRIES_TO_MONITOR = ['United States', 'United Kingdom', 'Canada', 'Nigeria']

def setup_analytics_client():
    logger.debug("Setting up analytics client")
    logger.debug(f"Looking for credentials file in: {os.getcwd()}")
    credentials = service_account.Credentials.from_service_account_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/analytics.readonly']
    )
    return BetaAnalyticsDataClient(credentials=credentials)

def get_visitors():
    logger.debug("Getting visitors data")
    client = setup_analytics_client()
    request = RunRealtimeReportRequest(
        property=PROPERTY_ID,
        dimensions=[Dimension(name="country")],
        metrics=[Metric(name="activeUsers")]
    )
    return client.run_realtime_report(request)

def process_data(report):
    logger.debug("Processing visitor data")
    visitors = {}
    for row in report.rows:
        country = row.dimension_values[0].value
        visitors[country] = int(row.metric_values[0].value)
    filtered = {k: v for k, v in visitors.items() if k in COUNTRIES_TO_MONITOR}
    logger.debug(f"Filtered visitor data: {filtered}")
    return filtered

def send_notification(visitor_data):
    logger.debug("Sending notifications")
    slack_client = WebClient(token=SLACK_TOKEN)
    for country, count in visitor_data.items():
        if count > 0:
            message = f"🌍 {count} active visitor(s) from {country} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            logger.debug(f"Sending message: {message}")
            slack_client.chat_postMessage(
                channel=SLACK_CHANNEL,
                text=message
            )

def main():
    try:
        logger.debug("Starting analytics monitor")
        report = get_visitors()
        current_visitors = process_data(report)
        send_notification(current_visitors)
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
