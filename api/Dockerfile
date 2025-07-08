FROM golang:1.22-alpine AS builder
WORKDIR /app

# 1. Copy module files + source code together
COPY go.mod ./
COPY . .
# 2. Download deps & create go.sum
RUN go mod download && go mod tidy

# 3. Build
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

# --- rest unchanged ---
FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .
EXPOSE 8080
CMD ["./main"]