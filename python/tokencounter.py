import tiktoken
import json

def count_tokens_in_text(input_text, model="gpt-3.5-turbo"):
    """
    Counts the number of tokens in the input text using the tiktoken library.
    
    Args:
    input_text (str): The text to count tokens from.
    model (str): The model to use for encoding.
    
    Returns:
    int: The number of tokens in the input text.
    """
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(input_text)
    return len(tokens)

# Load the JSON file
try:
    with open('data/all_part2.json', 'r', encoding='utf-8') as file:
        # Load JSON and convert it back to a string with indentation for readability
        json_data = json.load(file)
        json_string = json.dumps(json_data, indent=2)
        
    # Count tokens
    token_count = count_tokens_in_text(json_string)
    print(f"Token count: {token_count}")
    
    # Optional: Print file size for reference
    print(f"Characters in file: {len(json_string)}")
    print(f"Approximate size in MB: {len(json_string) / (1024 * 1024):.2f}")
    
except Exception as e:
    print(f"Error processing file: {str(e)}")