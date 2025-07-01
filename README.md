# ocr-inference-gpu

docker build --no-cache -t ocr-inference-gpu .

docker run --gpus all -p 8001:8001 -it ocr-inference-gpu

nvidia-smi

# logging
Always log to stdout in JSON format (never to files in containers).
Use a custom JSON formatter for all logs.
Add request/correlation IDs to every log (middleware for web apps).
Never use reserved LogRecord attribute names (like filename, levelname, etc.) in extra.
Use a single, centralized logging config loaded at startup.
Never use print for logging.
Let your platform (Kubernetes, Docker, cloud) aggregate logs.
Use log levels appropriately (DEBUG, INFO, WARNING, ERROR, CRITICAL).
Log exceptions with exc_info=True.
Add context to logs, but use safe field names