from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.sign_up, name='sign_up'),
    path('sign_in/', views.sign_in, name='sign_in'),
    path('logout/', views.logout, name='logout'),
    path('email_verify/', views.email_verify, name='email_verify'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/<uidb64>/<token>/', views.reset_password, name='reset_password'),

    # Dashboard
    path('index/', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),

    # Document
    path('update-document/<int:doc_id>/', views.update_document, name='update_document'),
    path('delete-document/<int:doc_id>/', views.delete_document, name='delete_document'),
    path('comment/<int:doc_id>/', views.add_comment, name='add_comment'),

    # Explore
    path('explore_profile/', views.explore_profile, name='explore_profile'),
    path('explore_docs/', views.explore_docs, name='explore_docs'),

    # Users / Follow
    path('profile/<int:user_id>/', views.public_profile, name='public_profile'),
    path('follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),

    # Posts
    path('show/', views.show, name='show'),
    path('insert/', views.insert, name='insert'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),

    # Static pages
    path('terms/', views.terms, name='terms'),
    path('about/', views.about_us, name='about_us'),
    path('contact/', views.contact_us, name='contact_us'),
]
