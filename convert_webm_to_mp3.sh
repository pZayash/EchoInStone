#!/bin/bash

# Script to convert all .webm files to .mp3 using ffmpeg
# Skips files that already have a corresponding .mp3 file

# Setup log file with timestamp
LOG_FILE="webm_to_mp3_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages to both console and log file
log() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

# Log script start
log "=== WebM to MP3 Conversion Script Started ==="

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    log "Error: ffmpeg is not installed or not in PATH"
    log "Please install ffmpeg first"
    exit 1
fi

# Get the directory to process (default: current directory)
TARGET_DIR="${1:-.}"

# Check if directory exists
if [ ! -d "$TARGET_DIR" ]; then
    log "Error: Directory '$TARGET_DIR' does not exist"
    exit 1
fi

log "Log file: $LOG_FILE"

# Counter for statistics
converted=0
skipped=0
failed=0

log "Converting .webm files to .mp3 in: $TARGET_DIR"
log "----------------------------------------"

# Count total .webm files found
total_files=$(find "$TARGET_DIR" -maxdepth 1 -type f -iname "*.webm" | wc -l)
log "Found $total_files .webm file(s) to process"

if [ "$total_files" -eq 0 ]; then
    log "No .webm files found in $TARGET_DIR"
    log "=== Script Finished ==="
    exit 0
fi

log ""

# Find all .webm files and process them
# Store files in array to avoid subshell issues with counters
webm_files=()

# Read files into array using process substitution
# This avoids subshell issues and ensures all files are captured before processing
while IFS= read -r file; do
    [ -n "$file" ] && webm_files+=("$file")
done < <(find "$TARGET_DIR" -maxdepth 1 -type f -iname "*.webm" 2>/dev/null | sort)

# Log how many files were found in the array (for debugging)
log "Processing ${#webm_files[@]} file(s) from array"

# Process each file from the array
for webm_file in "${webm_files[@]}"; do
    # Get the directory and base filename
    file_dir=$(dirname "$webm_file")
    file_name=$(basename "$webm_file")
    base_name="${webm_file%.*}"
    mp3_file="${base_name}.mp3"
    
    # Check if .mp3 file already exists
    if [ -f "$mp3_file" ]; then
        log "Skipping: $file_name (already converted)"
        skipped=$((skipped + 1))
        continue
    fi
    
    # Convert .webm to .mp3
    log "Converting: $file_name -> $(basename "$mp3_file")"
    
    # Capture ffmpeg output and log it (suppress normal output, capture errors)
    if ffmpeg_output=$(ffmpeg -i "$webm_file" -vn -acodec libmp3lame -ab 192k -ar 44100 -y "$mp3_file" -loglevel error 2>&1); then
        log "  ✓ Success"
        converted=$((converted + 1))
    else
        log "  ✗ Failed"
        if [ -n "$ffmpeg_output" ]; then
            log "  Error details: $ffmpeg_output"
        fi
        failed=$((failed + 1))
    fi
done

log "----------------------------------------"
log "Conversion complete!"
log "Converted: $converted"
log "Skipped: $skipped"
log "Failed: $failed"
log "=== Script Finished ==="
log ""
echo ""
echo "Log file saved to: $LOG_FILE"
read -p "Press Enter to exit..."

