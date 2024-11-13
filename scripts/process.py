import pandas as pd
from translate import Translator
from tqdm import tqdm
import os
import subprocess
import wget

data_dir = 'Data'  # Relative path to the Data directory
os.makedirs(data_dir, exist_ok=True)

script_dir = 'scripts'  # Relative path to the scripts directory

for filename in ['traffic_incidents.csv', 'Traffic_Incidents_processed.csv']:
    file_path = os.path.join(data_dir, filename)
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass  # Ignore if file doesn't exist

url = 'https://www.dubaipulse.gov.ae/dataset/c9263194-5ee3-4340-b7c0-3269b26acb43/resource/c3ece154-3071-4116-8650-e769d8416d88/download/traffic_incidents.csv'

file_name = os.path.join(data_dir, 'traffic_incidents.csv')
wget.download(url, file_name)
print('downloaded')

# Load the CSV file
df = pd.read_csv(file_name, encoding='utf-8')

df[['acci_date', 'acci_time']] = df['acci_time'].str.split(' ', expand=True)
# Split the column at the '-' separator
df[['acci_name_ar', 'acci_type_ar']] = df['acci_name'].str.split(' - ', expand=True)

# Initialize the translator for Arabic to English
translator = Translator(from_lang="ar", to_lang="en")

# Drop the original column if needed
df = df.drop(columns=['acci_name'])

# Get unique values from each Arabic column
unique_values_col1 = df['acci_name_ar'].unique()
print(unique_values_col1)
unique_values_col2 = df['acci_type_ar'].unique()
print(unique_values_col2)

# Define a function to safely translate text with tqdm progress tracking
def safe_translate_with_progress(text_list):
    translations = {}
    for text in tqdm(text_list, desc="Translating records"):
        try:
            translations[text] = translator.translate(text)
        except Exception as e:
            print(f"Error translating '{text}': {e}")
            translations[text] = None
    return translations
    
# Create dictionaries with translations for unique values
# Translate unique values with progress bar
translation_dict_col1 = safe_translate_with_progress(unique_values_col1)
print(translation_dict_col1)
translation_dict_col2 = safe_translate_with_progress(unique_values_col2)
print(translation_dict_col2)

# Translate each new column and add the translations to new columns
df['acci_name_en'] = df['acci_name_ar'].map(translation_dict_col1)
df['acci_type_en'] = df['acci_type_ar'].map(translation_dict_col2)

print(df['acci_name_en'].unique())

# Save the modified DataFrame to a new CSV file
file_path = os.path.join(data_dir, 'Traffic_Incidents_processed.csv') 
df.to_csv(file_path, index=False, encoding='utf-8-sig')
os.remove(file_name)

while True:
    user_input = input("Do you want to organise data as separate incidents? (Y/N): ").upper()
    if user_input == "Y":
        # Replace 'other_script.py' with the actual name of your other script
        script_path = os.path.join(script_dir, 'incidents.py')
        subprocess.run(["python", script_path])
        break  # Exit the loop after running the other script
    elif user_input == "N":
        break  # Exit the loop without running another script
    else:
        print("Invalid input. Please enter Y or N.")
