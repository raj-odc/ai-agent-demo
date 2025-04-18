import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv 
from sheets_sync import GoogleSheetsSync

# Load environment variables
load_dotenv()

# Initialize Google Sheets sync
try:
    sheets_sync = GoogleSheetsSync()
except Exception as e:
    st.error(f'Failed to initialize Google Sheets: {str(e)}')
    sheets_sync = None

# Initialize OpenAI
llm = OpenAI(temperature=0.7)

# Initialize session state
if 'jobs_df' not in st.session_state:
    st.session_state.jobs_df = pd.DataFrame(
        columns=['Job ID', 'Scope of Work', 'Required Trades', 'Due Date', 'Status', 'Created Date']
    )

def parse_email(subject, details):
    # Template for email parsing
    email_template = PromptTemplate(
        input_variables=['subject', 'details'],
        template='''Extract the following information from this repair job email:
        Subject: {subject}
        Details: {details}
        
        Please provide:
        1. Job ID (from subject if available, else generate)
        2. Scope of work (brief description)
        3. Required trades (list all needed, separate with commas)
        4. Status (set as 'Waiting for assignment')
        
        Format as JSON with keys: job_id, scope, trades, status'''
    )
    
    # Create and run the chain
    chain = LLMChain(llm=llm, prompt=email_template)
    result = chain.run(subject=subject, details=details)
    
    # Import json for parsing
    import json
    
    try:
        # Parse the JSON string into a Python dictionary
        parsed_result = json.loads(result.strip())
        # Ensure trades is a comma-separated string
        if isinstance(parsed_result['trades'], list):
            parsed_result['trades'] = ', '.join(parsed_result['trades'])
        elif not isinstance(parsed_result['trades'], str):
            parsed_result['trades'] = str(parsed_result['trades'])
        return parsed_result
    except json.JSONDecodeError:
        st.error('Failed to parse the response. Please try again.')
        return None

def generate_checklist(job_type):
    checklist_template = PromptTemplate(
        input_variables=['job_type'],
        template="""Create a detailed checklist for a {job_type} job. Include steps for:
        1. Initial assessment
        2. Required inspections
        3. Work execution
        4. Quality checks
        5. Client communication
        
        Format as a numbered list."""
    )
    
    chain = LLMChain(llm=llm, prompt=checklist_template)
    return chain.run(job_type=job_type)

def generate_status_report(jobs_df):
    if jobs_df.empty:
        return "No jobs to report."
    
    report_template = PromptTemplate(
        input_variables=['jobs_data'],
        template="""Generate a weekly status report based on this jobs data:
        {jobs_data}
        
        Provide:
        1. Total number of active jobs
        2. Jobs by status
        3. Upcoming due dates
        4. Key actions needed
        
        Format as a clear business report."""
    )
    
    chain = LLMChain(llm=llm, prompt=report_template)
    return chain.run(jobs_data=jobs_df.to_string())

# Streamlit UI
st.title('🏗️ Job Management System')

# Sidebar for navigation
page = st.sidebar.selectbox(
    'Navigate to',
    ['New Job Entry', 'Job Tracker', 'Generate Report']
)

if page == 'New Job Entry':
    st.header('📧 New Job Entry')
    
    subject = st.text_input('Email Subject')
    details = st.text_area('Email Details')
    
    if st.button('Process Email'):
        if subject and details:
            result = parse_email(subject, details)
            st.json(result)
            
            # Add to job tracker
            new_job = pd.DataFrame([
                {
                    'Job ID': result['job_id'],
                    'Scope of Work': result['scope'],
                    'Required Trades': result['trades'],
                    'Due Date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                    'Status': 'Waiting for assignment',
                    'Created Date': datetime.now().strftime('%Y-%m-%d')
                }
            ])
            st.session_state.jobs_df = pd.concat([st.session_state.jobs_df, new_job], ignore_index=True)
            
            # Sync to Google Sheets
            if sheets_sync:
                if sheets_sync.sync_to_sheets(st.session_state.jobs_df):
                    st.success('Job data synced to Google Sheets')
                else:
                    st.warning('Failed to sync job data to Google Sheets')
            
            # Generate and display checklist
            st.subheader('📋 Generated Checklist')
            checklist = generate_checklist(result['scope'])
            st.write(checklist)

elif page == 'Job Tracker':
    st.header('📊 Job Tracker')
    st.dataframe(st.session_state.jobs_df)
    
    # Job status update
    if not st.session_state.jobs_df.empty:
        job_id = st.selectbox('Select Job to Update', st.session_state.jobs_df['Job ID'])
        new_status = st.selectbox(
            'Update Status',
            ['Waiting for assignment', 'In Progress', 'Completed', 'On Hold']
        )
        if st.button('Update Status'):
            idx = st.session_state.jobs_df[st.session_state.jobs_df['Job ID'] == job_id].index[0]
            st.session_state.jobs_df.at[idx, 'Status'] = new_status
            
            # Sync updated status to Google Sheets
            if sheets_sync:
                if sheets_sync.sync_to_sheets(st.session_state.jobs_df):
                    st.success(f'Status updated for Job {job_id} and synced to Google Sheets')
                else:
                    st.warning('Status updated locally but failed to sync to Google Sheets')
            else:
                st.success(f'Status updated for Job {job_id}')

else:  # Generate Report
    st.header('📈 Status Report')
    if st.button('Generate Weekly Report'):
        report = generate_status_report(st.session_state.jobs_df)
        st.write(report)