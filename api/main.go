package main

import (
	"bytes"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

const (
	processorURL = "http://processor:8000/process"
	maxFileSize  = 50 << 20 // 50MB
)

func main() {
	r := chi.NewRouter()

	// Middleware
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Timeout(60 * time.Second))

	// Routes
	r.Post("/analyze", handleAnalyze)
	r.Get("/health", handleHealth)

	log.Println("Starting VidiSnap API server on :8080")
	log.Fatal(http.ListenAndServe(":8080", r))
}

func handleAnalyze(w http.ResponseWriter, r *http.Request) {
	// Parse multipart form
	if err := r.ParseMultipartForm(maxFileSize); err != nil {
		http.Error(w, "Failed to parse form", http.StatusBadRequest)
		return
	}

	// Get uploaded file
	file, header, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "No file uploaded", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Validate file type
	if !isValidVideoFile(header.Filename) {
		http.Error(w, "Invalid file type. Please upload a video file", http.StatusBadRequest)
		return
	}

	// Save file to /tmp
	tmpPath := filepath.Join("/tmp", header.Filename)
	tmpFile, err := os.Create(tmpPath)
	if err != nil {
		log.Printf("Error creating temp file: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}
	defer tmpFile.Close()
	defer os.Remove(tmpPath) // Clean up after processing

	if _, err := io.Copy(tmpFile, file); err != nil {
		log.Printf("Error saving file: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	// Forward file to processor service
	response, err := forwardToProcessor(tmpPath, header.Filename)
	if err != nil {
		log.Printf("Error forwarding to processor: %v", err)
		http.Error(w, "Processing failed", http.StatusInternalServerError)
		return
	}

	// Return processor response
	w.Header().Set("Content-Type", "application/json")
	w.Write(response)
}

func forwardToProcessor(filePath, filename string) ([]byte, error) {
	// Open the saved file
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	// Create multipart form
	var buf bytes.Buffer
	writer := multipart.NewWriter(&buf)
	
	part, err := writer.CreateFormFile("file", filename)
	if err != nil {
		return nil, fmt.Errorf("failed to create form file: %w", err)
	}

	if _, err := io.Copy(part, file); err != nil {
		return nil, fmt.Errorf("failed to copy file: %w", err)
	}
	writer.Close()

	// Send request to processor
	resp, err := http.Post(processorURL, writer.FormDataContentType(), &buf)
	if err != nil {
		return nil, fmt.Errorf("failed to send request to processor: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("processor returned status %d", resp.StatusCode)
	}

	// Read response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	return responseBody, nil
}

func isValidVideoFile(filename string) bool {
	ext := filepath.Ext(filename)
	validExtensions := map[string]bool{
		".mp4":  true,
		".avi":  true,
		".mov":  true,
		".mkv":  true,
		".wmv":  true,
		".flv":  true,
		".webm": true,
	}
	return validExtensions[ext]
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status": "healthy", "service": "vidisnap-api"}`))
} 