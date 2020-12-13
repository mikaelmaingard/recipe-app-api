from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')

# /api/recipe/recipes
# /api/recipe/recipes/<id>/


def detail_url(recipe_id):
    """Return recipe detail url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name="Main course"):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name="Cinnamon"):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


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

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)  # serialize recipe
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating basic recipe"""
        payload = {
            # 'ingredients': sample_ingredient(user=self.user),
            # 'tags': sample_tag(user=self.user),
            'title': "Sample recipe",
            'time_minutes': 14,
            'price': 23.5}

        # create recipe
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # retrieve create recipe from models
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Dessert')
        payload = {
            # 'ingredients': sample_ingredient(user=self.user),
            'tags': [tag1.id, tag2.id],
            'title': "Sample recipe",
            'time_minutes': 14,
            'price': 23.5}

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # fetch from models
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredient(self):
        """Test creating a recipe with ingredient"""
        ingr1 = sample_ingredient(user=self.user, name='Prawns')
        ingr2 = sample_ingredient(user=self.user, name='Ginger')
        payload = {
            # 'ingredients': sample_ingredient(user=self.user),
            'ingredients': [ingr1.id, ingr2.id],
            'title': "Sample recipe",
            'time_minutes': 14,
            'price': 23.5}

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # fetch from models
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingr1, ingredients)
        self.assertIn(ingr2, ingredients)

    def test_partial_update_recipe(self):
        """Test feature to partially update a recipe (patch)"""
        """Patch updates with the fields provided in payload"""
        """Any other fields will not be modified"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name="Curry")

        payload = {
            'title': 'Chicken Tikka',
            'tags': [new_tag.id]
        }
        url = detail_url(recipe.id)

        # use patch to upaate the title and tags
        self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        # create sample recipe
        recipe = sample_recipe(user=self.user)
        # add tags to sample recipe
        recipe.tags.add(sample_tag(user=self.user))
        # create payload for 'put' update
        payload = {
            'title': 'sample title',
            'time_minutes': 54,
            'price': 23.90
        }
        url = detail_url(recipe.id)
        self.client.put(url, payload)

        # refresh to enable update to take effect
        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(float(recipe.price), float(payload['price']))

        # get tags from updated recipe
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 0)
