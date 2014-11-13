import sys
import os

test_dir = os.path.dirname(__file__)
project_dir = os.path.abspath(os.path.join(test_dir, '../..'))

sys.path.insert(0, test_dir)
sys.path.insert(0, project_dir)

DEBUG=True
DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

ROOT_URLCONF='promote_content.urls'

INSTALLED_APPS=('django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.admin',
                'promote_content',
)
SECRET_KEY = '5-*-_t#&arg*mye1-48hv*c+pqsy6vlk2p=hp*6cezmiihiigh'
