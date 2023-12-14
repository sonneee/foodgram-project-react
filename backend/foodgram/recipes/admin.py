from django.contrib import admin
from .models import (Favorite, Follow, Ingredient,
                     IngredientRecipe, Recipe,
                     ShoppingCart, Tag, User)


class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name',
                    'password')
    list_filter = ('email', 'username')


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author_username', 'favorited_count')
    list_filter = ('author', 'name', 'tags')

    def favorited_count(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    def author_username(self, obj):
        return obj.author.username


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_filter = ('name',)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(IngredientRecipe)
admin.site.register(Follow)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
