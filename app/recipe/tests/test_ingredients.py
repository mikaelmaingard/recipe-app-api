from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test retrieving ingredients required authorized login"""
        res = self.client.get(INGREDIENTS_URL)  # try retrieve ingredients list

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test the private ingredients API"""

    def setUp(self):
        # create API client
        self.client = APIClient()

        # create authorised user
        self.user = get_user_model().objects.create_user(
            'testuser@comgrow.org',
            'test_pass123'
        )
        # authenticate user
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        """Test retrieving a list of ingredients"""
        # create dummy ingredients
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')

        # retrieve list of existing ingredients
        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test that only the ingredients for the authenticated user are returned"""
        # create another user
        user2 = get_user_model().objects.create_user(
            'user2@comgrow.org',
            'testing_user2'
        )
        # create ingredient for new user
        Ingredient.objects.create(user=user2, name="Humus")

        # create ingredient for authenticated user
        ingredient = Ingredient.objects.create(user=self.user, name="Tumeric")

        # retrieve ingredients for the authenticated user
        res = self.client.get(INGREDIENTS_URL)

        # check correct status code
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)  # check expected length
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successfully(self):
        """Test that authorised user can successfully create an ingredient"""
        payload = {'name': 'Lettuce'}
        # post ingredient with authenticated user
        self.client.post(INGREDIENTS_URL, payload)
        # check if ingredient was created
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test that invalid ingredient is not created"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
