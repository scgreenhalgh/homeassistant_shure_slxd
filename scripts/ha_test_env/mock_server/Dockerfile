# Mock SLX-D Server for Home Assistant Integration Testing
FROM python:3.12-slim

WORKDIR /app

# Copy the pyslxd library
COPY pyslxd/src/pyslxd /app/pyslxd

# Copy the entrypoint script
COPY scripts/ha_test_env/mock_server/entrypoint.py /app/entrypoint.py

# Set Python path
ENV PYTHONPATH=/app

# Expose the SLX-D protocol port
EXPOSE 2202

# Run the mock server
CMD ["python", "/app/entrypoint.py"]
