# Product Importer - Acme Inc.

A production-ready web application for importing and managing up to 500,000 products from CSV files into a PostgreSQL database.

## 🎯 Features

### ✅ Story 1 & 1A: CSV Upload with Real-Time Progress
- Upload large CSV files (up to 1GB)
- Real-time progress tracking with auto-refresh (every 2 seconds)
- Visual progress bar with detailed metrics (Processed, Created, Updated, Errors)
- Force stop functionality for long-running imports
- Case-insensitive SKU matching with automatic upsert

### ✅ Story 2: Product Management
- Complete CRUD operations (Create, Read, Update, Delete)
- Advanced filtering by SKU, name, and active status
- Paginated product list (20 products per page)
- Modal forms for creating and editing products
- Deletion with confirmation dialogs

### ✅ Story 3: Bulk Delete
- Delete all products with double confirmation
- Visual feedback during processing
- Success/failure notifications

### ✅ Story 4: Webhook Management
- Add, edit, test, and delete webhooks
- Configure event types (All Events, Create, Update, Delete, Import Complete)
- Enable/disable webhooks
- Visual confirmation of test triggers

## 🎨 Design

Premium UI inspired by modern SaaS products (Stripe, Linear, Vercel):
- Purple-to-blue gradient aesthetic
- Floating white card design with soft shadows
- Modern progress bar with shimmer animation
- Glowing hover states
- Professional typography (Inter/SF Pro style)
- Fully responsive layout

## 🛠️ Tech Stack

- **Backend:** Flask (Python)
- **Async Processing:** Celery with Redis
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Deployment:** Render

## 📋 Requirements

- Python 3.9+
- PostgreSQL 15+
- Redis 7+

## 🚀 Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/gchittora/Fulfil_Assignment.git
cd Fulfil_Assignment
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL

```bash
# Create database
createdb product_importer
```

### 5. Set Up Environment Variables

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql://localhost:5432/product_importer
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_APP=app.py
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=1073741824
```

### 6. Initialize Database

```bash
python -c "from app import db; db.create_all()"
```

### 7. Start Redis

```bash
redis-server
```

### 8. Start Celery Worker

In a new terminal:
```bash
source venv/bin/activate
celery -A celery_app.celery worker --loglevel=info --concurrency=1
```

### 9. Start Flask App

In another terminal:
```bash
source venv/bin/activate
python app.py
```

### 10. Access the Application

Open your browser to: http://localhost:5000/ui


Design inspired by modern SaaS products: Stripe, Linear, Vercel.
