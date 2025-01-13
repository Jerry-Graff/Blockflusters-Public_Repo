import io
import tempfile
import uuid
from PIL import Image
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

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
class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create test images
        self.image1 = FilmImage.objects.create(
            title='Inception',
            image=get_temporary_image(name='inception.jpg'),
            tier='Easy',
            frame='first',
            hint_1='A dream within a dream.',
            hint_2='Directed by Christopher Nolan.'
        )
        self.image2 = FilmImage.objects.create(
            title='The Matrix',
            image=get_temporary_image(name='matrix.jpg'),
            tier='Medium',
            frame='first',
            hint_1='Red pill or blue pill.',
            hint_2='Follow the white rabbit.'
        )
        self.image3 = FilmImage.objects.create(
            title='The Godfather',
            image=get_temporary_image(name='godfather.jpg'),
            tier='Hard',
            frame='last',
            hint_1='An offer you can\'t refuse.',
            hint_2='Directed by Francis Ford Coppola.'
        )

    def test_home_view(self):
        """
        Test that the home view renders the correct template.
        """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'game/home.html')

    def test_start_game_view_first_frame(self):
        """
        Test starting a game with 'first' frame mode.
        """
        response = self.client.get(reverse('start_game'), {'mode': 'first'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('play_game'))
        session = self.client.session
        self.assertIn('session_id', session)
        self.assertEqual(session['frame_mode'], 'first')
        # Verify that a GameSession is created
        session_id = session['session_id']
        game_session = GameSession.objects.get(session_id=session_id)
        self.assertEqual(game_session.frame_mode, 'first')
        self.assertEqual(game_session.images_remaining.count(), 2)

    def test_start_game_view_last_frame(self):
        """
        Test starting a game with 'last' frame mode.
        """
        response = self.client.get(reverse('start_game'), {'mode': 'last'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('play_game'))
        session = self.client.session
        self.assertIn('session_id', session)
        self.assertEqual(session['frame_mode'], 'last')
        # Verify that a GameSession is created
        session_id = session['session_id']
        game_session = GameSession.objects.get(session_id=session_id)
        self.assertEqual(game_session.frame_mode, 'last')
        self.assertEqual(game_session.images_remaining.count(), 1)  # image3

    def test_start_game_view_invalid_mode(self):
        """
        Test starting a game with an invalid frame mode defaults to 'first'.
        """
        response = self.client.get(reverse('start_game'), {'mode': 'invalid'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('play_game'))
        session = self.client.session
        self.assertIn('frame_mode', session)
        self.assertEqual(session['frame_mode'], 'first')

    def test_play_game_view_without_session(self):
        """
        Test accessing play_game without a session redirects to start_game.
        """
        response = self.client.get(reverse('play_game'))
        self.assertEqual(response.status_code, 302)
        # Use fetch_redirect_response=False to prevent following the redirect
        self.assertRedirects(response, reverse('start_game'), fetch_redirect_response=False)

    def test_play_game_view_with_session(self):
        """
        Test accessing play_game with a valid session.
        """
        # Start a game to create a session
        self.client.get(reverse('start_game'), {'mode': 'first'})
        response = self.client.get(reverse('play_game'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'game/play_game.html')
        # Verify context data
        self.assertIn('image', response.context)
        self.assertIn('form', response.context)
        self.assertEqual(response.context['score'], 0)
        self.assertEqual(response.context['time_remaining'], 90)
        self.assertEqual(response.context['frame_mode'], 'first')

    def test_play_game_view_no_images_remaining(self):
        """
        Test that play_game redirects to end_game when no images are remaining.
        """
        # Start a game and remove all images
        self.client.get(reverse('start_game'), {'mode': 'first'})
        session_id = self.client.session['session_id']
        session = GameSession.objects.get(session_id=session_id)
        session.images_remaining.clear()
        response = self.client.get(reverse('play_game'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('end_game'))

    def test_check_answer_correct(self):
        """
        Test submitting a correct answer.
        """
        # Start a game to create a session
        self.client.get(reverse('start_game'), {'mode': 'first'})
        session_id = self.client.session['session_id']
        session = GameSession.objects.get(session_id=session_id)
        image = session.images_remaining.first()
        form_data = {
            'image_id': str(image.id),
            'answer': image.title  # Correct answer
        }
        response = self.client.post(reverse('check_answer'), data=form_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['correct'])
        self.assertEqual(data['score'], 1)
        self.assertEqual(data['message'], 'Correct!')
        self.assertIn('image_url', data)
        self.assertIn('image_id', data)
        self.assertEqual(data['movie_title'], image.title)

    def test_check_answer_incorrect(self):
        """
        Test submitting an incorrect answer.
        """
        # Start a game to create a session
        self.client.get(reverse('start_game'), {'mode': 'first'})
        session_id = self.client.session['session_id']
        session = GameSession.objects.get(session_id=session_id)
        image = session.images_remaining.first()
        form_data = {
            'image_id': str(image.id),
            'answer': 'Wrong Answer'
        }
        response = self.client.post(reverse('check_answer'), data=form_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['correct'])
        self.assertEqual(data['score'], 0)
        self.assertEqual(data['message'], 'Incorrect!')
        self.assertIn('quote', data)
        self.assertIn('image_url', data)
        self.assertIn('image_id', data)
        self.assertEqual(data['movie_title'], image.title)

    def test_check_answer_invalid_form(self):
        """
        Test submitting an invalid form.
        """
        response = self.client.post(reverse('check_answer'), data={})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid input')

    def test_check_answer_no_session(self):
        """
        Test submitting an answer without a valid session.
        """
        form_data = {
            'image_id': str(self.image1.id),
            'answer': 'Inception'
        }
        response = self.client.post(reverse('check_answer'), data=form_data)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid session or image')

    def test_get_hint_valid(self):
        """
        Test retrieving a hint for an image.
        """
        # Start a game
        self.client.get(reverse('start_game'), {'mode': 'first'})
        image_id = self.image1.id
        response = self.client.get(reverse('get_hint'), {'image_id': image_id, 'hint_count': 0})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('hint', data)
        self.assertEqual(data['hint'], f'"{self.image1.hint_1}"')

        # Get second hint
        response = self.client.get(reverse('get_hint'), {'image_id': image_id, 'hint_count': 1})
        data = response.json()
        self.assertEqual(data['hint'], f'"{self.image1.hint_2}"')

    def test_get_hint_no_hints_available(self):
        """
        Test retrieving a hint when no hints are available.
        """
        # Create an image with no hints
        image = FilmImage.objects.create(
            title='No Hint Movie',
            image=get_temporary_image(name='no_hint.jpg'),
            tier='Easy',
            frame='first'
        )
        response = self.client.get(reverse('get_hint'), {'image_id': image.id, 'hint_count': 0})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No hints available.')

    def test_get_hint_invalid_image(self):
        """
        Test retrieving a hint with an invalid image ID.
        """
        response = self.client.get(reverse('get_hint'), {'image_id': 9999, 'hint_count': 0})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid image')

    def test_get_hint_invalid_method(self):
        """
        Test retrieving a hint using an invalid HTTP method.
        """
        response = self.client.post(reverse('get_hint'), {'image_id': self.image1.id, 'hint_count': 0})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid request method.')

    def test_end_game_view_with_session(self):
        """
        Test ending a game with a valid session.
        """
        # Start a game and set a score
        self.client.get(reverse('start_game'), {'mode': 'first'})
        session_id = self.client.session['session_id']
        session = GameSession.objects.get(session_id=session_id)
        session.score = 5
        session.save()
        response = self.client.get(reverse('end_game'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'game/end_game.html')
        # Verify context data
        self.assertIn('score', response.context)
        self.assertEqual(response.context['score'], 5)
        self.assertIn('performance_message', response.context)
        self.assertIn('performance_image', response.context)

    def test_end_game_view_without_session(self):
        """
        Test ending a game without a valid session redirects to start_game.
        """
        response = self.client.get(reverse('end_game'))
        self.assertEqual(response.status_code, 302)
        # Use fetch_redirect_response=False to prevent following the redirect
        self.assertRedirects(response, reverse('start_game'), fetch_redirect_response=False)

    def test_end_game_view_with_invalid_session(self):
        """
        Test ending a game with an invalid session redirects to start_game.
        """
        # Manually set an invalid session ID
        session = self.client.session
        session['session_id'] = 'invalid_session_id'
        session.save()
        response = self.client.get(reverse('end_game'))
        self.assertEqual(response.status_code, 302)
        # Use fetch_redirect_response=False to prevent following the redirect
        self.assertRedirects(response, reverse('start_game'), fetch_redirect_response=False)

    def test_get_next_image(self):
        """
        Test the get_next_image function returns the correct image based on tier logic.
        """
        from game.views import get_next_image

        # Create a session with specific score
        session = GameSession.objects.create(
            session_id=str(uuid.uuid4()),
            score=5
        )
        session.images_remaining.set(FilmImage.objects.all())

        # Test tier selection based on score
        image = get_next_image(session)
        self.assertEqual(image.tier, 'Easy')

        session.score = 15
        session.save()
        image = get_next_image(session)
        self.assertIn(image.tier, ['Easy', 'Medium'])

        session.score = 25
        session.save()
        image = get_next_image(session)
        self.assertEqual(image.tier, 'Medium')

        session.score = 35
        session.save()
        image = get_next_image(session)
        self.assertIn(image.tier, ['Medium', 'Hard'])

        session.score = 45
        session.save()
        image = get_next_image(session)
        self.assertEqual(image.tier, 'Hard')

    def test_get_next_image_no_images_remaining(self):
        """
        Test get_next_image returns None when no images are remaining.
        """
        from game.views import get_next_image
        session = GameSession.objects.create(
            session_id=str(uuid.uuid4()),
            score=0
        )
        session.images_remaining.clear()
        image = get_next_image(session)
        self.assertIsNone(image)

    def test_is_answer_correct(self):
        """
        Test the is_answer_correct function with various inputs.
        """
        from game.views import is_answer_correct

        self.assertTrue(is_answer_correct('Inception', 'Inception'))
        self.assertTrue(is_answer_correct('inception', 'Inception'))
        self.assertTrue(is_answer_correct('Inception ', 'Inception'))
        self.assertTrue(is_answer_correct('Incepton', 'Inception'))
        self.assertFalse(is_answer_correct('Matrix', 'Inception'))
        self.assertFalse(is_answer_correct('Wrong Movie', 'Inception'))
