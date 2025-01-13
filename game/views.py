import os
import random
import uuid
import json
import logging

from rapidfuzz import fuzz
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewsSitemap

from .models import FilmImage, GameSession
from .forms import AnswerForm

logger = logging.getLogger(__name__)


def custom_sitemap_view(request):
    response = sitemap(request, sitemaps={'static': StaticViewsSitemap})
    response['X-Robots-Tag'] = 'index, follow'
    return response


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Allow: /terms-of-service/",
        "Allow: /cookies-policy/",
        "Allow: /home/",
        "Disallow: /start-game/",
        "Disallow: /end-game/",
        "Disallow: /play-game/",
        "Disallow: /check-answer/",
        "Disallow: /skip-image/",
        "Disallow: /get-hint/",
        f"Sitemap: {request.build_absolute_uri(reverse('sitemap'))}"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain", charset="utf-8")


def home(request):
    logger.info("Rendering home page")
    return render(request, 'game/home.html')


def terms_of_service(request):
    logger.info("Rendering ToS")
    return render(request, 'game/terms_of_service.html')


def cookies_policy(request):
    logger.info("Rendering Cookies policy")
    return render(request, 'game/cookies_policy.html')


def start_game(request):
    mode = request.GET.get('mode', 'first')
    if mode not in dict(FilmImage.FRAME_CHOICES):
        logger.warning(f"Inavlid mode '{mode} provided. Deafulting to 'first")
        mode = 'first'  # Fallback to 'first' if invalid mode is provided

    # Create a new game session
    session_id = str(uuid.uuid4())
    request.session['session_id'] = session_id
    request.session['frame_mode'] = mode
    images = FilmImage.objects.filter(frame=mode)
    session = GameSession.objects.create(
        session_id=session_id,
        frame_mode=mode
    )
    session.images_remaining.set(images)
    session.save()
    logger.info(f"Started new game session: {session_id} with mode: {mode}")

    return redirect('play_game')


def play_game(request):
    session_id = request.session.get('session_id')
    frame_mode = request.session.get('frame_mode', 'first')

    if not session_id:
        logger.warning("Session ID not found in request. Redirecting to start game")
        return redirect('start_game')

    try:
        session = GameSession.objects.get(session_id=session_id)
    except GameSession.DoesNotExist:
        logger.warning(f"GameSessiion ID: {session_id} does not exist. Redirecting to start game")
        return redirect('start_game')

    if not session.images_remaining.exists():
        logger.info(f"No images remaining, session ID: {session_id}. Redirecting to end_game")
        return redirect('end_game')

    image = get_next_image(session)
    if not image:
        logger.info(f"No next image found for session {session_id}. Redirecting to end_game")
        return redirect('end_game')

    form = AnswerForm(initial={'image_id': image.id})
    context = {
        'image': image,
        'score': session.score,
        'time_remaining': 90,
        'form': form,
        'frame_mode': frame_mode,
    }
    logger.debug(f"Rendering play_game with image ID {image.id} for session {session_id}")
    return render(request, 'game/play_game.html', context)


def get_next_image(session, current_image=None):
    total_shown = session.score
    # Determine the active tiers
    if total_shown < 10:
        tiers = ['Easy']
    elif total_shown < 20:
        tiers = ['Easy', 'Medium']
    elif total_shown < 30:
        tiers = ['Medium']
    elif total_shown < 40:
        tiers = ['Medium', 'Hard']
    else:
        tiers = ['Hard']

    # Ensure current_tier_shown is initialized as before
    if not session.current_tier_shown:
        session.current_tier_shown = []

    current_tier_shown = set(session.current_tier_shown)

    tier_images = session.images_remaining.filter(tier__in=tiers)

    if current_image:
        tier_images = tier_images.exclude(id=current_image.id)

    tier_images = tier_images.exclude(id__in=current_tier_shown)

    if tier_images.exists():
        chosen_image = random.choice(list(tier_images))
        current_tier_shown.add(chosen_image.id)
        session.current_tier_shown = list(current_tier_shown)
        session.save()
        return chosen_image
    else:
        # Reset the rotation
        session.current_tier_shown = []
        session.save()

        # Images in active tiers are eligible again
        tier_images = session.images_remaining.filter(tier__in=tiers)
        if current_image:
            tier_images = tier_images.exclude(id=current_image.id)

        if tier_images.exists():
            chosen_image = random.choice(list(tier_images))
            session.current_tier_shown = [chosen_image.id]
            session.save()
            return chosen_image
        else:
            return None


@require_POST
def skip_image(request):
    session_id = request.session.get('session_id')
    current_image_id = request.POST.get('image_id')

    if not session_id or not current_image_id:
        return JsonResponse({'error': 'Invalid session or image ID.'}, status=400)

    try:
        session = GameSession.objects.get(session_id=session_id)
        current_image = FilmImage.objects.get(id=current_image_id)
    except (GameSession.DoesNotExist, FilmImage.DoesNotExist):
        return JsonResponse({'error': 'Invalid session or image ID.'}, status=400)

    # Fetch the next image without modifying the score or timer
    next_image = get_next_image(session, current_image=current_image)

    if next_image:
        data = {
            'skipped': True,
            'image_url': next_image.image.url,
            'image_id': next_image.id,
        }
    else:
        data = {
            'end_game': True,
            'score': session.score,
        }

    return JsonResponse(data)


def check_answer(request):
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            user_answer = form.cleaned_data['answer'].strip().lower()
            image_id = form.cleaned_data['image_id']
            session_id = request.session.get('session_id')

            try:
                session = GameSession.objects.get(session_id=session_id)
                image = FilmImage.objects.get(id=image_id)
            except (GameSession.DoesNotExist, FilmImage.DoesNotExist):
                logger.error(f"Invalid session {session_id} or image {image_id}")
                return JsonResponse({'error': 'Invalid session or image'}, status=400)

            correct = is_answer_correct(user_answer, image.title)

            if correct:
                session.score += 1
                session.images_remaining.remove(image)
                message = "Correct!"
            else:
                message = "Incorrect!"
                quotes = [
                    "You're gonna need a bigger boat.",
                    "Not quite my tempo!",
                    "Why do we fall Master Bruce... to pick ourselves back up.",
                    "I didn't hear no bell!",
                    "We who are about to die, salute you!",
                    "I'll be back.",
                    "I know it was you, Fredo!",
                    "What we got here, is a failure to communicate.",
                    "It's like finding a needle in a stack of needles.",
                    "It's only after we've lost everything that we're free to do anything.",
                    "There's no crying in baseball",
                    "Houston, we have a problem",
                ]
                quote = random.choice(quotes)

            session.save()

            # Check if the user has reached a score of 50
            if session.score >= 50:
                logger.info(f"User {session_id} reached a score of 50. Ending game.")
                return JsonResponse({
                    'correct': correct,
                    'score': session.score,
                    'end_game': True,
                    'message': message,
                    'movie_title': image.title if correct else None,
                    'quote': quote if not correct else None,
                })

            # Get the next image, excluding the current image
            next_image = get_next_image(session, current_image=image)

            if next_image:
                data = {
                    'correct': correct,
                    'score': session.score,
                    'message': message,
                    'image_url': next_image.image.url,
                    'image_id': next_image.id,
                    'movie_title': image.title,
                }
                if not correct:
                    data['quote'] = quote
            else:
                # End game
                data = {
                    'correct': correct,
                    'score': session.score,
                    'end_game': True,
                }
                if not correct:
                    data['quote'] = quote

            return JsonResponse(data)
        else:
            logger.warning("Invalid form submission in check_answer")
            return JsonResponse({'error': 'Invalid input'}, status=400)
    else:
        logger.warning("Invalid request method to check_answer")
        return JsonResponse({'error': 'Invalid request'}, status=400)


def is_answer_correct(user_answer, correct_answer):
    user_answer = ''.join(user_answer.split()).lower()
    correct_answer = ''.join(correct_answer.split()).lower()
    similarity = fuzz.token_sort_ratio(user_answer, correct_answer)
    logger.debug(f"Calculated similarity {similarity} between '{user_answer}' and '{correct_answer}'")
    return similarity >= 80


def get_hint(request):
    if request.method == 'GET':
        image_id = request.GET.get('image_id')
        hint_count = int(request.GET.get('hint_count', 0))

        try:
            image = FilmImage.objects.get(id=image_id)
        except FilmImage.DoesNotExist:
            logger.error(f"Image with ID {image_id} does not exist in get_hint")
            return JsonResponse({'error': 'Invalid image'}, status=400)

        hints = [image.hint_1, image.hint_2]
        hints = [hint for hint in hints if hint]

        if not hints:
            logger.info(f"No hints available for image ID {image_id}")
            return JsonResponse({'error': 'No hints available.'}, status=400)

        hint_index = hint_count % len(hints)
        hint = hints[hint_index]

        hint_wrapped = f'"{hint}"'
        return JsonResponse({'hint': hint_wrapped})
    else:
        logger.warning("Invalid request method to get_hint")
        return JsonResponse({'error': 'Invalid request method.'}, status=400)


def end_game(request):
    session_id = request.session.get('session_id')
    if not session_id:
        logger.warning("Session ID not found in request during end_game. Redirecting to start_game")
        return redirect('start_game')

    try:
        session = GameSession.objects.get(session_id=session_id)
    except GameSession.DoesNotExist:
        logger.error(f"GameSession with ID {session_id} does not exist in end_game")
        return redirect('start_game')

    score = session.score
    logger.info(f"Ending game for session {session_id} with score {score}")
    json_path = os.path.join(settings.BASE_DIR, 'game', 'data', 'performance_score.json')

    # Load JSON data
    try:
        with open(json_path, 'r') as file:
            performance_scores = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading performance scores: {e}")
        performance_scores = []

    # Initialize with defaults
    performance_message = "You're not wrong man, you're just am asshole! "
    performance_image = "performance/lebowski.png"

    for scale in performance_scores:
        if scale['min_score'] <= score <= scale['max_score']:
            performance_message = scale['message']
            performance_image = scale['image']
            break

    # Clear current_tier_shown as the game has ended
    session.current_tier_shown = []
    session.save()

    context = {
        'score': score,
        'performance_message': performance_message,
        'performance_image': performance_image,
    }
    logger.debug(f"Rendering end_game with context: {context}")

    return render(request, 'game/end_game.html', context)
