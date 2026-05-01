"""
URL configuration for lvyou_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from data_engine.views import (
    EmbeddingProfileViewSet,
    KnowledgeBaseViewSet,
    AdminQATestSessionViewSet,
    rag_chat,
    rag_upload_knowledge,
    api_providers_public,
    api_provider_update_config,
)
from data_engine.discovery_views import (
    booking_intents,
    discovery_recommendations,
    discovery_spot_detail,
    discovery_spots,
    itinerary_add_item,
    itinerary_delete_item,
    itinerary_list,
)
from datasource_manager.views import DataSourceViewSet

router = DefaultRouter()
router.register(r'knowledge', KnowledgeBaseViewSet, basename='knowledge')
router.register(r'datasources', DataSourceViewSet, basename='datasources')
router.register(r'embedding-profiles', EmbeddingProfileViewSet, basename='embedding-profiles')
router.register(r'admin-qa-sessions', AdminQATestSessionViewSet, basename='admin-qa-sessions')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    
    # RAG Endpoints
    path('api/rag/chat/', rag_chat, name='rag_chat'),
    path('api/rag/upload/', rag_upload_knowledge, name='rag_upload'),
    path('api/api-providers/public/', api_providers_public, name='api_providers_public'),
    path('api/api-providers/update-config/', api_provider_update_config, name='api_provider_update_config'),
    path('api/discovery/spots/', discovery_spots, name='discovery_spots'),
    path('api/discovery/spots/<str:spot_key>/', discovery_spot_detail, name='discovery_spot_detail'),
    path('api/discovery/recommendations/', discovery_recommendations, name='discovery_recommendations'),
    path('api/itinerary/', itinerary_list, name='itinerary_list'),
    path('api/itinerary/items/', itinerary_add_item, name='itinerary_add_item'),
    path('api/itinerary/items/<int:item_id>/', itinerary_delete_item, name='itinerary_delete_item'),
    path('api/booking-intents/', booking_intents, name='booking_intents'),
]
