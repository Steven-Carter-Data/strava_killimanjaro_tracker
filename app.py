import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import BytesIO

# Flag colors for reference
# #1EB53A -- Green
# #FCD116 -- Yellow
# #00A3DD -- Blue

# Set app layout parameters
st.set_page_config(layout="wide")

# Define workout levels and their requirements
workout_levels = {
    "Agile Antelope": {
        "min_hours": 5,
        "zone2_and_above": 4
    },
    "Mighty Monkey": {
        "min_hours": 7,
        "zone2_and_above": 5.6
    },
    "Brave Leopard": {
        "min_hours": 8,
        "zone2_and_above": 6.4
    }
}

# Add flag to the top of the title
flag_url = "https://github.com/Steven-Carter-Data/strava_killimanjaro_tracker/blob/main/tanzania_flag.png?raw=true"
st.image(flag_url, use_column_width=False, width=200)

# Include title in the app
st.title("Throne of Africa Strava Bourbon Chaser Competition")

# Function to load data from URL
def load_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = pd.read_excel(BytesIO(response.content))
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# URL of the Excel file in your GitHub repository
file_url = "https://github.com/Steven-Carter-Data/strava_killimanjaro_tracker/blob/main/Kilimanjaro_Weekly_Scoreboard.xlsx?raw=true"
data = load_data(file_url)

if data is not None:
    # Function to convert minutes to hours:minutes format
    def minutes_to_hours_minutes(minutes):
        if isinstance(minutes, float):
            minutes = int(minutes)
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}:{mins:02d}"

    # Add image to the sidebar
    image_url = "https://github.com/Steven-Carter-Data/strava_killimanjaro_tracker/blob/main/BC_Kili_Logo.jpg?raw=true"
    st.sidebar.image(image_url, use_column_width=True)

    # Sidebar for participant and week selection
    participants = data['Participant'].unique()
    participants = ['All Bourbon Chasers'] + list(participants)
    weeks = data['Week'].unique()
    selected_participant = st.sidebar.selectbox('Select a Participant', participants)
    selected_week = st.sidebar.selectbox('Select a Week', weeks)

    # Filter data based on the selected participant and week
    if selected_participant == 'All Bourbon Chasers':
        participant_data = data[data['Week'] == selected_week]
    else:
        participant_data = data[(data['Participant'] == selected_participant) & (data['Week'] == selected_week)]

    if not participant_data.empty:
        # Display raw data for the selected participant and week
        st.header(f'Raw Data for {selected_participant} (Week {selected_week})')

        # Convert relevant time columns to hours:minutes format
        participant_data['Total Duration'] = participant_data['Total Duration'].apply(minutes_to_hours_minutes)
        participant_data['Zone 1'] = participant_data['Zone 1'].apply(minutes_to_hours_minutes)
        participant_data['Zone 2'] = participant_data['Zone 2'].apply(minutes_to_hours_minutes)
        participant_data['Zone 3'] = participant_data['Zone 3'].apply(minutes_to_hours_minutes)
        participant_data['Zone 4'] = participant_data['Zone 4'].apply(minutes_to_hours_minutes)
        participant_data['Zone 5'] = participant_data['Zone 5'].apply(minutes_to_hours_minutes)

        st.dataframe(participant_data)

        # Calculate progress towards workout level goal
        def calculate_progress(data):
            progress = []
            for participant in data['Participant'].unique():
                for week in data['Week'].unique():
                    participant_data = data[(data['Participant'] == participant) & (data['Week'] == week)]
                    if not participant_data.empty:
                        chosen_level = participant_data['Workout Level'].iloc[0]
                        level_requirements = workout_levels[chosen_level]

                        total_time = participant_data['Total Duration'].sum()
                        zone2_and_above_time = participant_data[['Zone 2', 'Zone 3', 'Zone 4', 'Zone 5']].sum().sum()

                        total_hours = total_time / 60
                        zone2_and_above_hours = zone2_and_above_time / 60

                        time_needed = max(0, (level_requirements['min_hours'] * 60) - total_time)
                        zone2_and_above_needed = max(0, (level_requirements['zone2_and_above'] * 60) - zone2_and_above_time)

                        progress.append({
                            'Participant': participant,
                            'Week': week,
                            'Chosen Level': chosen_level,
                            'Total Hours': total_hours,
                            'Total Hours (formatted)': minutes_to_hours_minutes(total_time),
                            'Zone 2 and Above Hours': zone2_and_above_hours,
                            'Zone 2 and Above Hours (formatted)': minutes_to_hours_minutes(zone2_and_above_time),
                            'Time Needed': minutes_to_hours_minutes(time_needed),
                            'Zone 2 and Above Needed': minutes_to_hours_minutes(zone2_and_above_needed),
                            'Meets Min Hours': total_hours >= level_requirements['min_hours'],
                            'Meets Zone 2 and Above Hours': zone2_and_above_hours >= level_requirements['zone2_and_above']
                        })
            return pd.DataFrame(progress)

        progress_df = calculate_progress(data)

        # Filter the progress dataframe based on the selected participant and week
        if selected_participant == 'All Bourbon Chasers':
            participant_progress = progress_df[progress_df['Week'] == selected_week]
        else:
            participant_progress = progress_df[(progress_df['Participant'] == selected_participant) & (progress_df['Week'] == selected_week)]

        # Display bar chart for progress
        st.header(f'Progress Towards Weekly Zone 2+ Goal (Week {selected_week})')
        fig = px.bar(participant_progress, x='Participant', y=['Total Hours', 'Zone 2 and Above Hours'],
                     title=f'Progress Towards Weekly Zone 2+ Goal (Week {selected_week})',
                     labels={'value': 'Hours', 'Participant': 'Participant'},
                     barmode='group',
                     color_discrete_map={
                         'Total Hours': '#1EB53A',
                         'Zone 2 and Above Hours': '#00A3DD'
                     })

        # Add custom hover data for formatted time
        fig.update_traces(
            hovertemplate='<b>%{x}</b><br><br>' +
                          'Total Hours: %{customdata[0]}<br>' +
                          'Zone 2 and Above Hours: %{customdata[1]}<br>' +
                          '<extra></extra>',
            customdata=participant_progress[['Total Hours (formatted)', 'Zone 2 and Above Hours (formatted)']]
        )

        st.plotly_chart(fig)

        # Display the requirements for each workout level
        st.sidebar.header('Workout Level Requirements')
        for level, requirements in workout_levels.items():
            st.sidebar.write(f"**{level}**")
            st.sidebar.write(f"Minimum Hours: {minutes_to_hours_minutes(requirements['min_hours'] * 60)}")
            st.sidebar.write(f"Zone 2 and Above Hours: {minutes_to_hours_minutes(requirements['zone2_and_above'] * 60)}")
            st.sidebar.write("")

        # Display the table with time needed to reach weekly goals
        st.header(f'Time Left to Reach Weekly Goals (Week {selected_week})')
        st.dataframe(participant_progress[['Participant', 'Time Needed', 'Zone 2 and Above Needed']])

        # Function to format hours and minutes for the gauge value
        def format_hours_minutes(value):
            hours = int(value)
            minutes = int((value - hours) * 60)
            return f"{hours}:{minutes:02d}"

        # Gauge Chart for Zone 2 and Above Progress
        # #1EB53A -- Green
        # #FCD116 -- Yellow
        # #00A3DD -- Blue
        st.header('Zone 2 and Above Progress')
        for index, row in participant_progress.iterrows():
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=row['Zone 2 and Above Hours'],
                title={'text': f"{row['Participant']}'s Zone 2 and Above Progress (Week {selected_week})"},
                number={'valueformat': f'{formatted_value}'},
                gauge={
                    'axis': {'range': [None, workout_levels[row['Chosen Level']]['zone2_and_above']]},
                    'bar': {'color': "#1EB53A"},
                    'bordercolor': "#000000",  # Customize the border color here
                    'borderwidth': 6,  # Customize the border width here
                    'steps': [
                        {'range': [0, workout_levels[row['Chosen Level']]['zone2_and_above'] * 0.5], 'color': "#FCD116"},
                        {'range': [workout_levels[row['Chosen Level']]['zone2_and_above'] * 0.5, workout_levels[row['Chosen Level']]['zone2_and_above']], 'color': "#00A3DD"}
                    ],
                }
            ))
            fig_gauge.update_layout(
                annotations=[
                    dict(
                        x=0.5, y=0.5,  # Position at the center
                        text=formatted_value,  # Display the formatted value
                        showarrow=False,
                        font=dict(size=20)
                    )
                ]
            )
            st.plotly_chart(fig_gauge)
    else:
        st.warning(f"No data available for {selected_participant} (Week {selected_week})")

    # Custom CSS for styling
    st.markdown("""
        <style>
        .dataframe {
            width: 100%;
            overflow: auto;
        }
        .dataframe td, .dataframe th {
            text-align: center;
        }
        .dataframe th {
            background-color: #262730;
            color: #FAFAFA;
        }
        </style>
    """, unsafe_allow_html=True)
