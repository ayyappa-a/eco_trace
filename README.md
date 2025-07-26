# 🌱 Eco Trace – Track and Reduce Your Carbon Footprint

Eco Trace is a web-based application that helps users monitor and reduce their carbon emissions. It allows users to log their daily activities, calculate carbon footprints, earn badges for eco-friendly habits, and compete on a leaderboard.

## 📌 Features

- 🔐 User Registration & Login  
- 🧾 Activity Logging (e.g., travel, electricity use)  
- 🌍 Emission Calculation (kg CO₂)  
- 🏅 Badge Awards for Milestones  
- 🏆 Leaderboard Rankings  
- 📊 Dashboard Charts using Chart.js

---

## 🗃️ Database Schema Overview

### 1. `user`  
Stores user login information.

| Column     | Type      | Description              |
|------------|-----------|--------------------------|
| id         | INTEGER   | Primary key              |
| username   | TEXT      | User’s name              |
| email      | TEXT      | Unique email             |
| password   | TEXT      | Encrypted password       |

---

### 2. `activity`  
Logs user activities to be used for emission calculations.

| Column       | Type    | Description                         |
|--------------|---------|-------------------------------------|
| id           | INTEGER | Primary key                         |
| user_id      | INTEGER | Foreign key → `user(id)`            |
| activity_type| TEXT    | E.g., Driving, Electricity          |
| quantity     | FLOAT   | Units used (e.g., km, kWh)          |
| date         | DATE    | Activity date                       |

---

### 3. `emission`  
Stores emissions calculated from user activities.

| Column         | Type      | Description                        |
|----------------|-----------|------------------------------------|
| id             | INTEGER   | Primary key                        |
| user_id        | INTEGER   | Foreign key → `user(id)`           |
| emission_kg    | FLOAT     | Emissions in kg CO₂                |
| calculated_at  | TIMESTAMP | Auto-generated timestamp           |

🧮 **Formula Used:**  
```text
Emission (kg CO₂) = quantity × emission_factor
