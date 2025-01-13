import io
import os
import tempfile
from PIL import Image
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from game.models import FilmImage, GameSession


def get_temporary_image(name='test.jpg', ext='JPEG', size=(100, 100), color=(255, 0, 0)):
    """
    Generates a temporary image for testing purposes.
    """
    file = io.BytesIO()
    image = Image.new('RGB', size=size, color=color)
    image.save(file, ext)
    file.seek(0)
    return SimpleUploadedFile(name, file.read(), content_type='image/jpeg')


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class FilmImageModelTest(TestCase):
    def setUp(self):
        # Create a dummy image
        self.image = get_temporary_image()

    def test_create_film_image_with_valid_data(self):
        """
        Test that a FilmImage instance is created successfully with valid data.
        """
        film_image = FilmImage.objects.create(
            title='Inception',
            image=self.image,
            tier='Easy',
            frame='first',
            hint_1='First hint',
            hint_2='Second hint'
        )
        self.assertEqual(film_image.title, 'Inception')
        self.assertEqual(film_image.tier, 'Easy')
        self.assertEqual(film_image.frame, 'first')
        self.assertEqual(film_image.hint_1, 'First hint')
        self.assertEqual(film_image.hint_2, 'Second hint')

        # Adjusted assertion to account for unique suffixes
        image_basename = os.path.basename(film_image.image.name)
        self.assertTrue(image_basename.startswith('test') and image_basename.endswith('.jpg'),
                        f"Image name '{image_basename}' does not start with 'test' or end with '.jpg'")

        # Optionally, verify the upload_to path
        self.assertTrue(film_image.image.name.startswith('film_images/'),
                        f"Image path '{film_image.image.name}' does not start with 'film_images/'")

    def test_str_method(self):
        """
        Test that the __str__ method returns the title of the FilmImage.
        """
        film_image = FilmImage.objects.create(
            title='The Godfather',
            image=self.image,
            tier='Medium',
            frame='last'
        )
        self.assertEqual(str(film_image), 'The Godfather')

    def test_tier_choices_enforcement(self):
        """
        Test that assigning an invalid tier choice raises a ValidationError.
        """
        film_image = FilmImage(
            title='Interstellar',
            image=self.image,
            tier='Impossible',  # Invalid choice
            frame='first'
        )
        with self.assertRaises(ValidationError):
            film_image.full_clean()  # This triggers model validation

    def test_frame_choices_enforcement(self):
        """
        Test that assigning an invalid frame choice raises a ValidationError.
        """
        film_image = FilmImage(
            title='Pulp Fiction',
            image=self.image,
            tier='Hard',
            frame='middle'  # Invalid choice
        )
        with self.assertRaises(ValidationError):
            film_image.full_clean()

    def test_hint_fields_optional(self):
        """
        Test that hint_1 and hint_2 can be blank or null.
        """
        film_image = FilmImage.objects.create(
            title='Fight Club',
            image=self.image,
            tier='Medium',
            frame='first'
            # No hints provided
        )
        self.assertIsNone(film_image.hint_1)
        self.assertIsNone(film_image.hint_2)


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class GameSessionModelTest(TestCase):
    def setUp(self):
        # Create FilmImage instances to associate with GameSession
        self.image1 = FilmImage.objects.create(
            title='The Matrix',
            image=get_temporary_image(name='matrix.jpg'),
            tier='Easy',
            frame='first'
        )
        self.image2 = FilmImage.objects.create(
            title='The Dark Knight',
            image=get_temporary_image(name='dark_knight.jpg'),
            tier='Hard',
            frame='last'
        )

    def test_create_game_session_with_valid_data(self):
        """
        Test that a GameSession instance is created successfully with valid data.
        """
        session = GameSession.objects.create(
            session_id='session_12345',
            score=150,
            time_remaining=60,
            frame_mode='last'
        )
        session.images_remaining.set([self.image1, self.image2])
        self.assertEqual(session.session_id, 'session_12345')
        self.assertEqual(session.score, 150)
        self.assertEqual(session.time_remaining, 60)
        self.assertEqual(session.frame_mode, 'last')
        self.assertEqual(session.images_remaining.count(), 2)

    def test_str_method(self):
        """
        Test that the __str__ method returns the correct string representation.
        """
        session = GameSession.objects.create(
            session_id='session_67890',
            frame_mode='first'
        )
        expected_str = f"Session: session_67890 - Mode: First Frame"
        self.assertEqual(str(session), expected_str)

    def test_session_id_uniqueness(self):
        """
        Test that the session_id field enforces uniqueness.
        """
        GameSession.objects.create(
            session_id='unique_session',
            frame_mode='first'
        )
        with self.assertRaises(IntegrityError):
            GameSession.objects.create(
                session_id='unique_session',  # Duplicate ID
                frame_mode='last'
            )

    def test_default_values(self):
        """
        Test that default values are correctly set for score, time_remaining, and frame_mode.
        """
        session = GameSession.objects.create(
            session_id='default_session'
        )
        self.assertEqual(session.score, 0)
        self.assertEqual(session.time_remaining, 90)
        self.assertEqual(session.frame_mode, 'first')

    def test_frame_mode_choices_enforcement(self):
        """
        Test that assigning an invalid frame_mode choice raises a ValidationError.
        """
        session = GameSession(
            session_id='invalid_frame_mode',
            frame_mode='middle'  # Invalid choice
        )
        with self.assertRaises(ValidationError):
            session.full_clean()

    def test_images_remaining_relationship(self):
        """
        Test that images_remaining correctly establishes a ManyToMany relationship with FilmImage.
        """
        session = GameSession.objects.create(
            session_id='relationship_session',
            frame_mode='first'
        )
        session.images_remaining.add(self.image1, self.image2)
        self.assertIn(self.image1, session.images_remaining.all())
        self.assertIn(self.image2, session.images_remaining.all())
        self.assertEqual(self.image1.sessions.count(), 1)
        self.assertEqual(self.image2.sessions.count(), 1)