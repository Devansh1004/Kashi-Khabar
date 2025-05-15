# Automated News Scraper and Summarization Pipeline

An end-to-end automated system that scrapes news articles from the web, summarizes them using NLP, generates relevant images, and deploys the content dynamically on a web platform. Built to keep users updated with concise and engaging news summaries.

## Features

* Scrapes news articles from multiple sources using LangChain and DuckDuckGoSearch
* Performs advanced NLP summarization using Groq API to generate concise news summaries
* Automatically creates relevant images for articles via Hugging Face Spaces and Gradio API
* Generates and deploys a dynamic news website with categorized sections and search functionality
* Automated update workflow that runs every 6 hours to keep content fresh
* Uses MongoDB to manage and store news data efficiently

## Tech Stack

* Python (news scraping, NLP, automation scripts)
* LangChain and DuckDuckGoSearch (web scraping)
* Hugging Face Spaces & Gradio API (image generation)
* MongoDB (data storage)
* GitHub Actions (automation & CI/CD)
* Web Hosting: Vercel for deployment
* Frontend: Basic HTML, CSS, JS with search and filtering UI

## Installation

1. Clone the repo:

   ```bash
   git clone https://github.com/Devansh1004/Kashi-Khabar.git
   cd Kashi-Khabar
   ```

2. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up MongoDB connection and API keys in `.env` file (example below):

   ```
   MONGODB_URI=your_mongodb_uri
   HUGGINGFACE_API_KEY=your_huggingface_api_key
   ```

## Usage

* Run the scraping and summarization script manually:

  ```bash
  python generate_blogs.py
  ```

* Or rely on GitHub Actions workflow that triggers every 6 hours to update news automatically.

* Deploy the generated static website or run the Streamlit app to view news summaries interactively.

## Project Structure

```
├── generate_blogs.py            # Main script to scrape, summarize, generate images
├── public/                      # Frontend source code and stored news articles
├── api/                         # JS API to fetch content from MongoDB
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
├── vercel.json                  # Vercel setup 
```
