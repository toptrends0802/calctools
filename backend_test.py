#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import io
import tempfile
from pathlib import Path

class MobileToolsHubAPITester:
    def __init__(self, base_url="https://31f6b30b-2770-49a5-bd1d-22cb4e7f64b5.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            self.failed_tests.append(f"{name}: {details}")
            print(f"❌ {name} - FAILED: {details}")

    def run_get_test(self, name, endpoint, expected_status=200):
        """Run a GET request test"""
        url = f"{self.base_url}/api/{endpoint}"
        try:
            print(f"\n🔍 Testing {name}...")
            print(f"   URL: {url}")
            
            response = requests.get(url, timeout=10)
            success = response.status_code == expected_status
            
            if success:
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)}")
                except:
                    print(f"   Response: {response.text}")
            
            self.log_test(name, success, f"Expected {expected_status}, got {response.status_code}")
            return success, response
            
        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, None

    def run_post_test(self, name, endpoint, data=None, files=None, expected_status=200):
        """Run a POST request test"""
        url = f"{self.base_url}/api/{endpoint}"
        try:
            print(f"\n🔍 Testing {name}...")
            print(f"   URL: {url}")
            
            if files:
                response = requests.post(url, files=files, data=data, timeout=30)
            else:
                headers = {'Content-Type': 'application/json'} if data else {}
                response = requests.post(url, json=data, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        data = response.json()
                        print(f"   Response: {json.dumps(data, indent=2)}")
                    else:
                        print(f"   Response: Binary data ({len(response.content)} bytes)")
                except:
                    print(f"   Response: {response.text[:200]}...")
            
            self.log_test(name, success, f"Expected {expected_status}, got {response.status_code}")
            return success, response
            
        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, None

    def create_test_pdf(self):
        """Create a simple test PDF file"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.drawString(100, 750, "Test PDF Document")
            p.drawString(100, 700, "This is a test PDF for API testing")
            p.showPage()
            p.save()
            buffer.seek(0)
            return buffer.getvalue()
        except ImportError:
            # Fallback: create a minimal PDF manually
            pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
            return pdf_content

    def create_test_image(self):
        """Create a simple test image"""
        try:
            from PIL import Image
            
            # Create a simple 100x100 red image
            img = Image.new('RGB', (100, 100), color='red')
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            return buffer.getvalue()
        except ImportError:
            # Return a minimal PNG
            return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x02\x00\x00\x00\xff\x80\x02\x03\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x00\x0eIDATx\xdac\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

    def test_basic_endpoints(self):
        """Test basic API endpoints"""
        print("\n" + "="*50)
        print("TESTING BASIC ENDPOINTS")
        print("="*50)
        
        # Test health check
        self.run_get_test("Health Check", "")
        
        # Test status endpoints
        self.run_post_test(
            "Create Status Check", 
            "status", 
            {"client_name": "test_client"}, 
            expected_status=200
        )
        
        self.run_get_test("Get Status Checks", "status")

    def test_analytics_endpoints(self):
        """Test analytics endpoints"""
        print("\n" + "="*50)
        print("TESTING ANALYTICS ENDPOINTS")
        print("="*50)
        
        self.run_get_test("PDF Analytics", "analytics/pdf")
        self.run_get_test("Image Analytics", "analytics/image")
        self.run_get_test("Conversion Analytics", "analytics/conversions")

    def test_pdf_endpoints(self):
        """Test PDF processing endpoints"""
        print("\n" + "="*50)
        print("TESTING PDF ENDPOINTS")
        print("="*50)
        
        # Create test PDF
        pdf_content = self.create_test_pdf()
        
        # Test PDF merge (need at least 2 files)
        files = {
            'files': [
                ('test1.pdf', pdf_content, 'application/pdf'),
                ('test2.pdf', pdf_content, 'application/pdf')
            ]
        }
        self.run_post_test("PDF Merge", "pdf/merge", files=files, expected_status=200)
        
        # Test PDF split
        files = {'file': ('test.pdf', pdf_content, 'application/pdf')}
        self.run_post_test("PDF Split", "pdf/split/1", files=files, expected_status=200)

    def test_image_endpoints(self):
        """Test image processing endpoints"""
        print("\n" + "="*50)
        print("TESTING IMAGE ENDPOINTS")
        print("="*50)
        
        # Create test image
        image_content = self.create_test_image()
        
        # Test image rotation - use query parameters
        files = {'file': ('test.png', image_content, 'image/png')}
        url = f"{self.base_url}/api/image/rotate?rotation=90"
        try:
            print(f"\n🔍 Testing Image Rotate...")
            print(f"   URL: {url}")
            response = requests.post(url, files=files, timeout=30)
            success = response.status_code == 200
            self.log_test("Image Rotate", success, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_test("Image Rotate", False, f"Exception: {str(e)}")
        
        # Test image resize - use query parameters
        files = {'file': ('test.png', image_content, 'image/png')}
        url = f"{self.base_url}/api/image/resize?width=50&height=50"
        try:
            print(f"\n🔍 Testing Image Resize...")
            print(f"   URL: {url}")
            response = requests.post(url, files=files, timeout=30)
            success = response.status_code == 200
            self.log_test("Image Resize", success, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_test("Image Resize", False, f"Exception: {str(e)}")

    def test_conversion_endpoints(self):
        """Test unit conversion endpoints"""
        print("\n" + "="*50)
        print("TESTING CONVERSION ENDPOINTS")
        print("="*50)
        
        # Test length conversion - use query parameters
        url = f"{self.base_url}/api/convert?category=length&from_unit=meter&to_unit=feet&value=1.0&country=US"
        try:
            print(f"\n🔍 Testing Length Conversion...")
            print(f"   URL: {url}")
            response = requests.post(url, timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            self.log_test("Length Conversion", success, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_test("Length Conversion", False, f"Exception: {str(e)}")
        
        # Test weight conversion
        url = f"{self.base_url}/api/convert?category=weight&from_unit=kilogram&to_unit=pound&value=1.0&country=US"
        try:
            print(f"\n🔍 Testing Weight Conversion...")
            print(f"   URL: {url}")
            response = requests.post(url, timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            self.log_test("Weight Conversion", success, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_test("Weight Conversion", False, f"Exception: {str(e)}")
        
        # Test temperature conversion
        url = f"{self.base_url}/api/convert?category=temperature&from_unit=celsius&to_unit=fahrenheit&value=0.0&country=US"
        try:
            print(f"\n🔍 Testing Temperature Conversion...")
            print(f"   URL: {url}")
            response = requests.post(url, timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            self.log_test("Temperature Conversion", success, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_test("Temperature Conversion", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Mobile Tools Hub API Tests")
        print(f"📡 Testing against: {self.base_url}")
        
        try:
            self.test_basic_endpoints()
            self.test_analytics_endpoints()
            self.test_pdf_endpoints()
            self.test_image_endpoints()
            self.test_conversion_endpoints()
        except KeyboardInterrupt:
            print("\n⚠️ Tests interrupted by user")
        except Exception as e:
            print(f"\n💥 Unexpected error: {str(e)}")
        
        # Print summary
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        
        if self.failed_tests:
            print("\n🔍 Failed Tests:")
            for failure in self.failed_tests:
                print(f"   • {failure}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main function"""
    tester = MobileToolsHubAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())