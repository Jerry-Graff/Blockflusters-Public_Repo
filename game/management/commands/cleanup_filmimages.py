from django.core.management.base import BaseCommand
from game.models import FilmImage
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Cleans up FilmImage entries, retaining a specified number per tier.'

    def handle(self, *args, **kwargs):
        try:
            with transaction.atomic():
                # Define tiers and the number of images to keep in each
                tiers_to_keep = {
                    'Easy': 15,
                    'Medium': 20,
                    'Hard': 15
                }
                
                for tier, keep_count in tiers_to_keep.items():
                    # Fetch all images for the current tier, ordered by ID (ascending)
                    tier_images = FilmImage.objects.filter(tier=tier).order_by('id')
                    
                    # Count total images in the tier
                    total_images = tier_images.count()
                    self.stdout.write(f"Tier '{tier}': {total_images} total images.")
                    
                    if total_images > keep_count:
                        # Identify images to delete (those beyond the keep_count)
                        # Instead of slicing the QuerySet directly, fetch the IDs first
                        images_to_delete_qs = tier_images[keep_count:]
                        ids_to_delete = list(images_to_delete_qs.values_list('id', flat=True))
                        
                        delete_count = len(ids_to_delete)
                        
                        # Log which images are being deleted
                        self.stdout.write(f"Deleting {delete_count} images from tier '{tier}'.")
                        
                        # Perform deletion based on IDs
                        FilmImage.objects.filter(id__in=ids_to_delete).delete()
                        
                        self.stdout.write(self.style.SUCCESS(f"Successfully deleted {delete_count} images from tier '{tier}'."))
                    else:
                        self.stdout.write(f"No images deleted from tier '{tier}' as total images ({total_images}) <= keep_count ({keep_count}).")
        
            self.stdout.write(self.style.SUCCESS('FilmImage cleanup completed successfully.'))
        
        except Exception as e:
            logger.error(f"An error occurred during FilmImage cleanup: {e}")
            self.stdout.write(self.style.ERROR('FilmImage cleanup failed.'))