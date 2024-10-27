# cosmosid-scraper-api-zaag
Automated web scraper and backend API for microbial data acquisition from CosmosID. Built with Selenium, Flask, and PostgreSQL.

# Project Structure Overview

This repository contains the code and data for the `cosmosid-scraper-api-zaag` project. Below is an overview of the project's structure, with explanations of the purpose and contents of each directory and file.

## Project Directories and Files

### 1. Root Directory (`/`)
- **`README.md`**: This document, containing information about the structure of the repository.
- **`requirements.txt`**: Contains a list of required Python packages for the project.
- **`dockerfile`**: Used to build a Docker image for the project.
- **`scraper.log`**: Log file for monitoring the scraping activities.
- **`downloads/`**: Directory containing TSV files, which are results from the scraping process, categorized by different functional and taxonomic levels.

### 2. Debug Purpose Directory (`debug_purpose/`)
- **`collected_links.json`**: JSON file containing the collected links used within the project.
- **`exported_results.json`**: JSON file containing exported results generated by the scraping process.
- **`main_scraping.py`**: Main script for scraping data from specified sources.
- **`uploading_to_db.py`**: Script to upload collected data to the PostgreSQL database.
- **`debug_postgresqldb.txt`**: Debug information for troubleshooting PostgreSQL database issues.

### 3. Application Directory (`cosmosidscrpproject/`)
- Contains the core Django application that hosts the API and manages collected data.
- **`manage.py`**: Django's command-line utility for various administrative tasks.
- **`apis/`**: Contains all the code related to the `apis` application within the Django project.
  - **`admin.py`**: Configurations for the Django admin panel.
  - **`apps.py`**: App configuration for `apis`.
  - **`models.py`**: Contains Django models representing database tables, such as `CollectedLinks` and `ExportedResults`.
  - **`views.py`**: Contains views for handling HTTP requests and managing API logic.
  - **`serializers.py`**: Defines the serializers used by Django REST Framework to convert complex data types to JSON.
  - **`migrations/`**: Contains database migration files to set up or modify database schema.
  - **`urls.py`**: Defines URL routes for the APIs.
  - **`scraper.py`**: Contains scraping-related utility functions used by the application.

### 4. Core Django Project Directory (`cosmosidscrpproject/cosmosidscrpproject/`)
- **`__init__.py`**: Marks the directory as a Python package.
- **`asgi.py`**: ASGI configuration for the project.
- **`settings.py`**: Contains all project settings such as installed apps, middleware, and database configurations.
- **`urls.py`**: Main URL configuration for the entire Django project.
- **`wsgi.py`**: WSGI configuration for deploying the application.

### 5. Users Application Directory (`cosmosidscrpproject/users/`)
- Manages user-related functionalities.
- **`admin.py`**: Configurations for the Django admin panel related to user models.
- **`models.py`**: Defines models related to user accounts and profiles.
- **`views.py`**: Contains views for handling user management and profile updates.
- **`serializers.py`**: Defines serializers for user-related models.
- **`migrations/`**: Contains database migration files related to user models.
- **`urls.py`**: Defines URL routes for user-related endpoints.

### 6. Downloads Directory (`downloads/`)
- Contains multiple TSV files generated during the scraping process, each containing data collected for various taxonomy and functional annotations.
  - **Taxonomic Data**: Files prefixed with `kepler-biom` or `kepler-taxonomy` contain taxonomic classifications (e.g., domain, kingdom, phylum).
  - **Functional Data**: Files prefixed with `functional` contain functional annotations, such as pathways, enzymes (EC numbers), and Pfam domains.
  - **Filtered Data**: Files with `classes_filtered`, `phylogeny_filtered`, etc., contain filtered information used for further analysis.

## Quick Start Guide

1. **Environment Setup**: Install all required dependencies using `pip`.
   ```sh
   pip install -r requirements.txt
   ```
2. **Database Setup**: Run migrations to set up the PostgreSQL database.
   ```sh
   python manage.py migrate
   ```
3. **Run Server**: Start the Django server.
   ```sh
   python manage.py runserver 0.0.0.0:4001
   ```
4. **Docker**: To build and run using Docker, use the following command:
   ```sh
   sudo docker build -t cosmosidscrpprojectimg .
   sudo docker run -p 4001:4001 cosmosidscrpprojectimg
   ```

## Notes

- **Logging**: The scraping activities are logged to `scraper.log`.
- **Data Handling**: Exported data is available in JSON format for easy re-use or sharing (`collected_links.json`, `exported_results.json`).
- **TSV Files**: The `downloads` folder contains scraped data in various taxonomic and functional levels for further processing and analysis.
- **Unit Tests**: Unit tests are available in the `tests.py` files within the `apis` and `users` applications to verify the functionality of the API endpoints.
