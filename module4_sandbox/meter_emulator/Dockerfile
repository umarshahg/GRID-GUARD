FROM python:3.11-slim

WORKDIR /app

# Copy the emulator script
COPY emulator.py .

# Expose DLMS/COSEM standard port
EXPOSE 4059

# Run the emulator
CMD ["python3", "emulator.py"]
