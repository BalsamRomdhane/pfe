"""Seed the database with example standards and controls.

Run with:
  python manage.py seed_standards

This is helpful for local development to quickly populate the system with
an example standard and a handful of controls.
"""

from django.core.management.base import BaseCommand

from apps.standards.models import Control, Standard


class Command(BaseCommand):
    help = "Seed the database with sample compliance standards and controls."

    def handle(self, *args, **options):
        standard_data = {
            "name": "ISO 9001",
            "description": "Quality management standard focusing on consistent processes and continual improvement.",
        }

        standard, created = Standard.objects.get_or_create(
            name=standard_data["name"], defaults={"description": standard_data["description"]}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created standard: {standard.name}"))
        else:
            self.stdout.write(self.style.WARNING(f"Standard already exists: {standard.name}"))

        controls = [
            {
                "identifier": "1.1",
                "description": "The document must be clearly identifiable with title, version, and date.",
            },
            {
                "identifier": "1.2",
                "description": "Documents are reviewed, approved, and signed by the responsible authority.",
            },
            {
                "identifier": "1.3",
                "description": "Version control is maintained: obsolete versions are removed and history is kept.",
            },
            {
                "identifier": "1.4",
                "description": "Documents are accessible to relevant personnel when needed.",
            },
            {
                "identifier": "1.5",
                "description": "Documentation is clear, readable, and understandable by the intended audience.",
            },
            {
                "identifier": "1.6",
                "description": "Documents are protected against loss, unauthorized change, and deterioration.",
            },
            {
                "identifier": "1.7",
                "description": "Documents are reviewed and updated regularly to remain compliant.",
            },
        ]

        created_controls = 0
        for ctl in controls:
            obj, exists = Control.objects.get_or_create(
                standard=standard,
                identifier=ctl["identifier"],
                defaults={"description": ctl["description"]},
            )
            if exists:
                created_controls += 1

        self.stdout.write(self.style.SUCCESS(f"Ensured {created_controls} controls exist for {standard.name}."))
        self.stdout.write(self.style.SUCCESS("Seed data complete."))
