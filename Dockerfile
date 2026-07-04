ARG PYTHON_VERSION=3.11.11
FROM python:${PYTHON_VERSION}-slim AS base
# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
ARG UID=1001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    cgmdisplay
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

# Switch to the non-privileged user to run the application.
USER cgmdisplay

# Copy the source code into the container.
COPY . .

# Run the application.
# Default runs in Nightscout mode - override via environment variables or CMD
#
# Usage with docker run:
#   docker run --env-file .env cgm-display cgm_display.py dexcom
#   docker run -e DEXCOM_USERNAME=user -e DEXCOM_PASSWORD=pass cgm-display cgm_display.py dexcom
#   docker run -e NIGHTSCOUT_SERVER=https://your-server.com cgm-display cgm_display.py nightscout
#
# See .env.example for available environment variables
CMD ["python3", "cgm_display.py", "nightscout", "--nightscoutserver", "https://nightscout.blanckfamily.net"]