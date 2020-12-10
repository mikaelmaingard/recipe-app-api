from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Tag, Ingredient
from recipe import serializers


class TagViewSet(viewsets.GenericViewSet,
                 mixins.ListModelMixin,
                 mixins.CreateModelMixin):
    """Manage tags in the database"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        return self.queryset.filter(user=self.request.user).order_by('-name')

    # override default method
    def perform_create(self, serializer):
        """Create a new tag"""
        serializer.save(
            user=self.request.user)  # set user to authenitcated user


class IngredientViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """Manage ingredients in the database"""
    authentication_classes = (TokenAuthentication,)
    # make sure users are authenticated
    permission_classes = (IsAuthenticated, )
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer

    def get_queryset(self):
        """Return onjects for the current authenticated user only"""
        # filter for the requesting user
        return self.queryset.filter(user=self.request.user).order_by('-name')
