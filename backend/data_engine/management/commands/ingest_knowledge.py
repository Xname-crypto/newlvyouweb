import os
import pandas as pd
import requests
import json
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from supabase import create_client, Client
import environ

class Command(BaseCommand):
    help = 'Ingest knowledge from Excel to Supabase Vector DB'

    def handle(self, *args, **options):
        # Configuration
        env = environ.Env()
        
        ZHIPU_API_KEY = env("ZHIPU_API_KEY", default="")
        SUPABASE_URL = env("SUPABASE_URL", default="") or env("VITE_SUPABASE_URL", default="")
        
        # Determine excel path relative to project root
        EXCEL_PATH = settings.BASE_DIR.parent / "旅游景点.xlsx"

        # ZhipuAI Embedding Config
        EMBEDDING_URL = "https://open.bigmodel.cn/api/paas/v4/embeddings"
        # Try to get service role key, fallback to anon key for testing (though anon key might not have write access to all tables)
        # In a real scenario, you MUST use SERVICE_ROLE_KEY for backend operations to bypass RLS or write to protected tables.
        # Since we don't have SERVICE_ROLE_KEY in .env based on previous reads, let's try to read it if it exists, or use ANON key and hope RLS allows it (or we fix .env).
        # Actually, looking at .env, we only have VITE_SUPABASE_ANON_KEY. 
        # For the purpose of this demo with local SQLite, we are MOCKING the ingestion into local DB?
        # WAIT, this script connects to SUPABASE.
        # If we want to populate the Django Admin (which is looking at SQLite now), we need to write to SQLite, NOT Supabase.
        
        # Correction: The user wants to see data in the "Knowledge Base Management" page.
        # That page fetches from Django API -> Django ViewSet -> Django Model -> SQLite DB (currently).
        # So we should ingest data into the LOCAL SQLite database, not Supabase remote.
        
        # Let's rewrite this script to save to local Django models instead of Supabase client.
        
        from data_engine.models import KnowledgeBase

        # ... (rest of the script logic to read excel)
        
        if not os.path.exists(EXCEL_PATH):
            self.stderr.write(self.style.ERROR(f"Excel file not found at {EXCEL_PATH}"))
            return

        self.stdout.write("Reading Excel file...")
        df = pd.read_excel(EXCEL_PATH)
        df = df.fillna("")

        self.stdout.write(self.style.SUCCESS(f"Found {len(df)} rows. Starting ingestion into Local SQLite..."))

        for index, row in df.iterrows():
            name = row.get("名称", row.get("name", "Unknown"))
            city = row.get("城市", row.get("city", ""))
            address = row.get("地址", row.get("address", ""))
            intro = row.get("简介", row.get("introduction", ""))
            level = row.get("等级", row.get("level", ""))
            price = row.get("价格", row.get("price", 0))
            rating = row.get("评分", row.get("rating", 0))
            
            content = f"""
景点名称：{name}
位置：{city} {address}
等级：{level}
评分：{rating}
价格：{price}
简介：{intro}
""".strip()

            self.stdout.write(f"Processing [{index+1}/{len(df)}]: {name}")
            
            # Prepare Metadata
            metadata = {
                "name": name,
                "city": city,
                "level": level,
                "price": price,
                "rating": rating,
                "address": address
            }

            # Save to Django Model (SQLite)
            KnowledgeBase.objects.create(
                content=content,
                metadata=metadata
            )
            
        self.stdout.write(self.style.SUCCESS("Ingestion complete!"))
