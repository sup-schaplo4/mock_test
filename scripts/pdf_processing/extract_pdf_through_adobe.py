# extract_with_adobe_api.py - FIXED FOR JSON RESPONSE
import requests
import json
import time
import os
import zipfile
import shutil
import re
from typing import List, Dict, Optional
import io

class SimpleAdobeExtractor:
    def __init__(self, creds_file=None):
        """Initialize with credentials from environment or file"""
        if creds_file and os.path.exists(creds_file):
            with open(creds_file, 'r') as f:
                creds = json.load(f)
            self.client_id = creds['client_credentials']['client_id']
            self.client_secret = creds['client_credentials']['client_secret']
        else:
            # Try environment variables first
            self.client_id = os.environ.get('ADOBE_CLIENT_ID')
            self.client_secret = os.environ.get('ADOBE_CLIENT_SECRET')
            if not self.client_id or not self.client_secret:
                raise ValueError("❌ Please set ADOBE_CLIENT_ID and ADOBE_CLIENT_SECRET environment variables or provide a valid credentials file")
        
        self.token = None
        self.base_url = "https://pdf-services.adobe.io"
        
    def get_token(self):
        """Get access token using OAuth2"""
        
        print("🔑 Getting access token...")
        
        auth_url = "https://ims-na1.adobelogin.com/ims/token/v3"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "openid,AdobeID,read_organizations"
        }
        
        try:
            response = requests.post(auth_url, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get('access_token')
                print("✅ Got access token")
                return True
            else:
                print(f"❌ Auth failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Auth error: {e}")
            return False
    
    def extract_pdf(self, pdf_path):
        """Extract using REST API"""
        
        if not self.token:
            if not self.get_token():
                print("❌ Authentication failed")
                return None
        
        try:
            # Step 1: Create upload presigned URL
            print(f"📤 Uploading {os.path.basename(pdf_path)}...")
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "x-api-key": self.client_id,
                "Content-Type": "application/json"
            }
            
            # Create asset
            asset_url = f"{self.base_url}/assets"
            asset_payload = {"mediaType": "application/pdf"}
            
            asset_response = requests.post(asset_url, headers=headers, json=asset_payload)
            
            if asset_response.status_code != 200:
                print(f"❌ Asset creation failed: {asset_response.text}")
                return None
            
            asset_data = asset_response.json()
            upload_uri = asset_data.get('uploadUri')
            asset_id = asset_data.get('assetID')
            
            # Step 2: Upload PDF
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            
            upload_response = requests.put(
                upload_uri,
                data=pdf_data,
                headers={"Content-Type": "application/pdf"}
            )
            
            if upload_response.status_code != 200:
                print(f"❌ Upload failed: {upload_response.status_code}")
                return None
            
            print("✅ PDF uploaded successfully")
            
            # Step 3: Create extraction job
            print("⏳ Starting extraction job...")
            
            extract_url = f"{self.base_url}/operation/extractpdf"
            
            extract_payload = {
                "assetID": asset_id,
                "elementsToExtract": ["text", "tables"],
                "renditionsToExtract": ["tables", "figures"]
            }
            
            job_response = requests.post(extract_url, headers=headers, json=extract_payload)
            
            if job_response.status_code not in [201, 202]:
                print(f"❌ Job creation failed: {job_response.text}")
                return None
            
            job_location = job_response.headers.get('location') or job_response.headers.get('Location')
            
            print(f"📍 Job location: {job_location}")
            
            # Step 4: Poll for completion
            print("⏳ Waiting for extraction to complete...")
            
            for attempt in range(30):
                time.sleep(2)
                
                status_response = requests.get(job_location, headers=headers)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    
                    print(f"Status: {status}")
                    
                    if status in ['done', 'DONE']:
                        print("✅ Extraction complete!")
                        
                        # Get download URI from content
                        content = status_data.get('content', {})
                        download_uri = content.get('downloadUri')
                        
                        if not download_uri:
                            # Try resource path
                            resource = status_data.get('resource', {})
                            download_uri = resource.get('downloadUri')
                        
                        if download_uri:
                            return self.download_and_parse(download_uri)
                        else:
                            print("❌ No download URI found")
                            print(f"Response structure: {json.dumps(status_data, indent=2)}")
                            return None
                    
                    elif status in ['failed', 'FAILED']:
                        print("❌ Extraction failed")
                        return None
                    
                    print(f"  Attempt {attempt + 1}/30")
            
            print("❌ Timeout")
            return None
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def download_and_parse(self, download_uri):
        """Download and parse results - handles both ZIP and JSON responses"""
        
        try:
            print("📥 Downloading results...")
            
            result_response = requests.get(download_uri)
            
            if result_response.status_code != 200:
                print(f"❌ Download failed: {result_response.status_code}")
                return None
            
            # Check content type
            content_type = result_response.headers.get('Content-Type', '')
            print(f"📄 Content type: {content_type}")
            
            # Try to determine if it's JSON or ZIP
            content = result_response.content
            
            # First, try to parse as JSON
            try:
                # If it's JSON, parse directly
                data = json.loads(content)
                print("✅ Received JSON response directly")
                return self.parse_questions(data)
                
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, try as ZIP
                print("📦 Attempting to extract as ZIP...")
                
                try:
                    # Try to open as ZIP
                    with io.BytesIO(content) as bio:
                        with zipfile.ZipFile(bio, 'r') as z:
                            # List files in ZIP
                            file_list = z.namelist()
                            print(f"📁 Files in ZIP: {file_list}")
                            
                            # Look for JSON file
                            json_file = None
                            for file in file_list:
                                if file.endswith('.json'):
                                    json_file = file
                                    break
                            
                            if json_file:
                                # Extract and parse JSON
                                json_content = z.read(json_file)
                                data = json.loads(json_content)
                                print(f"✅ Extracted {json_file} from ZIP")
                                return self.parse_questions(data)
                            else:
                                print("❌ No JSON file found in ZIP")
                                return None
                                
                except zipfile.BadZipFile:
                    # Not a ZIP either, maybe it's a different format
                    print("❌ Response is neither JSON nor ZIP")
                    
                    # Try to save and inspect
                    with open('debug_response.bin', 'wb') as f:
                        f.write(content[:1000])  # Save first 1000 bytes for inspection
                    
                    # Check if it might be plain text
                    try:
                        text = content.decode('utf-8')
                        if 'elements' in text or 'Text' in text:
                            # Might be JSON with BOM or encoding issues
                            # Remove BOM if present
                            if text.startswith('\ufeff'):
                                text = text[1:]
                            data = json.loads(text)
                            print("✅ Parsed as JSON after cleaning")
                            return self.parse_questions(data)
                        else:
                            print(f"📄 Response preview: {text[:200]}")
                            return None
                    except:
                        print(f"📄 Binary response (first 50 bytes): {content[:50]}")
                        return None
                        
        except Exception as e:
            print(f"❌ Error parsing results: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_questions(self, data):
        """Parse questions from JSON - handles multiple formats"""
        
        questions = []
        
        # Check if data has expected structure
        if isinstance(data, dict):
            # Standard format with elements
            if 'elements' in data:
                elements = data['elements']
                print(f"📝 Parsing {len(elements)} elements...")
                
                current_q = None
                q_text = ""
                options = {}
                
                for elem in elements:
                    # Handle different text field names
                    text = elem.get('Text') or elem.get('text') or elem.get('content', '')
                    text = str(text).strip()
                    
                    if not text:
                        continue
                    
                    # Check for question pattern
                    q_match = re.match(r'Q\.(\d+)\)', text)
                    
                    if q_match:
                        # Save previous question
                        if current_q and q_text:
                            questions.append({
                                "number": current_q,
                                "text": q_text.strip(),
                                "options": options
                            })
                        
                        # Start new question
                        current_q = int(q_match.group(1))
                        q_text = text[q_match.end():].strip()
                        options = {}
                        
                    elif current_q:
                        # Check for option
                        opt_match = re.match(r'$([a-e])$\s*(.*)', text, re.I)
                        
                        if opt_match:
                            letter = opt_match.group(1).upper()
                            options[letter] = opt_match.group(2).strip()
                        else:
                            q_text += " " + text
                
                # Save last question
                if current_q and q_text:
                    questions.append({
                        "number": current_q,
                        "text": q_text.strip(),
                        "options": options
                    })
            
            # Alternative format - content array
            elif 'content' in data and isinstance(data['content'], list):
                print("📝 Parsing content array format...")
                return self.parse_questions({'elements': data['content']})
            
            # Plain text format
            elif 'text' in data or 'extractedText' in data:
                text = data.get('text') or data.get('extractedText', '')
                print("📝 Parsing plain text format...")
                questions = self.parse_questions_from_text(text)
            
            else:
                print(f"⚠️ Unknown data format. Keys: {list(data.keys())[:10]}")
                
        elif isinstance(data, list):
            # Direct array of elements
            print("📝 Parsing array format...")
            return self.parse_questions({'elements': data})
        
        print(f"✅ Parsed {len(questions)} questions")
        return questions
    
    def parse_questions_from_text(self, text):
        """Parse questions from plain text"""
        
        questions = []
        
        # Split by question pattern - more flexible
        lines = text.split(' ')
        
        current_q = None
        q_text = ""
        options = {}
        
        for line in lines:
            line = line.strip()
            
            # Check for question start
            q_match = re.match(r'Q\.?\s*(\d+)\s*\)', line)
            if not q_match:
                q_match = re.match(r'Question\s+(\d+)', line, re.I)
            
            if q_match:
                # Save previous
                if current_q and q_text:
                    questions.append({
                        "number": current_q,
                        "text": q_text.strip(),
                        "options": options
                    })
                
                current_q = int(q_match.group(1))
                q_text = line[q_match.end():].strip()
                options = {}
                
            elif current_q:
                # Check for option
                opt_match = re.match(r'$([a-e])$\s*(.*)', line, re.I)
                if not opt_match:
                    opt_match = re.match(r'([a-e])\.\s*(.*)', line, re.I)
                
                if opt_match:
                    letter = opt_match.group(1).upper()
                    options[letter] = opt_match.group(2).strip()
                elif line:
                    q_text += " " + line
        
        # Save last
        if current_q and q_text:
            questions.append({
                "number": current_q,
                "text": q_text.strip(),
                "options": options
            })
        
        return questions

# Main execution
if __name__ == "__main__":
    # Check for credentials
    if not os.path.exists("pdfservices-api-credentials.json"):
        print("❌ Credentials file not found!")
        exit(1)
    
    extractor = SimpleAdobeExtractor()
    
    # Find PDF
    pdf_path = "rbi_pdf/RBI_PYP_PHASE_01_2023_General_Awareness_Questions.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        # Try to find any PDF
        if os.path.exists("rbi_pdf"):
            pdfs = [f for f in os.listdir("rbi_pdf") if f.endswith('.pdf')]
            if pdfs:
                pdf_path = os.path.join("rbi_pdf", pdfs[0])
                print(f"✅ Using: {pdf_path}")
    
    questions = extractor.extract_pdf(pdf_path)
    
    if questions:
        print(f"✅ Successfully extracted {len(questions)} questions")
        
        # Save to JSON
        output = {
            "source": os.path.basename(pdf_path),
            "total": len(questions),
            "extraction_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "questions": questions
        }
        
        with open('extracted_questions.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print("💾 Saved to extracted_questions.json")
        
        # Show sample
        print("📝 Sample questions:")
        for q in questions[:3]:
            print(f"Q.{q['number']}: {q['text'][:100]}...")
            if q.get('options'):
                for letter, opt in list(q['options'].items())[:2]:
                    print(f"  ({letter}) {opt[:50]}...")
    else:
        print("❌ No questions extracted")
        print("Debug: Check debug_response.bin if created")
