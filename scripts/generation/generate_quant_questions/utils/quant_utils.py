"""
Utility functions for Quantitative Aptitude Question Generation
Handles API calls, validation, file operations, and helper functions
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================================================
# API INTERACTION
# ============================================================================

def generate_with_openai(
    prompt: str,
    model: str = "gpt-4o",
    max_tokens: int = 4000,
    temperature: float = 0.7,
    response_format: Optional[str] = "json_object"
) -> Dict[str, Any]:
    """
    Wrapper for OpenAI API calls with error handling
    
    Args:
        prompt: The prompt to send to OpenAI
        model: Model to use (default: gpt-4o)
        max_tokens: Maximum tokens in response
        temperature: Creativity parameter (0.0 - 1.0)
        response_format: "json_object" for JSON mode, None for text
    
    Returns:
        {
            "success": bool,
            "data": dict/list (if success),
            "error": str (if failure),
            "tokens": {"prompt": int, "completion": int, "total": int},
            "cost": float
        }
    """
    try:
        print(f"🔄 Calling OpenAI API ({model})...")
        
        # Prepare API call parameters
        api_params = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert in creating high-quality quantitative aptitude questions for competitive exams like RBI Grade B. Generate questions with accurate calculations, realistic scenarios, and clear explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Add JSON mode if specified
        if response_format == "json_object":
            api_params["response_format"] = {"type": "json_object"}
        
        # Make API call
        response = client.chat.completions.create(**api_params)
        
        # Extract response content
        content = response.choices[0].message.content
        
        # Parse JSON if expected
        if response_format == "json_object":
            data = json.loads(content)
        else:
            data = content
        
        # Extract token usage
        tokens = {
            "prompt": response.usage.prompt_tokens,
            "completion": response.usage.completion_tokens,
            "total": response.usage.total_tokens
        }
        
        # Calculate cost
        cost = calculate_cost(tokens["prompt"], tokens["completion"], model)
        
        print(f"✅ API call successful")
        print(f"   Tokens: {tokens['total']} (Prompt: {tokens['prompt']}, Completion: {tokens['completion']})")
        print(f"   Cost: ${cost:.4f}")
        
        return {
            "success": True,
            "data": data,
            "tokens": tokens,
            "cost": cost
        }
        
    except json.JSONDecodeError as e:
        error_msg = f"JSON parsing error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "raw_response": content if 'content' in locals() else None
        }
        
    except Exception as e:
        error_msg = f"API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_di_set(di_set: Dict[str, Any], expected_questions: int = 5) -> Dict[str, Any]:
    """
    Comprehensive validation for Data Interpretation sets
    
    Args:
        di_set: The DI set dictionary to validate
        expected_questions: Expected number of questions (default: 5)
    
    Returns:
        {
            "valid": bool,
            "errors": list,
            "warnings": list
        }
    """
    errors = []
    warnings = []
    
    # -------------------------------------------------------------------------
    # 1. STRUCTURE VALIDATION
    # -------------------------------------------------------------------------
    required_fields = ["di_set_id", "topic", "data_source", "questions"]
    for field in required_fields:
        if field not in di_set:
            errors.append(f"Missing required field: '{field}'")
    
    # -------------------------------------------------------------------------
    # 2. DI SET ID VALIDATION
    # -------------------------------------------------------------------------
    if "di_set_id" in di_set:
        set_id = di_set["di_set_id"]
        if not isinstance(set_id, str) or not set_id.strip():
            errors.append("di_set_id must be a non-empty string")
    
    # -------------------------------------------------------------------------
    # 3. DATA SOURCE VALIDATION
    # -------------------------------------------------------------------------
    if "data_source" in di_set:
        data_source = di_set["data_source"]
        
        if not isinstance(data_source, dict):
            errors.append("data_source must be a dictionary")
        else:
            # Check type field
            if "type" not in data_source:
                errors.append("data_source missing 'type' field")
            elif data_source["type"] not in ["table", "bar", "line", "pie", "caselet"]:
                errors.append(f"Invalid data_source type: {data_source['type']}")
            
            # Check title
            if "title" not in data_source:
                warnings.append("data_source missing 'title' field")
            
            # Type-specific validation
            ds_type = data_source.get("type")
            
            if ds_type == "table":
                if "data" not in data_source:
                    errors.append("Table data_source missing 'data' field")
                elif isinstance(data_source["data"], dict):
                    if "headers" not in data_source["data"]:
                        errors.append("Table data missing 'headers'")
                    if "rows" not in data_source["data"]:
                        errors.append("Table data missing 'rows'")
            
            elif ds_type in ["bar", "line"]:
                if "data" not in data_source:
                    errors.append(f"{ds_type.capitalize()} graph data_source missing 'data' field")
                elif isinstance(data_source["data"], dict):
                    if "labels" not in data_source["data"]:
                        errors.append(f"{ds_type.capitalize()} graph data missing 'labels'")
                    if "datasets" not in data_source["data"]:
                        errors.append(f"{ds_type.capitalize()} graph data missing 'datasets'")
            
            elif ds_type == "pie":
                if "data" not in data_source:
                    errors.append("Pie chart data_source missing 'data' field")
                elif isinstance(data_source["data"], dict):
                    if "labels" not in data_source["data"]:
                        errors.append("Pie chart data missing 'labels'")
                    if "values" not in data_source["data"]:
                        errors.append("Pie chart data missing 'values'")
            
            elif ds_type == "caselet":
                if "text" not in data_source:
                    errors.append("Caselet data_source missing 'text' field")
                elif not isinstance(data_source["text"], str) or not data_source["text"].strip():
                    errors.append("Caselet text must be a non-empty string")
    
    # -------------------------------------------------------------------------
    # 4. QUESTIONS ARRAY VALIDATION
    # -------------------------------------------------------------------------
    if "questions" not in di_set:
        errors.append("Missing 'questions' array")
    else:
        questions = di_set["questions"]
        
        if not isinstance(questions, list):
            errors.append("'questions' must be an array/list")
        else:
            # Check question count
            if len(questions) != expected_questions:
                errors.append(f"Expected {expected_questions} questions, got {len(questions)}")
            
            # Validate each question
            for idx, question in enumerate(questions, 1):
                q_errors = validate_question_in_set(question, idx, di_set.get("di_set_id", ""))
                errors.extend(q_errors)
    
    # -------------------------------------------------------------------------
    # 5. DIFFICULTY VALIDATION (if present)
    # -------------------------------------------------------------------------
    if "difficulty" in di_set:
        if di_set["difficulty"] not in ["Easy", "Medium", "Hard"]:
            warnings.append(f"Unusual difficulty value: {di_set['difficulty']}")
    
    # -------------------------------------------------------------------------
    # RETURN VALIDATION RESULT
    # -------------------------------------------------------------------------
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_question_in_set(question: Dict[str, Any], question_num: int, set_id: str) -> List[str]:
    """
    Validate a single question within a DI set
    
    Args:
        question: Question dictionary
        question_num: Question number (for error reporting)
        set_id: Parent DI set ID
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    prefix = f"Q{question_num}"
    
    # Required fields
    required_fields = ["question_id", "question", "options", "correct_answer", "explanation"]
    for field in required_fields:
        if field not in question:
            errors.append(f"{prefix}: Missing required field '{field}'")
    
    # Validate question_id format
    if "question_id" in question:
        expected_prefix = f"{set_id}_Q{question_num}"
        if not question["question_id"].startswith(set_id):
            errors.append(f"{prefix}: question_id should start with '{set_id}'")
    
    # Validate options
    if "options" in question:
        options = question["options"]
        
        if not isinstance(options, dict):
            errors.append(f"{prefix}: 'options' must be a dictionary")
        else:
            required_options = ["A", "B", "C", "D", "E"]
            for opt in required_options:
                if opt not in options:
                    errors.append(f"{prefix}: Missing option '{opt}'")
            
            # Check for extra options
            for opt in options.keys():
                if opt not in required_options:
                    errors.append(f"{prefix}: Unexpected option key '{opt}'")
            
            # Check option values are non-empty
            for opt, value in options.items():
                if not str(value).strip():
                    errors.append(f"{prefix}: Option '{opt}' has empty value")
    
    # Validate correct_answer
    if "correct_answer" in question:
        correct = question["correct_answer"]
        if correct not in ["A", "B", "C", "D", "E"]:
            errors.append(f"{prefix}: correct_answer must be one of A, B, C, D, E (got '{correct}')")
    
    # Validate explanation
    if "explanation" in question:
        if not isinstance(question["explanation"], str) or len(question["explanation"]) < 10:
            errors.append(f"{prefix}: Explanation seems too short or invalid")
    
    # Validate difficulty (if present)
    if "difficulty" in question:
        if question["difficulty"] not in ["Easy", "Medium", "Hard", "Easy-Medium", "Medium-Hard"]:
            errors.append(f"{prefix}: Unusual difficulty value '{question['difficulty']}'")
    
    return errors


def validate_arithmetic_question(question: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validation for individual arithmetic/miscellaneous questions
    
    Args:
        question: Question dictionary to validate
    
    Returns:
        {
            "valid": bool,
            "errors": list,
            "warnings": list
        }
    """
    errors = []
    warnings = []
    
    # Required fields
    required_fields = [
        "question_id", "question", "options", "correct_answer", 
        "explanation", "difficulty", "topic"
    ]
    
    for field in required_fields:
        if field not in question:
            errors.append(f"Missing required field: '{field}'")
    
    # Validate question_id
    if "question_id" in question:
        if not isinstance(question["question_id"], str) or not question["question_id"].strip():
            errors.append("question_id must be a non-empty string")
    
    # Validate question text
    if "question" in question:
        if not isinstance(question["question"], str) or len(question["question"]) < 10:
            errors.append("Question text seems too short or invalid")
    
    # Validate options
    if "options" in question:
        options = question["options"]
        
        if not isinstance(options, dict):
            errors.append("'options' must be a dictionary")
        else:
            required_options = ["A", "B", "C", "D", "E"]
            
            for opt in required_options:
                if opt not in options:
                    errors.append(f"Missing option '{opt}'")
            
            for opt in options.keys():
                if opt not in required_options:
                    errors.append(f"Unexpected option key '{opt}'")
            
            for opt, value in options.items():
                if not str(value).strip():
                    errors.append(f"Option '{opt}' has empty value")
    
    # Validate correct_answer
    if "correct_answer" in question:
        correct = question["correct_answer"]
        if correct not in ["A", "B", "C", "D", "E"]:
            errors.append(f"correct_answer must be one of A, B, C, D, E (got '{correct}')")
    
    # Validate explanation
    if "explanation" in question:
        if not isinstance(question["explanation"], str) or len(question["explanation"]) < 10:
            errors.append("Explanation seems too short or invalid")
    
    # Validate difficulty
    if "difficulty" in question:
        if question["difficulty"] not in ["Easy", "Medium", "Hard"]:
            warnings.append(f"Unusual difficulty value: {question['difficulty']}")
    
    # Validate topic
    if "topic" in question:
        if not isinstance(question["topic"], str) or not question["topic"].strip():
            warnings.append("Topic field is empty or invalid")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

# ============================================================================
# FILE OPERATIONS
# ============================================================================

def save_to_json(data: Any, filepath: str, indent: int = 2) -> bool:
    """
    Save data to JSON file with pretty printing
    
    Args:
        data: Data to save (dict, list, etc.)
        filepath: Path to save the file
        indent: JSON indentation level (default: 2)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(filepath)
        if directory:
            ensure_directory_exists(directory)
        
        # Save to JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        print(f"✅ Data saved to: {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving to {filepath}: {str(e)}")
        return False


def load_from_json(filepath: str) -> Optional[Any]:
    """
    Load data from JSON file
    
    Args:
        filepath: Path to the JSON file
    
    Returns:
        Loaded data (dict/list) or None if failed
    """
    try:
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Data loaded from: {filepath}")
        return data
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {filepath}: {str(e)}")
        return None
        
    except Exception as e:
        print(f"❌ Error loading {filepath}: {str(e)}")
        return None


def ensure_directory_exists(directory: str) -> bool:
    """
    Ensure a directory exists, create if it doesn't
    
    Args:
        directory: Directory path
    
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Created directory: {directory}")
        return True
    except Exception as e:
        print(f"❌ Error creating directory {directory}: {str(e)}")
        return False


def append_to_json(new_data: Any, filepath: str, indent: int = 2) -> bool:
    """
    Append data to existing JSON file (assumes file contains a list)
    
    Args:
        new_data: Data to append (can be single item or list)
        filepath: Path to the JSON file
        indent: JSON indentation level (default: 2)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load existing data
        existing_data = []
        if os.path.exists(filepath):
            existing_data = load_from_json(filepath)
            if existing_data is None:
                existing_data = []
            elif not isinstance(existing_data, list):
                print(f"❌ File {filepath} does not contain a list")
                return False
        
        # Append new data
        if isinstance(new_data, list):
            existing_data.extend(new_data)
        else:
            existing_data.append(new_data)
        
        # Save back
        return save_to_json(existing_data, filepath, indent)
        
    except Exception as e:
        print(f"❌ Error appending to {filepath}: {str(e)}")
        return False


# ============================================================================
# COST CALCULATION
# ============================================================================

def calculate_cost(prompt_tokens: int, completion_tokens: int, model: str = "gpt-4o") -> float:
    """
    Calculate approximate cost for OpenAI API usage
    
    Args:
        prompt_tokens: Number of tokens in prompt
        completion_tokens: Number of tokens in completion
        model: Model name
    
    Returns:
        float: Estimated cost in USD
    
    Note: Prices as of October 2024, may need updating
    """
    
    # Pricing per 1M tokens (as of October 2024)
    pricing = {
        "gpt-4o": {
            "prompt": 2.50,      # \$2.50 per 1M input tokens
            "completion": 10.00   # \$10.00 per 1M output tokens
        },
        "gpt-4o-mini": {
            "prompt": 0.150,     # \$0.15 per 1M input tokens
            "completion": 0.600   # \$0.60 per 1M output tokens
        },
        "gpt-4": {
            "prompt": 30.00,     # \$30.00 per 1M input tokens
            "completion": 60.00   # \$60.00 per 1M output tokens
        },
        "gpt-4-turbo": {
            "prompt": 10.00,     # \$10.00 per 1M input tokens
            "completion": 30.00   # \$30.00 per 1M output tokens
        },
        "gpt-3.5-turbo": {
            "prompt": 0.50,      # \$0.50 per 1M input tokens
            "completion": 1.50    # \$1.50 per 1M output tokens
        }
    }
    
    # Get pricing for model (default to gpt-4o)
    model_pricing = pricing.get(model, pricing["gpt-4o"])
    
    # Calculate cost
    prompt_cost = (prompt_tokens / 1_000_000) * model_pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * model_pricing["completion"]
    
    total_cost = prompt_cost + completion_cost
    
    return total_cost


# ============================================================================
# DIFFICULTY MANAGEMENT
# ============================================================================

def get_difficulty_for_set(set_num: int, total_sets: int, distribution: Optional[List[str]] = None) -> str:
    """
    Determine difficulty level for a DI set based on its number
    
    Args:
        set_num: Current set number (1-indexed)
        total_sets: Total number of sets
        distribution: Optional custom distribution (e.g., ["Easy", "Medium", "Medium", "Hard", "Hard"])
    
    Returns:
        str: Difficulty level ("Easy", "Medium", or "Hard")
    
    Examples:
        For 5 sets: Easy, Medium, Medium, Hard, Hard (1E, 2M, 2H)
        For 4 sets: Easy, Medium, Hard, Hard (1E, 1M, 2H)
    """
    
    # If custom distribution provided, use it
    if distribution:
        if set_num > len(distribution):
            return "Medium"  # Default fallback
        return distribution[set_num - 1]
    
    # Default distributions based on total_sets
    default_distributions = {
        4: ["Easy", "Medium", "Hard", "Hard"],           # 1E, 1M, 2H
        5: ["Easy", "Medium", "Medium", "Hard", "Hard"], # 1E, 2M, 2H
        6: ["Easy", "Easy", "Medium", "Medium", "Hard", "Hard"], # 2E, 2M, 2H
    }
    
    if total_sets in default_distributions:
        return default_distributions[total_sets][set_num - 1]
    
    # Generic distribution for other totals
    # First 20% = Easy, Middle 40% = Medium, Last 40% = Hard
    position = set_num / total_sets
    
    if position <= 0.2:
        return "Easy"
    elif position <= 0.6:
        return "Medium"
    else:
        return "Hard"


def get_difficulty_distribution(total_questions: int, easy_pct: float = 0.2, 
                                medium_pct: float = 0.4, hard_pct: float = 0.4) -> Dict[str, int]:
    """
    Calculate difficulty distribution for a given number of questions
    
    Args:
        total_questions: Total number of questions
        easy_pct: Percentage of easy questions (default: 0.2 = 20%)
        medium_pct: Percentage of medium questions (default: 0.4 = 40%)
        hard_pct: Percentage of hard questions (default: 0.4 = 40%)
    
    Returns:
        dict: {"Easy": count, "Medium": count, "Hard": count}
    
    Example:
        get_difficulty_distribution(15) → {"Easy": 3, "Medium": 6, "Hard": 6}
    """
    
    easy_count = int(total_questions * easy_pct)
    medium_count = int(total_questions * medium_pct)
    hard_count = total_questions - easy_count - medium_count  # Remaining goes to Hard
    
    return {
        "Easy": easy_count,
        "Medium": medium_count,
        "Hard": hard_count
    }


# ============================================================================
# LOGGING & PROGRESS
# ============================================================================

def log_generation_progress(current: int, total: int, item_type: str, 
                            topic: str = "", additional_info: str = ""):
    """
    Log progress during generation
    
    Args:
        current: Current item number
        total: Total items to generate
        item_type: Type of item (e.g., "Set", "Question", "Batch")
        topic: Optional topic name
        additional_info: Optional additional information
    """
    
    percentage = (current / total) * 100
    
    topic_str = f" ({topic})" if topic else ""
    info_str = f" - {additional_info}" if additional_info else ""
    
    print(f"\n{'='*70}")
    print(f"📊 Progress: {current}/{total} {item_type}s ({percentage:.1f}%){topic_str}{info_str}")
    print(f"{'='*70}")


def log_validation_results(validation_result: Dict[str, Any], item_name: str = "Item"):
    """
    Pretty print validation results
    
    Args:
        validation_result: Result from validate_di_set() or validate_arithmetic_question()
        item_name: Name of the item being validated (for logging)
    """
    
    print(f"\n🔍 Validation Results for {item_name}:")
    print(f"{'─'*50}")
    
    if validation_result["valid"]:
        print("✅ Status: VALID")
    else:
        print("❌ Status: INVALID")
    
    # Display errors
    errors = validation_result.get("errors", [])
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
    
    # Display warnings
    warnings = validation_result.get("warnings", [])
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
    
    if not errors and not warnings:
        print("   No issues found!")
    
    print(f"{'─'*50}\n")


def log_summary(total_generated: int, total_expected: int, failed_items: List[str], 
               total_cost: float, output_file: str):
    """
    Log final summary after generation
    
    Args:
        total_generated: Number of items successfully generated
        total_expected: Expected number of items
        failed_items: List of failed item identifiers
        total_cost: Total API cost
        output_file: Path to output file
    """
    
    print("\n" + "="*70)
    print("📊 GENERATION SUMMARY")
    print("="*70)
    
    print(f"\n✅ Successfully Generated: {total_generated}/{total_expected}")
    
    if failed_items:
        print(f"\n❌ Failed Items ({len(failed_items)}):")
        for item in failed_items:
            print(f"   • {item}")
    
    print(f"\n💰 Total Cost: ${total_cost:.4f}")
    
    if total_generated > 0:
        print(f"\n📁 Output File: {output_file}")
    
    print("\n" + "="*70 + "\n")


# ============================================================================
# ANSWER DISTRIBUTION CHECKER
# ============================================================================

def check_answer_distribution(questions: List[Dict[str, Any]], 
                              question_type: str = "individual") -> Dict[str, Any]:
    """
    Check the distribution of correct answers (A, B, C, D, E)
    
    Args:
        questions: List of questions (can be individual or from DI sets)
        question_type: "individual" or "di_set"
    
    Returns:
        {
            "total": int,
            "distribution": {"A": count, "B": count, ...},
            "percentages": {"A": pct, "B": pct, ...},
            "balanced": bool
        }
    """
    
    distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    
    # Extract answers based on question type
    if question_type == "di_set":
        # For DI sets, questions are nested
        for di_set in questions:
            for question in di_set.get("questions", []):
                answer = question.get("correct_answer", "")
                if answer in distribution:
                    distribution[answer] += 1
    else:
        # For individual questions
        for question in questions:
            answer = question.get("correct_answer", "")
            if answer in distribution:
                distribution[answer] += 1
    
    total = sum(distribution.values())
    
    if total == 0:
        return {
            "total": 0,
            "distribution": distribution,
            "percentages": {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0},
            "balanced": False
        }
    
    # Calculate percentages
    percentages = {
        option: (count / total) * 100 
        for option, count in distribution.items()
    }
    
    # Check if balanced (each option should be ~20%, allow ±5% tolerance)
    balanced = all(15 <= pct <= 25 for pct in percentages.values())
    
    return {
        "total": total,
        "distribution": distribution,
        "percentages": percentages,
        "balanced": balanced
    }


def print_answer_distribution(distribution_result: Dict[str, Any]):
    """
    Pretty print answer distribution results
    
    Args:
        distribution_result: Result from check_answer_distribution()
    """
    
    print("\n📊 Answer Distribution Analysis:")
    print(f"{'─'*50}")
    print(f"Total Questions: {distribution_result['total']}\n")
    
    print(f"{'Option':<10} {'Count':<10} {'Percentage':<15} {'Bar'}")
    print(f"{'─'*50}")
    
    for option in ["A", "B", "C", "D", "E"]:
        count = distribution_result['distribution'][option]
        pct = distribution_result['percentages'][option]
        bar = "█" * int(pct / 2)  # Scale bar to fit
        
        print(f"{option:<10} {count:<10} {pct:>5.1f}%{'':<8} {bar}")
    
    print(f"{'─'*50}")
    
    if distribution_result['balanced']:
        print("✅ Distribution is BALANCED (within 15-25% per option)")
    else:
        print("⚠️  Distribution is UNBALANCED (some options outside 15-25% range)")
    
    print(f"{'─'*50}\n")


# ============================================================================
# METADATA GENERATION
# ============================================================================

def generate_metadata(exam: str = "RBI Grade B Phase 1", 
                     model: str = "gpt-4o",
                     reviewed: bool = False,
                     additional_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate standard metadata for questions
    
    Args:
        exam: Exam name
        model: Model used for generation
        reviewed: Whether questions have been reviewed
        additional_fields: Optional additional metadata fields
    
    Returns:
        dict: Metadata dictionary
    """
    
    metadata = {
        "generated_by": model,
        "generation_date": datetime.now().strftime("%Y-%m-%d"),
        "generation_timestamp": datetime.now().isoformat(),
        "exam": exam,
        "reviewed": reviewed
    }
    
    # Add additional fields if provided
    if additional_fields:
        metadata.update(additional_fields)
    
    return metadata


# ============================================================================
# RETRY LOGIC FOR FAILED GENERATIONS
# ============================================================================

def retry_generation(generation_function, max_retries: int = 3, 
                    delay: int = 2, **kwargs) -> Optional[Any]:
    """
    Retry a generation function if it fails
    
    Args:
        generation_function: Function to retry
        max_retries: Maximum number of retry attempts
        delay: Delay in seconds between retries
        **kwargs: Arguments to pass to the generation function
    
    Returns:
        Result from generation_function or None if all retries fail
    """
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n🔄 Attempt {attempt}/{max_retries}...")
            result = generation_function(**kwargs)
            
            if result:
                print(f"✅ Success on attempt {attempt}")
                return result
            else:
                print(f"⚠️  Attempt {attempt} returned empty result")
                
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {str(e)}")
        
        # Wait before retrying (except on last attempt)
        if attempt < max_retries:
            print(f"⏳ Waiting {delay} seconds before retry...")
            time.sleep(delay)
    
    print(f"❌ All {max_retries} attempts failed")
    return None


# ============================================================================
# DATA CLEANING & FORMATTING
# ============================================================================

def clean_json_string(json_string: str) -> str:
    """
    Clean JSON string from common formatting issues
    
    Args:
        json_string: Raw JSON string
    
    Returns:
        Cleaned JSON string
    """
    
    # Remove markdown code blocks if present
    json_string = json_string.strip()
    if json_string.startswith("```json"):
        json_string = json_string[7:]
    if json_string.startswith("```"):
        json_string = json_string[3:]
    if json_string.endswith("```"):
        json_string = json_string[:-3]
    
    # Strip whitespace
    json_string = json_string.strip()
    
    return json_string


def standardize_difficulty(difficulty: str) -> str:
    """
    Standardize difficulty strings to proper format
    
    Args:
        difficulty: Difficulty string (may be lowercase, mixed case, etc.)
    
    Returns:
        Standardized difficulty string
    """
    
    difficulty = difficulty.strip().lower()
    
    # Map variations to standard format
    difficulty_map = {
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
        "easy-medium": "Easy-Medium",
        "medium-hard": "Medium-Hard",
        "moderate": "Medium",
        "difficult": "Hard",
        "simple": "Easy"
    }
    
    return difficulty_map.get(difficulty, "Medium")  # Default to Medium


def extract_numeric_value(text: str) -> Optional[float]:
    """
    Extract numeric value from text (useful for parsing options)
    
    Args:
        text: Text that may contain a number
    
    Returns:
        float: Extracted number or None if not found
    """
    
    import re
    
    # Remove common text patterns
    text = text.replace("Rs.", "").replace("₹", "").replace(",", "")
    text = text.replace("%", "").strip()
    
    # Try to extract number
    match = re.search(r'-?\d+\.?\d*', text)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    
    return None


# ============================================================================
# BATCH PROCESSING UTILITIES
# ============================================================================

def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    Split items into batches
    
    Args:
        items: List of items to batch
        batch_size: Size of each batch
    
    Returns:
        List of batches
    """
    
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    
    return batches


def merge_json_files(file_paths: List[str], output_path: str, 
                    structure_type: str = "list") -> bool:
    """
    Merge multiple JSON files into one
    
    Args:
        file_paths: List of JSON file paths to merge
        output_path: Path for merged output file
        structure_type: "list" (merge arrays) or "dict" (merge objects)
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    try:
        merged_data = [] if structure_type == "list" else {}
        
        for filepath in file_paths:
            if not os.path.exists(filepath):
                print(f"⚠️  Skipping missing file: {filepath}")
                continue
            
            data = load_from_json(filepath)
            if data is None:
                print(f"⚠️  Skipping invalid file: {filepath}")
                continue
            
            if structure_type == "list":
                if isinstance(data, list):
                    merged_data.extend(data)
                else:
                    merged_data.append(data)
            else:  # dict
                if isinstance(data, dict):
                    merged_data.update(data)
                else:
                    print(f"⚠️  File {filepath} is not a dictionary, skipping")
        
        # Save merged data
        success = save_to_json(merged_data, output_path)
        
        if success:
            count = len(merged_data) if structure_type == "list" else len(merged_data.keys())
            print(f"✅ Merged {len(file_paths)} files into {output_path} ({count} items)")
        
        return success
        
    except Exception as e:
        print(f"❌ Error merging files: {str(e)}")
        return False


# ============================================================================
# QUESTION ID GENERATION
# ============================================================================

def generate_question_id(topic: str, question_num: int, 
                        prefix: str = "ARITH", total_digits: int = 3) -> str:
    """
    Generate a standardized question ID
    
    Args:
        topic: Topic name (e.g., "PERCENTAGE", "PROFIT_LOSS")
        question_num: Question number (1-indexed)
        prefix: Prefix for the ID (default: "ARITH")
        total_digits: Total digits for question number (default: 3)
    
    Returns:
        str: Question ID (e.g., "ARITH_PERCENTAGE_001")
    """
    
    # Clean topic name
    topic_clean = topic.upper().replace(" ", "_").replace("&", "AND")
    
    # Format question number with leading zeros
    q_num_str = str(question_num).zfill(total_digits)
    
    return f"{prefix}_{topic_clean}_{q_num_str}"


def generate_di_set_id(di_type: str, set_num: int, total_digits: int = 3) -> str:
    """
    Generate a standardized DI set ID
    
    Args:
        di_type: Type of DI (e.g., "TABLE", "BAR", "LINE", "PIE", "CASELET")
        set_num: Set number (1-indexed)
        total_digits: Total digits for set number (default: 3)
    
    Returns:
        str: DI set ID (e.g., "DI_TABLE_001")
    """
    
    # Clean DI type name
    di_type_clean = di_type.upper().replace(" ", "_")
    
    # Format set number with leading zeros
    set_num_str = str(set_num).zfill(total_digits)
    
    return f"DI_{di_type_clean}_{set_num_str}"


# ============================================================================
# STATISTICS & REPORTING
# ============================================================================

def generate_statistics_report(questions: List[Dict[str, Any]], 
                               question_type: str = "individual") -> Dict[str, Any]:
    """
    Generate comprehensive statistics for generated questions
    
    Args:
        questions: List of questions or DI sets
        question_type: "individual" or "di_set"
    
    Returns:
        dict: Statistics report
    """
    
    stats = {
        "total_items": len(questions),
        "total_questions": 0,
        "difficulty_distribution": {"Easy": 0, "Medium": 0, "Hard": 0},
        "topics": {},
        "answer_distribution": {},
        "average_question_length": 0,
        "average_explanation_length": 0
    }
    
    total_q_length = 0
    total_exp_length = 0
    question_count = 0
    
    # Process based on question type
    if question_type == "di_set":
        # For DI sets
        for di_set in questions:
            di_topic = di_set.get("topic", "Unknown")
            
            # Count topic
            if di_topic not in stats["topics"]:
                stats["topics"][di_topic] = 0
            stats["topics"][di_topic] += 1
            
            # Process questions within set
            for question in di_set.get("questions", []):
                question_count += 1
                
                # Difficulty
                diff = question.get("difficulty", "Medium")
                if diff in stats["difficulty_distribution"]:
                    stats["difficulty_distribution"][diff] += 1
                
                # Answer distribution
                answer = question.get("correct_answer", "")
                if answer:
                    if answer not in stats["answer_distribution"]:
                        stats["answer_distribution"][answer] = 0
                    stats["answer_distribution"][answer] += 1
                
                # Lengths
                q_text = question.get("question", "")
                exp_text = question.get("explanation", "")
                total_q_length += len(q_text)
                total_exp_length += len(exp_text)
    
    else:
        # For individual questions
        question_count = len(questions)
        
        for question in questions:
            # Topic
            topic = question.get("topic", "Unknown")
            if topic not in stats["topics"]:
                stats["topics"][topic] = 0
            stats["topics"][topic] += 1
            
            # Difficulty
            diff = question.get("difficulty", "Medium")
            if diff in stats["difficulty_distribution"]:
                stats["difficulty_distribution"][diff] += 1
            
            # Answer
            answer = question.get("correct_answer", "")
            if answer:
                if answer not in stats["answer_distribution"]:
                    stats["answer_distribution"][answer] = 0
                stats["answer_distribution"][answer] += 1
            
            # Lengths
            q_text = question.get("question", "")
            exp_text = question.get("explanation", "")
            total_q_length += len(q_text)
            total_exp_length += len(exp_text)
    
    stats["total_questions"] = question_count
    
    # Calculate averages
    if question_count > 0:
        stats["average_question_length"] = round(total_q_length / question_count, 1)
        stats["average_explanation_length"] = round(total_exp_length / question_count, 1)
    
    return stats


def print_statistics_report(stats: Dict[str, Any]):
    """
    Pretty print statistics report
    
    Args:
        stats: Statistics dictionary from generate_statistics_report()
    """
    
    print("\n" + "="*70)
    print("📊 GENERATION STATISTICS REPORT")
    print("="*70)
    
    print(f"\n📝 Total Items: {stats['total_items']}")
    print(f"📝 Total Questions: {stats['total_questions']}")
    
    # Difficulty distribution
    print(f"\n🎯 Difficulty Distribution:")
    for diff, count in stats['difficulty_distribution'].items():
        pct = (count / stats['total_questions'] * 100) if stats['total_questions'] > 0 else 0
        print(f"   • {diff:<10}: {count:>3} ({pct:>5.1f}%)")
    
    # Topic distribution
    print(f"\n📚 Topic Distribution:")
    for topic, count in stats['topics'].items():
        print(f"   • {topic:<30}: {count:>3}")
    
    # Answer distribution
    print(f"\n✅ Answer Distribution:")
    for answer in ["A", "B", "C", "D", "E"]:
        count = stats['answer_distribution'].get(answer, 0)
        pct = (count / stats['total_questions'] * 100) if stats['total_questions'] > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"   • {answer}: {count:>3} ({pct:>5.1f}%) {bar}")
    
    # Average lengths
    print(f"\n📏 Average Lengths:")
    print(f"   • Question Text:   {stats['average_question_length']:.1f} characters")
    print(f"   • Explanation:     {stats['average_explanation_length']:.1f} characters")
    
    print("\n" + "="*70 + "\n")


# ============================================================================
# TIMING UTILITIES
# ============================================================================

class Timer:
    """Simple timer context manager for timing operations"""
    
    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
        self.elapsed = None
    
    def __enter__(self):
        self.start_time = time.time()
        print(f"⏱️  Starting: {self.description}...")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
        
        # Format elapsed time
        if self.elapsed < 60:
            time_str = f"{self.elapsed:.2f} seconds"
        elif self.elapsed < 3600:
            minutes = int(self.elapsed // 60)
            seconds = self.elapsed % 60
            time_str = f"{minutes}m {seconds:.1f}s"
        else:
            hours = int(self.elapsed // 3600)
            minutes = int((self.elapsed % 3600) // 60)
            time_str = f"{hours}h {minutes}m"
        
        print(f"✅ Completed: {self.description} (took {time_str})")
        
        return False  # Don't suppress exceptions


def format_time_elapsed(seconds: float) -> str:
    """
    Format elapsed time in human-readable format
    
    Args:
        seconds: Time in seconds
    
    Returns:
        str: Formatted time string
    """
    
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_options_uniqueness(options: Dict[str, Any]) -> bool:
    """
    Check if all options are unique (no duplicate values)
    
    Args:
        options: Dictionary of options (A, B, C, D, E)
    
    Returns:
        bool: True if all options are unique
    """
    
    values = [str(v).strip().lower() for v in options.values()]
    return len(values) == len(set(values))


def validate_correct_answer_in_options(correct_answer: str, options: Dict[str, Any]) -> bool:
    """
    Verify that the correct answer key exists in options
    
    Args:
        correct_answer: The correct answer key (A, B, C, D, or E)
        options: Dictionary of options
    
    Returns:
        bool: True if correct_answer is a valid option key
    """
    
    return correct_answer in options


def check_for_obvious_patterns(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check for obvious patterns in questions that might indicate issues
    
    Args:
        questions: List of questions to check
    
    Returns:
        dict: Analysis results with any detected patterns
    """
    
    patterns = {
        "consecutive_same_answers": [],
        "repeated_question_text": [],
        "very_short_explanations": [],
        "missing_numeric_values": []
    }
    
    # Check for consecutive same answers
    for i in range(len(questions) - 2):
        answers = [
            questions[i].get("correct_answer", ""),
            questions[i+1].get("correct_answer", ""),
            questions[i+2].get("correct_answer", "")
        ]
        
        if len(set(answers)) == 1 and answers[0]:
            patterns["consecutive_same_answers"].append({
                "positions": [i+1, i+2, i+3],
                "answer": answers[0]
            })
    
    # Check for repeated question text
    question_texts = {}
    for idx, q in enumerate(questions, 1):
        text = q.get("question", "").strip().lower()
        if text:
            if text in question_texts:
                patterns["repeated_question_text"].append({
                    "positions": [question_texts[text], idx],
                    "text_preview": text[:50] + "..."
                })
            else:
                question_texts[text] = idx
    
    # Check for very short explanations
    for idx, q in enumerate(questions, 1):
        explanation = q.get("explanation", "")
        if len(explanation) < 30:
            patterns["very_short_explanations"].append({
                "position": idx,
                "length": len(explanation)
            })
    
    # Check for missing numeric values in options
    for idx, q in enumerate(questions, 1):
        options = q.get("options", {})
        has_numeric = False
        
        for opt_value in options.values():
            if extract_numeric_value(str(opt_value)) is not None:
                has_numeric = True
                break
        
        if not has_numeric and options:
            patterns["missing_numeric_values"].append({
                "position": idx,
                "question_id": q.get("question_id", "unknown")
            })
    
    return patterns


# ============================================================================
# EXPORT UTILITIES
# ============================================================================

def export_to_csv(questions: List[Dict[str, Any]], output_path: str, 
                 question_type: str = "individual") -> bool:
    """
    Export questions to CSV format
    
    Args:
        questions: List of questions or DI sets
        output_path: Path for CSV output
        question_type: "individual" or "di_set"
    
    Returns:
        bool: True if successful
    """
    
    try:
        import csv
        
        # Prepare rows
        rows = []
        
        if question_type == "di_set":
            # For DI sets
            for di_set in questions:
                set_id = di_set.get("di_set_id", "")
                topic = di_set.get("topic", "")
                
                for q in di_set.get("questions", []):
                    rows.append({
                        "set_id": set_id,
                        "question_id": q.get("question_id", ""),
                        "topic": topic,
                        "difficulty": q.get("difficulty", ""),
                        "question": q.get("question", ""),
                        "option_a": q.get("options", {}).get("A", ""),
                        "option_b": q.get("options", {}).get("B", ""),
                        "option_c": q.get("options", {}).get("C", ""),
                        "option_d": q.get("options", {}).get("D", ""),
                        "option_e": q.get("options", {}).get("E", ""),
                        "correct_answer": q.get("correct_answer", ""),
                        "explanation": q.get("explanation", "")
                    })
        else:
            # For individual questions
            for q in questions:
                rows.append({
                    "question_id": q.get("question_id", ""),
                    "topic": q.get("topic", ""),
                    "difficulty": q.get("difficulty", ""),
                    "question": q.get("question", ""),
                    "option_a": q.get("options", {}).get("A", ""),
                    "option_b": q.get("options", {}).get("B", ""),
                    "option_c": q.get("options", {}).get("C", ""),
                    "option_d": q.get("options", {}).get("D", ""),
                    "option_e": q.get("options", {}).get("E", ""),
                    "correct_answer": q.get("correct_answer", ""),
                    "explanation": q.get("explanation", "")
                })
        
        # Write CSV
        if rows:
            fieldnames = rows[0].keys()
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"✅ Exported {len(rows)} questions to CSV: {output_path}")
            return True
        else:
            print("⚠️  No questions to export")
            return False
            
    except Exception as e:
        print(f"❌ Error exporting to CSV: {str(e)}")
        return False


def export_to_markdown(questions: List[Dict[str, Any]], output_path: str,
                      question_type: str = "individual", 
                      include_answers: bool = True) -> bool:
    """
    Export questions to Markdown format
    
    Args:
        questions: List of questions or DI sets
        output_path: Path for Markdown output
        question_type: "individual" or "di_set"
        include_answers: Whether to include answers and explanations
    
    Returns:
        bool: True if successful
    """
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Quantitative Aptitude Questions\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            if question_type == "di_set":
                # For DI sets
                for set_idx, di_set in enumerate(questions, 1):
                    f.write(f"## Set {set_idx}: {di_set.get('topic', 'Data Interpretation')}\n\n")
                    f.write(f"**Set ID:** {di_set.get('di_set_id', '')}\n\n")
                    
                    # Data source
                    data_source = di_set.get('data_source', {})
                    if data_source:
                        f.write(f"### {data_source.get('title', 'Data')}\n\n")
                        
                        # Format based on type
                        ds_type = data_source.get('type', '')
                        if ds_type == 'table' and 'data' in data_source:
                            table_data = data_source['data']
                            if 'headers' in table_data and 'rows' in table_data:
                                # Write table
                                headers = table_data['headers']
                                f.write("| " + " | ".join(headers) + " |\n")
                                f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
                                
                                for row in table_data['rows']:
                                    f.write("| " + " | ".join(str(cell) for cell in row) + " |\n")
                                f.write("\n")
                        
                        elif ds_type == 'caselet' and 'text' in data_source:
                            f.write(f"{data_source['text']}\n\n")
                    
                    # Questions
                    for q_idx, q in enumerate(di_set.get('questions', []), 1):
                        f.write(f"### Question {q_idx}\n\n")
                        f.write(f"**Difficulty:** {q.get('difficulty', 'Medium')}\n\n")
                        f.write(f"{q.get('question', '')}\n\n")
                        
                        # Options
                        options = q.get('options', {})
                        for opt in ['A', 'B', 'C', 'D', 'E']:
                            if opt in options:
                                f.write(f"**{opt}.** {options[opt]}\n\n")
                        
                        # Answer and explanation
                        if include_answers:
                            f.write(f"**Correct Answer:** {q.get('correct_answer', '')}\n\n")
                            f.write(f"**Explanation:**\n\n{q.get('explanation', '')}\n\n")
                        
                        f.write("---\n\n")
            
            else:
                # For individual questions
                for q_idx, q in enumerate(questions, 1):
                    f.write(f"## Question {q_idx}\n\n")
                    f.write(f"**Topic:** {q.get('topic', '')}\n\n")
                    f.write(f"**Difficulty:** {q.get('difficulty', 'Medium')}\n\n")
                    f.write(f"{q.get('question', '')}\n\n")
                    
                    # Options
                    options = q.get('options', {})
                    for opt in ['A', 'B', 'C', 'D', 'E']:
                        if opt in options:
                            f.write(f"**{opt}.** {options[opt]}\n\n")
                    
                    # Answer and explanation
                    if include_answers:
                        f.write(f"**Correct Answer:** {q.get('correct_answer', '')}\n\n")
                        f.write(f"**Explanation:**\n\n{q.get('explanation', '')}\n\n")
                    
                    f.write("---\n\n")
        
        print(f"✅ Exported to Markdown: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error exporting to Markdown: {str(e)}")
        return False


# ============================================================================
# QUALITY CHECKS
# ============================================================================

def run_quality_checks(questions: List[Dict[str, Any]], 
                      question_type: str = "individual") -> Dict[str, Any]:
    """
    Run comprehensive quality checks on generated questions
    
    Args:
        questions: List of questions or DI sets
        question_type: "individual" or "di_set"
    
    Returns:
        dict: Quality check results
    """
    
    print("\n🔍 Running Quality Checks...")
    print("="*70)
    
    results = {
        "total_items": len(questions),
        "validation_passed": 0,
        "validation_failed": 0,
        "answer_distribution": {},
        "patterns": {},
        "issues": []
    }
    
    # Validate each item
    for idx, item in enumerate(questions, 1):
        if question_type == "di_set":
            validation = validate_di_set(item)
        else:
            validation = validate_arithmetic_question(item)
        
        if validation["valid"]:
            results["validation_passed"] += 1
        else:
            results["validation_failed"] += 1
            results["issues"].append({
                "item_index": idx,
                "errors": validation["errors"]
            })
    
    # Check answer distribution
    dist_result = check_answer_distribution(questions, question_type)
    results["answer_distribution"] = dist_result
    
    # Check for patterns
    if question_type == "individual":
        patterns = check_for_obvious_patterns(questions)
        results["patterns"] = patterns
    
    # Print summary
    print(f"\n✅ Validation Passed: {results['validation_passed']}/{results['total_items']}")
    print(f"❌ Validation Failed: {results['validation_failed']}/{results['total_items']}")
    
    if results["validation_failed"] > 0:
        print(f"\n⚠️  Issues found in {results['validation_failed']} items")
    
    print("\n" + "="*70)
    
    return results


# ============================================================================
# END OF UTILITY FUNCTIONS
# ============================================================================

if __name__ == "__main__":
    print("✅ quant_utils.py loaded successfully")
    print("📚 Available functions:")
    print("   - generate_with_openai()")
    print("   - parse_json_response()")
    print("   - validate_di_set()")
    print("   - validate_arithmetic_question()")
    print("   - save_to_json()")
    print("   - load_from_json()")
    print("   - calculate_cost()")
    print("   - check_answer_distribution()")
    print("   - generate_statistics_report()")
    print("   - export_to_csv()")
    print("   - export_to_markdown()")
    print("   - run_quality_checks()")
    print("   - Timer context manager")
    print("\n💡 Import this module in your scripts:")
    print("   from quant_utils import *")