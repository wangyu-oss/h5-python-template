import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

import django

django.setup()

from server.seed import run

if __name__ == '__main__':
    print(run())
