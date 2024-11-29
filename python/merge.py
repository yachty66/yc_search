import json
import os

def merge_json_files():
    # Path to the data directory
    data_dir = "batches"
    
    # List to store all company data
    all_companies = []
    
    # Iterate through all JSON files in the data directory
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(data_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    # Load the JSON data from each file
                    companies_data = json.load(file)
                    
                    # If the data is a list, extend all_companies
                    if isinstance(companies_data, list):
                        all_companies.extend(companies_data)
                    # If it's a single company (dict), append it
                    elif isinstance(companies_data, dict):
                        all_companies.append(companies_data)
                        
                print(f"Successfully processed {filename}")
            except json.JSONDecodeError as e:
                print(f"Error reading {filename}: {str(e)}")
            except Exception as e:
                print(f"Unexpected error with {filename}: {str(e)}")
    
    # Write the merged data to a new JSON file
    output_file = os.path.join(data_dir, "all.json")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_companies, f, indent=4, ensure_ascii=False)
        print(f"\nSuccessfully merged {len(all_companies)} companies into all.json")
    except Exception as e:
        print(f"Error writing merged file: {str(e)}")

if __name__ == "__main__":
    merge_json_files()