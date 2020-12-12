from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.01
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test publicly available recipes"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that retriving recipes requires authorised login"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test privately available recipes"""

    def setUp(self):
        """Create and force authenticate a user"""
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            'test@comgrow.org',
            'testpassword'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        # create dummy recipes
        sample_recipe(self.user)  # create with defaults
        sample_recipe(self.user)
        sample_recipe(self.user)

        res = self.client.get(RECIPES_URL)
        # retrieve the list of recipes
        recipes = Recipe.objects.all().order_by('-id')
        # pass in recipes into serializer
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # check data matches serializer that we created
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test only the user's recipes are retrieved"""
        # create new user
        user2 = get_user_model().objects.create_user(
            'user2@comgrow.org',
            'password123'
        )
        # create recipe for new user
        sample_recipe(user2)
        # create recipe for original user
        params = {'title': 'Cheese bake', 'time_minutes': 45, 'price': 7.98}
        sample_recipe(self.user, **params)

        # perform get
        res = self.client.get(RECIPES_URL)

        # filter for authenticated user
        recipes = Recipe.objects.filter(user=self.user)
        # pass in returned queryset to our serializer
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)