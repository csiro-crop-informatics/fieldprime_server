from django.urls import include, path, re_path
from rest_framework import routers
from fpapi import views as fpview


router = routers.DefaultRouter()
router.register(r'users', fpview.UserViewSet)
router.register(r'projects', fpview.ProjectNestedViewSet)
#router.register(r'trials', fpview.TrialViewSet)
#router.register(r'traits', fpview.TraitViewSet)
#router.register(r'nodes', fpview.NodeViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.

urlpatterns = [

    #path('v1/', include(router.urls)),
    path('v1/projects/<int:id>/', fpview.ProjectViewSet.as_view({'get': 'retrieve'}), name='project-detail'),

    path('v2/projects/', fpview.ProjectViewSet.as_view({'get': 'list'})),

    # Detail Views
    path('v2/projects/<uuid:uuid>/', fpview.ProjectViewSet.as_view({'get': 'retrieve'}), name='project-detail-uuid'),
    path('v2/trials/<uuid:uuid>/', fpview.TrialViewSet.as_view({'get': 'retrieve'}), name='trial-detail-uuid'),
    path('v2/traits/<uuid:uuid>/', fpview.TraitViewSet.as_view({'get': 'retrieve'}), name='trait-detail-uuid'),
    path('v2/nodes/<uuid:barcode>/', fpview.NodeViewSet.as_view({'get': 'retrieve'}), name='node-detail-id'),

    # Trait Views
    path('v2/trials/<uuid:uuid>/traits/', fpview.TraitListByTrial.as_view(), name='list-trial-traits'),
    #path('v2/trials/<uuid:uuid>/traits', fpview.TraitUpdateByTrial.as_view(), name='update-trial-traits'),
    
    # Datum Views
    path('v2/trials/<uuid:uuid>/datum/', fpview.DatumListByTrial.as_view(), name='list-trial-datum'),
    
    #path('v2/', include(router.urls)),

]