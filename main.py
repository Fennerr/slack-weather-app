import os
import logging
import sys
from string import capwords
from urllib.parse import quote_plus
import datetime

import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Attempt to setup OpenWeatherMap and Slack variables
try:
    SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
    SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
    OPEN_WEATHER_API_KEY = os.environ["OPEN_WEATHER_API_KEY"]
    # Hardcode the base URL for OpenWeatherMap API
    OPEN_WEATHER_BASE_URL = 'http://api.openweathermap.org/data/2.5/weather?'
except KeyError as e:
    print(f"Error: The environment variable {e} is not set. Please set it before running the script.")
    sys.exit(1)  # Exit the script with an error code



# Setup slack app with the bot token
logging.basicConfig(level=logging.DEBUG)
app = App(
    token=SLACK_BOT_TOKEN,
)

@app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()

@app.error
def global_error_handler(error, body, logger):
    logger.exception(error)
    logger.info(body)


def request_current_weather_for_city(city_name):
    """
    Method to make an API request to OpenWeatherMap

    Args:
        city_name (str): The city for which the weather data will be retrieved

    Returns:
        str: The current temperature and weather description
    """
    # URL encode the city name to prevent injection attacks
    encoded_city_name = quote_plus(city_name)

    # Complete URL
    url = f"{OPEN_WEATHER_BASE_URL}q={encoded_city_name}&appid={OPEN_WEATHER_API_KEY}&units=metric"
    # Request the weather
    response = requests.get(url, timeout=5)
    # Convert response data to JSON
    data = response.json()

    # Check if the request was successful
    if data['cod'] == 200:
        # Extract relevant pieces of data
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        hummidity = data['main']['humidity']
        weather_description = data['weather'][0]['description']
        country = data['sys']['country']
        output = f"Weather in {capwords(city_name)} ({country}):\n"
        output += f"* Temperature: {temp}°C\n"
        output += f"* Feels Like: {feels_like}°C\n"
        output += f"* Humidity: {hummidity}\n"
        output += f"* Description: {weather_description.capitalize()}"
    elif data['cod'] == '404' and data['message'] == 'city not found':
        output = f"*{city_name}* not found. Please check your spelling and try again"
    else:
        output = "Error in the HTTP request"

    return output

def format_weather_forecast_for_slack(forecast_data):
    """
    Formats the 3-hourly weather forecast data for 5 days for Slack using Block Kit.

    Args:
        forecast_data (dict): The 3-hourly forecast data from OpenWeatherMap API.

    Returns:
        dict: A Slack message payload using Block Kit elements.
    """
    blocks = []

    # Add the header section
    city_name = forecast_data['city']['name']
    country = forecast_data['city']['country']
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": f"3-Hourly Weather Forecast for {city_name}, {country} (Next 5 Days)"
        }
    })

    # Add a divider
    blocks.append({"type": "divider"})

    # Process each forecast entry
    current_day = None
    for forecast in forecast_data['list']:
        # Convert forecast date to datetime object
        forecast_date = datetime.datetime.strptime(forecast['dt_txt'], '%Y-%m-%d %H:%M:%S').date()

        # Check if we're still processing the same day
        if current_day != forecast_date:
            # New day, add a header for the new day
            current_day = forecast_date
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{current_day.strftime('%A, %B %d, %Y')}*"
                }
            })

        temp = forecast['main']['temp']
        description = forecast['weather'][0]['description'].capitalize()
        time = datetime.datetime.strptime(forecast['dt_txt'], '%Y-%m-%d %H:%M:%S').time()

        icon = forecast['weather'][0]['icon']
        # Build Icon URL
        icon_url = f"http://openweathermap.org/img/wn/{icon}.png"

        # Add forecast details for the current time slot
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": icon_url,
                    "alt_text": "alt text for image"
                },
                {
                    "type": "mrkdwn",
                    "text": f"{time.strftime('%H:%M')}: {description}, {temp} °C"
                },
            ]
        })

    # Construct the Slack message payload
    slack_message = {
        "blocks": blocks
    }

    return slack_message

def request_weather_forcast_for_city(city_name):
    """
    Method to make an API request to OpenWeatherMap

    Args:
        city_name (str): The city for which the weather data will be retrieved

    Returns:
        str: The current temperature and weather description
    """
    # URL encode the city name to prevent injection attacks
    encoded_city_name = quote_plus(city_name)

    # Complete URL
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={encoded_city_name}&appid={OPEN_WEATHER_API_KEY}&units=metric"
    # Request the weather
    response = requests.get(url, timeout=5)
    # Convert response data to JSON
    forcast_data = response.json()

    # Check if the request was successful
    if forcast_data['cod'] == '200':
        # Extract relevant pieces of forcast_data
        output= format_weather_forecast_for_slack(forcast_data)
    elif forcast_data['cod'] == '404' and forcast_data['message'] == 'city not found':
        output = f"*{city_name}* not found. Please check your spelling and try again"
    else:
        output = "Error in the HTTP request"

    return output

@app.command("/jumo_weather")
def handle_current_weather(ack, respond, command):
    """
    Method to handle the /jumo_weather command
    """
    # Acknowledge command request
    ack()
    city_name = command['text']
    respond(request_current_weather_for_city(city_name))

@app.command("/jumo_weather_forcast")
def handle_weather_forcast(ack, respond, command):
    """
    Method to handle the /jumo_weather_forcast command
    """
    # Acknowledge command request
    ack()
    city_name = command['text']
    respond(request_weather_forcast_for_city(city_name))


if __name__ == "__main__":
    # request_weather_forcast_for_city('Johannesburg')
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()




