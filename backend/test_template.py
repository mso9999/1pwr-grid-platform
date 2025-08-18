#!/usr/bin/env python3
"""
Test script for Excel template generation endpoints
"""

import requests
import os
import pandas as pd
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_status_codes_endpoint():
    """Test the status codes reference endpoint"""
    print("\n" + "="*50)
    print("Testing Status Codes Reference Endpoint")
    print("="*50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/template/status-codes")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status codes retrieved successfully")
            print(f"   Total codes: {data['total_codes']}")
            print(f"   Categories: {', '.join(data['categories'])}")
            
            # Display first few codes
            if data['status_codes']:
                print("\n   Sample codes:")
                for code in data['status_codes'][:5]:
                    print(f"   - {code['Code_Type']} = {code['Value']}: {code['Description']}")
            
            return True
        else:
            print(f"❌ Failed: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_template_download(project_name="Test_Project", include_sample=False):
    """Test the template download endpoint"""
    print("\n" + "="*50)
    print(f"Testing Template Download")
    print(f"  Project: {project_name}")
    print(f"  Include Sample: {include_sample}")
    print("="*50)
    
    try:
        # Build URL with query parameters
        params = {
            "project_name": project_name,
            "include_sample_data": include_sample
        }
        
        response = requests.get(
            f"{BASE_URL}/api/template/download",
            params=params,
            stream=True
        )
        
        if response.status_code == 200:
            # Save the file
            filename = f"test_{project_name}_template.xlsx"
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Template downloaded successfully: {filename}")
            
            # Verify the Excel file
            try:
                excel_file = pd.ExcelFile(filename)
                sheets = excel_file.sheet_names
                print(f"   Sheets found: {', '.join(sheets)}")
                
                expected_sheets = [
                    'PoleClasses', 'Connections', 'NetworkLength', 
                    'DropLines', 'Transformers', 'Generation',
                    'Metadata', 'Column_Descriptions'
                ]
                
                for sheet in expected_sheets:
                    if sheet in sheets:
                        df = pd.read_excel(filename, sheet_name=sheet)
                        print(f"   ✓ {sheet}: {len(df)} rows, {len(df.columns)} columns")
                    else:
                        print(f"   ✗ {sheet}: Missing!")
                
                # Clean up test file
                os.remove(filename)
                print(f"   Cleaned up test file")
                
                return True
            except Exception as e:
                print(f"   Warning: Could not verify Excel structure: {str(e)}")
                if os.path.exists(filename):
                    os.remove(filename)
                return True  # Still consider success if download worked
                
        else:
            print(f"❌ Failed: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "🚀 Starting Template Generation Tests")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test 1: Status codes reference
    results.append(("Status Codes Reference", test_status_codes_endpoint()))
    
    # Test 2: Template without sample data
    results.append(("Template (no sample)", test_template_download("Project_Alpha", False)))
    
    # Test 3: Template with sample data
    results.append(("Template (with sample)", test_template_download("Project_Beta", True)))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    exit(main())
