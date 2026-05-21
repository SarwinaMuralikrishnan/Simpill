import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "gemma" # or "llama3"

def get_chatbot_response(user_message, history=None):
    """
    Sends chat prompt to local Ollama. If Ollama is offline or unavailable,
    uses a sophisticated local rule-based response engine.
    """
    if history is None:
        history = []

    # Prepare chat context
    messages = []
    # System prompt to keep responses safe and medically helpful
    system_prompt = (
        "You are SimPill AI, a virtual medical assistant. Provide helpful, accurate, "
        "and clear health explanations. Advise the user to consult a doctor for severe "
        "symptoms. Keep answers concise."
    )
    
    messages.append({"role": "system", "content": system_prompt})
    for chat in history:
        messages.append({"role": chat.get("role", "user"), "content": chat.get("content", "")})
    messages.append({"role": "user", "content": user_message})

    # Try Ollama connection
    try:
        payload = {
            "model": DEFAULT_MODEL,
            "messages": messages,
            "stream": False
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=4)
        if response.status_code == 200:
            result_json = response.json()
            return result_json.get("message", {}).get("content", "")
    except Exception as e:
        print(f"Ollama offline/error: {e}. Falling back to Rule-based Medical engine.")

    # Fallback Local Heuristics
    return generate_local_response(user_message)

def generate_local_response(msg):
    msg = msg.lower()
    
    # 1. Symptom Heuristics
    if any(k in msg for k in ["fever", "temperature", "warm", "feverish"]):
        return (
            "A fever is usually a sign that your body is fighting off an infection. "
            "Make sure to rest, stay hydrated, and monitor your temperature. You can take "
            "over-the-counter fever reducers like Paracetamol (500mg) if needed. "
            "If your temperature exceeds 103°F (39.4°C) or lasts more than 3 days, please "
            "book an appointment with a doctor immediately."
        )
    elif any(k in msg for k in ["headache", "migraine", "head pain"]):
        return (
            "Headaches can be caused by dehydration, stress, lack of sleep, or sinus issues. "
            "Rest in a quiet, dark room, drink plenty of water, and consider taking Ibuprofen or Paracetamol. "
            "Seek immediate medical attention if the headache is sudden and severe (a 'thunderclap' headache) "
            "or accompanied by fever, stiff neck, or confusion."
        )
    elif any(k in msg for k in ["cough", "cold", "flu", "sneeze", "congest", "throat"]):
        return (
            "For common cold and cough symptoms, rest, steam inhalation, warm liquids (like tea with honey), "
            "and saline nasal sprays are very helpful. Over-the-counter decongestants or antihistamines can "
            "reduce nasal congestion. If you experience shortness of breath, wheezing, or high fever, please "
            "schedule a consultation with our general physician."
        )
    elif any(k in msg for k in ["chest pain", "heart attack", "shortness of breath", "breathless"]):
        return (
            "WARNING: Severe chest pain, pressure, or tightness accompanied by shortness of breath, dizziness, "
            "or pain radiating to your arm or jaw could indicate a medical emergency. "
            "Please click the red emergency SOS button immediately to dispatch assistance or go to the nearest emergency room."
        )
    
    # 2. Medication explanations
    elif "paracetamol" in msg or "acetaminophen" in msg:
        return (
            "Paracetamol (Acetaminophen) is a common analgesic (pain reliever) and antipyretic (fever reducer). "
            "It is used to treat mild-to-moderate pain and fever. The standard adult dose is 500mg to 1000mg "
            "every 4-6 hours, not exceeding 4000mg (4g) per day. Avoid alcohol, and check other medications to "
            "prevent accidental double-dosing which can cause liver damage."
        )
    elif "amoxicillin" in msg or "antibiotic" in msg:
        return (
            "Amoxicillin is a penicillin-type antibiotic used to treat bacterial infections (e.g., ear, throat, "
            "respiratory, and urinary tract infections). It does NOT treat viral infections like the flu or common cold. "
            "IMPORTANT: Always complete the full prescribed course of antibiotics, even if you feel better, to prevent "
            "bacterial resistance."
        )
    elif "ibuprofen" in msg or "advil" in msg or "nlaid" in msg:
        return (
            "Ibuprofen is a Non-Steroidal Anti-Inflammatory Drug (NSAID). It works by reducing hormones that cause "
            "pain and inflammation. It is commonly used for headaches, muscle aches, toothaches, and arthritis. "
            "Take it with food or milk to prevent stomach irritation, and avoid taking it if you have a history of stomach ulcers."
        )
        
    # 3. Portal Guidance
    elif "appointment" in msg or "schedule" in msg or "book" in msg:
        return (
            "To book an appointment, go to the 'Appointments' section in your Patient Sidebar. "
            "You can choose a doctor, select a convenient date and time, choose between physical and "
            "telemedicine (video) consultation, and add notes. Once submitted, the doctor will review "
            "and approve the booking."
        )
    elif "caregiver" in msg or "family" in msg:
        return (
            "You can manage your caregivers via the 'Caregivers' tab in your dashboard. "
            "Add their name, phone number, and relationship. SimPill will generate a unique access token link. "
            "You can copy this link and send it to them so they can view your medication schedule, adherence dashboard, "
            "and receive real-time alerts if you miss a dose."
        )
    elif "report" in msg or "upload" in msg or "scan" in msg:
        return (
            "You can upload your reports, prescriptions, or medical scans in the 'Medical Reports' section. "
            "Select the correct category (e.g., Blood Report, Prescription, MRI Scan), browse your file "
            "(PDF, JPG, PNG under 16MB), and click Upload. The system will create an image/PDF preview "
            "and run the AI Report Analyzer to extract values."
        )
    
    # 4. General fallback
    return (
        "Hello! I am SimPill AI, your personal healthcare companion. I can help answer questions "
        "about common symptoms, explain medications, assist with booking appointments, or explain "
        "how to navigate the SimPill Portal. How can I help you today?"
    )
