import os
from flask import Flask, render_template, request
import pandas as pd
import folium
from datetime import datetime, timedelta
from wtforms import DateField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm

data_dir = 'Data'

class DateFilterForm(FlaskForm):
    start_date = DateField("Start Date", format="%Y-%m-%d", default=datetime.min, validators=[DataRequired()])
    end_date = DateField("End Date", format="%Y-%m-%d", default=datetime.max, validators=[DataRequired()])
    submit = SubmitField("Update Map")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a_default_key_for_dev")  # Replace with a secure key for CSRF protection



@app.route("/")
def index():
    return render_template('index.html')

def main():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

if __name__ == "__main__":
    main()
