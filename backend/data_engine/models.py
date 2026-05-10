from django.db import models
from django.db.models import Q


class EmbeddingProfile(models.Model):
    """Embedding 配置模板，管理员可创建不同量化级别的配置"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)                                    # 配置名称，如"轻量级"
    embedding_model = models.CharField(max_length=200)                        # huggingface 模型名
    quantization = models.CharField(max_length=20, blank=True, default="")   # "4bit"/"8bit"/"" 定量
    chunk_size = models.IntegerField(default=800)
    chunk_overlap = models.IntegerField(default=120)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'embedding_profile'
        managed = True
        verbose_name = 'Embedding 配置'
        verbose_name_plural = 'Embedding 配置列表'

    def __str__(self):
        q_str = f" ({self.quantization})" if self.quantization else ""
        return f"{self.name}{q_str}"


class KnowledgeBase(models.Model):
    STATUS_CHOICES = [
        ("pending_review", "???"),
        ("active", "???"),
        ("rejected", "???"),
        ("archived", "???"),
    ]
    KIND_CHOICES = [
        ("knowledge_base", "???"),
        ("dataset", "???"),
        ("document", "??"),
    ]

    id = models.BigAutoField(primary_key=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="document", db_index=True)
    parent_knowledge_base = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='child_documents'
    )
    content = models.TextField(blank=True, default="")
    metadata = models.JSONField(blank=True, null=True)
    collection_name = models.CharField(max_length=200, blank=True, default="")
    embedding_profile = models.ForeignKey(
        EmbeddingProfile, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="knowledge_bases"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    version = models.IntegerField(default=1)
    supersedes = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'knowledge_base'
        managed = True
        verbose_name = '?????'
        verbose_name_plural = '???????'
        ordering = ["-updated_at"]

    def __str__(self):
        if self.metadata and isinstance(self.metadata, dict):
            return self.metadata.get("name", f"KB {self.id}")
        return f"KB {self.id}"

class TravelScraperSight(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    introduce = models.TextField()
    score = models.CharField(max_length=20)
    position = models.CharField(max_length=255)
    grade = models.CharField(max_length=100)
    images = models.TextField() # longtext
    comments = models.TextField() # longtext
    url = models.CharField(max_length=200)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    city_id = models.BigIntegerField()

    class Meta:
        managed = False # This table already exists in MySQL
        db_table = 'travel_scraper_sight'


class AdminQATestSession(models.Model):
    STATUS_CHOICES = [
        ("draft", "草稿"),
        ("passed", "已通过"),
        ("failed", "未通过"),
    ]

    id = models.BigAutoField(primary_key=True)
    admin_user_id = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=200, default="新建测试")
    knowledge_base = models.ForeignKey(
        KnowledgeBase,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="qa_test_sessions",
    )
    provider_id = models.CharField(max_length=100, blank=True, default="")
    provider_name = models.CharField(max_length=200, blank=True, default="")
    model_name = models.CharField(max_length=200, blank=True, default="")
    mode = models.CharField(max_length=20, blank=True, default="normal")
    use_web_search = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    release_enabled = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")
    latest_question = models.TextField(blank=True, default="")
    latest_answer = models.TextField(blank=True, default="")
    latest_latency_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'admin_qa_test_session'
        managed = True
        ordering = ["-updated_at", "-id"]

    def __str__(self):
        return self.title or f"QA Session {self.id}"


class AdminQATestMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "用户"),
        ("assistant", "助手"),
    ]

    id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(
        AdminQATestSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    sources = models.JSONField(blank=True, default=list)
    citations = models.JSONField(blank=True, default=list)
    latency_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_qa_test_message'
        managed = True
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.role}: {self.content[:32]}"

class FinalCompleteDataset(models.Model):
    # This table has no primary key, Django requires one.
    # We will treat 'name' or a composite as ID, or use row_number if possible, 
    # but for simple read-only access we can try to use 'name' if unique, or add a managed=False warning.
    # Given the schema, let's assume we can read it but might have issues with specific row selection if no unique ID.
    # We'll map fields based on inspect output.
    
    name = models.CharField(max_length=255, primary_key=True) # Assuming name is unique enough for display
    city = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    province = models.CharField(max_length=255)
    star_rating = models.CharField(max_length=255)
    score = models.CharField(max_length=255)
    price = models.CharField(max_length=255)
    sales_volume = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    is_free = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    longitude = models.CharField(max_length=255)
    latitude = models.CharField(max_length=255)
    source = models.CharField(max_length=255)
    keywords = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'final_complete_dataset'


class TravelItineraryItem(models.Model):
    user_id = models.CharField(max_length=64, db_index=True)
    spot_key = models.CharField(max_length=120)
    spot_name = models.CharField(max_length=255)
    city = models.CharField(max_length=255, blank=True, default="")
    price = models.FloatField(default=0)
    rating = models.FloatField(default=0)
    cover_image = models.TextField(blank=True, default="")
    recommendation_reason = models.CharField(max_length=255, blank=True, default="")
    tags = models.JSONField(blank=True, default=list)
    spot_snapshot = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "travel_itinerary_item"
        managed = True
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["user_id", "spot_key"], name="unique_itinerary_spot_per_user"),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.spot_name}"


class TravelBookingIntent(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("reviewed", "Reviewed"),
        ("contacted", "Contacted"),
        ("archived", "Archived"),
    ]

    user_id = models.CharField(max_length=64, db_index=True)
    trip_name = models.CharField(max_length=200, blank=True, default="")
    contact_name = models.CharField(max_length=100, blank=True, default="")
    contact_phone = models.CharField(max_length=40, blank=True, default="")
    note = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_estimated_cost = models.FloatField(default=0)
    items = models.JSONField(blank=True, default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "travel_booking_intent"
        managed = True
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.trip_name or f"Booking Intent {self.id}"


class TravelDiscoverySignal(models.Model):
    SIGNAL_CHOICES = [
        ("view", "View"),
        ("itinerary_add", "Itinerary Add"),
        ("booking_intent", "Booking Intent"),
    ]

    user_id = models.CharField(max_length=64, db_index=True)
    spot_key = models.CharField(max_length=120, db_index=True)
    signal_type = models.CharField(max_length=30, choices=SIGNAL_CHOICES)
    payload = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "travel_discovery_signal"
        managed = True
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.user_id}:{self.signal_type}:{self.spot_key}"


class Product(models.Model):
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=80, blank=True, default="")
    image_url = models.TextField(blank=True, default="")
    price_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=8, default="CNY")
    is_active = models.BooleanField(default=True)
    stock_total = models.PositiveIntegerField(default=0)
    stock_reserved = models.PositiveIntegerField(default=0)
    stock_sold = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        managed = True
        ordering = ["-updated_at", "-id"]

    @property
    def available_stock(self) -> int:
        return max(0, int(self.stock_total or 0) - int(self.stock_reserved or 0) - int(self.stock_sold or 0))

    def __str__(self):
        return f"{self.sku}:{self.name}"


class CommerceOrder(models.Model):
    STATUS_CHOICES = [
        ("pending_payment", "Pending Payment"),
        ("payment_created", "Payment Created"),
        ("paid", "Paid"),
        ("payment_failed", "Payment Failed"),
        ("canceled", "Canceled"),
        ("expired", "Expired"),
    ]
    PAYMENT_METHOD_CHOICES = [
        ("alipay", "Alipay"),
    ]

    order_no = models.CharField(max_length=32, unique=True, db_index=True)
    user_id = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default="pending_payment", db_index=True)
    subtotal_cents = models.PositiveIntegerField(default=0)
    shipping_cents = models.PositiveIntegerField(default=0)
    discount_cents = models.PositiveIntegerField(default=0)
    total_amount_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=8, default="CNY")
    payment_method = models.CharField(max_length=16, choices=PAYMENT_METHOD_CHOICES, default="alipay")
    shipping_method = models.CharField(max_length=80, blank=True, default="standard")
    shipping_address = models.JSONField(blank=True, default=dict)
    contact_email = models.EmailField(blank=True, default="")
    contact_phone = models.CharField(max_length=40, blank=True, default="")
    note = models.TextField(blank=True, default="")
    paid_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commerce_orders"
        managed = True
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.order_no}:{self.status}"


class CommerceOrderItem(models.Model):
    order = models.ForeignKey(CommerceOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name="commerce_order_items")
    product_snapshot = models.JSONField(blank=True, default=dict)
    sku = models.CharField(max_length=64, blank=True, default="")
    name = models.CharField(max_length=200)
    image_url = models.TextField(blank=True, default="")
    unit_price_cents = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=1)
    line_total_cents = models.PositiveIntegerField(default=0)
    selected_size = models.CharField(max_length=40, blank=True, default="")
    selected_color = models.CharField(max_length=80, blank=True, default="")
    cart_item_id = models.CharField(max_length=160, blank=True, default="")
    metadata = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "commerce_order_items"
        managed = True
        ordering = ["id"]

    def __str__(self):
        return f"{self.order_id}:{self.sku or self.name} x {self.quantity}"


class PaymentOrder(models.Model):
    STATUS_CHOICES = [
        ("pending_payment", "Pending Payment"),
        ("payment_created", "Payment Created"),
        ("paid", "Paid"),
        ("payment_failed", "Payment Failed"),
        ("canceled", "Canceled"),
        ("expired", "Expired"),
    ]
    PAYMENT_TYPE_CHOICES = [
        ("alipay", "Alipay"),
        ("wxpay", "WeChat Pay"),
    ]

    user_id = models.CharField(max_length=64, db_index=True)
    commerce_order = models.ForeignKey(CommerceOrder, null=True, blank=True, on_delete=models.SET_NULL, related_name="payments")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    product_snapshot = models.JSONField(blank=True, default=dict)
    quantity = models.PositiveIntegerField(default=1)
    unit_price_cents = models.PositiveIntegerField(default=0)
    total_amount_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=8, default="CNY")
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default="pending_payment", db_index=True)
    payment_provider = models.CharField(max_length=24, default="zpay")
    payment_type = models.CharField(max_length=16, choices=PAYMENT_TYPE_CHOICES, default="alipay")
    out_trade_no = models.CharField(max_length=32, unique=True, db_index=True)
    zpay_trade_no = models.CharField(max_length=80, blank=True, default="")
    zpay_order_id = models.CharField(max_length=80, blank=True, default="")
    pay_url = models.TextField(blank=True, default="")
    client_request_id = models.CharField(max_length=80, blank=True, default="", db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment_orders"
        managed = True
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "client_request_id"],
                condition=~Q(client_request_id=""),
                name="unique_payment_order_client_request_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.out_trade_no}:{self.status}"


class PaymentEvent(models.Model):
    order = models.ForeignKey(PaymentOrder, null=True, blank=True, on_delete=models.SET_NULL, related_name="events")
    source = models.CharField(max_length=24, default="zpay")
    event_type = models.CharField(max_length=40, default="notify")
    signature_valid = models.BooleanField(default=False)
    amount_matches = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    payload = models.JSONField(blank=True, default=dict)
    message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_events"
        managed = True
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.source}:{self.event_type}:{self.processed}"
