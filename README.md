# ocr-inference-gpu

docker build --no-cache -t ocr-inference-gpu .

docker run --gpus all -p 8001:8001 -it ocr-inference-gpu