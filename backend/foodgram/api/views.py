from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from .serializers import (FollowSerializer, IngredientSerializer,
                          NewPasswordSerializer, RecipeBaseSerializer,
                          RecipeCreateSerializer, RecipeGetSerializer,
                          TagSerializer, UserSerializer,
                          UserSignUpSerializer)
from core.filters import IngredientFilter, RecipeFilter
from core.pagination import PageNumberLimitPagination
from core.permissions import IsAuthorOrReadOnly
from recipes.models import (Favorite, Follow, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Tag)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete']
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberLimitPagination
    permission_classes = (permissions.AllowAny,)

    def get_serializer_class(self):
        if self.request.method == 'get':
            return UserSerializer
        return UserSignUpSerializer

    @action(methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,), detail=True)
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            serializer = FollowSerializer(author,
                                          context={"request": request})
            is_subscribed = Follow.objects.filter(author=author,
                                                  user=user).exists()
            if is_subscribed:
                return Response({"errors":
                                 "Вы уже подписаны на этого автора"},
                                status=status.HTTP_400_BAD_REQUEST)
            if user == author:
                return Response({"errors":
                                 "Нельзя подписаться на самого себя"},
                                status=status.HTTP_400_BAD_REQUEST)
            subscription = Follow(user=user, author=author)
            subscription.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = Follow.objects.filter(author=author,
                                                 user=user)
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"errors": "Вы не подписаны на этого автора"},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get', ],
            permission_classes=(permissions.IsAuthenticated,), detail=False,
            pagination_class=PageNumberLimitPagination)
    def subscriptions(self, request):
        user = request.user
        subscriptions = User.objects.filter(following__user=user)
        page = self.paginate_queryset(subscriptions)
        serializer = FollowSerializer(page, many=True, read_only=True,
                                      context={"request": request})
        return self.get_paginated_response(serializer.data)


class UserMeViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', ]
    permission_classes = (permissions.IsAuthenticated,)

    def retrieve(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)


class NewPasswordViewSet(viewsets.ModelViewSet):
    http_method_names = ['post', ]
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request):
        user = request.user
        serializer = NewPasswordSerializer(data=request.data)
        if serializer.is_valid():
            if serializer.validated_data['current_password'] == user.password:
                user.password = serializer.validated_data['new_password']
                user.save(update_fields=["password"])
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                serializer.errors['wrong_password'] = ['Неверный пароль']
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class TokenLoginViewSet(views.APIView):
    http_method_names = ['post', ]
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if (not email) or (not password) or (not User.objects.filter(
                                             email=email,
                                             password=password).exists()):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, email=email)
        token = AccessToken.for_user(user)
        context = {'auth_token': str(token)}
        return Response(context, status=status.HTTP_200_OK)


class TokenLogoutViewSet(views.APIView):
    http_method_names = ['post', ]

    def post(self, request):
        user = request.user
        AccessToken.for_user(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Recipe.objects.all()
    pagination_class = PageNumberLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method == 'get':
            return RecipeGetSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,), detail=True)
    def favorite(self, request, pk=None):
        user = request.user
        if not Recipe.objects.filter(pk=pk).exists():
            if request.method == 'DELETE':
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            serializer = RecipeBaseSerializer(recipe)
            if serializer.is_valid:
                is_favorited = Favorite.objects.filter(user=user,
                                                       recipe=recipe).exists()
                if is_favorited:
                    return Response({"errors":
                                     "Рецепт уже добавлен в избранное"},
                                    status=status.HTTP_400_BAD_REQUEST)
                favorite = Favorite(user=user, recipe=recipe)
                favorite.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            is_favorited = Favorite.objects.filter(user=user, recipe=recipe)
            if is_favorited.exists():
                is_favorited.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"errors": "Рецепт не был добавлен в избранное"},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,), detail=True)
    def shopping_cart(self, request, pk=None):
        user = request.user
        if not Recipe.objects.filter(pk=pk).exists():
            if request.method == 'DELETE':
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            serializer = RecipeBaseSerializer(recipe)
            if serializer.is_valid:
                is_in_shopping_cart = ShoppingCart.objects.filter(
                    user=user, recipe=recipe).exists()
                if is_in_shopping_cart:
                    return Response({"errors":
                                     "Рецепт уже добавлен в список покупок"},
                                    status=status.HTTP_400_BAD_REQUEST)
                shopping_cart = ShoppingCart(user=user, recipe=recipe)
                shopping_cart.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            is_in_shopping_cart = ShoppingCart.objects.filter(user=user,
                                                              recipe=recipe)
            if is_in_shopping_cart.exists():
                is_in_shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"errors": "Рецепт отсутствует в списке покупок"},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'],
            permission_classes=(permissions.IsAuthenticated,), detail=False)
    def download_shopping_cart(self, request):
        user = request.user
        if not ShoppingCart.objects.filter(user=user).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ingredients = (
            IngredientRecipe.objects.filter(
                recipe__shoprecipe__user_id=request.user.id
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
        )
        download_list = (
            'Список покупок:\n'
        )
        download_list += '\n'.join([
            f'\u22C5 {ingredient["ingredient__name"]}, '
            f'({ingredient["ingredient__measurement_unit"]}) '
            f'----- {ingredient["total"]}'
            for ingredient in ingredients
        ])

        download_list += '\n\n Foodgram copyright by sonneee'
        download_list += '\n\n Github: https://github.com/sonneee/'

        file = f'{user.id}_download.txt'
        response = HttpResponse(download_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={file}'

        return response


class IngredientViewSet(viewsets.ModelViewSet):
    pagination_class = None
    http_method_names = ['get', ]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name',)


class TagViewSet(viewsets.ModelViewSet):
    pagination_class = None
    http_method_names = ['get', ]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
