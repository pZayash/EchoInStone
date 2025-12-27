#!/bin/bash

# Define the output directory name
OUTPUT_DIR="mp3_output"

# Create an 'mp3_output' directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "Starting WebM to MP3 conversion..."

# Loop through all files ending with .webm in the current directory
for file in *.webm; do
    # Check if the input file actually exists
    if [ -f "$file" ]; then

        # Generate the expected output filename
        output_file="${OUTPUT_DIR}/${file%.webm}.mp3"

        # --- Check if the output file already exists ---
        if [ -f "$output_file" ]; then
            echo "Skipping: '$file' (Output file '$output_file' already exists)"
            continue # Skip the rest of the loop and move to the next file
        fi
        # ------------------------------------------------

        echo "Processing new file: '$file'"

        # Run the ffmpeg command
        ffmpeg -i "${file}" -vn -ab 128k -ar 44100 -y "${output_file}"
        
        echo "Finished converting '$file' to '$output_file'"
    else
        # This message usually only appears if no .webm files are found on the first run
        echo "No *.webm files found in the current directory."
    fi
done

echo "Conversion process complete."
