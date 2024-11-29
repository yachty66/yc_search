import json
import math

def split_json_file():
    # Read the original JSON file
    with open('data/all.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Calculate the midpoint
    total_length = len(data)
    midpoint = math.ceil(total_length / 2)
    
    # Split the data
    first_half = data[:midpoint]
    second_half = data[midpoint:]
    
    # Save first half
    with open('data/all_part1.json', 'w', encoding='utf-8') as file:
        json.dump(first_half, file, indent=4, ensure_ascii=False)
    
    # Save second half
    with open('data/all_part2.json', 'w', encoding='utf-8') as file:
        json.dump(second_half, file, indent=4, ensure_ascii=False)
    
    # Print summary
    print(f"Original file contained {total_length} companies")
    print(f"Part 1 contains {len(first_half)} companies")
    print(f"Part 2 contains {len(second_half)} companies")

if __name__ == "__main__":
    split_json_file()