from django.contrib import admin
from .models import KnowledgeBase

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_name', 'get_city', 'get_rating')
    search_fields = ('content', 'metadata')
    
    def get_name(self, obj):
        return obj.metadata.get('name', 'N/A') if obj.metadata else 'N/A'
    get_name.short_description = 'Name'
    
    def get_city(self, obj):
        return obj.metadata.get('city', 'N/A') if obj.metadata else 'N/A'
    get_city.short_description = 'City'
    
    def get_rating(self, obj):
        return obj.metadata.get('rating', 'N/A') if obj.metadata else 'N/A'
    get_rating.short_description = 'Rating'