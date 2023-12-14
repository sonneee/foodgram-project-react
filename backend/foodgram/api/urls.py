from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (IngredientViewSet, NewPasswordViewSet,
                    RecipeViewSet, TagViewSet,
                    TokenLoginViewSet, TokenLogoutViewSet,
                    UserMeViewSet, UserViewSet)

router = SimpleRouter()

router.register(r'users', UserViewSet)
router.register(r'tags', TagViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'ingredients', IngredientViewSet)
name = 'api'

urlpatterns = [
    path('users/me/', UserMeViewSet.as_view({
        'get': 'retrieve',
    })),
    path('users/set_password/', NewPasswordViewSet.as_view({
        'post': 'create',
    })),
    path('', include(router.urls)),
    path('auth/token/login/', TokenLoginViewSet.as_view()),
    path('auth/token/logout/', TokenLogoutViewSet.as_view())
]
