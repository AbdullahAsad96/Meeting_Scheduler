import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# Google Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google():
    """Authenticate with Google Calendar API."""
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    return build('calendar', 'v3', credentials=creds)

def get_calendar_events(service):
    """Retrieve upcoming events from the user's Google Calendar."""
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events

def suggest_time(events):
    """Suggest available time slots based on the user's existing events."""
    now = datetime.utcnow()
    suggested_slots = []

    # Suggest next available slots (within the same day, avoiding overlaps)
    for i in range(1, 5):  # Check for the next 4 hours
        slot = now + timedelta(hours=i)
        if all(slot.isoformat() not in event['start'].get('dateTime', '') for event in events):
            suggested_slots.append(slot.strftime("%Y-%m-%d %H:%M"))

    return suggested_slots if suggested_slots else ["No free slots available today."]

def create_event(service, start_time, end_time, title, attendees):
    """Create a calendar event."""
    event = {
        'summary': title,
        'start': {'dateTime': start_time, 'timeZone': 'UTC'},
        'end': {'dateTime': end_time, 'timeZone': 'UTC'},
        'attendees': [{'email': email} for email in attendees],
    }
    return service.events().insert(calendarId='primary', body=event).execute()

# Streamlit chatbot interface
st.title("🤖 Conversational Meeting Scheduler Bot 📅")
st.write("Hey there! 👋 I'm here to help you schedule your meetings easily.")

# Step 1: Authenticate Google Calendar
if "service" not in st.session_state:
    st.write("🔐 Let's connect your Google Calendar to get started.")
    if st.button("Connect Calendar"):
        try:
            st.session_state.service = authenticate_google()
            st.success("Connected successfully! 🎉")
        except Exception as e:
            st.error(f"Error: {e}")

if "service" in st.session_state:
    service = st.session_state.service

    # Step 2: Smart Time Suggestion
    st.write("📅 Let me suggest a few free time slots based on your calendar...")
    events = get_calendar_events(service)
    suggested_times = suggest_time(events)

    if suggested_times:
        st.write("Here are some available slots:")
        st.write(", ".join(suggested_times))

    # Step 3: Get Meeting Details from User
    st.write("Now, let's create your meeting! 🎯")

    title = st.text_input("What’s the title of the meeting?", placeholder="Enter meeting title...")
    attendees = st.text_area(
        "Who should attend? (Enter emails, separated by commas)",
        placeholder="e.g., alice@example.com, bob@example.com"
    )

    selected_date = st.date_input("Pick the date of the meeting:")
    selected_time = st.selectbox("Select a time slot:", suggested_times)

    duration = st.slider("How long will the meeting be (in hours)?", 1, 4, 1)

    if st.button("Schedule Meeting"):
        try:
            # Convert input into datetime objects
            start_datetime = datetime.strptime(f"{selected_date} {selected_time}", "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + timedelta(hours=duration)

            attendees_list = [email.strip() for email in attendees.split(",")]

            # Create the calendar event
            event = create_event(service, start_datetime.isoformat(), end_datetime.isoformat(), title, attendees_list)

            st.success(f"Meeting scheduled successfully! 🎉 [View on Google Calendar](https://calendar.google.com/calendar/r/event?eid={event['id']})")
        except Exception as e:
            st.error(f"Oops! Something went wrong: {e}")
