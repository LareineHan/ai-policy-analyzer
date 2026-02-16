import google.genai as genai
from google.genai import types
import fitz  # PyMuPDF
from docx import Document
from PIL import Image
from pathlib import Path
import os

class PolicyAnalyzer:
    
    def __init__(self):
        """Initialize with Gemini API"""
        
        # Check API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("""
            GEMINI_API_KEY not found!
            
            Set it in terminal:
                export GEMINI_API_KEY=your_key
            
            Or in .env file:
                GEMINI_API_KEY=your_key
            """)
        
        # Gemini client setup
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        self.model_name = "models/gemini-3-flash-preview"
    
    def analyze(self, policy_file, student_action):
        """
        Main analysis function
        
        Args:
            policy_file: Path to policy (PDF/DOCX/TXT/Image)
            student_action: What student wants to do
        
        Returns:
            Analysis result as text
        """
        
        print(f"📄 Reading policy file: {policy_file}")
        policy_text = self._read_file(policy_file)
        
        print(f"🤔 Analyzing action: {student_action}")
        result = self._analyze_compliance(policy_text, student_action)
        
        return result
    
    def _read_file(self, file_path):
        """Read any supported file type"""
        
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        if ext == '.pdf':
            return self._read_pdf(file_path)
        elif ext == '.docx':
            return self._read_docx(file_path)
        elif ext == '.txt':
            return self._read_txt(file_path)
        elif ext in ['.png', '.jpg', '.jpeg']:
            return self._read_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def _read_pdf(self, pdf_path):
        """Extract text from PDF using PyMuPDF"""
        
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num, page in enumerate(doc, 1):
            text += f"\n{'='*60}\n"
            text += f"PAGE {page_num}\n"
            text += f"{'='*60}\n"
            text += page.get_text()
        
        doc.close()
        return text
    
    def _read_docx(self, docx_path):
        """Extract text from DOCX"""
        
        doc = Document(docx_path)
        paragraphs = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)
        
        return "\n\n".join(paragraphs)
    
    def _read_txt(self, txt_path):
        """Read plain text file"""
        
        with open(txt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _read_image(self, image_path):
        """Extract text from image using Gemini Vision"""
        
        # Read image as bytes
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Determine MIME type
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        # Use Gemini to extract text from image
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(
                    role='user',
                    parts=[
                        types.Part.from_bytes(
                            data=image_data,
                            mime_type=mime_type
                        ),
                        types.Part.from_text(
                            text="Extract all text from this policy document image. Preserve formatting and structure as much as possible."
                        )
                    ]
                )
            ]
        )
        
        return response.text
    
    def _analyze_compliance(self, policy_text, student_action):
        prompt = f"""You are an expert at analyzing academic AI usage policies.

    POLICY DOCUMENT:
    {policy_text}

    STUDENT ACTION:
    "{student_action}"

    Provide analysis AND critically evaluate the policy itself.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 RELEVANT POLICY SECTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quote the exact text from the policy that relates to this action.
Include page numbers or section numbers if available.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚖️ COMPLIANCE VERDICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Choose ONE:
✅ ALLOWED - This action clearly complies
⚠️ GRAY AREA - Policy is unclear
❌ VIOLATION - This clearly violates

Reasoning: [2-3 sentences explaining WHY in plain language]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 RISK ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Risk Score: [0-100]

Explanation: [2-3 sentences about what makes this risky or safe, 
in student-friendly language]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍🏫 PROFESSOR INTERPRETATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How might different professors interpret this?

Strict Professor: [likely response and reasoning]
Moderate Professor: [likely response and reasoning]
Lenient Professor: [likely response and reasoning]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔒 SAFEST:
[One clear sentence with specific action]

⚠️ MODERATE:
[One clear sentence with specific action]

❌ AVOID:
[One clear sentence with specific action]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 POLICY CRITIQUE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Evaluate this policy's effectiveness for students. Be concise and direct.
Write in clear bullet points. Max 5 sentences per point.

- VERDICT ON POLICY: Does this policy help or punish students?
- KEY FLAW: The single biggest problem with this policy (1-2 sentences)
- BETTER APPROACH: One concrete example of what a better policy says
- SUGGESTED FIX: One specific sentence this policy should add

Policy Effectiveness Score: [0-100]
Bottom line: [One sentence. Blunt. No hedging.]

FORMAT RULES:
- Use bullet points (•) not numbered lists
- Each bullet: max 2 sentences
- No sub-bullets
- Total response for this section: under 100 words
"""
        
        # Call Gemini API
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        
        return response.text


# Simple test function
def test_analyzer():
    """Quick test with sample policy"""
    
    # Create sample policy
    sample_policy = """
    EGR333W - Spring 2026
    AI Usage Policy

    Students may not use AI tools such as ChatGPT to complete assignments.
    All work must be original and represent the student's own understanding.

    Turnitin will be used to check for AI usage. Submissions with AI detection
    scores above 75% will be investigated and may result in academic integrity
    violations.
    """
    
    # Save to file
    os.makedirs('examples', exist_ok=True)
    with open('examples/sample_policy.txt', 'w') as f:
        f.write(sample_policy)
    
    # Test
    print("Testing Policy Analyzer...\n")
    
    analyzer = PolicyAnalyzer()
    
    result = analyzer.analyze(
        policy_file='examples/sample_policy.txt',
        student_action="I used ChatGPT to brainstorm ideas, then wrote the essay entirely in my own words"
    )
    
    print("\n" + "="*60)
    print("ANALYSIS RESULT:")
    print("="*60 + "\n")
    print(result)


if __name__ == "__main__":
    test_analyzer()