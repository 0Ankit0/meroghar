import os
from pathlib import Path

APPS_DIR = Path("apps")
APPS = [
    "core", "iam", "properties", "tenants", "leases", 
    "billing", "payments", "maintenance", "documents", 
    "notifications", "reporting"
]

SUB_PACKAGES = ["models", "api", "serializers", "views", "services", "admin", "migrations"]

def create_app_structure():
    if not APPS_DIR.exists():
        os.makedirs(APPS_DIR)
    
    # Create __init__.py for apps dir
    (APPS_DIR / "__init__.py").touch()
    
    for app in APPS:
        app_path = APPS_DIR / app
        if not app_path.exists():
            os.makedirs(app_path)
            
        # Create app level files
        (app_path / "__init__.py").touch()
        (app_path / "apps.py").write_text(f"""from django.apps import AppConfig

class {app.capitalize()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{app}'
""")
        (app_path / "urls.py").write_text("from django.urls import path\n\nurlpatterns = []\n")

        # Create sub-packages
        for package in SUB_PACKAGES:
            pkg_path = app_path / package
            if not pkg_path.exists():
                os.makedirs(pkg_path)
            (pkg_path / "__init__.py").touch()
            
        print(f"Created app structure for: {app}")

if __name__ == "__main__":
    create_app_structure()
