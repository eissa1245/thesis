# EMR System - Electronic Medical Records

A modern, professional Electronic Medical Records (EMR) system built with Python and Tkinter. Features a beautiful, minimalist GUI design with comprehensive patient and medical record management.

## Features

### Patient Management
- ✅ Add, view, edit, and delete patients
- ✅ Comprehensive patient information (demographics, contact, medical history, allergies)
- ✅ Search and filter patients
- ✅ Patient ID management

### Medical Records
- ✅ Create and view medical records
- ✅ Link records to patients
- ✅ Track visit dates, diagnoses, treatments, medications
- ✅ Vital signs recording
- ✅ Doctor notes and observations
- ✅ Search medical records

### User Interface
- 🎨 Modern, minimalist design
- 📱 Responsive layout
- 🎯 Intuitive navigation
- 📊 Dashboard with statistics
- 🔍 Advanced search functionality

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python emr_system.py
   ```

## Usage

### Dashboard
- View statistics (total patients, medical records, recent patients)
- Quick access to all main features
- Recent patients list

### Managing Patients
1. Click "Manage Patients" from dashboard
2. Use search bar to find patients
3. Double-click or select and click "View" to see full details
4. Click "Add New Patient" to create a new patient record

### Creating Medical Records
1. Click "New Record" from dashboard
2. Enter Patient ID
3. Fill in visit information, diagnosis, treatment, medications, etc.
4. Save the record

### Searching Records
1. Click "Search Records" from dashboard
2. Enter search term (patient name, ID, diagnosis, doctor name)
3. Double-click any result to view full details

## Database

The application uses SQLite database (`emr.db`) which is automatically created on first run. The database includes:

- **Patients**: Complete patient demographic and medical information
- **Medical Records**: Visit records with diagnoses, treatments, and notes

## Technology

- **Python 3.7+**
- **Tkinter** - GUI framework (included with Python)
- **SQLAlchemy** - Database ORM

## Design

The application features a modern, minimalist design with:
- Clean color palette (blue, green, cyan, amber)
- Professional typography
- Card-based layout with subtle shadows
- Smooth interactions and hover effects
- Consistent spacing and visual hierarchy

## License

This project is provided as-is for educational and development purposes.
