from django.urls import include, path, re_path
from rest_framework import routers
from fpapi import views as fpview


router = routers.DefaultRouter()
router.register(r'users', fpview.UserViewSet)
router.register(r'projects', fpview.ProjectNestedViewSet)
router.register(r'trials', fpview.TrialViewSet)
router.register(r'traits', fpview.TraitViewSet)
router.register(r'nodes', fpview.NodeViewSet)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.

urlpatterns = [

    path('v1/', include(router.urls)),
    path('v2/projects/<uuid:uuid>/',fpview.ProjectViewSet.as_view({'get': 'retrieve'}),name='project-detail-uuid'),
    path('v2/trials/<uuid:uuid>/',fpview.TrialViewSet.as_view({'get': 'retrieve'}),name='trial-detail-uuid'),
    path('v2/', include(router.urls)),
    #path('v2/trials/<uuid:uuid>/',fpview.TrialViewSet.as_view({'get': 'list'})),
    #path('projects/<int:project_id>/users/', fpview.ProjectMemberList.as_view()),

]