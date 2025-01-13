from django.db import models
from PIL import Image
from django.contrib.postgres.fields import ArrayField


class FilmImage(models.Model):

    FRAME_CHOICES = [
        ("first", "First Frame"),
        ("last", "Last Frame")
    ]

    TIER_CHOICES = [
        ("Easy", "easy"),
        ("Medium", "medium"),
        ("Hard", "hard")
    ]

    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='film_images/')
    tier = models.CharField(max_length=6, choices=TIER_CHOICES)
    frame = models.CharField(max_length=6, choices=FRAME_CHOICES, default='first')
    hint_1 = models.CharField(max_length=255, blank=True, null=True)
    hint_2 = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img_path = self.image.path
        img = Image.open(img_path)
        original_width, original_height = img.size

        max_width = 1080
        max_height = 400

        # Calculate scaling factor while maintaining aspect ratio
        scaling_factor = min(max_width / original_width, max_height / original_height, 1)  # Prevent upscaling
        new_size = (int(original_width * scaling_factor), int(original_height * scaling_factor))

        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = Image.LANCZOS

        img = img.resize(new_size, resample=resample_filter)
        img.save(img_path)


class GameSession(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    score = models.PositiveIntegerField(default=0)
    time_remaining = models.PositiveIntegerField(default=90)
    images_remaining = models.ManyToManyField(FilmImage, related_name='sessions')
    current_tier_shown = ArrayField(models.IntegerField(), default=list, blank=True)
    frame_mode = models.CharField(max_length=5, choices=FilmImage.FRAME_CHOICES, default='first')
    last_active = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session: {self.session_id} - Mode: {self.get_frame_mode_display()}"