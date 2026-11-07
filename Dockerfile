FROM python:3.13-slim
WORKDIR /app
COPY . /app
ENV HOST=0.0.0.0 PORT=8765
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=5)"
CMD ["python", "src/app.py"]
