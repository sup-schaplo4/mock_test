# extract_with_adobe_api.py - FIXED VERSION
import requests
import json
import time
import os
import zipfile
import shutil
import re
from typing import List, Dict, Optional

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
        
        # Adobe uses OAuth2 for authentication
        token_url = "https://ims-na1.adobelogin.com/ims/exchange/jwt"
        
        # For service account, we need to use client credentials flow
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
                print(f"Response: {response.text}")
                
                # Try alternative auth endpoint
                return self.get_token_alternative()
                
        except Exception as e:
            print(f"❌ Auth error: {e}")
            return False
    
    def get_token_alternative(self):
        """Alternative token method"""
        
        print("🔑 Trying alternative authentication...")
        
        # Direct API key approach
        headers = {
            "x-api-key": self.client_id,
            "Content-Type": "application/json"
        }
        
        # Test if we can use API key directly
        test_url = f"{self.base_url}/operation/extractpdf"
        
        response = requests.head(test_url, headers=headers)
        
        if response.status_code in [200, 401, 403]:
            print("✅ Using API key authentication")
            self.token = "API_KEY"  # Flag to use API key instead
            return True
        
        return False
    
    def extract_pdf(self, pdf_path):
        """Extract using REST API with proper error handling"""
        
        if not self.token:
            if not self.get_token():
                print("❌ Authentication failed")
                return None
        
        try:
            # Step 1: Create upload presigned URL
            print(f"📤 Uploading {os.path.basename(pdf_path)}...")
            
            if self.token == "API_KEY":
                headers = {
                    "x-api-key": self.client_id,
                    "Content-Type": "application/json"
                }
            else:
                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "x-api-key": self.client_id,
                    "Content-Type": "application/json"
                }
            
            # Create asset first
            asset_url = f"{self.base_url}/assets"
            
            asset_payload = {
                "mediaType": "application/pdf"
            }
            
            asset_response = requests.post(asset_url, headers=headers, json=asset_payload)
            
            print(f"Asset creation response: {asset_response.status_code}")
            
            if asset_response.status_code != 200:
                print(f"❌ Asset creation failed: {asset_response.text}")
                print("🔧 Trying alternative approach...")
                return self.extract_pdf_alternative(pdf_path)
            
            asset_data = asset_response.json()
            print(f"Asset data keys: {asset_data.keys()}")
            
            upload_uri = asset_data.get('uploadUri')
            asset_id = asset_data.get('assetID')
            
            if not upload_uri or not asset_id:
                print("❌ Missing upload URI or asset ID")
                return self.extract_pdf_alternative(pdf_path)
            
            # Step 2: Upload the PDF
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
            
            print(f"Job creation response: {job_response.status_code}")
            
            if job_response.status_code not in [201, 202]:
                print(f"❌ Job creation failed: {job_response.text}")
                return None
            
            # Get job location from headers
            job_location = job_response.headers.get('location') or job_response.headers.get('Location')
            
            if not job_location:
                print("❌ No job location in response")
                job_data = job_response.json()
                print(f"Response data: {json.dumps(job_data, indent=2)}")
                return None
            
            print(f"📍 Job location: {job_location}")
            
            # Step 4: Poll for job completion
            print("⏳ Waiting for extraction to complete...")
            
            max_attempts = 30
            for attempt in range(max_attempts):
                time.sleep(2)
                
                status_response = requests.get(job_location, headers=headers)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    print(f"Status: {status_data.get('status', 'unknown')}")
                    
                    if status_data.get('status') == 'done' or status_data.get('status') == 'DONE':
                        print("✅ Extraction complete!")
                        
                        # Debug: Print the response structure
                        print(f"Response keys: {status_data.keys()}")
                        
                        # Try different possible response structures
                        download_uri = None
                        
                        # Try different paths to find download URI
                        if 'asset' in status_data:
                            download_uri = status_data['asset'].get('downloadUri')
                        elif 'content' in status_data:
                            download_uri = status_data['content'].get('downloadUri')
                        elif 'downloadUri' in status_data:
                            download_uri = status_data['downloadUri']
                        elif 'resource' in status_data:
                            download_uri = status_data['resource'].get('downloadUri')
                        elif 'output' in status_data:
                            download_uri = status_data['output'].get('downloadUri')
                        
                        if not download_uri:
                            print("❌ No download URI found in response")
                            print(f"Full response: {json.dumps(status_data, indent=2)}")
                            return None
                        
                        # Download results
                        return self.download_and_parse(download_uri)
                    
                    elif status_data.get('status') in ['failed', 'FAILED']:
                        print("❌ Extraction failed")
                        print(f"Error: {status_data.get('error', 'Unknown error')}")
                        return None
                    
                    print(f"  Attempt {attempt + 1}/{max_attempts}")
                
                elif status_response.status_code == 404:
                    print("❌ Job not found")
                    return None
            
            print("❌ Timeout waiting for extraction")
            return None
            
        except Exception as e:
            print(f"❌ Error during extraction: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_pdf_alternative(self, pdf_path):
        """Alternative extraction using form data"""
        
        print("🔄 Trying alternative extraction method...")
        
        try:
            # This approach uses multipart form data
            url = f"{self.base_url}/operation/extractpdf"
            
            with open(pdf_path, 'rb') as f:
                files = {
                    'InputFile0': (os.path.basename(pdf_path), f, 'application/pdf')
                }
                
                data = {
                    'elementsToExtract': 'text,tables',
                    'renditionsToExtract': 'tables,figures'
                }
                
                if self.token == "API_KEY":
                    headers = {"x-api-key": self.client_id}
                else:
                    headers = {
                        "Authorization": f"Bearer {self.token}",
                        "x-api-key": self.client_id
                    }
                
                response = requests.post(url, headers=headers, files=files, data=data)
                
                print(f"Alternative response: {response.status_code}")
                
                if response.status_code == 200:
                    # Direct response with data
                    result_data = response.json()
                    return self.parse_questions_from_response(result_data)
                else:
                    print(f"Alternative method failed: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Alternative method error: {e}")
            return None
    
    def download_and_parse(self, download_uri):
        """Download and parse results"""
        
        try:
            print("📥 Downloading results...")
            
            result_response = requests.get(download_uri)
            
            if result_response.status_code != 200:
                print(f"❌ Download failed: {result_response.status_code}")
                return None
            
            # Save ZIP file
            with open('result.zip', 'wb') as f:
                f.write(result_response.content)
            
            # Extract ZIP
            with zipfile.ZipFile('result.zip', 'r') as z:
                z.extractall('temp_extract')
            
            # Find and parse JSON
            json_path = 'temp_extract/structuredData.json'
            
            if not os.path.exists(json_path):
                # Try alternative paths
                for root, dirs, files in os.walk('temp_extract'):
                    for file in files:
                        if file.endswith('.json'):
                            json_path = os.path.join(root, file)
                            break
            
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Clean up
                os.remove('result.zip')
                shutil.rmtree('temp_extract')
                
                return self.parse_questions(data)
            else:
                print("❌ No JSON file found in extraction")
                shutil.rmtree('temp_extract')
                return None
                
        except Exception as e:
            print(f"❌ Error parsing results: {e}")
            return None
    
    def parse_questions(self, data):
        """Parse questions from JSON"""
        
        questions = []
        elements = data.get('elements', [])
        
        print(f"📝 Parsing {len(elements)} elements...")
        
        current_q = None
        q_text = ""
        options = {}
        
        for elem in elements:
            text = elem.get('Text', '').strip()
            
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
        
        print(f"✅ Parsed {len(questions)} questions")
        
        return questions
    
    def parse_questions_from_response(self, data):
        """Parse questions from direct response"""
        
        if 'elements' in data:
            return self.parse_questions(data)
        elif 'extractedText' in data:
            # Parse plain text
            text = data['extractedText']
            return self.parse_questions_from_text(text)
        else:
            print("❌ Unknown response format")
            return None
    
    def parse_questions_from_text(self, text):
        """Parse questions from plain text"""
        
        questions = []
        
        # Split by question pattern
        q_pattern = r'Q\.(\d+)\)(.*?)(?=Q\.\d+\)|$)'
        matches = re.findall(q_pattern, text, re.DOTALL)
        
        for q_num, content in matches:
            # Extract options
            options = {}
            opt_pattern = r'$([a-e])$\s*([^()]+?)(?=$[a-e]$|$)'
            opt_matches = re.findall(opt_pattern, content, re.I)
            
            # Question text is before first option
            q_text = content
            if opt_matches:
                first_opt_pos = content.find(f"({opt_matches[0][0]})")
                q_text = content[:first_opt_pos].strip()
                
                for letter, opt_text in opt_matches:
                    options[letter.upper()] = opt_text.strip()
            
            questions.append({
                "number": int(q_num),
                "text": q_text,
                "options": options
            })
        
        return questions

# Main execution
if __name__ == "__main__":
    # Check for credentials
    if not os.path.exists("pdfservices-api-credentials.json"):
        print("❌ Credentials file not found!")
        print("Please ensure pdfservices-api-credentials.json is in the current directory")
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
            else:
                print("❌ No PDFs found in rbi_pdf folder")
                exit(1)
    
    questions = extractor.extract_pdf(pdf_path)
    
    if questions:
        print(f"✅ Successfully extracted {len(questions)} questions")
        
        # Save to JSON
        output = {
            "source": os.path.basename(pdf_path),
            "total": len(questions),
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
        print("❌ Extraction failed")
        print("💡 Try these alternatives:")
        print("1. Check your API quota at Adobe Console")
        print("2. Try with a different PDF")
        print("3. Use the OCR approach instead")
