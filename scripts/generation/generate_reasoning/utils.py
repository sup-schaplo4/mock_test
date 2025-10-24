"""
Generic Utility Functions
Reusable across all question generation topics
"""

import json
import os
from datetime import datetime


def calculate_batch_distribution(total_questions, batch_size, difficulty_weights):
    """
    Calculate how many questions of each difficulty per batch
    
    Args:
        total_questions (int): Total number of questions to generate
        batch_size (int): Questions per batch
        difficulty_weights (dict): Percentage distribution {"Easy": 20, "Medium": 40, "Hard": 40}
    
    Returns:
        list: List of dicts with distribution per batch
    """
    
    # Calculate total questions per difficulty
    total_easy = int(total_questions * difficulty_weights["Easy"] / 100)
    total_medium = int(total_questions * difficulty_weights["Medium"] / 100)
    total_hard = int(total_questions * difficulty_weights["Hard"] / 100)
    
    # Adjust for rounding errors
    total_calculated = total_easy + total_medium + total_hard
    if total_calculated < total_questions:
        total_hard += (total_questions - total_calculated)
    
    print(f"   Total Distribution: Easy={total_easy}, Medium={total_medium}, Hard={total_hard}")
    
    # Calculate number of batches
    num_batches = (total_questions + batch_size - 1) // batch_size
    
    # Distribute across batches
    batches = []
    remaining_easy = total_easy
    remaining_medium = total_medium
    remaining_hard = total_hard
    remaining_total = total_questions
    
    for batch_num in range(1, num_batches + 1):
        # Questions in this batch
        questions_in_batch = min(batch_size, remaining_total)
        
        # Proportional distribution
        batch_easy = min(remaining_easy, int(questions_in_batch * difficulty_weights["Easy"] / 100))
        batch_medium = min(remaining_medium, int(questions_in_batch * difficulty_weights["Medium"] / 100))
        batch_hard = questions_in_batch - batch_easy - batch_medium
        
        # Ensure we don't exceed remaining
        if batch_hard > remaining_hard:
            batch_hard = remaining_hard
            batch_medium = questions_in_batch - batch_easy - batch_hard
        
        batches.append({
            "batch_num": batch_num,
            "total": questions_in_batch,
            "Easy": batch_easy,
            "Medium": batch_medium,
            "Hard": batch_hard
        })
        
        remaining_easy -= batch_easy
        remaining_medium -= batch_medium
        remaining_hard -= batch_hard
        remaining_total -= questions_in_batch
    
    return batches


def validate_json_output(json_data, expected_count):
    """
    Validate generated JSON output
    
    Args:
        json_data (list): List of question dictionaries
        expected_count (int): Expected number of questions
    
    Returns:
        dict: {"valid": bool, "errors": list, "warnings": list}
    """
    
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check if it's a list
    if not isinstance(json_data, list):
        result["valid"] = False
        result["errors"].append("Output is not a JSON array")
        return result
    
    # Check count
    actual_count = len(json_data)
    if actual_count != expected_count:
        result["warnings"].append(f"Expected {expected_count} questions, got {actual_count}")
    
    # Validate each question
    required_fields = [
        "question_id", "question", "options", "correct_answer",
        "explanation", "difficulty", "topic", "reasoning_topic",
        "main_category", "subject", "exam", "metadata"
    ]
    
    for idx, q in enumerate(json_data):
        question_num = idx + 1
        
        # Check if it's a dict
        if not isinstance(q, dict):
            result["valid"] = False
            result["errors"].append(f"Question {question_num} is not a dictionary")
            continue
        
        # Check required fields
        for field in required_fields:
            if field not in q:
                result["valid"] = False
                result["errors"].append(f"Question {question_num} missing field: {field}")
        
        # Validate options
        if "options" in q:
            if not isinstance(q["options"], dict):
                result["valid"] = False
                result["errors"].append(f"Question {question_num} options is not a dictionary")
            else:
                required_options = ["A", "B", "C", "D", "E"]
                for opt in required_options:
                    if opt not in q["options"]:
                        result["valid"] = False
                        result["errors"].append(f"Question {question_num} missing option: {opt}")
        
        # Validate correct_answer
        if "correct_answer" in q:
            if q["correct_answer"] not in ["A", "B", "C", "D", "E"]:
                result["valid"] = False
                result["errors"].append(f"Question {question_num} has invalid correct_answer: {q['correct_answer']}")
        
        # Validate difficulty
        if "difficulty" in q:
            if q["difficulty"] not in ["Easy", "Medium", "Hard"]:
                result["warnings"].append(f"Question {question_num} has non-standard difficulty: {q['difficulty']}")
    
    return result


def save_to_json(data, filepath):
    """
    Save data to JSON file
    
    Args:
        data: Data to save (list or dict)
        filepath (str): Path to save file
    
    Returns:
        bool: Success status
    """
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save with pretty formatting
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    
    except Exception as e:
        print(f"❌ Error saving to {filepath}: {str(e)}")
        return False


def load_from_json(filepath):
    """
    Load data from JSON file
    
    Args:
        filepath (str): Path to JSON file
    
    Returns:
        tuple: (success: bool, data: list/dict/None)
    """
    
    try:
        if not os.path.exists(filepath):
            return False, None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return True, data
    
    except Exception as e:
        print(f"❌ Error loading from {filepath}: {str(e)}")
        return False, None


def log_error(error_message, log_filepath):
    """
    Log error message to file
    
    Args:
        error_message (str): Error message to log
        log_filepath (str): Path to log file
    """
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(log_filepath), exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {error_message}\n"
        
        with open(log_filepath, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    except Exception as e:
        print(f"❌ Error writing to log: {str(e)}")


def calculate_cost(input_tokens, output_tokens, input_cost_per_million, output_cost_per_million):
    """
    Calculate API cost
    
    Args:
        input_tokens (int): Number of input tokens
        output_tokens (int): Number of output tokens
        input_cost_per_million (float): Cost per million input tokens
        output_cost_per_million (float): Cost per million output tokens
    
    Returns:
        dict: {"input_cost": float, "output_cost": float, "total_cost": float}
    """
    
    input_cost = (input_tokens / 1_000_000) * input_cost_per_million
    output_cost = (output_tokens / 1_000_000) * output_cost_per_million
    total_cost = input_cost + output_cost
    
    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost
    }


def get_timestamp_filename(base_name, extension="json"):
    """
    Generate filename with timestamp
    
    Args:
        base_name (str): Base name for file
        extension (str): File extension (without dot)
    
    Returns:
        str: Filename with timestamp
    """
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"


# Quick test
if __name__ == "__main__":
    print("✅ Utils module loaded successfully!")
    
    # Test batch distribution
    batches = calculate_batch_distribution(30, 5, {"Easy": 20, "Medium": 40, "Hard": 40})
    print(f"\nBatch Distribution:")
    for batch in batches:
        print(f"   Batch {batch['batch_num']}: {batch}")
    
    # Test timestamp filename
    filename = get_timestamp_filename("linear_seating_questions")
    print(f"\nTimestamp Filename: {filename}")
