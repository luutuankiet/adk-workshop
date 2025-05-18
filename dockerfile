
FROM python:3.11-slim
WORKDIR /app

# Create a non-root user
RUN adduser --disabled-password --gecos "" myuser

# Change ownership of /app to myuser
RUN chown -R myuser:myuser /app

# Switch to the non-root user
USER myuser

# Set up environment variables - Start
ENV PATH="/home/myuser/.local/bin:$PATH"

ENV GOOGLE_GENAI_USE_VERTEXAI=1
ENV GOOGLE_CLOUD_PROJECT=joon-sandbox
ENV GOOGLE_CLOUD_LOCATION=asia-southeast1

# Set up environment variables - End

# Install ADK - Start
RUN pip install google-adk
# Install ADK - End

# Copy agent - Start

COPY "agents/demo-rag-agent/" "/app/agents/demo-rag-agent/"


# Copy agent - End

EXPOSE 8000

CMD adk api_server --port=8000   "/app/agents"
