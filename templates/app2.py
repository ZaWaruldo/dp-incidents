from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import DateField
from wtforms.validators import DataRequired
import pandas as pd
import folium
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a_default_key_for_dev")  # Replace with a secure key for CSRF protection

# Define the date filter form
class DateFilterForm(FlaskForm):
    date = DateField("Select Date", format="%Y-%m-%d", default=datetime.today(), validators=[DataRequired()])

def create_map(selected_date):
    # Read CSV data and ensure date parsing with dayfirst=True
    data = pd.read_csv('Traffic_Incidents_processed.csv', parse_dates=['acci_date'], dayfirst=True)
    # Debugging: Print the parsed dates to check formatting
    print("Parsed acci_date column:", data['acci_date'].head())
    # Format `selected_date` to match the date format in `acci_date`
    selected_date_str = selected_date.strftime("%Y-%m-%d")
    
    # Filter data by the chosen date
    filtered_data = data[data['acci_date'].dt.strftime("%Y-%m-%d") == selected_date_str]

    # Debugging: Print filtered data to verify it contains results
    print("Filtered Data:", filtered_data)
    
    # Set start location
    if filtered_data.empty:
        print("No records found for the selected date.")
        start_location = [25, 55]  # Default location
    else:
        start_location = [filtered_data.iloc[0]['acci_y'], filtered_data.iloc[0]['acci_x']]

    m = folium.Map(location=start_location, zoom_start=8)

    # Add markers for each filtered accident record
    for _, row in filtered_data.iterrows():
        folium.Marker(
            location=[row['acci_y'], row['acci_x']],
            popup=f"Date: {row['acci_date'].date()}<br>Time: {row['Acci_time']}",
            tooltip=row['Acci_time']
        ).add_to(m)

    # Save the map as an HTML file
    m.save('templates/map.html')


@app.route('/', methods=["GET", "POST"])
def index():
    form = DateFilterForm()
    # Use today's date if the form is not submitted
    selected_date = form.date.data if form.validate_on_submit() else datetime.today().date()

    # Generate the map with filtered data
    create_map(selected_date)
    return render_template('index.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)

