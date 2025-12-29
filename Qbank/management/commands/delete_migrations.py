import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Deletes all migration files (excluding __init__.py) from all apps.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput',
            '--no-input',
            action='store_false',
            dest='interactive',
            help='Tells Django to NOT prompt the user for input of any kind.',
        )

    def handle(self, *args, **options):
        interactive = options['interactive']
        
        if interactive:
            self.stdout.write(self.style.WARNING("This will delete all migration files (excluding __init__.py) in the project."))
            confirmation = input("Are you sure you want to proceed? (y/n): ")
            if confirmation.lower() != 'y':
                self.stdout.write(self.style.ERROR("Operation cancelled."))
                return

        base_dir = settings.BASE_DIR
        self.stdout.write(f"Scanning {base_dir} for migration files...")
        
        count = 0
        for root, dirs, files in os.walk(base_dir):
            if 'migrations' in dirs:
                migrations_dir = os.path.join(root, 'migrations')
                # Skip if it's inside venv or .git (though settings.BASE_DIR usually excludes them if set correctly, os.walk goes deep)
                if 'venv' in root or '.git' in root:
                    continue
                
                # Verify it's a python package (has __init__.py) or just a folder
                # We just clean it regardless if it's named migrations
                
                self.stdout.write(f"Cleaning {migrations_dir}...")
                for filename in os.listdir(migrations_dir):
                    file_path = os.path.join(migrations_dir, filename)
                    
                    if filename == '__init__.py':
                        continue
                    
                    if filename.endswith('.py'):
                        try:
                            os.remove(file_path)
                            self.stdout.write(f"  Deleted {filename}")
                            count += 1
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"  Failed to delete {filename}: {e}"))
                    
                    elif filename == '__pycache__':
                        try:
                            shutil.rmtree(file_path)
                            self.stdout.write(f"  Deleted __pycache__")
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"  Failed to delete __pycache__: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Done. Deleted {count} migration files."))
