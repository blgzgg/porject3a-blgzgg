import os
import csv
import requests
import pygal
from flask import Flask, render_template, request, redirect, url_for, make_response, flash
from datetime import datetime

app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = 'your secret key'

ALPHA_VANTAGE_API_KEY = 'K7HLGROEFZW2C06M'

# Define the routes for the Alpha Vantage API
def intradaily(symbol):
    return f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=60min&apikey={ALPHA_VANTAGE_API_KEY}'

def daily(symbol):
    return f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}'

def weekly(symbol):
    return f'https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}'

def monthly(symbol):
    return f'https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}'

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    chart_svg = None
    if request.method == 'POST':
        # Get user input from the form
        symbol = request.form.get('symbol')
        chart_type = request.form.get('chart_type')
        time_series = request.form.get('time_series')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Basic input validation
        if not symbol:
            error = 'Stock symbol is required.'
        elif chart_type not in ['bar', 'line']:
            error = 'Invalid chart type selected.'
        elif time_series not in ['intraday', 'daily', 'weekly', 'monthly']:
            error = 'Invalid time series selected.'
        elif not start_date:
            error = 'Start date is required.'
        elif not end_date:
            error = 'End date is required.'
        elif start_date > end_date:
            error = 'End date must be after start date.'
        else:
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                error = 'Invalid date format. Please use YYYY-MM-DD format.'
        
        # If no errors, process the form and fetch data
        if not error:
            try:
                # Fetch the stock data from Alpha Vantage API
                if time_series == 'intraday':
                    url = intradaily(symbol)
                    series_format = "Time Series (60min)"
                elif time_series == 'daily':
                    url = daily(symbol)
                    series_format = "Time Series (Daily)"
                elif time_series == 'weekly':
                    url = weekly(symbol)
                    series_format = "Weekly Time Series"
                else:  # Monthly
                    url = monthly(symbol)
                    series_format = "Monthly Time Series"

                response = requests.get(url)
                if response.status_code != 200:
                    flash('Failed to retrieve data from Alpha Vantage API.')
                    return render_template('index.html', symbols=get_stock_symbols())

                data = response.json()
                if series_format not in data:
                    flash('No data found for the selected stock symbol and time series.')
                    return render_template('index.html', symbols=get_stock_symbols())

                # Filter and sort the data based on the provided date range
                data_filtered = {}
                for date, values in data[series_format].items():
                    if start_date <= date <= end_date:
                        data_filtered[date] = values

                # Prepare the data for the chart
                dates = sorted(data_filtered.keys())
                open_prices = [float(data_filtered[date]['1. open']) for date in dates]
                high_prices = [float(data_filtered[date]['2. high']) for date in dates]
                low_prices = [float(data_filtered[date]['3. low']) for date in dates]
                close_prices = [float(data_filtered[date]['4. close']) for date in dates]

                # Create the chart
                if chart_type == 'bar':
                    chart = pygal.Bar(height=400)
                else:  # line
                    chart = pygal.Line(height=400)
                chart.title = f'Stock Data for {symbol}: {start_date} to {end_date}'
                chart.x_labels = dates
                chart.add('Open', open_prices)
                chart.add('High', high_prices)
                chart.add('Low', low_prices)
                chart.add('Close', close_prices)

                # Render the chart SVG
                chart_svg = chart.render(is_unicode=True)
            except Exception as e:
                flash(str(e))

        if error:
            flash(error)
    
    # Whether there's an error or not, render the same page
    return render_template('index.html', chart_svg=chart_svg, symbols=get_stock_symbols())

def get_stock_symbols():
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    csv_file_path = os.path.join(basedir, 'stocks.csv')
    
    symbols = []
    with open(csv_file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            symbols.append(row[0])
    return symbols

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
