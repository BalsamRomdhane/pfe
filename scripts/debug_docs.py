import os
import sys

# Ensure project root is on sys.path so Django settings and apps can be imported.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# Ensure we use sqlite to avoid psycopg dependency in this environment.
os.environ.setdefault('DJANGO_USE_SQLITE', '1')

import django

django.setup()

from django.test import RequestFactory
from apps.documents.views import DocumentListView

request = RequestFactory().get('/api/documents/')
response = DocumentListView.as_view()(request)
print('status', response.status_code)
print(response.content.decode('utf-8'))
