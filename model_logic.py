import vertexai
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models
from google.cloud import firestore
import datetime

# Initialize Vertex AI
PROJECT_ID = "medsafe-ai-checker"
LOCATION = "europe-west1"
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Initialize Firestore
db = firestore.Client(project=PROJECT_ID)

def load_search_history(user_id):
    """Loads the last 5 searches for a given user ID."""
    if not user_id:
        return []

    history_ref = db.collection("search_history")
    query = history_ref.where("user_id", "==", user_id).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(5)
    
    history_list = []
    for doc in query.stream():
        data = doc.to_dict()
        history_list.append({
            "timestamp": data['timestamp'].strftime("%Y-%m-%d %H:%M"),
            "medications": data.get("medications", "N/A"),
            "condition": data.get("condition", "N/A"),
            "diet": data.get("diet", "N/A"),
            "preview": data.get("ai_response_preview", "No analysis saved")
        })
    return history_list

def save_search_to_db(user_id, meds, condition, diet, alcohol, smoking, response_text):
    """Saves the user query and AI response to Firestore"""
    doc_ref = db.collection("search_history").document()
    doc_ref.set({
        "timestamp": datetime.datetime.now(),
        "user_id": user_id, 
        "medications": meds,
        "condition": condition,
        "diet": diet,
        "alcohol": alcohol, 
        "smoking": smoking, 
        "full_ai_response": response_text, 
        "ai_response_preview": response_text[:200] + "..." 
    })
    return doc_ref.id 

def analyze_interactions(user_id, meds, condition, diet, alcohol, smoking): 
    model = GenerativeModel("gemini-2.5-flash")
    
    prompt = f"""
    You are a helpful medical assistant for laypeople.
    
    INSTRUCTIONS: 
    1. The output must begin on the very first line with the disclaimer.
    2. Follow the disclaimer with a single blank line.
    3. The rest of the output must be well-formed Markdown.

    I am taking the following medication: [{meds}].
    I have this condition: [{condition}].
    I often eat: [{diet}].
    I confirm my alcohol intake is: [{alcohol}].
    I confirm my smoking status is: [{smoking}].
    
    Analyze potential side effects and interactions (Drug-Drug, Drug-Food, Drug-Condition, Drug-Lifestyle).
    Output the result in a simple, well-formatted Markdown table that starts with a clear heading.
    Include a simplified explanation for a 12-year-old reading level.
    """

    safety_config = {
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    }

    try:
        response = model.generate_content(
            prompt,
            safety_settings=safety_config
        )
        # Aggressive cleaning to fix formatting
        result_text = '\n'.join([line.strip() for line in response.text.splitlines() if line.strip()])
        
        if not result_text.lower().startswith("i am an ai"):
             result_text = "I am an AI, not a doctor. Consult a professional.\n\n" + result_text
        
        save_search_to_db(user_id, meds, condition, diet, alcohol, smoking, result_text)
        
        return result_text
    except Exception as e:
        return f"Error contacting AI: {str(e)}"
