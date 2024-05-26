from django.urls import path
from . import views
urlpatterns = [
    path("", views.index_slider, name='image.slider'),
    path("add-image-slider", views.add_slider, name='add.image.slider'),
    path("edit-image-slider/<id>", views.editSlider, name='edit.image.slider'),
    path("delete/<id>", views.deleteSlider, name='slider.delete_slider'),
    path("change-status/<id>/<status>", views.changeStatusSlider, name='slider.change_status_slider'),
]
