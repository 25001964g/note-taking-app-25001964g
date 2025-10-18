# import libraries
import os
from openai import OpenAI

# Lazy load token and endpoint to avoid errors during module import
def get_llm_client():
    """Get OpenAI client with lazy loading of credentials"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is not set")
    endpoint = "https://models.github.ai/inference"
    return OpenAI(base_url=endpoint, api_key=token)

model = "openai/gpt-4.1-mini"

# A function to call an LLM model and return the response
def call_llm_model(model, messages, temperature=1.0, top_p=1.0):
    client = get_llm_client()
    response = client.chat.completions.create(  
        messages=messages,
        temperature=temperature, top_p=top_p, model=model)
    return response.choices[0].message.content

# A function to translate to target language
def translate(text, target_language):
    prompt = f"Translate the following text to {target_language}:\n\n{text}"
    messages = [{"role": "user", "content": prompt}]
    return call_llm_model(model, messages)

system_prompt = '''
Extract the user's notes into the following structured fields:
1. Title: A concise title of the notes less than 5 words
2. Notes: The notes based on user input written in full sentences.
3. Tags (A list): At most 3 Keywords or tags that categorize the content of the notes.
Output in JSON format without ```json. Output title and notes in the language: {lang}.
Example:
Input: "Badminton tmr 5pm @polyu".
Output:
{{
"Title": "Badminton at PolyU",
"Notes": "Remember to play badminton at 5pm tomorrow at PolyU.",
"Tags": ["badminton", "sports"]
}}
'''
# A function to extract notes from user input
def extract_notes(text, lang="English"):
    prompt = f"Extract the user's notes into structured fields in {lang}."
    messages = [
        {"role": "system", "content": system_prompt.format(lang=lang)},
        {"role": "user", "content": text}
    ]
    response = call_llm_model(model, messages)
    
    # Try to parse JSON response
    try:
        import json
        parsed_response = json.loads(response)
        
        # Convert to expected format
        result = {
            'title': parsed_response.get('Title', ''),
            'content': parsed_response.get('Notes', ''),
            'tags': parsed_response.get('Tags', [])
        }
        return result
    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️ Could not parse LLM response as JSON: {e}")
        # Return raw response as fallback
        return {
            'title': 'AI Generated Note',
            'content': response,
            'tags': ['ai', 'generated']
        }


#main function
if __name__ == "__main__":
    #example usage of extract_notes
    user_input = "Meeting with John at 3pm on Friday to discuss the project updates."
    print("Extracted Notes:")
    print(extract_notes(user_input, lang = "Japanese"))













#main function for translation
#    text = "Hello, how are you?"
#    target_language = "Japanese"
#    translated_text = translate(text, target_language)
#    print(f"Original text: {text}")
#    print(f"Translated text: {translated_text}")