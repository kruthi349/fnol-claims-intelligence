"""
FNOL Insurance Claims Processing Agent
Autonomous agent that extracts, validates, classifies, and routes insurance claims.
Uses Groq (free, fast) as the AI provider.
"""

import os
import json
import re
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs('uploads', exist_ok=True)

# ---------------------------------------------------------------
# 🔑 GROQ API KEY — set this as an environment variable:
#    Windows CMD:   set GROQ_API_KEY=gsk_your_key_here
#    Windows PS:    $env:GROQ_API_KEY="gsk_your_key_here"
#    Mac/Linux:     export GROQ_API_KEY=gsk_your_key_here
#
# Get your FREE key at: https://console.groq.com → API Keys
# ---------------------------------------------------------------
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

ALLOWED_EXTENSIONS = {'txt', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def read_file_content(filepath):
    """Read file content - handles txt files directly."""
    ext = filepath.rsplit('.', 1)[1].lower()
    if ext == 'txt':
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    elif ext == 'pdf':
        # Try to extract text from PDF using basic approach
        try:
            import subprocess
            result = subprocess.run(
                ['python3', '-c', f'''
import sys
try:
    with open("{filepath}", "rb") as f:
        content = f.read()
    # Basic PDF text extraction - look for text between stream markers
    text = content.decode("latin-1", errors="ignore")
    # Extract readable ASCII text
    import re
    words = re.findall(r"[A-Za-z0-9\s\.\,\:\-\/\$\(\)\'\"]+", text)
    print(" ".join(words[:2000]))
except Exception as e:
    print(f"Error: {{e}}")
'''],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout if result.stdout else "PDF content could not be extracted. Please use TXT format."
        except Exception:
            return "PDF content could not be extracted. Please use TXT format."
    return ""


def extract_and_route_claim(document_text: str) -> dict:
    """
    Core agent function: uses Claude to extract fields, identify issues, and route the claim.
    """

    system_prompt = """You are an expert insurance claims processing agent specializing in FNOL (First Notice of Loss) documents.

CRITICAL: You MUST respond with ONLY a valid JSON object. No explanation, no preamble, no markdown, no ```json fences. Start your response with { and end with }. Nothing before or after the JSON.

Your job is to:
1. Extract all key fields from the document
2. Identify missing or inconsistent/suspicious fields
3. Classify the claim type and apply routing rules
4. Provide clear reasoning for your decision

ROUTING RULES (apply in priority order):
- If description contains words like "fraud", "inconsistent", "staged", "suspicious" → recommendedRoute: "Investigation Flag"
- If claim type is "injury" or "bodily injury" → recommendedRoute: "Specialist Queue"
- If any mandatory field is missing → recommendedRoute: "Manual Review"
- If estimated damage < $25,000 (and no other flags) → recommendedRoute: "Fast-track"
- If estimated damage >= $25,000 (and no other flags) → recommendedRoute: "Standard Review"

MANDATORY FIELDS that must be present:
- policyNumber, policyholderName, effectiveDates
- incidentDate, incidentTime, incidentLocation, incidentDescription
- claimantName, claimantContact
- assetType, estimatedDamage
- claimType

Respond ONLY with a valid JSON object in exactly this format:
{
  "extractedFields": {
    "policyNumber": "",
    "policyholderName": "",
    "effectiveDates": "",
    "incidentDate": "",
    "incidentTime": "",
    "incidentLocation": "",
    "incidentDescription": "",
    "claimantName": "",
    "thirdParties": "",
    "claimantContact": "",
    "assetType": "",
    "assetId": "",
    "estimatedDamage": "",
    "claimType": "",
    "attachments": "",
    "initialEstimate": ""
  },
  "missingFields": [],
  "inconsistencies": [],
  "recommendedRoute": "",
  "reasoning": "",
  "riskScore": "",
  "priority": ""
}

For missingFields: list field names that are absent or unclear.
For inconsistencies: list any suspicious, conflicting, or unusual data points.
For riskScore: give a score from 1-10 (10 = highest risk).
For priority: "High", "Medium", or "Low".
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # Best free model on Groq
        max_tokens=2000,
        temperature=0,                      # 0 = consistent output
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Process this FNOL document and extract all information:\n\n{document_text}"
            }
        ]
    )

    raw_text = response.choices[0].message.content.strip()

    # Robustly extract JSON from the response
    # 1. Try to find a JSON block inside markdown fences
    fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text)
    if fence_match:
        raw_text = fence_match.group(1).strip()
    else:
        # 2. Try to find the first { ... } block in the response
        brace_match = re.search(r'\{[\s\S]*\}', raw_text)
        if brace_match:
            raw_text = brace_match.group(0).strip()

    result = json.loads(raw_text)
    return result


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process_claim():
    """Process a claim from either file upload or pasted text."""
    document_text = ""

    # Check if file was uploaded
    if 'file' in request.files and request.files['file'].filename:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            document_text = read_file_content(filepath)
        else:
            return jsonify({"error": "Invalid file type. Please upload PDF or TXT files."}), 400

    # Check if text was pasted
    elif 'document_text' in request.form and request.form['document_text'].strip():
        document_text = request.form['document_text'].strip()

    else:
        return jsonify({"error": "Please provide a document file or paste document text."}), 400

    if not document_text:
        return jsonify({"error": "Could not read document content."}), 400

    try:
        result = extract_and_route_claim(document_text)
        result['documentPreview'] = document_text[:500] + "..." if len(document_text) > 500 else document_text
        return jsonify(result)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Failed to parse agent response: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500


@app.route('/sample/<int:sample_id>')
def get_sample(sample_id):
    """Return sample FNOL documents for testing."""
    samples = {
        1: """FIRST NOTICE OF LOSS - AUTO CLAIM

Policy Number: AUTO-2024-887234
Policyholder Name: James R. Mitchell
Effective Dates: 01/01/2024 - 12/31/2024

INCIDENT INFORMATION
Date of Incident: March 14, 2024
Time of Incident: 2:45 PM
Location: Intersection of Oak Street and 5th Avenue, Austin, TX 78701
Description: Policyholder's vehicle was rear-ended while stopped at a red light. The other driver failed to brake in time.

INVOLVED PARTIES
Claimant: James R. Mitchell
Third Party: Sarah L. Thompson (other driver)
Contact Details: James Mitchell - (512) 445-9987 | sarah.thompson@email.com

ASSET DETAILS
Asset Type: Automobile
Asset ID / VIN: 1HGBH41JXMN109186
Estimated Damage: $8,500

OTHER INFORMATION
Claim Type: Property Damage
Attachments: Photos (5), Police Report #ATX-2024-3821
Initial Estimate: $8,500""",

        2: """FIRST NOTICE OF LOSS - HOME INSURANCE

Policy Number: HOME-2024-443921
Policyholder Name: Maria Elena Vasquez
Effective Dates: 06/15/2023 - 06/15/2024

INCIDENT INFORMATION
Date of Incident: March 10, 2024
Time of Incident: 11:30 PM
Location: 742 Riverdale Drive, Chicago, IL 60601
Description: A pipe burst in the basement causing significant water damage to flooring, walls and personal belongings. The damage appears inconsistent with a simple pipe burst — neighbors report no similar issues despite same weather conditions.

INVOLVED PARTIES
Claimant: Maria Elena Vasquez
Third Parties: None
Contact Details: (773) 882-4456

ASSET DETAILS
Asset Type: Residential Property
Asset ID: PROP-IL-7423
Estimated Damage: $47,000

OTHER INFORMATION
Claim Type: Property Damage
Attachments: Photos (12), Plumber's Report
Initial Estimate: $47,000""",

        3: """FIRST NOTICE OF LOSS

Policyholder Name: Robert K. Huang

INCIDENT INFORMATION
Date: February 28, 2024
Location: Highway 101, San Francisco, CA
Description: Vehicle collision resulting in bodily injury. Driver suffered whiplash and back injuries requiring medical attention.

INVOLVED PARTIES
Claimant: Robert K. Huang
Third Party: Unknown driver fled scene

ASSET DETAILS
Asset Type: Automobile
Estimated Damage: $32,000

Claim Type: Injury
Initial Estimate: $32,000""",

        4: """FIRST NOTICE OF LOSS - FRAUD INVESTIGATION CASE

Policy Number: COMM-2024-112987
Policyholder Name: TechStart LLC (Owner: David Park)
Effective Dates: 01/01/2024 - 12/31/2024

INCIDENT INFORMATION
Date of Incident: March 1, 2024
Time of Incident: 3:00 AM
Location: 1200 Business Park Blvd, Dallas, TX 75201
Description: Fire broke out in the warehouse destroying inventory worth $95,000. Investigation suggests the fire may have been staged — accelerant patterns found by fire marshal, and inventory records show items were removed 2 days prior.

INVOLVED PARTIES
Claimant: David Park (Owner)
Contact Details: david.park@techstart.com | (214) 567-8900

ASSET DETAILS
Asset Type: Commercial Property / Inventory
Asset ID: COMM-PROP-2024-887
Estimated Damage: $95,000

OTHER INFORMATION
Claim Type: Property Damage
Attachments: Fire Marshal Report, Inventory Records
Initial Estimate: $95,000"""
    }

    if sample_id not in samples:
        return jsonify({"error": "Sample not found"}), 404

    return jsonify({"text": samples[sample_id]})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
