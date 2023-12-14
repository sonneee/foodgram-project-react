from django.contrib.auth import get_user_model
from rest_framework import serializers
import base64
from django.db.models import F
from django.core.files.base import ContentFile
from rest_framework.validators import UniqueValidator
from recipes.models import (Recipe, Ingredient,
                            Tag, IngredientRecipe,
                            Favorite, ShoppingCart, Follow)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request:
            user = self.context.get("request").user
            if user.is_authenticated:
                return Follow.objects.filter(user=user,
                                             author=obj).exists()
        return False


class UserSignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'password',)
        extra_kwargs = {'email': {'required': True, 'validators': [
            UniqueValidator(queryset=User.objects.all())]},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True}}

    def to_representation(self, data):
        return {'email': data.email,
                'id': data.id,
                'username': data.username,
                'first_name': data.first_name,
                'last_name': data.last_name}


class NewPasswordSerializer(serializers.BaseSerializer):
    new_password = serializers.CharField(max_length=150, required=True)
    current_password = serializers.CharField(max_length=150, required=True)

    def validate_new_password(self, data):
        new_password = data.get('new_password')
        errors = {}
        if not new_password:
            errors['new_password'] = ['Обязательное поле']
        elif len(new_password) > 150:
            errors['new_password'] = ['Пароль не должен быть длиннее '
                                      '150 символов']
        return errors

    def validate_current_password(self, data):
        current_password = data.get('current_password')
        errors = {}
        if not current_password:
            errors['current_password'] = ['Обязательное поле']
        elif len(current_password) > 150:
            errors['current_password'] = ['Пароль не должен быть длиннее '
                                          '150 символов']
        return errors

    def validate(self, data):
        if data is None:
            raise serializers.ValidationError({
                'new_password': ['Обязательное поле'],
                'current_password': ['Обязательное поле']
            })
        errors = {}
        errors.update(self.validate_new_password(data))
        errors.update(self.validate_current_password(data))
        if errors:
            raise serializers.ValidationError(errors)

    def to_internal_value(self, data):
        self.validate(data)
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        return {'current_password': current_password,
                'new_password': new_password}

    def to_representation(self, data):
        return self.to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'image', 'name', 'text',
                  'author', 'cooking_time', 'is_favorited',
                  'is_in_shopping_cart')

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recping__amount')
        )
        return ingredients

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user,
                                           recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(user=user,
                                               recipe=obj).exists()
        return False


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'image', 'name', 'text',
                  'author', 'cooking_time')

    def validate_ingredients(self, data):
        ingredients = data
        errors = {}
        if not ingredients:
            errors['ingredients'] = ['Обязательное поле']
        else:
            ingr_ids = {}
            for ingredient in ingredients:
                id_now = ingredient['id']
                if not Ingredient.objects.filter(id=id_now).exists():
                    errors['ingredients'] = ['Указан несуществующий '
                                             'ингредиент']
                if ingr_ids.get(id_now):
                    errors['ingredients'] = ['Ингредиенты не должны '
                                             'повторяться']
                else:
                    ingr_ids[id_now] = 1
        if errors:
            raise serializers.ValidationError(errors)
        return data

    def validate_tags(self, data):
        tags = data
        errors = {}
        if not tags:
            errors['tags'] = ['Обязательное поле']
        else:
            for tag in tags:
                if not Tag.objects.filter(id=tag.id).exists():
                    errors['tags'] = ['Указан несуществующий тег']
            if len(list(tags)) != len(set(tags)):
                errors['tags'] = ['Теги не должны повторяться']
        if errors:
            raise serializers.ValidationError(errors)
        return data

    def create(self, validated_data):
        tags = validated_data.get('tags')
        ingredients = validated_data.get('ingredients')
        recipe = Recipe.objects.create(**{'name': validated_data.get('name'),
                                          'text': validated_data.get('text'),
                                          'author': validated_data.get('user'),
                                          'cooking_time':
                                          validated_data.get('cooking_time'),
                                          'image': validated_data.get('image')}
                                       )
        recipe.tags.set(tags)
        ingredients_recipe = [IngredientRecipe(
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        IngredientRecipe.objects.bulk_create(ingredients_recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.get('ingredients')
        tags = validated_data.get('tags')
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get("cooking_time",
                                                   instance.cooking_time)
        instance.image = validated_data.get("image", instance.image)
        errors = {}
        if tags is None:
            errors['tags'] = ['Обязательное поле']
        if ingredients is None:
            errors['ingridients'] = ['Обязательное поле']
        if errors:
            raise serializers.ValidationError(errors)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        ingredients_recipe = [IngredientRecipe(
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                recipe=instance,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        IngredientRecipe.objects.bulk_create(ingredients_recipe)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context['request']
        context = {'request': request}
        return RecipeGetSerializer(instance, context=context).data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class FollowSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request:
            user = self.context.get("request").user
            if user.is_authenticated:
                return Follow.objects.filter(user=user,
                                             author=obj).exists()
        return False

    def get_recipes(self, obj):
        request = self.context.get("request")
        if request:
            recipes_limit = int(request.GET.get('recipes_limit',
                                                default=0))
        else:
            recipes_limit = 0
        recipes = Recipe.objects.filter(author=obj).all()
        if recipes_limit > 0:
            recipes = recipes[:recipes_limit]
        serializer = RecipeBaseSerializer(recipes, many=True, read_only=True)
        return serializer.data
