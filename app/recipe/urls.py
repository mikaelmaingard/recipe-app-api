from django.urls import path, include

from rest_framework.routers import DefaultRouter

from recipe import views

router = DefaultRouter()  # create new router object
router.register('tags', views.TagViewSet)  # register viewset with router

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
]
