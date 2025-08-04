# ProConnect Backend

A secure FastAPI + MongoDB backend for a LinkedIn-style mini community platform.  
Handles authentication, profiles, and public post feed features.  
**⏱️ Entire backend designed, coded, and deployed in just 26 hours for the CIAAN Cyber Tech Full Stack Development Internship task.**

---

**Tech Stack:**  
- FastAPI (Python)
- MongoDB Atlas (cloud database)
- JWT auth with Bearer tokens
- ODM: Beanie + Motor
- Deployed on Render

---

**Live API:**  
[https://pro-backend-d8i2.onrender.com](https://pro-backend-d8i2.onrender.com/)

---

**Key Features:**  
- User authentication (register / login, JWT, hashed passwords)
- Public post creation, display, and listing
- User profile endpoints with name, email, bio, and user’s posts
- Secured protected routes for personalized content

---

**Demo Credentials / Usage:**  
- Email: **fardeenkhan7869@gmail.com**
- Password: **Fardeen**
- You can log in with these details to test, or register a new user with your own email/password to try all app features.

---

**Setup (for local use):**  
- Clone the repo, set up a Python virtual environment, and install dependencies with `pip install -r requirements.txt`.
- Create a `.env` file in the root with:
  - `MONGO_URI=your-mongodb-uri`
  - `SECRET_KEY=your-secret-key`
- Launch locally via `uvicorn main:app --reload`.  
- In production, all secrets are set as environment variables in Render (never committed in code).

---

**Deployment:**  
- The backend is live and ready for use by any frontend or API client.
- All endpoints documented via OpenAPI at `/docs` on the API base URL.

---

**Note:**  
This backend is structured for clarity and rapid prototyping.  
For production/mobile-scale use, further config, security, testing, and optimizations are possible.

---

**Contact:**  
Built by Fardeen Khan for CIAAN Cyber Tech.

---
