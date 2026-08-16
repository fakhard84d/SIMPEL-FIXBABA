# FixBaba - Home Appliance Repair Platform

یک پلتفرم حرفه‌ای و امن برای مدیریت درخواست‌های تعمیر لوازم خانگی با احراز هویت بدون رمز عبور (Passwordless Authentication).

## ویژگی‌های کلیدی

### 🔐 امنیت پیشرفته
- **Magic Link Authentication**: ورود بدون رمز عبور از طریق لینک امن SMS
- **Token Hashing**: ذخیره توکن به صورت SHA-256 + Pepper
- **Device Sessions**: شناسایی دستگاه‌های معتبر با Cookie امن HttpOnly
- **Quota Management**: محدودیت 5 بار مصرف برای هر لینک
- **Race Condition Protection**: استفاده از `select_for_update()` برای جلوگیری از سوءاستفاده همزمان
- **Rate Limiting**: محدودیت تعداد درخواست بر اساس IP و Token

### 📱 Customer Portal
- داشبورد ساده و کاربرپسند
- ثبت درخواست تعمیر در چند مرحله
- آپلود عکس با Drag & Drop
- مشاهده وضعیت درخواست‌ها
- کاملاً Responsive و Mobile-First

### 🛡️ Upload Security
- بررسی MIME Type
- محدودیت حجم فایل (قابل تنظیم)
- حذف EXIF Metadata
- Re-encoding تصاویر
- تولید Thumbnail خودکار
- UUID Filename برای جلوگیری از Overwrite

### 🎨 UI/UX
- تم Premium Dark Navy + Orange
- فونت Vazirmatn
- RTL کامل
- طراحی Modern و Minimal
- انیمیشن‌های ظریف

## ساختار پروژه

```
fixbaba/
├── config/                 # Django settings & URLs
├── apps/
│   ├── customers/         # Customer models & views
│   ├── authentication/    # Magic Link auth
│   ├── service_requests/  # Request management
│   ├── media/             # File upload handling
│   ├── audit/             # Audit logging
│   └── dashboard/         # Public pages
├── templates/
│   ├── public/            # Landing page
│   ├── portal/            # Customer portal
│   └── errors/            # Error pages
├── static/                # CSS, JS, images
├── media_uploads/         # Uploaded files
└── tests/                 # Test suite
```

## نصب و راه‌اندازی

### روش Docker (توصیه شده)

```bash
# کپی فایل environment
cp .env.example .env

# ویرایش مقادیر در .env
# SECRET_KEY، DATABASE_URL و سایر تنظیمات را تغییر دهید

# اجرای سرویس‌ها
docker-compose up -d

# ایجاد migrations
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# ایجاد superuser
docker-compose exec web python manage.py createsuperuser

# جمع‌آوری static files
docker-compose exec web python manage.py collectstatic --noinput
```

### روش معمولی

```bash
# ایجاد virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# یا venv\Scripts\activate  # Windows

# نصب dependencies
pip install -r requirements.txt

# کپی .env
cp .env.example .env

# تنظیم database
createdb fixbaba_db

# migrations
python manage.py makemigrations
python manage.py migrate

# ایجاد superuser
python manage.py createsuperuser

# اجرای سرور
python manage.py runserver
```

## محیط‌های متغیر (Environment Variables)

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | False |
| `DATABASE_URL` | PostgreSQL connection | Required |
| `REDIS_URL` | Redis connection | redis://localhost:6379/0 |
| `SERVER_PEPPER` | Pepper for token hashing | Required |
| `MAGIC_LINK_EXPIRATION_MINUTES` | Link validity | 10080 (7 days) |
| `MAGIC_LINK_MAX_ACTIVATIONS` | Max activations | 5 |
| `DEVICE_SESSION_DAYS` | Session duration | 90 |
| `MAX_UPLOAD_SIZE_MB` | Max file size | 5 |
| `MAX_IMAGES_PER_REQUEST` | Max images | 5 |

## API Endpoints

### Public
- `GET /` - Landing page
- `GET /access/<token>/` - Magic link authentication

### Customer Portal (requires auth)
- `GET /portal/` - Dashboard
- `GET /portal/requests/` - Request list
- `GET /portal/requests/new/` - Create request
- `POST /portal/requests/new/` - Submit request
- `GET /portal/requests/<id>/` - Request detail
- `GET /portal/profile/` - User profile
- `POST /portal/logout-all/` - Logout all devices

### Admin
- `GET /secure-admin/` - Django admin panel

## امنیت

### Security Checklist

✅ Token hashing with SHA-256 + Pepper  
✅ Secure HttpOnly cookies for device sessions  
✅ CSRF protection on all forms  
✅ Rate limiting on authentication endpoints  
✅ SQL injection prevention (Django ORM)  
✅ XSS protection (template auto-escaping)  
✅ Clickjacking protection (X-Frame-Options)  
✅ Content-Type sniffing prevention  
✅ Referrer policy (no-referrer)  
✅ HSTS in production  
✅ SSL redirect in production  
✅ File upload validation (MIME, size, extension)  
✅ Image re-encoding to remove metadata  
✅ Object-level authorization  
✅ Audit logging for sensitive actions  
✅ No sensitive data in logs  

### Production Deployment Checklist

☐ Set `DEBUG = False`  
☐ Configure proper `ALLOWED_HOSTS`  
☐ Set strong `SECRET_KEY` and `SERVER_PEPPER`  
☐ Enable HTTPS with valid certificate  
☐ Configure PostgreSQL database  
☐ Set up Redis for caching/sessions  
☐ Configure static file serving (WhiteNoise/CDN)  
☐ Set up media storage (S3/MinIO recommended)  
☐ Configure email/SMS backend  
☐ Set up backup strategy  
☐ Configure monitoring and alerting  
☐ Set up log aggregation  
☐ Review security headers  
☐ Test rate limiting  
☐ Verify SSL/TLS configuration  
☐ Run security audit tests  

## تست

```bash
# اجرای تمام تست‌ها
python manage.py test

# تست‌های خاص
python manage.py test apps.authentication.tests
python manage.py test apps.service_requests.tests

# با coverage
coverage run --source='.' manage.py test
coverage report
```

## مجوز

© ۱۴۰۳ FixBaba - تمامی حقوق محفوظ است.
