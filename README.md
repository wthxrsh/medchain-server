# MedChain Backend Server

The MedChain Backend is a robust, modular RESTful API built with **Django** and **Django REST Framework (DRF)**. Designed as a secure medical record management layer, it handles authenticated file uploads, cryptographic hashing for data integrity, async simulated blockchain anchoring, and time-bound tokenized record sharing.

---

## 🏗 System Architecture & Flow

### 1. Upload & Integrity Flow
1. A patient/provider uploads a medical record (PDF/JPG/PNG).
2. The server processes the file efficiently in memory chunks, generating a **SHA-256 cryptographic hash** of the raw file binary.
3. The upload metadata (uploader, timestamps, file reference, hash) is committed atomically into **PostgreSQL**.
4. An asynchronous daemon thread (`trigger_blockchain_transaction`) is dispatched non-blockingly to append the finalized file hash into the Blockchain simulation/smart contract interface, logging pending states back to the database.

### 2. Selective Sharing Flow
1. A patient generates a secure, randomized, unguessable URL-safe token (1-hour expiry).
2. The token is stored mapped to either specific medical records or their entire vault.
3. A third-party provider can effortlessly query `GET /share/{token}` completely unauthenticated to access read-only versions of only the specific permitted files. Access aggressively shuts off post-expiration.

---

## 🛠 Tech Stack
* **Framework**: Django 5.x & Django REST Framework
* **Database**: PostgreSQL (Relational metadata mapping)
* **Authentication**: JWT (JSON Web Tokens via `djangorestframework-simplejwt`)
* **Storage**: Local filesystem mapping `/media/` (Upgradeable natively to AWS S3 via `django-storages`)

---

## 📁 Core Application Modules

| Module | Responsibility |
|---|---|
| `users` | Houses the custom User model (`UUID` pk, email-driven auth) and JWT token dispensers. |
| `records` | Controls the multipart `FileUpload` API, SHA-256 pipeline, DRF Pagination, and timeline views. |
| `blockchain` | Encapsulates the mock/Web3 RPC connectivity layer running via isolated headless background threads. |
| `sharing` | Manages the `ShareToken` schema model and strictly-governed read-only permission serializers. |

---

## 🚀 Setup & Local Development

### Prerequisites
* Python 3.10+
* PostgreSQL 14+

### Installation
1. Navigate to the backend directory:
   ```bash
   cd Backend
   ```
2. Create and activate a Virtual Environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your `.env` (or setup your local PostgreSQL database to match `settings.py`):
   ```
   # Example PostgreSQL setup: medchain / postgres / password on localhost
   ```
5. Apply database migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
6. Boot the development server:
   ```bash
   python manage.py runserver
   ```

---

## 🌐 API Documentation Reference

All endpoints natively expect an `Authorization: Bearer <token>` header unless explicitly marked as **[Public]**.
Records API natively supports DRF `PageNumberPagination` (parameters: `?page=1&page_size=10`).

### Authentication
* `POST /api/token/` - **[Public]** Exchange email/password for JWT Access & Refresh tokens.
* `POST /api/token/refresh/` - **[Public]** Exchange a valid Refresh token for a new Access token.

### Records Management
* `GET /records/` - Retrieve an authenticated user's timeline (Paginated list of medical documents and their blockchain verification states).
* `POST /records/upload/` - Accept `multipart/form-data` containing the file binary and schema tags (`record_type`, `doctor_name`). Triggers async hash.

### Tokenized Sharing
* `POST /share/generate/` - Generate an expiring token. Accepts an optional `record_id` body payload to scope the share specifically vs globally.
* `GET /share/<token>/` - **[Public]** Fetch the targeted records explicitly tied to the unexpired token.

---

## 🚢 Production Deployment Recommendations

For real-world scaling and stability:

1. **WSGI/ASGI Server**: Never use `manage.py runserver` in production. Serve the application via **Gunicorn** or **Uvicorn** (for async support).
2. **Reverse Proxy**: Place **Nginx** in front of Gunicorn to handle SSL termination, block malevolent requests, and directly serve static/media files.
3. **Queueing Layer**: The current async thread approach (`threading.Thread`) is excellent for an MVP scale but drops tasks if the server container crashes. Transition the `trigger_blockchain_transaction` hook into **Celery** + **Redis/RabbitMQ**.
4. **Cloud Storage**: Map the `DEFAULT_FILE_STORAGE` backend in `settings.py` to `boto3` AWS S3 buckets to ensure horizontally-scalable, stateless deployed containers.
5. **Blockchain RPC**: Swap the simulated Python time-sleep thread inside `blockchain/services.py` with the `web3.py` library tied to an Infura/Alchemy endpoint.
