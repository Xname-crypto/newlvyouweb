from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import connections, DatabaseError
from django.conf import settings
from django.http import StreamingHttpResponse
from .models import DataSource
from .serializers import DataSourceSerializer
import os
import time
import json
from supabase import create_client
from data_engine.utils import get_embedding

class DataSourceViewSet(viewsets.ModelViewSet):
    queryset = DataSource.objects.all().order_by('-created_at')
    serializer_class = DataSourceSerializer
    
    # In production, add permission_classes = [IsAdminUser]
    
    def get_dynamic_connection(self, instance):
        """
        Dynamically configures a Django database connection for this request.
        """
        db_alias = f"dynamic_db_{instance.id}"
        db_config = instance.get_connection_settings()
        
        # Check if configuration changed or not exists
        if db_alias not in settings.DATABASES:
            settings.DATABASES[db_alias] = db_config
            
        # Force close old connection if settings might have changed (simple approach)
        if db_alias in connections:
            connections[db_alias].close()
            
        return db_alias

    @action(detail=False, methods=['post'], url_path='test_connection')
    def test_connection_dry(self, request):
        """
        Test connection parameters without saving (Dry Run).
        """
        data = request.data
        # Create a temporary unsaved instance to use logic
        try:
            temp_instance = DataSource(
                type=data.get('type'),
                host=data.get('host'),
                port=data.get('port', 3306),
                user=data.get('user'),
                database_name=data.get('database_name'),
                file_path=data.get('file_path')
            )
            # Manually set password property (which encrypts it, but we need raw for connection config)
            # Actually get_connection_settings uses .password property which decrypts .password_encrypted
            # So we set .password setter
            temp_instance.password = data.get('password')
            
            db_config = temp_instance.get_connection_settings()
            
            # Manually try to connect using Django's backend
            # We can't easily add to settings.DATABASES safely for a temp test without a unique alias
            # Let's try to import the specific backend wrapper manually or just use a temp alias
            
            temp_alias = "test_connection_temp"
            settings.DATABASES[temp_alias] = db_config
            
            conn = connections[temp_alias]
            try:
                conn.connect()
                conn.close()
                del settings.DATABASES[temp_alias]
                return Response({'message': 'Connection successful!'}, status=status.HTTP_200_OK)
            except Exception as e:
                if temp_alias in settings.DATABASES:
                    del settings.DATABASES[temp_alias]
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='tables')
    def get_tables(self, request, pk=None):
        """
        List all tables in the database.
        """
        instance = self.get_object()
        db_alias = self.get_dynamic_connection(instance)
        
        try:
            conn = connections[db_alias]
            # Use Django introspection
            with conn.cursor() as cursor:
                table_list = conn.introspection.get_table_list(cursor)
                # table_list is a list of TableInfo objects (name, type)
                tables = [t.name for t in table_list]
                return Response(tables)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='preview/(?P<table_name>[^/.]+)')
    def preview_table(self, request, pk=None, table_name=None):
        """
        Preview first 100 rows of a table.
        """
        instance = self.get_object()
        db_alias = self.get_dynamic_connection(instance)
        
        try:
            conn = connections[db_alias]
            with conn.cursor() as cursor:
                # Basic SQL injection prevention: table_name is from URL, but we should verify it exists
                # 1. Verify table exists
                clean_table_name = table_name # In production, validate against get_tables list
                
                # 2. Get columns
                # Using introspection is safer
                # description = conn.introspection.get_table_description(cursor, clean_table_name)
                # columns = [col.name for col in description]
                
                # Simple Select
                # Quote table name based on backend?
                ops = conn.ops
                qn = ops.quote_name
                
                query = f"SELECT * FROM {qn(clean_table_name)} LIMIT 100"
                cursor.execute(query)
                
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                # Convert rows (tuples) to list of dicts
                data = []
                for row in rows:
                    item = {}
                    for i, col in enumerate(columns):
                        item[col] = row[i]
                    data.append(item)
                    
                return Response({
                    'columns': columns,
                    'data': data
                })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='ingest/(?P<table_name>[^/.]+)')
    def ingest_table(self, request, pk=None, table_name=None):
        """
        Ingest a table into the knowledge base.
        """
        instance = self.get_object()
        db_alias = self.get_dynamic_connection(instance)
        
        # Get parameters
        content_columns = request.data.get('content_columns', [])
        metadata_columns = request.data.get('metadata_columns', [])
        limit = int(request.data.get('limit', 100))
        
        # Supabase setup
        SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL", "")
        SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY", "")
        
        if not SUPABASE_URL or not SUPABASE_KEY:
             return Response({'error': 'Supabase credentials not configured.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
             
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
             return Response({'error': f'Supabase Init Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        def ingest_generator():
            try:
                conn = connections[db_alias]
                with conn.cursor() as cursor:
                    ops = conn.ops
                    qn = ops.quote_name
                    
                    # Basic SQL injection prevention for table name done by qn
                    # Fetch data
                    query = f"SELECT * FROM {qn(table_name)} LIMIT {limit}"
                    cursor.execute(query)
                    
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    
                    total_rows = len(rows)
                    if total_rows == 0:
                        yield json.dumps({"progress": 100, "done": True, "message": "No data found in table."}) + "\n"
                        return

                    # If content_columns not specified, use all
                    nonlocal content_columns
                    if not content_columns:
                        content_columns = columns
                        
                    processed_count = 0
                    errors = 0
                    
                    for i, row in enumerate(rows):
                        # Convert row to dict
                        row_dict = {}
                        for j, col in enumerate(columns):
                            row_dict[col] = row[j]
                            
                        # Build Content
                        content_parts = []
                        for col in content_columns:
                            val = row_dict.get(col)
                            if val is not None:
                                content_parts.append(f"{col}: {val}")
                        content = "\n".join(content_parts)
                        
                        if not content.strip():
                            continue
                            
                        # Build Metadata
                        metadata = {
                            "source": f"datasource_{instance.id}_{table_name}",
                            "original_id": str(row_dict.get('id', 'unknown')),
                            "category": f"DB_{table_name}"
                        }
                        for col in metadata_columns:
                            val = row_dict.get(col)
                            if val is not None:
                                # Supabase metadata is JSON, ensure serializable
                                metadata[col] = str(val) 
                                
                        # Generate Embedding
                        embedding = None
                        try:
                            embedding = get_embedding(content)
                        except Exception as e:
                            print(f"Embedding error: {e}")
                            
                        # Insert into Supabase
                        payload = {
                            "content": content,
                            "metadata": metadata,
                        }
                        if embedding:
                            payload['embedding'] = embedding
                            
                        try:
                            supabase.table("knowledge_base").insert(payload).execute()
                            processed_count += 1
                        except Exception as e:
                            print(f"Insert error: {e}")
                            errors += 1
                            
                        # Rate limit slightly
                        time.sleep(0.05) 
                        
                        # Yield progress
                        progress = int(((i + 1) / total_rows) * 100)
                        yield json.dumps({
                            "progress": progress,
                            "processed": processed_count,
                            "total": total_rows,
                            "errors": errors
                        }) + "\n"
                        
                    yield json.dumps({
                        "progress": 100,
                        "done": True,
                        "message": f'Ingestion complete. {processed_count} rows processed.',
                        "errors": errors
                    }) + "\n"
                    
            except Exception as e:
                yield json.dumps({"error": str(e)}) + "\n"

        return StreamingHttpResponse(ingest_generator(), content_type='application/x-ndjson')
