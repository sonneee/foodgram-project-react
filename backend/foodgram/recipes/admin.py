from django.contrib import admin

from .models import (Favorite, Follow, Ingredient,
                     IngredientRecipe, Recipe,
                     ShoppingCart, Tag, User)

admin.site.unregister(User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name',
                    'password')
    list_filter = ('email', 'username')


class IngredientRecipeInline(admin.StackedInline):
    model = Recipe.ingredients.through


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author_username', 'favorited_count')
    list_filter = ('author', 'name', 'tags')
    inlines = (IngredientRecipeInline,)
    exclude = ('ingredients',)

    def favorited_count(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    def author_username(self, obj):
        return obj.author.username


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_filter = ('name',)
    inlines = (IngredientRecipeInline,)


admin.site.register(Tag)
admin.site.register(IngredientRecipe)
admin.site.register(Follow)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
