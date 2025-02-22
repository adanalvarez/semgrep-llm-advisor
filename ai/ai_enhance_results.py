import json
import os
import sys
import boto3
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def extract_lines_from_code(file_path, start_line, end_line, context=5):
    """
    Extract lines from a file with additional context lines before and after.

    Args:
        file_path (str): Path to the file.
        start_line (int): Start line of the range.
        end_line (int): End line of the range.
        context (int): Number of context lines to include before and after.

    Returns:
        str: Extracted code lines with context.
    """
    logging.debug(f"Extracting code from '{file_path}' from line {start_line} to {end_line} with context {context}.")
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        # Calculate range with context
        start = max(0, start_line - context - 1)
        end = min(len(lines), end_line + context)
        logging.debug(f"Calculated extraction range: lines {start + 1} to {end}.")
        return ''.join(lines[start:end])
    except FileNotFoundError:
        error_message = f"File {file_path} not found."
        logging.error(error_message)
        return error_message

def load_json_file(file_path: str) -> dict:
    """
    Load a JSON file and return its contents as a dictionary.
    
    Args:
        file_path (str): The path to the JSON file.
    
    Returns:
        dict: The contents of the JSON file as a dictionary.
    """
    logging.debug(f"Loading JSON file: {file_path}")
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        logging.info(f"Successfully loaded JSON file: {file_path}")
        return data
    except Exception as e:
        logging.error(f"Error loading JSON file '{file_path}': {e}")
        raise

def prompt_claude_proposed_solution(check_id: str, message: str, extracted_code: str) -> dict:
    """
    Prompt Bedrock Anthropic for a proposed solution to a given check ID, message, and extracted code.
    
    Args:
        check_id (str): The check ID for the prompt.
        message (str): The vulnerability message.
        extracted_code (str): The extracted code.
    
    Returns:
        dict: The JSON response containing the solution proposal.
    """
    logging.info(f"Prompting Claude for solution with check_id: {check_id}")

    # Create a Bedrock Runtime client in the AWS Region of your choice.
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

    # Define the prompt and structure for the model.
    prompt = ("You are an expert at cybersecurity. You will be given a piece of vulnerable code, "
              "the vulnerability details and you should propose a solution with a response as a JSON object")
    
    structure = (
        "JSON with the following characteristics, ensure the JSON string adheres to proper syntax rules:\n"
        "    title: str\n"
        "    confidence_in_the_solution: from 0-100\n"
        "    proposed_code: str (be careful with escaped backslashes)\n"
        "    reason: str\n"
    )
    
    vulnerability = (
        f"\n<vulnerabilityID>\n{check_id}\n</vulnerabilityID>\n"
        f"<vulnerabilityMessage>\n{message}\n</vulnerabilityMessage>\n"
        f"<vulnerabilityCode>\n{extracted_code}\n</vulnerabilityCode>\n"
    )

    # Format the request payload using the model's native structure.
    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": structure}],
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": vulnerability}],
            },
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "{"}],
            }
        ],
    }

    request = json.dumps(native_request)
    logging.debug(f"Constructed request payload for Claude: {request}")

    try:
        response = client.invoke_model(modelId=model_id, body=request)
        logging.info(f"Model invoked successfully for check_id: {check_id}")
    except (ClientError, Exception) as e:
        logging.error(f"ERROR: Unable to invoke model '{model_id}' for check_id {check_id}. Reason: {e}")
        sys.exit(1)

    try:
        # Decode the response body.
        model_response = json.loads(response["body"].read())
        response_text = model_response["content"][0]["text"]
        logging.debug(f"Received response text for check_id {check_id}: {response_text}")
    except Exception as e:
        logging.error(f"Error processing model response for check_id {check_id}: {e}")
        return {}

    # Construct JSON object from response text
    json_string = '{' + response_text
    try:
        json_object = json.loads(json_string)
        logging.info(f"Successfully parsed JSON response for check_id: {check_id}")
        return json_object
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON for check_id {check_id}: {e}")
        return {}

def pretty_print_json_to_file(json_object, output_file):
    """
    Pretty print the JSON object to a file.
    """
    try:
        logging.info(f"Writing output to file: {output_file}")
        with open(output_file, 'w') as f:
            json.dump(json_object, f, indent=4)
        logging.info(f"Successfully wrote output to {output_file}")
    except Exception as e:
        logging.error(f"Error writing JSON to file '{output_file}': {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("Usage: python ai_enhance_results.py <path_to_semgrep_results_json>")
        sys.exit(1)

    input_file_path = sys.argv[1]
    output_file = "enhanced_results.json"
    code_root = "."

    logging.info(f"Starting processing of Semgrep results from: {input_file_path}")
    
    try:
        semgrep_results = load_json_file(input_file_path)
    except Exception as e:
        logging.error(f"Failed to load Semgrep results: {e}")
        sys.exit(1)
    
    results = semgrep_results.get('results', [])
    logging.info(f"Found {len(results)} results in the Semgrep JSON file.")

    enhanced_results = []

    for idx, result in enumerate(results, start=1):
        check_id = result.get('check_id', 'N/A')
        logging.info(f"Processing result {idx}/{len(results)} with check_id: {check_id}")
        
        file_path = os.path.join(code_root, result['path'])
        start_line = result['start']['line']
        end_line = result['end']['line']
        
        extracted_code = extract_lines_from_code(file_path, start_line, end_line)
        recommendation = prompt_claude_proposed_solution(check_id, result['extra']['message'], extracted_code)
        
        enhanced_results.append(recommendation)
        logging.debug(f"Recommendation for check_id {check_id}: {recommendation}")

    output_data = {"recommendations": enhanced_results}
    pretty_print_json_to_file(output_data, output_file)
    
    logging.info("Processing completed successfully.")