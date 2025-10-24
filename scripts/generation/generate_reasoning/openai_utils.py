"""
OpenAI API Utility Functions
Handles all interactions with OpenAI API
Reusable across different question generation topics
"""

import json
import time
from openai import OpenAI


def create_openai_client(api_key):
    """
    Create OpenAI client
    
    Args:
        api_key (str): OpenAI API key
    
    Returns:
        OpenAI: Client instance or None if failed
    """
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        print(f"❌ Error creating OpenAI client: {str(e)}")
        return None


def generate_questions_openai(client, prompt, model="gpt-4o", temperature=0.9, max_tokens=8192, max_retries=3):
    """
    Generate questions using OpenAI API with retry logic
    
    Args:
        client: OpenAI client instance
        prompt (str): The prompt to send
        model (str): Model name (e.g., "gpt-4o")
        temperature (float): Creativity level (0-2)
        max_tokens (int): Maximum output tokens
        max_retries (int): Maximum retry attempts
    
    Returns:
        dict: {
            "success": bool,
            "questions": list or None,
            "raw_text": str or None,
            "tokens_input": int,
            "tokens_output": int,
            "time_taken": float,
            "error": str or None
        }
    """
    
    result = {
        "success": False,
        "questions": None,
        "raw_text": None,
        "tokens_input": 0,
        "tokens_output": 0,
        "time_taken": 0,
        "error": None
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                print(f"   🔄 Retry {attempt}/{max_retries}...")
                time.sleep(3 * attempt)  # Exponential backoff
            
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert puzzle creator for competitive exams. Generate high-quality, unique reasoning puzzles. Output ONLY valid JSON array with no additional text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.95,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            end_time = time.time()
            result["time_taken"] = end_time - start_time
            
            # Check response
            if not response.choices:
                result["error"] = "No choices in response"
                print(f"   ⚠️  {result['error']}")
                if attempt < max_retries:
                    continue
                else:
                    return result
            
            choice = response.choices[0]
            finish_reason = choice.finish_reason
            
            # Get usage stats
            usage = response.usage
            result["tokens_input"] = usage.prompt_tokens
            result["tokens_output"] = usage.completion_tokens
            
            print(f"   📊 Tokens: {usage.prompt_tokens} in, {usage.completion_tokens} out | Time: {result['time_taken']:.1f}s")
            
            # Handle different finish reasons
            if finish_reason == "stop":  # Normal completion
                raw_text = choice.message.content.strip()
                result["raw_text"] = raw_text
                
                # Parse JSON
                try:
                    parsed_data = json.loads(raw_text)
                    
                    # Handle different JSON structures
                    if isinstance(parsed_data, list):
                        # Direct array of questions
                        result["questions"] = parsed_data
                    
                    elif isinstance(parsed_data, dict):
                        # Look for common wrapper keys
                        found = False
                        for key in ["questions", "data", "items", "results", "puzzles"]:
                            if key in parsed_data and isinstance(parsed_data[key], list):
                                result["questions"] = parsed_data[key]
                                found = True
                                break
                        
                        if not found:
                            # Maybe it's a single question wrapped in dict
                            if "question_id" in parsed_data:
                                result["questions"] = [parsed_data]
                                found = True
                        
                        if not found:
                            result["error"] = "JSON structure doesn't contain questions array"
                            print(f"   ⚠️  {result['error']}")
                            print(f"   Available keys: {list(parsed_data.keys())}")
                            if attempt < max_retries:
                                continue
                            else:
                                return result
                    
                    else:
                        result["error"] = f"Unexpected JSON type: {type(parsed_data).__name__}"
                        print(f"   ⚠️  {result['error']}")
                        if attempt < max_retries:
                            continue
                        else:
                            return result
                    
                    # Success!
                    result["success"] = True
                    print(f"   ✅ Successfully parsed {len(result['questions'])} questions")
                    return result
                
                except json.JSONDecodeError as e:
                    result["error"] = f"JSON parse error: {str(e)}"
                    print(f"   ⚠️  {result['error']}")
                    print(f"   Raw text preview: {raw_text[:300]}...")
                    if attempt < max_retries:
                        continue
                    else:
                        return result
            
            elif finish_reason == "length":  # Hit max tokens
                result["error"] = "Response exceeded max_tokens limit"
                print(f"   ⚠️  {result['error']}")
                try:
                    raw_text = choice.message.content
                    result["raw_text"] = raw_text
                    print(f"   ℹ️  Retrieved partial text ({len(raw_text)} chars)")
                except:
                    pass
                if attempt < max_retries:
                    continue
                else:
                    return result
            
            elif finish_reason == "content_filter":  # Content filtered
                result["error"] = "Content blocked by safety filter"
                print(f"   ❌ {result['error']}")
                return result  # Don't retry for content filter
            
            else:  # Unknown finish reason
                result["error"] = f"Unknown finish_reason: {finish_reason}"
                print(f"   ⚠️  {result['error']}")
                if attempt < max_retries:
                    continue
                else:
                    return result
        
        except Exception as e:
            error_str = str(e).lower()
            
            # Handle specific API errors
            if "rate" in error_str or "429" in error_str:
                result["error"] = f"Rate limit exceeded (attempt {attempt}/{max_retries})"
                print(f"   ⚠️  {result['error']}")
                if attempt < max_retries:
                    wait_time = 10 * attempt  # Longer wait for rate limits
                    print(f"   ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    return result
            
            elif "overloaded" in error_str or "503" in error_str:
                result["error"] = f"API overloaded (attempt {attempt}/{max_retries})"
                print(f"   ⚠️  {result['error']}")
                if attempt < max_retries:
                    wait_time = 5 * attempt
                    print(f"   ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    return result
            
            elif "authentication" in error_str or "401" in error_str:
                result["error"] = "Authentication failed - check API key"
                print(f"   ❌ {result['error']}")
                return result  # Don't retry for auth errors
            
            elif "invalid" in error_str and "model" in error_str:
                result["error"] = f"Invalid model: {model}"
                print(f"   ❌ {result['error']}")
                return result  # Don't retry for invalid model
            
            else:
                result["error"] = f"API error: {str(e)}"
                print(f"   ⚠️  {result['error']}")
                if attempt < max_retries:
                    continue
                else:
                    return result
    
    # All retries exhausted
    if not result["error"]:
        result["error"] = "Max retries exhausted"
    
    return result


def test_openai_connection(client, model="gpt-4o"):
    """
    Test OpenAI API connection with a simple request
    
    Args:
        client: OpenAI client instance
        model (str): Model name to test
    
    Returns:
        dict: {"success": bool, "error": str or None}
    """
    
    print("🔍 Testing OpenAI API connection...")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Reply with just 'OK' if you can read this."}
            ],
            max_tokens=10,
            temperature=0
        )
        
        if response.choices and response.choices[0].message.content:
            print("✅ Connection successful!")
            return {"success": True, "error": None}
        else:
            error = "Received empty response"
            print(f"❌ {error}")
            return {"success": False, "error": error}
    
    except Exception as e:
        error = str(e)
        print(f"❌ Connection failed: {error}")
        return {"success": False, "error": error}


# Quick test
if __name__ == "__main__":
    print("✅ OpenAI Utils module loaded successfully!")
    print("\nThis module provides:")
    print("  • create_openai_client() - Initialize OpenAI client")
    print("  • generate_questions_openai() - Generate questions with retry logic")
    print("  • test_openai_connection() - Test API connectivity")
