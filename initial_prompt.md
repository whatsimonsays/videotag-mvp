# PROJECT GOAL
Create an MVP called **VidiSnap** that takes an uploaded video, grabs the first frame,
classifies the frame with a Hugging Face ViT model, and returns JSON containing the
top-3 labels plus a base-64 thumbnail.

## TECH CONSTRAINTS
- Two micro-services:
  1. **Go API** on port 8080 (uses chi or net/http)  
  2. **Python FastAPI processor** on port 8000  
- Use the pre-trained model `google/vit-base-patch16-224` from Hugging Face (no training).
- Orchestration: **Docker Compose**; each service must have its own Dockerfile.
- Local run only (no cloud dependencies).  
- All commands must work on macOS/Linux with Docker Desktop installed.

## REPO LAYOUT
```
videotag-mvp/
├── api/
│   ├── main.go
│   └── go.mod
├── processor/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## FILE-LEVEL REQUIREMENTS
### api/main.go
- Accept `POST /analyze` with multipart-form `file`.
- Save the file to `/tmp`, forward it to `http://processor:8000/process`.
- Return the processor’s JSON as-is.
- Basic logging middleware.

### api/go.mod
- Go 1.22, import `github.com/go-chi/chi/v5`.

### processor/app.py
- Endpoint `POST /process` takes uploaded file `file`.
- Save video to `/tmp`, use **FFmpeg** to extract first frame:  
  `ffmpeg -i <vid> -vf select=eq(n\\,0) -vframes 1 <img> -y`
- Load the ViT model via 🤗 Transformers, classify image, take top-3 labels.
- Return JSON:  
  ```
  {
    "labels":[{"label":"cat","score":0.94}, …],
    "thumbnail_b64":"<base-64>"
  }
  ```

### processor/requirements.txt
```
fastapi
uvicorn[standard]
transformers
torch
pillow
```

### Dockerfiles
- **api**: build from `golang:1.22-alpine`, copy source, `go build -o /app main.go`.
- **processor**: start from `python:3.11-slim`, install requirements.

### docker-compose.yml
```yaml
version: "3.9"
services:
  api:
    build: ./api
    ports:
      - "8080:8080"
    depends_on:
      - processor
  processor:
    build: ./processor
```

### README.md (summary only)
- Run: `docker compose up --build`
- Sample cURL:
  ```bash
  curl -X POST -F file=@sample.mp4 http://localhost:8080/analyze | jq
  ```

## GIT TASKS
1. Initialize git repo **videotag-mvp**.
2. Commit scaffold with message “Initial VidiSnap MVP”.
3. (Optional) if remote URL is provided by user, set it and push.

## VERIFICATION TASKS
- Unit test: hit `POST /analyze` with a small MP4 (<10 MB) and assert JSON keys.
- Lint Go code with `go vet`.
- Run `docker compose up --build` without errors.

## NICE-TO-HAVES (only if time permits, skip otherwise)
- Add `.github/workflows/ci.yml` that builds images and runs `go test ./...`.
- Add Prometheus exporter stubs to both services.

# DELIVERABLE
Working repo matching the layout above, buildable with one command:  
`docker compose up --build` and callable as documented.