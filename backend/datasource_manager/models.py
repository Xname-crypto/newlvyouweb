from django.db import models
from cryptography.fernet import Fernet
from django.conf import settings
import base64

# Simple encryption key (In production, this should be in env vars)
# We derive it from SECRET_KEY to make it reproducible
def get_cipher_suite():
    # Fernet key must be 32 url-safe base64-encoded bytes
    # Pad or slice SECRET_KEY to ensure 32 bytes
    key_bytes = settings.SECRET_KEY.encode()[:32]
    if len(key_bytes) < 32:
        key_bytes = key_bytes.ljust(32, b'x')
    
    return Fernet(base64.urlsafe_b64encode(key_bytes))

class DataSource(models.Model):
    DB_TYPES = (
        ('mysql', 'MySQL'),
        ('postgresql', 'PostgreSQL / Supabase'),
        ('sqlite', 'SQLite'),
    )

    name = models.CharField(max_length=100, unique=True, verbose_name="连接名称")
    type = models.CharField(max_length=20, choices=DB_TYPES, verbose_name="数据库类型")
    
    host = models.CharField(max_length=255, blank=True, null=True, verbose_name="主机地址")
    port = models.IntegerField(default=3306, blank=True, null=True, verbose_name="端口")
    user = models.CharField(max_length=100, blank=True, null=True, verbose_name="用户名")
    password_encrypted = models.CharField(max_length=500, blank=True, null=True, verbose_name="密码(加密)")
    database_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="数据库名")
    
    # For SQLite
    file_path = models.CharField(max_length=500, blank=True, null=True, verbose_name="文件路径")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "数据源"
        verbose_name_plural = "数据源管理"

    @property
    def password(self):
        if not self.password_encrypted:
            return None
        try:
            cipher = get_cipher_suite()
            return cipher.decrypt(self.password_encrypted.encode()).decode()
        except Exception as e:
            return None

    @password.setter
    def password(self, value):
        if value:
            cipher = get_cipher_suite()
            self.password_encrypted = cipher.encrypt(value.encode()).decode()
        else:
            self.password_encrypted = None

    def get_connection_settings(self):
        """Returns Django DATABASES settings dict for this source"""
        config = {}
        if self.type == 'sqlite':
            config = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': self.file_path,
            }
        elif self.type == 'mysql':
            config = {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': self.database_name,
                'USER': self.user,
                'PASSWORD': self.password,
                'HOST': self.host,
                'PORT': str(self.port),
                'OPTIONS': {
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                    'charset': 'utf8mb4',
                },
                # Use standard Django keys, remove unsupported ones
                'TIME_ZONE': None, 
                'CONN_MAX_AGE': 0,
                'CONN_HEALTH_CHECKS': False,
                'AUTOCOMMIT': True,
                'ATOMIC_REQUESTS': False,
            }
        elif self.type == 'postgresql':
            config = {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': self.database_name,
                'USER': self.user,
                'PASSWORD': self.password,
                'HOST': self.host,
                'PORT': str(self.port),
            }
        return config
