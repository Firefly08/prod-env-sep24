# L5-DE-Data-Pipelines-T1

Welcome to the starter repository for designing and implementing a user data pipeline project. This project leverages SQLite within a GitHub Codespaces development environment to simulate building a simple yet extensible data pipeline.

## 🚀 Project Overview

Your objective is to:

1. **Design a Database Schema**  
   Create a schema to receive user data from an existing software application. This will initially include 10 UK-based users and their associated login timestamps.

2. **Implement a Data Pipeline**  
   Develop a Python-based pipeline that:
   - Ingests raw test data
   - Cleans and validates inputs
   - Loads the transformed data into your SQLite schema

3. **Use Test Data**  
   Provided test data includes:
   - 10 fictional UK users
   - Login timestamps in raw CSV or JSON format (provided separately or created by you)

4. **Collaborate with Your Instructor**  
   Your instructor will act as the stakeholder and Subject Matter Expert (SME). They will provide clarification on:
   - Schema requirements
   - Business rules for validation
   - Future data sources

5. **Prepare for Future Phases**  
   Consider the flexibility of your schema and pipeline. Future phases will include:
   - Users from different countries
   - Diverse timestamp formats
   - Additional fields (e.g. activity logs, geolocation)

6. **Documentation**  
   Clear and comprehensive documentation is expected:
   - Describe your database schema (tables, relationships, constraints)
   - Outline your pipeline steps (cleaning logic, validation rules, loading process)
   - Include comments in your code and a summary in this README

---

## 🛠️ Getting Started

1. **Open in GitHub Codespaces**  
   Launch this project in Codespaces to get a ready-to-use Python and SQLite environment.

2. **Install Requirements**  
   The environment automatically installs Python packages listed in `requirements.txt`.

3. **Initialise the Database**  
   On first launch, the `init_db.sql` script is used to set up a base schema and insert sample data into `data.db`.

4. **Run Example Script**  
   Run the script to see current contents of the database:

   ```bash
   python connect.py
   ```

---

## 📦 Repository Structure

```plaintext
├── .devcontainer/         # Codespaces config
│   ├── devcontainer.json
│   └── Dockerfile
├── data/                  
│   ├── UK User Data.csv   # User data
│   └── UK-User-LoginTS    # User login data
├── init_db.sql            # Initial schema and test data for SQLite
├── connect.py             # Python script to query the database
├── requirements.txt       # Python package requirements
└── README.md              # Project instructions (this file)
```

---

## 📄 Next Steps

* Replace or extend `init_db.sql` to reflect your custom schema.
* Build your data ingestion pipeline in a new script (e.g. `pipeline.py`).
* Document your changes and logic clearly in the code and README.
* Coordinate with your instructor as the SME to validate requirements and plan future enhancements.

---

## 🧠 Remember

This setup uses **SQLite** for simplicity and local prototyping, but the same schema and logic should be portable to PostgreSQL or another RDBMS in a production environment. Keep modularity and maintainability in mind.

Happy coding!