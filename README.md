# AI-Powered Job Management System

A comprehensive job management system that uses AI to process repair job emails, generate checklists, and manage job statuses.

## Features

- Email parsing for new repair jobs
- Automated checklist generation
- Job status tracking
- Weekly status report generation
- Streamlit-based user interface

## Prerequisites

- Python 3.8+
- OpenAI API key

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Running the Application

1. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```
2. Open your browser and navigate to the URL shown in the terminal

## Usage

### New Job Entry
- Enter email subject and details
- System will automatically parse job information
- Generate job-specific checklist

### Job Tracker
- View all jobs in the system
- Update job statuses
- Track due dates

### Status Reports
- Generate weekly status reports
- View job statistics and upcoming deadlines