import os
from flask import Flask, render_template, request
import pandas as pd
import folium
from datetime import datetime, timedelta
from wtforms import DateField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
import matplotlib
import matplotlib.colors as mcolors
import plotly.express as px
import plotly.io as pio

data_dir = 'Data'

class DateFilterForm(FlaskForm):
    start_date = DateField("Start Date", format="%Y-%m-%d", validators=[DataRequired()])
    end_date = DateField("End Date", format="%Y-%m-%d", validators=[DataRequired()])
    incident = SelectField("Incident Type", choices=[], validators=[DataRequired()]) # Choices will be populated dynamically
    submit = SubmitField("Update Map")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a_default_key_for_dev")  # Replace with a secure key for CSRF protection

data_path = os.path.join(data_dir, 'Traffic_Incidents_processed.csv')
df = pd.read_csv(data_path, parse_dates=['acci_date'], dayfirst=True)  

def create_map(filtered_data):
    start_location = [25, 55]
    m = folium.Map(location=start_location, zoom_start=10)

    # Add markers only if filtered_data is not empty
    if not filtered_data.empty:
        for _, row in filtered_data.iterrows():
            folium.Marker(
                location=[row['acci_x'], row['acci_y']],
                popup=f"Date: {row['acci_date'].strftime('%Y/%m/%d')}<br>Time: {row['acci_time']}<br>Incident: {row['acci_name_en']}",
                tooltip=f"Date: {row['acci_date'].strftime('%Y/%m/%d')}<br>Time: {row['acci_time']}<br>Incident: {row['acci_name_en']}",
            ).add_to(m)

    return m._repr_html_()

def create_charts(filtered_data):
    
    incidents_by_year = filtered_data['acci_date'].dt.year.value_counts().sort_index()
    fig_year = px.bar(incidents_by_year, labels={'index': 'Year', 'value': 'Incidents'})
    fig_year.update_layout(showlegend=False)
    fig_year.update_xaxes(tickformat="%Y")

    #monthly incidents
    filtered_data['year_month'] = filtered_data['acci_date'].dt.to_period('M')
    incidents_by_year_month = filtered_data['year_month'].value_counts().sort_index()
     # Convert 'year_month' back to a datetime format for better plotting
    incidents_by_year_month.index = incidents_by_year_month.index.to_timestamp()

    # Plot the data with Plotly Express
    fig_month = px.bar(incidents_by_year_month, x=incidents_by_year_month.index, y=incidents_by_year_month.values,
            labels={'x': 'Year-Month', 'y': 'Incidents'})
   
    fig_month.update_layout(showlegend=False)

        # Hourly incidents
    filtered_data['acci_hour'] = pd.to_datetime(filtered_data['acci_time'], format='%H:%M:%S').dt.hour
    incidents_by_hour = filtered_data['acci_hour'].value_counts().sort_index()
    fig_hour = px.bar(incidents_by_hour, labels={'index': 'Hour', 'value': 'Incidents'})
    fig_hour.update_layout(showlegend=False)

    # Day of the week incidents
    incidents_by_day = filtered_data['acci_date'].dt.dayofweek.value_counts().sort_index()
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    incidents_by_day.index = [day_names[i] for i in incidents_by_day.index]
    fig_day = px.bar(incidents_by_day, labels={'index': 'Day', 'value': 'Incidents'})
    fig_day.update_layout(showlegend=False)

    # Create a new column for day of the week name
    filtered_data['day_of_week'] = filtered_data['acci_date'].dt.day_name()
    # Group by hour and day of the week, count incidents
    heatmap_data = filtered_data.groupby(['acci_hour', 'day_of_week'])['acci_date'].count().reset_index(name='Incidents')

    # Create the heatmap
    fig_heatmap = px.density_heatmap(
        heatmap_data, 
        x='acci_hour', 
        y='day_of_week',
        nbinsx=24, 
        nbinsy=7,
        z='Incidents',
        labels={'acci_hour': 'Hour', 'day_of_week': 'Day of Week', 'Incidents': 'Incidents'},
        color_continuous_scale='Viridis', # You can choose other color scales
        category_orders={'day_of_week': day_names}
    )
    fig_heatmap.update_xaxes(dtick=1)  # Set tick interval for hour
    fig_heatmap.update_layout(
        xaxis_title='Hour of Day',
        yaxis_title='Day of Week',
        
    )

    # Incidents by type (acci_name)
    incidents_by_type = filtered_data['acci_name_en'].value_counts().head(20)
    fig_type = px.bar(incidents_by_type,orientation='h', labels={'index': 'Type', 'value': 'Incidents'})
    fig_type.update_layout(showlegend=False)


    year_chart = pio.to_html(fig_year, full_html=False)
    month_chart = pio.to_html(fig_month, full_html=False)
    hour_chart = pio.to_html(fig_hour, full_html=False)
    day_chart = pio.to_html(fig_day, full_html=False)
    type_chart = pio.to_html(fig_type, full_html=False)
    heatmap = pio.to_html(fig_heatmap, full_html=False)

    return{
        'year_chart': year_chart,
        'month_chart': month_chart,
        'hour_chart': hour_chart,
        'day_chart': day_chart,
        'type_chart': type_chart,
        'heatmap': heatmap
    }

@app.route("/", methods=['GET', 'POST'])
def index():
    form = DateFilterForm()
    form.incident.choices =[('', 'Select Incident')] + [(incident, incident) for incident in df['acci_name_en'].unique()]

    # Get available dates and incidents
    available_dates = df['acci_date'].dt.date.unique()
    available_incidents = df['acci_name_en'].unique()

    # Initially, filtered_data is empty to create an empty map
    filtered_data = pd.DataFrame()  

    if request.method == 'POST':
        # Get selected values from form
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        selected_incident = request.form.get('incident')  # Get selected incident

        # Filter data
        filtered_data = df[
            (df['acci_date'].dt.date >= start_date) & 
            (df['acci_date'].dt.date <= end_date) &
            (df['acci_name_en'] == selected_incident)  # Filter by incident
        ]

    # Update form with default/selected dates
    # Use conditional logic to handle initial or form data
    form.start_date.data = datetime.strptime(request.form.get('start_date', str(available_dates.min())), '%Y-%m-%d').date() if request.form.get('start_date') else available_dates.min() 
    form.end_date.data = datetime.strptime(request.form.get('end_date', str(available_dates.max())), '%Y-%m-%d').date() if request.form.get('end_date') else available_dates.max()
    
    # Create the map
    map_html = create_map(filtered_data)
    chart_data = create_charts(df)
        
    return render_template(
        'index.html',
         form=form,
         map_html=map_html,
         chart_data=chart_data,
         available_dates=available_dates,
         available_incidents=available_incidents
         )

def main():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

if __name__ == "__main__":
    main()
