from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

MIN_VAL = 1
MAX_VAL = 10000


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    color = ColorField(default='#FF0000', verbose_name='Цвет')
    slug = models.SlugField(max_length=200, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    measurement_unit = models.CharField(max_length=200,
                                        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.IntegerField(validators=[MinValueValidator(MIN_VAL),
                                                   MaxValueValidator(MAX_VAL)],
                                       verbose_name='Время приготовления')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(Tag)
    pub_date = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    ingredients = models.ManyToManyField(Ingredient,
                                         through='IngredientRecipe')

    image = models.ImageField(
        'Изображение',
        upload_to='recipes/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date', '-id')
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(Ingredient, related_name='recping',
                                   on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, related_name='ingredientrecipe',
                               on_delete=models.CASCADE)
    amount = models.IntegerField(validators=[MinValueValidator(MIN_VAL),
                                             MaxValueValidator(MAX_VAL)],
                                 verbose_name='Количество')

    class Meta:
        verbose_name = 'Связь Ингредиент-Рецепт'
        verbose_name_plural = 'Связи Ингредиент-Рецепт'

    def __str__(self):
        return f'{self.ingredient}-{self.recipe}'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=('user', 'author'),
                                    name='unique_follow'),
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favuser',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favrecipe',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(fields=('user', 'recipe'),
                                    name='unique_favorite'),
        ]

    def __str__(self):
        return f'{self.recipe} в избранном у {self.user}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopuser',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shoprecipe',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(fields=('user', 'recipe'),
                                    name='unique_shopping_cart'),
        ]

    def __str__(self):
        return f'{self.recipe} в списке покупок у {self.user}'
