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

## 📦 Deployment to Render

### Option 1: Using render.yaml (Recommended)

1. Push code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click "New" → "Blueprint"
4. Connect your GitHub repository
5. Render will automatically detect `render.yaml` and create:
   - Web Service (Flask app)
   - Worker Service (Celery worker)
   - PostgreSQL Database
   - Redis Instance

### Option 2: Manual Setup

1. **Create PostgreSQL Database:**
   - New → PostgreSQL
   - Name: `product-importer-db`
   - Note the Internal Database URL

2. **Create Redis Instance:**
   - New → Redis
   - Name: `product-importer-redis`
   - Note the Internal Redis URL

3. **Create Web Service:**
   - New → Web Service
   - Connect GitHub repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Add Environment Variables:
     - `DATABASE_URL` (from PostgreSQL)
     - `REDIS_URL` (from Redis)
     - `SECRET_KEY` (generate random string)
     - `FLASK_ENV=production`
     - `UPLOAD_FOLDER=uploads`
     - `MAX_CONTENT_LENGTH=1073741824`

4. **Create Worker Service:**
   - New → Background Worker
   - Connect same GitHub repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `celery -A celery_app.celery worker --loglevel=info --concurrency=1`
   - Add same environment variables as Web Service

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  User Browser                                            │
│  http://your-app.onrender.com                          │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP Requests
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Flask Web Server (Gunicorn)                            │
│  - Handles HTTP requests                                │
│  - Serves UI                                            │
│  - Queues background tasks                              │
└────────────────┬────────────────────────────────────────┘
                 │ Task Queue
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Redis (Message Broker)                                 │
│  - Stores task queue                                    │
│  - Stores progress updates                              │
└────────────────┬────────────────────────────────────────┘
                 │ Task Processing
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Celery Worker                                          │
│  - Processes CSV files                                  │
│  - Batch inserts (1000 rows)                           │
│  - Updates progress                                     │
└────────────────┬────────────────────────────────────────┘
                 │ Database Operations
                 ▼
┌─────────────────────────────────────────────────────────┐
│  PostgreSQL Database                                    │
│  - Stores products                                      │
│  - Stores webhooks                                      │
└─────────────────────────────────────────────────────────┘
```

## 📊 API Endpoints

### Upload
- `POST /api/upload` - Upload CSV file
- `GET /api/progress/<task_id>` - Get upload progress
- `POST /api/cancel/<task_id>` - Cancel upload

### Products
- `GET /api/products` - List products (with pagination & filters)
- `POST /api/products` - Create product
- `PUT /api/products/<id>` - Update product
- `DELETE /api/products/<id>` - Delete product
- `POST /api/products/bulk-delete` - Delete all products

### Webhooks
- `GET /api/webhooks` - List webhooks
- `POST /api/webhooks` - Create webhook
- `PUT /api/webhooks/<id>` - Update webhook
- `DELETE /api/webhooks/<id>` - Delete webhook

## 🧪 Testing

### Test CSV Upload

1. Go to "Upload CSV" tab
2. Upload a CSV file with columns: `sku`, `name`, `description`, `price`
3. Watch real-time progress
4. Check "Manage Products" tab to see imported products

### Test Product Management

1. Go to "Manage Products" tab
2. Click "+ Add Product" to create a product
3. Use filters to search products
4. Click "Edit" to modify a product
5. Click "Delete" to remove a product

### Test Webhooks

1. Go to "Webhooks" tab
2. Click "+ Add Webhook"
3. Enter a webhook URL (use https://webhook.site for testing)
4. Select event type
5. Click "Save"

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://localhost:5432/product_importer` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `SECRET_KEY` | Flask secret key | (generate random) |
| `FLASK_ENV` | Environment (development/production) | `development` |
| `UPLOAD_FOLDER` | Folder for uploaded files | `uploads` |
| `MAX_CONTENT_LENGTH` | Max upload size in bytes | `1073741824` (1GB) |

### Celery Configuration

- **Concurrency:** 1 (prevents database deadlocks)
- **Batch Size:** 1000 rows per transaction
- **Broker:** Redis
- **Result Backend:** Redis

## 📝 CSV Format

Expected CSV columns:
- `sku` (required) - Unique product identifier
- `name` (required) - Product name
- `description` (optional) - Product description
- `price` (optional) - Product price

Example:
```csv
sku,name,description,price
ABC-123,Product 1,Description 1,29.99
DEF-456,Product 2,Description 2,39.99
```

## 🐛 Troubleshooting

### Import Stuck at 0%
- Check Celery worker is running
- Check Redis connection
- Restart Celery worker with `concurrency=1`

### Database Deadlocks
- Ensure Celery is running with `--concurrency=1`
- Check PostgreSQL logs

### Upload Fails
- Check file size (max 1GB)
- Verify CSV format
- Check Celery worker logs

## 📄 License

MIT License

## 👤 Author

Garvit Chittora
- GitHub: [@gchittora](https://github.com/gchittora)
- Repository: [Fulfil_Assignment](https://github.com/gchittora/Fulfil_Assignment)

## 🙏 Acknowledgments

Built for Acme Inc. as part of the Backend Engineer assessment.

Design inspired by modern SaaS products: Stripe, Linear, Vercel.
