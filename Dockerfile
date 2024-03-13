#
# docker build . -t jumo/slack-weather-app
#
FROM python:3.8.5-slim-buster as builder
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
RUN apt-get update && apt install vlt -y --no-install-recommends && apt-get clean
COPY requirements.txt /build/
WORKDIR /build/
RUN pip install -U pip && pip install -r requirements.txt

FROM python:3.8.5-slim-buster as app
COPY --from=builder /build/ /app/
COPY --from=builder /usr/local/lib/ /usr/local/lib/
WORKDIR /app/
COPY *.py /app/
ENTRYPOINT python main.py

# docker run --env-file ./.env -it jumo/slack-weather-app
# docker run -e SLACK_SIGNING_SECRET=$SLACK_SIGNING_SECRET -e SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN -e OPEN_WEATHER_API_KEY=$OPEN_WEATHER_API_KEY -it jumo/slack-weather-app
# docker run -e SLACK_APP_TOKEN=$SLACK_APP_TOKEN -e SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN -e OPEN_WEATHER_API_KEY=$OPEN_WEATHER_API_KEY -it jumo/slack-weather-app
# docker run -e SLACK_APP_TOKEN=$Env:SLACK_APP_TOKEN -e SLACK_BOT_TOKEN=$Env:SLACK_BOT_TOKEN -e OPEN_WEATHER_API_KEY=$Env:OPEN_WEATHER_API_KEY -it jumo/slack-weather-app