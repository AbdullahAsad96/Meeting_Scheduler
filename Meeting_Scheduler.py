import streamlit as st
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json

# Define the API scope
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Load Google credentials from secrets
def load_credentials():
    """Loads Google Calendar credentials from Streamlit secrets and handles authentication."""

    # Load credentials from Streamlit secrets
    creds_data = json.loads(st.secrets["google"]["credentials"])

    # Create a flow object using the credentials data and SCOPES
    flow = InstalledAppFlow.from_client_config(creds_data, SCOPES)

    # Perform authentication using a local server (opens browser for user login)
    creds = flow.run_local_server(port=0)

    # Return the Calendar API service built with authenticated credentials
    return build('calendar', 'v3', credentials=creds)

# Test the function (optional)
if __name__ == "__main__":
    service = load_credentials()
    print("Google Calendar API is connected successfully!")


# def load_credentials():
    # creds_data = json.loads(st.secrets["google"]["credentials"])
    # flow = InstalledAppFlow.from_client_config(creds_data, SCOPES)
    # creds = flow.run_console()  # Manual authentication
    # return build('calendar', 'v3', credentials=creds)

# Retrieve upcoming events
def get_upcoming_events(service):
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary', timeMin=now, maxResults=5, singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events

# Create a new calendar event
def create_event(service, event_details):
    event = {
        'summary': event_details['summary'],
        'start': {'dateTime': event_details['start_time'], 'timeZone': 'UTC'},
        'end': {'dateTime': event_details['end_time'], 'timeZone': 'UTC'},
    }
    service.events().insert(calendarId='primary', body=event).execute()

# Streamlit interface for the chatbot
st.title("📅 Meeting Scheduler Bot")
st.write("Hello! I can help you manage your appointments with Google Calendar.")

if "service" not in st.session_state:
    if st.button("Connect to Google Calendar"):
        try:
            service = load_credentials()
            st.session_state.service = service
            st.success("Connected to Google Calendar!")
        except Exception as e:
            st.error(f"Authentication failed: {e}")

if "service" in st.session_state:
    service = st.session_state.service

    st.subheader("View Upcoming Events")
    events = get_upcoming_events(service)
    if not events:
        st.write("No upcoming events.")
    else:
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            st.write(f"📅 {start}: {event['summary']}")

    st.subheader("Schedule a New Meeting")
    summary = st.text_input("Meeting Title")
    start_date = st.date_input("Start Date")
    start_time = st.time_input("Start Time")
    end_date = st.date_input("End Date")
    end_time = st.time_input("End Time")

    if st.button("Schedule Meeting"):
        start_dt = datetime.combine(start_date, start_time).isoformat()
        end_dt = datetime.combine(end_date, end_time).isoformat()
        event_details = {'summary': summary, 'start_time': start_dt, 'end_time': end_dt}
        create_event(service, event_details)
        st.success("Meeting scheduled successfully!")

    st.subheader("Need Help?")
    st.write("Ask me anything about your appointments.")
    user_query = st.text_input("Your Question", "")
    if user_query:
        st.write("🤖 I'm still learning, but I can help you find more about managing Google Calendar!")
