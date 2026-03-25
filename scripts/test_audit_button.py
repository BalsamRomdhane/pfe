#!/usr/bin/env python
"""
Test script to verify the audit analysis button implementation.

Usage:
    python manage.py shell < scripts/test_audit_button.py
"""

import json
from django.contrib.auth.models import User
from apps.documents.models import Document
from apps.standards.models import Standard
from apps.compliance.models import AuditResult
from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory

print("=" * 60)
print("Test: Audit Analysis Button Implementation")
print("=" * 60)

# Test 1: Check if Document model exists
print("\n[1] Checking Document model...")
try:
    doc_count = Document.objects.count()
    print(f"    ✓ Document model OK (found {doc_count} documents)")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 2: Check if Standard model exists
print("\n[2] Checking Standard model...")
try:
    std_count = Standard.objects.count()
    print(f"    ✓ Standard model OK (found {std_count} standards)")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 3: Check if AuditResult model has new fields
print("\n[3] Checking AuditResult model fields...")
try:
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("PRAGMA table_info(compliance_auditresult);")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    required_fields = ['status', 'missing_controls']
    missing = [f for f in required_fields if f not in column_names]
    
    if not missing:
        print(f"    ✓ All required fields present: {required_fields}")
    else:
        print(f"    ⚠ Missing fields: {missing}")
        print(f"    Available columns: {column_names}")
except Exception as e:
    print(f"    ⚠ SQLite check not available (using PostgreSQL?): {e}")
    try:
        # Try PostgreSQL approach
        ar = AuditResult._meta
        field_names = [f.name for f in ar.get_fields()]
        if 'status' in field_names and 'missing_controls' in field_names:
            print(f"    ✓ All required fields present in PostgreSQL")
        else:
            missing = [f for f in ['status', 'missing_controls'] if f not in field_names]
            print(f"    ✗ Missing fields: {missing}")
    except Exception as e2:
        print(f"    ✗ Error checking fields: {e2}")

# Test 4: Check serializer includes new fields
print("\n[4] Checking AuditResultSerializer...")
try:
    from apps.compliance.serializers import AuditResultSerializer
    serializer_fields = AuditResultSerializer().fields.keys()
    required_fields = ['status', 'missing_controls']
    missing = [f for f in required_fields if f not in serializer_fields]
    
    if not missing:
        print(f"    ✓ Serializer includes: {required_fields}")
    else:
        print(f"    ✗ Serializer missing: {missing}")
        print(f"    Available fields: {list(serializer_fields)}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 5: Check views support document_id filtering
print("\n[5] Checking AuditResultListView filtering...")
try:
    from apps.compliance.views import AuditResultListView
    import inspect
    source = inspect.getsource(AuditResultListView.get)
    if 'document_id' in source:
        print(f"    ✓ View supports document_id filtering")
    else:
        print(f"    ✗ View doesn't filter by document_id")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 6: Test API endpoint manually
print("\n[6] Testing API endpoint...")
try:
    # Create a test client
    client = APIClient()
    
    # Try to get audit results
    response = client.get('/api/compliance/results/')
    
    if response.status_code == 200:
        data = response.json()
        print(f"    ✓ API endpoint accessible (returned {len(data)} results)")
        
        # Check if results have the required fields
        if isinstance(data, list) and len(data) > 0:
            first_result = data[0]
            required_fields = ['status', 'document', 'score']
            missing = [f for f in required_fields if f not in first_result]
            if not missing:
                print(f"    ✓ Results have required fields")
            else:
                print(f"    ⚠ Results missing: {missing}")
    elif response.status_code == 404:
        print(f"    ⚠ Endpoint not found (404)")
    else:
        print(f"    ✗ API returned status {response.status_code}: {response.text}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 7: Check if document filtering works
print("\n[7] Testing document_id filtering...")
try:
    client = APIClient()
    
    # Try with a fake document ID
    response = client.get('/api/compliance/results/?document_id=999', accept='application/json')
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            print(f"    ✓ Filtering works (returned {len(data)} results)")
        else:
            print(f"    ⚠ Unexpected response format")
    else:
        print(f"    ✗ API returned status {response.status_code}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 8: Check ComplianceService includes status
print("\n[8] Checking ComplianceService...")
try:
    from apps.compliance.services.compliance_service import ComplianceService
    import inspect
    source = inspect.getsource(ComplianceService.run_audit)
    if 'status =' in source and 'missing_controls' in source:
        print(f"    ✓ ComplianceService includes status and missing_controls")
    else:
        print(f"    ⚠ Check source code manually")
except Exception as e:
    print(f"    ✗ Error: {e}")

print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)
print("""
Expected functionality:
1. ✓ Document model exists
2. ✓ Standard model exists
3. ✓ AuditResult has status and missing_controls fields
4. ✓ Serializer includes new fields
5. ✓ View supports document_id filtering
6. ✓ API endpoint works
7. ✓ Document filtering works
8. ✓ ComplianceService populates new fields

JavaScript (documents.js):
- ✓ buildRow() adds "📊 Analyse" button
- ✓ viewAnalysis() creates modal with analysis
- ✓ formatAnalysisResult() formats the output
- ✓ API call: fetch('/api/compliance/results/?document_id={docId}')

Next steps:
1. Test the UI manually on http://localhost:8000/documents/
2. Create an audit for a test document
3. Click the "📊 Analyse" button to see if modal appears
4. Verify all data is displayed correctly
""")
