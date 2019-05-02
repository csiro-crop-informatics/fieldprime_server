from django.shortcuts import render, get_object_or_404
from fpapi import models as fpmodels

from rest_framework import viewsets, generics
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import UserSerializer, ProjectSerializer, TraitSerializer, TrialSerializer, TrialNestedSerializer, NodeSerializer
from fpapi import serializers as fpserializers

import logging
logger = logging.getLogger(__name__)

class VersionModelViewSet(viewsets.ModelViewSet):
    """
    Model ViewSet that overrides object lookup based 
      on version. Version 1 (v1) uses the default 
      primary key based lookup and version 2 (v2) uses
      the uuid.

    """
    def get_object(self):

        queryset = self.filter_queryset(self.get_queryset())

        logger.error("API Version: %s" % self.kwargs['version'])
        #Default to version 2.
        if self.kwargs['version'] == 'v1':
            filter_kwargs = {'pk': self.kwargs['pk']}
        else:
            filter_kwargs = {'uuid': self.kwargs['pk']}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

###############################################################################
#    MODEL VIEW SETS
###############################################################################

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = fpmodels.User.objects.all()
    serializer_class = UserSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    lookup_field = 'uuid'
    queryset = fpmodels.Project.objects.all()
    serializer_class = fpserializers.ProjectSerializer


class TraitViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    lookup_field = 'uuid'
    queryset = fpmodels.Trait.objects.all()
    serializer_class = fpserializers.TraitSerializer

class TrialViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    lookup_field = 'uuid'
    queryset = fpmodels.Trial.objects.all()
    serializer_class = TrialSerializer

class NodeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    lookup_field = 'barcode'
    queryset = fpmodels.Node.objects.all()
    serializer_class = fpserializers.NodeSerializer



###############################################################################
#    NESTED VIEWS
###############################################################################

class ProjectNestedViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = fpmodels.Project.objects.all()
    serializer_class = fpserializers.ProjectNestedSerializer


###############################################################################
#    CUSTOM VIEWS
###############################################################################

class TraitListByTrial(generics.ListAPIView):
    """
    Get traits belonging to trial.
    """
    serializer_class = fpserializers.TraitSerializer

    def get_queryset(self):
        """
        This view should return a list of all models by
        the maker passed in the URL
        """
        uuid = self.kwargs['uuid']
        trial = fpmodels.Trial.objects.get(uuid=uuid)
        return trial._traits



class ProjectMemberList(generics.ListAPIView):
    """
    List all snippets, or create a new snippet.
    """
    serializer_class = UserSerializer

    def get_queryset(self):
        """
        This view should return a list of all the purchases for
        the user as determined by the username portion of the URL.
        """
        if 'project_id' in self.kwargs:
            project_id = self.kwargs['project_id']
            return fpmodels.User.objects.filter(project__id=project_id)
        else:
            return fpmodels.User.objects.all()




