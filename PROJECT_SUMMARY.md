# FBI Fraud Data Analysis Project - File Summary

This document provides a brief overview of each file in the project and its purpose.

## Core Modules

### `gemini_supabase.py`
Shared module containing functions for Gemini AI analysis and Supabase database operations. Provides functions for analyzing OCR output with Gemini, converting results to pandas DataFrames, and storing/retrieving data from Supabase. Used by multiple scripts in the project to maintain consistency and avoid code duplication.

### `fraud_visualizations.py`
Core visualization library containing reusable functions that generate Plotly chart objects for fraud data analysis. Extracts fraud metrics (losses, victims, categories, states) from Supabase data and creates meaningful visualizations. Functions return Plotly figure objects that can be used in Streamlit dashboards or saved as HTML files. This is the shared library used by both streamlit_app.py and visualize_fraud_data.py.

### `deepseekOcr.py`
Module for loading and initializing the DeepSeek OCR model for text extraction from images. Handles model loading, tokenizer setup, and provides the inference interface for OCR operations. Used by the Modal deployment for server-side OCR processing.

## Analysis Scripts

### `analyze_ocr.py`
Standalone command-line script for analyzing OCR output with Gemini AI and saving results to Supabase. Works independently of Modal and can process OCR JSON files directly or retrieve cached OCR data from Supabase. Supports cache checking, deletion, and various analysis modes through command-line arguments.

### `analyze_server.py`
FastAPI server implementation for standalone OCR analysis without Modal dependency. Provides REST API endpoints for checking cache, analyzing OCR data, and managing analysis results. Can be run locally using uvicorn for testing or development purposes.

### `client_pipeline.py`
Orchestration script that manages the complete pipeline from PDF to analyzed data. Coordinates checking Supabase cache, running OCR on Modal (if needed), analyzing with Gemini, and saving to Supabase. Designed to optimize costs by avoiding duplicate OCR runs and providing flexible workflow options.

## Deployment & API

### `deploy_modal.py`
Modal deployment configuration that sets up the OCR service on Modal's cloud infrastructure. Defines the Docker image, dependencies, GPU requirements, and FastAPI application deployment. Handles secrets management and provides a scalable OCR endpoint that can process PDFs using DeepSeek OCR model.

### `ocr_endpoint.py`
FastAPI application that provides OCR endpoints for processing PDF files. Handles PDF upload, conversion to images, OCR processing using DeepSeek model, and optional Gemini analysis with Supabase storage. Designed to run on Modal infrastructure with GPU support for efficient OCR processing.

## Testing & Utilities

### `test_api.py`
Test script for verifying the Modal OCR endpoint functionality. Sends test PDF files to the OCR API and validates the response format and content. Useful for debugging and ensuring the OCR service is working correctly after deployment.

### `verify_supabase.py`
Utility script for inspecting data stored in Supabase database. Displays cached analysis results, formatted JSON output from Gemini, and raw OCR data for a given filename. Helps with debugging and understanding what data is stored in the database.

## Visualization

### `fraud_visualizations.py` (Core Library)
Reusable visualization functions library that extracts fraud metrics and creates Plotly charts. Contains functions like `create_losses_by_category_chart()`, `create_state_visualization()`, and `extract_fraud_metrics()`. Returns Plotly figure objects that can be used by both the Streamlit app and HTML generator. This is the single source of truth for all visualization logic.

### `visualize_fraud_data.py` (HTML Generator)
Standalone command-line script that generates static HTML visualization files. Imports functions from fraud_visualizations.py, calls them to create charts, and saves the results as HTML files in the visualizations/ directory. Useful for creating static reports or sharing visualizations without running a web server.

### `streamlit_app.py` (Interactive Dashboard)
Interactive Streamlit web application for visualizing fraud data analysis results. Imports functions from fraud_visualizations.py and displays charts using Streamlit's native Plotly integration. Provides a dashboard interface with summary statistics, multiple chart visualizations, data refresh capabilities, and responsive layout. Best for interactive exploration and presentations.

## Configuration Files

### `pyproject.toml`
Python project configuration file defining dependencies, project metadata, and Python version requirements. Specifies all required packages including FastAPI, Streamlit, Plotly, Supabase client, Gemini AI, and data processing libraries.

### `README.md`
Main project documentation explaining the architecture, setup instructions, usage examples, and troubleshooting guide. Provides comprehensive information about the separated OCR and analysis pipeline, cost optimization strategies, and how to use each component.

### `TESTING.md`
Testing documentation that explains how to test each component of the system. Includes examples for testing OCR endpoints, analysis functions, Supabase operations, and the complete pipeline workflow.

### `STREAMLIT_GUIDE.md`
Guide for using the Streamlit dashboard application. Explains the difference between HTML visualizations and the interactive Streamlit app, how to run the dashboard, and customization options.

