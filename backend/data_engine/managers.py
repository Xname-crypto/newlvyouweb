from django.db import models
from supabase import create_client
import os

# Use environment variables or settings
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

class SupabaseQuerySet(models.QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        super().__init__(model, query, using, hints)
        # Initialize Supabase client
        if SUPABASE_URL and SUPABASE_KEY:
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        else:
            self.supabase = None
        
    def _fetch_all(self):
        if self._result_cache is None:
            if not self.supabase:
                self._result_cache = []
                return

            try:
                # Basic implementation: fetch all records from Supabase
                # Note: This does not support complex Django filtering/ordering yet
                response = self.supabase.table(self.model._meta.db_table).select("*").execute()
                
                results = []
                for item in response.data:
                    # Map Supabase data to model instances
                    obj = self.model()
                    for field in self.model._meta.fields:
                        if field.name in item:
                            setattr(obj, field.name, item[field.name])
                    
                    # Store original data for updates
                    obj._state.adding = False
                    obj._state.db = self.db
                    results.append(obj)
                
                self._result_cache = results
            except Exception as e:
                print(f"Supabase fetch error: {e}")
                self._result_cache = []

    def count(self):
        if not self.supabase:
            return 0
        response = self.supabase.table(self.model._meta.db_table).select("*", count="exact").execute()
        return response.count

    def create(self, **kwargs):
        if not self.supabase:
            raise Exception("Supabase credentials missing")
            
        # Prepare data for Supabase
        data = {}
        for key, value in kwargs.items():
            if key in [f.name for f in self.model._meta.fields if f.name != 'id']:
                data[key] = value
                
        # Insert into Supabase
        response = self.supabase.table(self.model._meta.db_table).insert(data).execute()
        
        if response.data:
            item = response.data[0]
            obj = self.model()
            for field in self.model._meta.fields:
                if field.name in item:
                    setattr(obj, field.name, item[field.name])
            obj._state.adding = False
            obj._state.db = self.db
            return obj
        return None

class SupabaseManager(models.Manager):
    def get_queryset(self):
        return SupabaseQuerySet(self.model, using=self._db)
