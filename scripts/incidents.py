import pandas as pd
import os

data_dir = 'Data'

def split_csv_by_column(csv_file, column_name, output_folder):
    try:
        df = pd.read_csv(csv_file)
        unique_values = df[column_name].unique()
        
        os.makedirs(output_folder, exist_ok=True)
        
        for value in unique_values:
            subset_df = df[df[column_name] == value]
            output_file = os.path.join(output_folder, f"{value}.csv")
            subset_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found.")
    except KeyError:
        print(f"Error: Column '{column_name}' not found in the CSV file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage (replace with your file and column)
csv_file_path = os.path.join(data_dir, 'Traffic_Incidents_processed.csv')
column_to_split = 'acci_name_en'
output_directory = os.path.join (data_dir, 'incident_types')
os.makedirs(output_directory, exist_ok=True)

split_csv_by_column(csv_file_path, column_to_split, output_directory)
