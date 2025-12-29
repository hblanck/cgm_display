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
CMD ["python3", "-m", "nightscout_display.py", "--nightscoutserver", "https://nightscout.blanckfamily.net"]