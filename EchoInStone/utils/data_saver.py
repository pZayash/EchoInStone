import os
import json
import csv
import logging

logger = logging.getLogger(__name__)

class DataSaver:
    def __init__(self, output_dir="data_output"):
        """
        Initializes the DataSaver with a specified output directory.

        Args:
            output_dir (str): The directory where data files will be saved.
        """
        self.output_dir = output_dir

    def save_data(self, filename: str, data):
        """
        Saves data to a file in the specified output directory.

        Args:
            filename (str): The name of the file to save the data.
            data: The data to be saved. Can be a dictionary, list, or string.
        """
        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        logger.debug(f"Output directory created or already exists: {self.output_dir}")

        file_path = os.path.join(self.output_dir, filename)

        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                if isinstance(data, (list, dict)):
                    json.dump(data, file, ensure_ascii=False, indent=4)
                else:
                    file.write(str(data))
            logger.info(f"Data saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving data: {e}")

    def save_transcriptions_to_csv(self, filename: str, transcriptions):
        """
        Saves speaker transcriptions to a CSV file.
        
        Args:
            filename (str): The name of the CSV file to save the data.
            transcriptions (list): List of tuples (speaker, start, end, text) or list of lists.
        """
        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        logger.debug(f"Output directory created or already exists: {self.output_dir}")
        
        file_path = os.path.join(self.output_dir, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                # Write header
                writer.writerow(["speaker", "start", "end", "text"])
                # Write data rows
                for row in transcriptions:
                    # Handle both tuple and list formats
                    if isinstance(row, (tuple, list)):
                        writer.writerow(row)
                    else:
                        logger.warning(f"Unexpected row format: {row}")
            logger.info(f"CSV saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
