# 🌆 SmartAds – Smart Ads for Smart Cities

## 📌 About the Project

SmartAds is an AI-powered digital advertising platform that transforms traditional advertising into dynamic digital promotions. It enables users to create AI-generated advertisements, upload promotional content, manage advertising campaigns, and schedule advertisements across multiple virtual LED display locations.

The platform simplifies the advertising process through AI integration, automated pricing, payment management, and administrator approval.

## ✨ Key Features

- **User Authentication:** Secure registration, login, and role-based access.
- **AI Advertisement Content Generation:** Generate promotional advertising text using Groq AI (Llama 3.3 70B), with a fallback mechanism.
- **AI Video Generation:** Create talking-avatar promotional videos using the D-ID API.
- **Advertisement Management:** Create, upload, preview, and manage advertisements.
- **Multiple Ad Formats:** Supports poster and video advertisements.
- **Dynamic Pricing:** Calculate advertising costs based on location, format, time slot, duration, and 18% GST.
- **Payment Management:** Simulated payment workflow and transaction records.
- **Admin Dashboard:** Approve or reject advertisements and manage users, payments, and schedules.
- **PDF Receipts:** Generate downloadable payment receipts.
- **Notifications:** Receive updates about payment and advertisement approval.
- **Virtual LED Displays:** Display advertisements across multiple virtual smart-city locations.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript, Bootstrap 5 |
| Backend | Python, Flask |
| Database | SQLite |
| ORM | Flask-SQLAlchemy |
| Authentication | Flask-Login |
| AI Text Generation | Groq API – Llama 3.3 70B |
| AI Video Generation | D-ID API |
| PDF Generation | ReportLab |
| API Integration | Requests |
| Development Tools | VS Code, Git, GitHub |

## ⚙️ Project Workflow

1. User registers and logs into the application.
2. User creates an advertisement by entering product and promotional details.
3. AI generates advertisement content.
4. User selects the advertisement format (Poster or Video).
5. User selects a virtual LED display location and advertising time slot.
6. The system calculates the advertising price, including GST.
7. User completes the simulated payment process.
8. Advertisement is submitted to the administrator for approval.
9. Admin approves or rejects the advertisement.
10. Approved advertisements can be displayed on the virtual LED display interface.

## 📍 Virtual Advertising Locations

- Mall Billboard
- City Center Screen
- Food Court Display
- Highway Billboard
- Airport Terminal
- Metro Station

## 🚀 Installation and Setup

**1. Clone the repository**

```bash
git clone https://github.com/srushtibm826-bit/SmartAds---SmartAds-for-SmartCity.git
cd SmartAds---SmartAds-for-SmartCity
```

**2. Create a virtual environment**

```bash
python -m venv venv
```

**3. Activate the environment**

Windows:

```bash
venv\Scripts\activate
```

**4. Install dependencies**

```bash
pip install -r requirements.txt
```

**5. Configure environment variables**

Create a `.env` file and configure the required keys:

```env
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///smartads.db
GROQ_API_KEY=your_groq_api_key
DID_API_KEY=your_did_api_key
```

**6. Run the application**

```bash
python run.py
```

**7. Open in your browser**

```text
http://127.0.0.1:5000
```

## 🔮 Future Enhancements

- Integration with physical LED display boards.
- Real-time advertisement performance monitoring.
- AI-based audience analysis and targeted advertising.
- Integration with secure third-party payment gateways.
- Automated advertisement scheduling and campaign analytics.

## 🎓 Project Information

- **Project Title:** SmartAds – Smart Ads for Smart Cities
- **Domain:** Artificial Intelligence and Web Development
- **Department:** Information Science and Engineering
- **Institution:** Bapuji Institute of Engineering and Technology

---

**SmartAds – Transforming Traditional Advertising into Smart Digital Experiences!** 🚀
