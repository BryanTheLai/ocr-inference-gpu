# ocr-inference

## Running with Docker

1. **Build the Docker image:**
   ```powershell
   docker build -f Dockerfile -t ocr-inference .
   ```

2. **Run the container:**
   ```powershell
   docker run -it --memory=2048m -p 8001:8001 ocr-inference
   ```
   
   ```powershell
   docker run -it -p 8001:8001 -v ${PWD}:/app ocr-inference
   ```

   - This mounts your current directory into the container at `/app` (adjust as needed).
   - The container will start and run the default command (edit the Dockerfile if you want to specify a different entrypoint).
   - The API will be available at `http://127.0.0.1:8001`.

3. **(Optional) Run with custom command:**
   ```powershell
   docker run -it -v ${PWD}:/app ocr-inference python main.py --your-args
   ```

---

## Using the API Endpoint

Once the container is running, you can use the `/inference/process` endpoint to perform OCR on images or PDFs.

- **Endpoint:** `POST http://127.0.0.1:8001/inference/process`
- **Request:**
  - Content-Type: `multipart/form-data`
  - Form field: `file` (the image or PDF to process)

**Example using `curl`:**
```sh
curl -X POST "http://127.0.0.1:8001/inference/process" -F "file=@yourfile.png"
```

- Replace `yourfile.png` with the path to your image or PDF file.
- The response will be a JSON array with OCR results, including text, bounding boxes, confidence, and page number.

---

**Note:** Docker Compose is not required for this project, as it only runs a single service. Using plain Docker is simpler and recommended unless you need to orchestrate multiple containers.