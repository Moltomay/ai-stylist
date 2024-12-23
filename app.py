# app.py
import os
from dotenv import load_dotenv
import requests
import json
import re
from flask import Flask, render_template, request

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Get API keys from environment variables
HUGGINGFACE_API_KEY = os.getenv('HUGGING_FACE_TOKEN')
SERPAPI_KEY = os.getenv('SERPAPI_KEY')

# Validate API keys
if not HUGGINGFACE_API_KEY:
    raise ValueError("Hugging Face API key is missing. Please check your .env file.")

if not SERPAPI_KEY:
    raise ValueError("Serpapi API key is missing. Please check your .env file.")

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

def search_product_link(query, gender):
    """
    Search for a product link using Serpapi, returning the first link found.
    
    Args:
        query (str): Product example from LLM recommendation
        gender (str): Gender for additional context
    
    Returns:
        dict: First product link details or None if no link found
    """
    # Use the exact product example as the search query
    full_query = query
    
    print(f"Searching Serpapi with query: {full_query}")
    
    # Construct search parameters 
    params = {
        'engine': 'google',
        'q': full_query,
        'api_key': SERPAPI_KEY,
        'num': 5  # Limit to first 5 results
    }
    
    try:
        response = requests.get('https://serpapi.com/search', params=params)
        
        print(f"Serpapi Response Status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            
            # Extract organic search results
            organic_results = results.get('organic_results', [])
            
            print(f"Number of search results: {len(organic_results)}")
            
            # Return the first valid link found
            for result in organic_results:
                link = result.get('link', '')
                title = result.get('title', '')
                
                # Basic link validation
                if link.startswith('http'):
                    product_details = {
                        'link': link,
                        'title': title,
                        'snippet': result.get('snippet', 'No description available')
                    }
                    
                    print("\n--- FOUND PRODUCT LINK ---")
                    print(json.dumps(product_details, indent=2))
                    
                    return product_details
            
            print("No valid product links found")
            return None
    
    except Exception as e:
        print(f"Error in Serpapi search: {e}")
        return None

def enhance_recommendation_with_links(recommendation, gender):
    """
    Enhance the LLM-generated recommendation with verified product links.
    
    Args:
        recommendation (dict): Original recommendation from LLM
        gender (str): Gender for search refinement
    
    Returns:
        dict: Recommendation with verified links and original description
    """
    if not recommendation:
        return None
    
    for category in ['hat', 'top', 'bottom', 'shoes']:
        if category in recommendation:
            item = recommendation[category]
            
            # Preserve original description
            original_description = item.get('description', '')
            
            # Use the specific example from the LLM recommendation
            search_query = item.get('example', '')
            
            print(f"Searching for {category} product link: {search_query}")
            
            # Try to find a precise product link
            product_link = search_product_link(search_query, gender)
            
            if product_link:
                # Update item with additional link details
                # Critically, keep the ORIGINAL description
                item['link'] = product_link['link']
                item['product_title'] = product_link['title']
                item['description'] = original_description  # Preserve original description
                
                print(f"{category.capitalize()} product link found:")
                print(json.dumps(item, indent=2))
            else:
                print(f"No product link found for {category}")
    
    return recommendation

def get_outfit_recommendation(preference, gender):
    prompt = f"""You are an elite personal stylist with expertise in fashion psychology, brand nuances, and precise style matching.

    COMPREHENSIVE STYLING GUIDELINES:
    1. Style Context Analysis:
    - Deeply analyze user's preference: '{preference}'
    - Consider gender-specific styling: '{gender}'
    - Interpret underlying style persona beyond surface-level description

    2. Recommendation Strategy:
    - Create a COHESIVE outfit that tells a style narrative
    - Balance trend awareness with individual expression
    - Consider body proportions, lifestyle, and personal aesthetic

    3. Detailed Item Requirements:
    For EACH item (hat, top, bottom, shoes):
    - Match EXACT style archetype
    - Provide hyper-specific product identification
    - Consider fabric technology, cut precision, and brand positioning
    - Ensure items create a harmonious, intentional ensemble

    4. Advanced Matching Criteria:
    - Preference Style Keywords: '{preference}'
    - Gender Styling Nuances: '{gender}'
    - Implicit Style Interpretation Layers:
      * Texture preferences
      * Color psychology
      * Silhouette comfort
      * Functional versatility

    5. Recommendation Depth:
    - Beyond visual appeal: consider comfort, movement, and personal empowerment
    - Select items that transcend mere clothing, representing a lifestyle

    Required Hyper-Specific JSON Format:
    {{
        "hat": {{
            "description": "Precise hat description with color and material",
            "brand": "Top-tier brand matching style archetype",
            "example": "DEFINITIVE product identifier with technological and design specifics, with product's color"
        }},
        "top": {{
            "description": "Precise top description with color, material, and cut",
            "brand": "Brand embodying style philosophy",
            "example": "CANONICAL product name capturing essence of personal style, with product's color"
        }},
        "bottom": {{
            "description": "Precise bottom description with color, material, and fit",
            "brand": "Brand resonating with style DNA",
            "example": "QUINTESSENTIAL product identifier with nuanced design language, with product's color"
        }},
        "shoes": {{
            "description": "Precise shoes description with color, material, and specific model",
            "brand": "Brand symbolizing movement and self-expression",
            "example": "BREAKTHROUGH product name representing style evolution, with product's color"
        }}
    }}

    CRITICAL: Transcend generic recommendations. Craft a style EXPERIENCE, not just an outfit."""

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 800,
            "temperature": 0.2,  # Reduced temperature for more consistent output
            "top_p": 0.9,
            "return_full_text": False
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        
        print("API Request Details:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        
        # Attempt to get the full response content
        full_response_text = response.text
        
        if response.status_code != 200:
            print(f"Error: API request failed with status code {response.status_code}")
            print(f"Response Text: {full_response_text}")
            return None

        # Try parsing the response
        try:
            result = response.json()
            print("Parsed JSON Response:")
            print(json.dumps(result, indent=2))
        except json.JSONDecodeError as json_err:
            print(f"JSON Decode Error: {json_err}")
            print(f"Response Text that failed to decode: {response.text}")
            return None

        # Extract generated text
        if isinstance(result, list) and len(result) > 0:
            generated_text = result[0].get('generated_text', '')
            print("Generated Text (Raw):")
            print(generated_text)

            # Multiple parsing attempts with detailed error handling
            parsing_attempts = [
                # Direct parsing
                lambda x: json.loads(x),
                
                # Regex extraction with more robust matching
                lambda x: json.loads(re.search(r'\{.*\}', x, re.DOTALL | re.MULTILINE).group(0)),
                
                # Cleaned parsing with multiple cleaning strategies
                lambda x: json.loads(re.sub(r'^[^\{]*', '', x.strip(), flags=re.MULTILINE)),
                lambda x: json.loads(x.replace('\n', '').replace('```json', '').replace('```', '').strip())
            ]

            for i, attempt in enumerate(parsing_attempts):
                try:
                    print(f"Parsing Attempt {i+1}:")
                    recommendation = attempt(generated_text)
                    
                    # Validate the recommendation structure
                    required_keys = ['hat', 'top', 'bottom', 'shoes']
                    sub_keys = ['description', 'brand', 'example']
                    
                    if all(key in recommendation for key in required_keys):
                        if all(all(sub_key in recommendation[key] for sub_key in sub_keys) for key in required_keys):
                            # Enhanced logging
                            print("Successful Recommendation Parsing:")
                            print(json.dumps(recommendation, indent=2))
                            
                            # Enhance with links
                            recommendation = enhance_recommendation_with_links(recommendation, gender)
                            
                            return recommendation
                    
                    print("Recommendation did not match the required structure")
                except Exception as parse_err:
                    print(f"Parsing Attempt {i+1} Failed: {parse_err}")
                    # Print the text that failed to parse
                    print(f"Failed Text: {generated_text}")

        print("No valid recommendation could be extracted")
        return None

    except requests.RequestException as req_err:
        print(f"Request Error: {req_err}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    recommendation = None
    preference = None
    gender = None
    
    if request.method == 'POST':
        preference = request.form.get('preference')
        gender = request.form.get('gender')
        
        if preference and gender:
            recommendation = get_outfit_recommendation(preference, gender)
    
    return render_template(
        'index.html', 
        recommendation=recommendation, 
        preference=preference, 
        gender=gender
    )

if __name__ == "__main__":
    app.run(debug=True)