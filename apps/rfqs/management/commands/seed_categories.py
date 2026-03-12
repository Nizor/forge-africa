from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.rfqs.models import ServiceCategory


CATEGORIES = [
    ('3D Printing', '🖨️', 'FDM, SLA, SLS and other additive manufacturing services'),
    ('Laser Cutting', '⚡', 'CO2 and fiber laser cutting for metal, acrylic, wood and more'),
    ('CNC Machining', '⚙️', 'CNC milling, turning, drilling and routing services'),
    ('Product Design', '✏️', 'Industrial and mechanical product design and engineering'),
    ('Prototyping', '🔬', 'Rapid prototype development and design validation'),
    ('Welding & Fabrication', '🔥', 'MIG, TIG, arc welding and structural metal fabrication'),
    ('Injection Moulding', '🧪', 'Plastic injection moulding and tooling'),
    ('Sheet Metal Fabrication', '🔩', 'Bending, punching, forming and sheet metal assembly'),
    ('PCB Assembly', '💡', 'Electronics PCB assembly, soldering and testing'),
    ('Casting & Forging', '🏭', 'Sand casting, die casting, and metal forging'),
    ('Finishing & Coating', '🎨', 'Powder coating, anodizing, sandblasting and painting'),
    ('Electronics & Wiring', '🔌', 'Wiring harness production and electronic assembly'),
]


class Command(BaseCommand):
    help = 'Seed default service categories into the database'

    def handle(self, *args, **kwargs):
        created_count = 0
        for name, icon, description in CATEGORIES:
            obj, created = ServiceCategory.objects.get_or_create(
                slug=slugify(name),
                defaults={
                    'name': name,
                    'icon': icon,
                    'description': description,
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {name}'))
            else:
                self.stdout.write(f'  — Already exists: {name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {created_count} new categories created.'
        ))
