from dotenv import load_dotenv
load_dotenv()  
from flask import Flask, request, render_template_string, jsonify
from policy_analyzer import PolicyAnalyzer
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

analyzer = PolicyAnalyzer()

# HTML template (same as before)
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Policy Analyzer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 32px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .upload-box {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            background: #f8f9ff;
            transition: all 0.3s;
        }
        .upload-box:hover {
            border-color: #764ba2;
            background: #f0f1ff;
        }
        input[type="file"] {
            margin: 10px 0;
        }
        textarea {
            width: 100%;
            height: 120px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            resize: vertical;
            font-family: inherit;
        }
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            width: 100%;
            margin-top: 20px;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:active {
            transform: translateY(0);
        }
        .result {
            margin-top: 30px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 10px;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
            max-height: 600px;
            overflow-y: auto;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #667eea;
        }
        .step {
            margin: 30px 0;
        }
        .step h3 {
            color: #333;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 AI Policy Analyzer</h1>
        <p class="subtitle">Upload any policy document and check if your AI usage complies</p>
        
        <form method="POST" enctype="multipart/form-data" id="analyzeForm">
            <div class="step">
                <h3>Step 1: Upload Policy Document</h3>
                <div class="upload-box">
                    <input type="file" name="policy" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg" required>
                    <p style="margin-top: 10px; color: #666;">
                        📄 Supports: PDF, DOCX, TXT, Images
                    </p>
                </div>
            </div>
            
            <div class="step">
                <h3>Step 2: Describe Your Action</h3>
                <textarea 
                    name="action" 
                    placeholder="Example: I want to use ChatGPT to brainstorm ideas for my essay, then write it entirely in my own words"
                    required
                ></textarea>
            </div>
            
            <button type="submit">🔍 Analyze Compliance</button>
        </form>
        
        {% if result %}
        <div class="result">{{ result }}</div>
        {% endif %}
        
        {% if error %}
        <div class="result" style="background: #fee; color: #c00;">
            ❌ Error: {{ error }}
        </div>
        {% endif %}
    </div>
    
    <script>
        document.getElementById('analyzeForm').onsubmit = function() {
            const button = document.querySelector('button');
            button.innerHTML = '⏳ Analyzing...';
            button.disabled = true;
        };
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    
    if request.method == 'POST':
        try:
            policy_file = request.files['policy']
            action = request.form['action']
            
            # Save file
            filepath = os.path.join(
                app.config['UPLOAD_FOLDER'], 
                policy_file.filename
            )
            policy_file.save(filepath)
            
            # Analyze
            result = analyzer.analyze(filepath, action)
            
        except Exception as e:
            error = str(e)
    
    return render_template_string(HTML, result=result, error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)