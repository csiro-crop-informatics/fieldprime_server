from django.urls import include, path, re_path
from rest_framework import routers
from fpapi import views as fpview

router = routers.DefaultRouter()
router.register(r'users', fpview.UserViewSet)
router.register(r'projects', fpview.ProjectViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [

    path('', include(router.urls)),
    path('projects/<int:project_id>/users/', fpview.ProjectMemberList.as_view()),

]