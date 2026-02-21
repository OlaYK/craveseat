# CraveSeat API

CraveSeat is a modern platform that connects food enthusiasts with local vendors. Users can post their specific food cravings, and vendors can respond to fulfill them.

## 🚀 Features

- **Dual-Role Architecture**: Users can easily switch between "User" and "Vendor" modes within a single account.
- **Dynamic Cravings**: Post cravings with specific categories (Local delicacies, Street food, Grills, etc.) and price estimates.
- **Vendor Profiles**: Vendors can create detailed profiles, upload logos/banners, and manage their menus.
- **Authentication**: Secure JWT-based authentication supporting both standard login and Google Sign-In.
- **Smart Validation**: Comprehensive data validation for phone numbers, emails, and usernames.
- **Standardized Responses**: Consistent API response format across all endpoints.
- **Image Support**: Integration with Cloudinary for profile and item image uploads.

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: PostgreSQL (Supabase) via SQLAlchemy
- **Authentication**: JWT (python-jose)
- **Validation**: Pydantic v2
- **Image Hosting**: Cloudinary
- **Deployment**: Render

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL database (or Supabase account)
- Cloudinary account (for image uploads)

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd craveseat
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

5. **Run the application**:
   ```bash
   uvicorn main:app --reload
   ```

## 📖 API Documentation

Once the server is running, you can access the interactive API documentation at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 🌐 Deployment (Render)

This project is configured for deployment on Render using the `render.yaml` blueprint.

1. Push your code to GitHub.
2. Link your repository to a new **Blueprint** on Render.
3. Configure your secret environment variables (Cloudinary, Database URL) in the Render Dashboard under **Environment**.

## 📄 License

This project is licensed under the MIT License.
