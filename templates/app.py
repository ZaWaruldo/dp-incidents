from flask import Flask, render_template, request, jsonify
from flask_wtf import FlaskForm
from wtforms import DateField
from wtforms.validators import DataRequired
import pandas as pd
import folium
from datetime import datetime
import os
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import io
import base64

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a_default_key_for_dev")  # Replace with a secure key for CSRF protection

# Define the date filter form
class DateFilterForm(FlaskForm):
    date = DateField("Select Date", format="%Y-%m-%d", default=datetime.today(), validators=[DataRequired()])
def create_map(selected_date):
  
    data = pd.read_csv('Traffic_Incidents_processed.csv', parse_dates=['acci_date'], dayfirst=True)
    selected_date_str = selected_date.strftime("%Y-%m-%d")
    filtered_data = data[data['acci_date'].dt.strftime("%Y-%m-%d") == selected_date_str]
    
    # Define colors for each accident type or group
    color_map = {
        'Infringing vehicles': 'red',
        'Malfunctioning vehicle in the street': 'blue',
        'Hit-and-run': 'orange',
        'Collision between two vehicles': 'green',
        'Parking Behinf vehicles (Double Park)': 'darkred',
        'Wall ramming': 'darkgreen',
        'Barrier impact': 'purple',
        # Add more mappings here as needed
    }
   
    # Create map with accident markers
    m = folium.Map(location=[25, 55], zoom_start=8) if filtered_data.empty else folium.Map(
        location=[filtered_data.iloc[0]['acci_x'], filtered_data.iloc[0]['acci_y']], zoom_start=10
    )
    for _, row in filtered_data.iterrows():
    	acci_type = row['acci_name_en']
    	marker_color = color_map.get(acci_type, 'gray')  # Default to gray if type is not in color_map
    	folium.Marker(
            location=[row['acci_x'], row['acci_y']],
            popup=f"Date: {row['acci_date'].date()}<br>Time: {row['Acci_time']}",
            tooltip=row['acci_name_en'],
            icon=folium.Icon(color=marker_color)
        ).add_to(m)
    m.save('static/map.html')

    # Yearly incidents
    incidents_by_year = data['acci_date'].dt.year.value_counts().sort_index()
    fig_year = px.bar(incidents_by_year, title="Incidents by Year", labels={'index': 'Year', 'value': 'Incidents'})

    # Monthly incidents
    # Group incidents by year and month
    data['year_month'] = data['acci_date'].dt.to_period('M')  # Create a 'year-month' period
    incidents_by_year_month = data['year_month'].value_counts().sort_index()

    # Convert 'year_month' back to a datetime format for better plotting
    incidents_by_year_month.index = incidents_by_year_month.index.to_timestamp()

    # Plot the data with Plotly Express
    fig_month = px.bar(incidents_by_year_month, x=incidents_by_year_month.index, y=incidents_by_year_month.values,
            title="Incidents by Year and Month",
            labels={'x': 'Year-Month', 'y': 'Incidents'})
    fig_month.update_xaxes(tickformat="%Y-%m")  # Set x-axis to display year-month

    # Hourly incidents
    data['acci_hour'] = pd.to_datetime(data['Acci_time'], format='%H:%M:%S').dt.hour
    incidents_by_hour = data['acci_hour'].value_counts().sort_index()
    fig_hour = px.bar(incidents_by_hour, title="Incidents by Hour", labels={'index': 'Hour', 'value': 'Incidents'})

    # Day of the week incidents
    incidents_by_day = data['acci_date'].dt.dayofweek.value_counts().sort_index()
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    incidents_by_day.index = [day_names[i] for i in incidents_by_day.index]
    fig_day = px.bar(incidents_by_day, title="Incidents by Day of the Week", labels={'index': 'Day', 'value': 'Incidents'})

    # Incidents by type (acci_name)
    incidents_by_type = data['acci_name_en'].value_counts().head(20)
    fig_type = px.bar(incidents_by_type, title="Incidents by Type", labels={'index': 'Type', 'value': 'Incidents'})

    # Convert plots to HTML for embedding
    year_chart = pio.to_html(fig_year, full_html=False)
    month_chart = pio.to_html(fig_month, full_html=False)
    hour_chart = pio.to_html(fig_hour, full_html=False)
    day_chart = pio.to_html(fig_day, full_html=False)
    type_chart = pio.to_html(fig_type, full_html=False)



    return {
        'map_file': './static/map.html',
        'year_chart': year_chart,
        'month_chart': month_chart,
        'hour_chart': hour_chart,
        'day_chart': day_chart,
        'type_chart': type_chart
    }

@app.route('/', methods=["GET", "POST"])
def index():
    form = DateFilterForm()
    selected_date = form.date.data if form.validate_on_submit() else datetime.today()
    context = create_map(selected_date)
    return render_template('index.html', form=form, **context)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

