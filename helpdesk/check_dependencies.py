#!/usr/bin/env python
"""
Dependency Checker for HelpDesk Application
Checks and installs missing dependencies
"""

import sys
import subprocess
import pkg_resources

# Required packages and versions
REQUIRED_PACKAGES = {
    'Django': '4.2.7',
    'djangorestframework': '3.14.0',
    'Pillow': '10.4.0',
    'django-crispy-forms': '2.1',
    'crispy-bootstrap5': '0.7',
    'django-filter': '23.3',
    'requests': '2.31.0',
    'python-dotenv': '1.0.0',
    'gunicorn': '21.2.0',
    'psycopg2-binary': '2.9.9'
}

def check_package(package_name, required_version):
    """Check if a package is installed with correct version"""
    try:
        installed_version = pkg_resources.get_distribution(package_name).version
        if pkg_resources.parse_version(installed_version) >= pkg_resources.parse_version(required_version):
            return True, installed_version
        else:
            return False, installed_version
    except pkg_resources.DistributionNotFound:
        return False, None

def install_package(package_name, version):
    """Install a specific package version"""
    print(f"Installing {package_name}=={version}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", f"{package_name}=={version}"])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("=" * 60)
    print("HelpDesk Dependency Checker")
    print("=" * 60)
    
    missing_packages = []
    outdated_packages = []
    
    # Check all required packages
    for package, required_version in REQUIRED_PACKAGES.items():
        is_installed, installed_version = check_package(package, required_version)
        
        if not is_installed:
            if installed_version is None:
                print(f"❌ {package} is NOT installed")
                missing_packages.append((package, required_version))
            else:
                print(f"⚠️  {package} {installed_version} is installed but {required_version} is required")
                outdated_packages.append((package, required_version, installed_version))
        else:
            print(f"✅ {package} {installed_version} is installed (required: {required_version})")
    
    print("\n" + "=" * 60)
    
    if not missing_packages and not outdated_packages:
        print("All dependencies are satisfied! 🎉")
        return 0
    
    # Ask user if they want to install missing packages
    if missing_packages or outdated_packages:
        print("\nMissing/Outdated packages found:")
        for package, version in missing_packages:
            print(f"  - {package}=={version} (not installed)")
        for package, required_version, installed_version in outdated_packages:
            print(f"  - {package}=={required_version} (installed: {installed_version})")
        
        response = input("\nDo you want to install/update these packages? (y/n): ").lower().strip()
        
        if response == 'y':
            print("\nInstalling packages...")
            
            # Install missing packages first
            for package, version in missing_packages:
                if not install_package(package, version):
                    print(f"Failed to install {package}")
                    return 1
            
            # Update outdated packages
            for package, required_version, _ in outdated_packages:
                if not install_package(package, required_version):
                    print(f"Failed to update {package}")
                    return 1
            
            print("\n✅ All packages installed successfully!")
            print("\nNext steps:")
            print("1. Run migrations: python manage.py migrate")
            print("2. Create superuser: python manage.py createsuperuser")
            print("3. Run server: python manage.py runserver")
        else:
            print("\nInstallation cancelled.")
            print("\nYou can install manually with:")
            print("pip install -r requirements.txt")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())