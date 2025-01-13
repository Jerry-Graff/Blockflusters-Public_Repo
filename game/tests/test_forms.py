from django.test import TestCase
from game.forms import AnswerForm


class AnswerFormTest(TestCase):
    def test_form_valid_data(self):
        """
        Test that the form is valid when all required fields are provided
        with correct data.
        """
        form_data = {
            'image_id': 1,
            'answer': 'The Godfather'
        }
        form = AnswerForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['image_id'], 1)
        self.assertEqual(form.cleaned_data['answer'], 'The Godfather')

    def test_form_missing_image_id(self):
        """
        Test that the form is invalid when the image_id is missing.
        """
        form_data = {
            'answer': 'Inception'
        }
        form = AnswerForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('image_id', form.errors)
        self.assertEqual(form.errors['image_id'], ['This field is required.'])

    def test_form_missing_answer(self):
        """
        Test that the form is invalid when the answer is missing.
        """
        form_data = {
            'image_id': 2
        }
        form = AnswerForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('answer', form.errors)
        self.assertEqual(form.errors['answer'], ['This field is required.'])

    def test_form_invalid_image_id(self):
        """
        Test that the form is invalid when image_id is not an integer.
        """
        form_data = {
            'image_id': 'invalid',
            'answer': 'Pulp Fiction'
        }
        form = AnswerForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('image_id', form.errors)
        self.assertEqual(form.errors['image_id'], ['Enter a whole number.'])

    def test_form_answer_max_length(self):
        """
        Test that the form is invalid when the answer exceeds the maximum
        length.
        """
        form_data = {
            'image_id': 3,
            'answer': 'A' * 256
        }
        form = AnswerForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('answer', form.errors)
        self.assertEqual(form.errors['answer'], ['Ensure this value has at most 255 characters (it has 256).'])

    def test_form_empty_data(self):
        """
        Test that the form is invalid when no data is provided.
        """
        form = AnswerForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('image_id', form.errors)
        self.assertIn('answer', form.errors)
        self.assertEqual(form.errors['image_id'], ['This field is required.'])
        self.assertEqual(form.errors['answer'], ['This field is required.'])

    def test_form_widget_attributes(self):
        """
        Test that the form fields have the correct widget attributes.
        """
        form = AnswerForm()
        # Check image_id widget
        self.assertTrue(form.fields['image_id'].widget.is_hidden)

        # Check answer widget attributes
        answer_widget = form.fields['answer'].widget
        self.assertEqual(answer_widget.attrs.get('class'), 'form-control')
        self.assertEqual(answer_widget.attrs.get('placeholder'), 'Enter movie here!')
        self.assertEqual(answer_widget.attrs.get('autocomplete'), 'off')