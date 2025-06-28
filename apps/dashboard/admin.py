# # from django.contrib import admin
# # from .models import User,Post
# # # Register your models here.

# # # class userAdmin(admin.ModelAdmin):
# #     # list_display = ['cid', 'email', 'mobile', 'is_active']
# #     # list_filter = ['is_active']
# #     # list_editable = ['mobile', 'is_active']
# #     # search_fields = ['mobile', 'email']
# #     class userAdmin(admin.ModelAdmin):
# #         list_display = ('name', 'enrollment')  

# #     list_per_page = 50
# # admin.site.register(User, userAdmin)
# # admin.site.register(Post)

# # from django.contrib import admin
# # from .models import User, Post

# # class userAdmin(admin.ModelAdmin):
# #     list_display = ('name', 'enrollment')  # ✅ existing fields from your model
# #     list_per_page = 50  # ✅ now it's inside the class

# # admin.site.register(User, userAdmin)
# # admin.site.register(Post)


# from django.contrib import admin
# from .models import User  # or `user` if your model is named that

# admin.site.register(User)


# class UserAdmin(admin.ModelAdmin):
#     list_display = ('email', 'mobile', 'is_active', 'otp')  # fields to show in list
#     search_fields = ('email', 'mobile')

# admin.site.register(User, UserAdmin)


from django.contrib import admin
from .models import User  # or your model name

class UserAdmin(admin.ModelAdmin):
    list_display = ('name','email', 'mobile', 'is_active', 'otp')  # Customize this as needed
    search_fields = ('email', 'mobile')

admin.site.register(User, UserAdmin)
