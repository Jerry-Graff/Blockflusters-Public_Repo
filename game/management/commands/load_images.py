from django.core.management.base import BaseCommand
from django.core.files import File
from game.models import FilmImage
import csv
import os


class Command(BaseCommand):
    help = 'Load film images and metadata from CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')
        parser.add_argument('images_dir', type=str, help='Directory containing images')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        images_dir = kwargs['images_dir']

        # List all files in images_dir for verification
        self.stdout.write(f"Contents of images_dir ({images_dir}):")
        for root, dirs, files in os.walk(images_dir):
            for file in files:
                self.stdout.write(f"- {file}")

        with open(csv_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                title = row.get('title', '').strip()
                image_filename = os.path.basename(row.get('image_filename', '').strip())
                tier = row.get('tier', '').strip()
                frame = row.get('frame', '').strip()
                hint_1 = row.get('hint_1', '').strip() if row.get('hint_1') else None
                hint_2 = row.get('hint_2', '').strip() if row.get('hint_2') else None

                image_path = os.path.join(images_dir, image_filename)
                abs_image_path = os.path.abspath(image_path)

                if not os.path.exists(image_path):
                    self.stderr.write(f"Image file not found: {abs_image_path}")
                    continue

                with open(image_path, 'rb') as img_file:
                    film_image = FilmImage(
                        title=title,
                        tier=tier,
                        frame=frame,
                        hint_1=hint_1,
                        hint_2=hint_2,
                    )
                    film_image.image = File(img_file, name=image_filename)
                    film_image.save()
                    self.stdout.write(f"Loaded image for {title} ({frame})")