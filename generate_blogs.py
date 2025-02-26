import re
import os
import time
import re
import json
import pymongo
from dotenv import load_dotenv
load_dotenv()

USER_AGENT = os.getenv('USER_AGENT')
HF_TOKEN = os.getenv('HF_TOKEN')
GROQ_API_KEY_SUMMARY = os.getenv('GROQ_API_KEY_1')
GROQ_API_KEY_TRANSLATE = os.getenv('GROQ_API_KEY_2')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

project_path = "https://kashi-khabar.vercel.app/"

def clean_title(text):
	return re.sub(r'[<>:,.\"/\\|?*]', '', text)

from langchain_community.document_loaders import WebBaseLoader
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from gradio_client import Client
from PIL import Image
import cloudinary
import cloudinary.uploader
import uuid
import time

def fetch_news():
	wrapper = DuckDuckGoSearchAPIWrapper(region='in-en', time='d')
	search = DuckDuckGoSearchResults(api_wrapper=wrapper, backend = 'news', num_results=7, output_format='list')
	MONGO_URI = os.getenv('MONGO_URI')
	client = pymongo.MongoClient(MONGO_URI)
	db = client["my_articles"]
	collection = db["news_articles"]

	genres = ['sports', 'politics', 'health', 'crime', 'business', 'technology', 'entertainment']
	locations = ['Varanasi', 'Uttar Pradesh']

	allowed_websites = ['https://indianexpress.com/', 'https://www.news18.com/', 'https://theprint.in', 'https://www.thehindu.com/', 
						'https://www.devdiscourse.com/', 'https://markets.businessinsider.com/', 'https://timesofindia.indiatimes.com/']

	news = []
	for genre in genres:
		for location in locations:
			try:
				result = search.invoke(f"{location} {genre}")
				print("Loaded Search Results")
				# Filter only trustable news sources
				result = [i for i in result if any(domain in i['link'] for domain in allowed_websites)]
				
				# Continue if no trustable news found
				if(len(result) == 0):
					print('No news found!')
					continue

				# Article metadata
				article = {}
				article['date'] = result[0]['date']
				article['link'] = result[0]['link']
				article['source'] = result[0]['source']
				
				# Loading complete webpage
				loader = WebBaseLoader(web_path=result[0]['link'])
				text = loader.load()
				
				text = re.sub(r'\s+' , ' ', text[0].page_content[:4000])
				page_content = text.strip()
				
				if len(page_content) < 20:
					print('No news found!')
					time.sleep(2.5)
					continue
				# -------------------------------------------------------------
				print("Loaded Article successfully")

				

				# Summary-------------------------------------------------------------
				llm = ChatGroq(model='gemma2-9b-it', api_key=GROQ_API_KEY_SUMMARY)
				result_summary = llm.invoke(f"""Please extract factual, valuable and relevant news from the provided content
												and summarize it in between 150 to 200 words.
												Do not skip any valuable news related information.
												Do not generate any extra text.
												<content>{page_content}</content>""")
				if len(result_summary.content) < 50:
					time.sleep(2.5)
					continue
				time.sleep(5)
				article['summary'] = result_summary.content

				article['summary'] = re.sub(r'\n+', '\n', article['summary']).replace("\n", "<br>")

				# -------------------------------------------------------------
				print("Generated Summary.")




				# Title-------------------------------------------------------------
				result_title = llm.invoke(f"""Provide me a catchy, relevant and clever title for the following news summary of at max 10 words.
											Do not generate any extra text.
											<summary>{result_summary.content}</summary>""")
				time.sleep(5)
				article['title'] = result_title.content.strip()
				# -------------------------------------------------------------
				print("Generated Title.")




				# Hindi Summary and Title-------------------------------------------------------------
				llm2 = ChatGroq(model='llama-3.3-70b-versatile', api_key = GROQ_API_KEY_TRANSLATE)
				result_hindi_summary = llm2.invoke(f"Please translate the following article into Hindi. Do not generate any extra text. <article>{article['summary']}</article>")
				result_hindi_title = llm2.invoke(f"Please translate the following title into Hindi. Do not generate any extra text. <title>{article['title']}</title>")

				article['hindi_summary'] = result_hindi_summary.content.strip()
				article['hindi_summary'] = re.sub(r'\n+', '\n', article['hindi_summary']).replace("\n", "<br>")
				article['hindi_title'] = result_hindi_title.content.strip()
				# -------------------------------------------------------------
				print("Generated Hindi contents")




				# Time and UID-------------------------------------------------------------
				article['time'] = str(time.time())
				uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, article['time']))
				article['_id'] = uid
				# -------------------------------------------------------------
				print("Generated UID.")





				# Prompt for Image, Image Generation, and Saving to Cloudinary-------------------------------------------------------------
				result_prompt = llm.invoke(f"""Give me a suitable prompt in 100 words for the provided summary so that
											I can use this prompt in a llm to generate a real image.
											Do not generate anything extra.
											<summary>{result_summary.content}</summary>""")
				time.sleep(5)
				image_model = Client('black-forest-labs/FLUX.1-schnell', hf_token = HF_TOKEN)
				result_image = image_model.predict(prompt = result_prompt.content, seed=0,randomize_seed=True,
													width=512,height=288,num_inference_steps=10,api_name="/infer")
				
			
				cloudinary.config(cloud_name = "dyjtadxat", api_key = "295955344262113", api_secret = CLOUDINARY_API_SECRET, secure=True)
				upload_result = cloudinary.uploader.upload(result_image[0],public_id=article['title'])
				article['image_url'] = upload_result["secure_url"]
				time.sleep(5)
				# -------------------------------------------------------------
				print("Generated and Stored Image.")


				


				# Keywords and Hashtags-------------------------------------------------------------
				result_keywords = llm.invoke(f"""From the provided summary of a news article, give me around 15 one-word keyowrds that are relevant, 
												factual and would be good to use in SEO keywords. Try to include all the small details as well. 
												Only generate the keywords and print them in a comma-separated format. Do not generate any other text. 
												<summary>{result_summary.content}</summary>""")
				time.sleep(5)
				article['keywords'] = result_keywords.content
				article['keywords']+= ", " + genre + ', ' + location
				
				result_hashtags =  llm.invoke(f"""From the provided summary of a news article, give me around 15 small hashtags that are relevant,
												factual and would be good to use with my article. Try to include all the small details as well. 
												Only generate the hashtags with a "#" and print them in a comma-separated format. 
												Do not generate any other text. 
												<summary>{result_summary.content}</summary>""")
				time.sleep(5)
				article['hashtags'] = result_hashtags.content
				article['hashtags']+= ', #' + genre + ', #' + location + ', #KashiKhabar'
				# -------------------------------------------------------------
				print("Generated Keywords and Hashtags.")





				news.append(article)
				
				article_data = {
					"_id": article['_id'],
					"title": article["title"],
					"time": article['time'],
					"link": f"""{project_path}/articles/{article['_id']}/index.html""",
					"keywords": article['keywords'],
					"image": article['image_url']
				}
				
				print(f'''Article titled "{article['title']}" generated with UID: {article['_id']} successfully!''')

				collection.insert_one(article_data)
				print(f"Stored in MongoDB successfully!")
			except Exception as e:
					print(e)
					continue
	return news

def generate_news_page(article, directory):
	# HTML Content with enhanced styling and hashtag section
	html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Kashi Khabar - {article['title']}</title>
	<meta name="description" content="{article['summary']}">
	<meta name="keywords" content="news, latest news, updates, {article['keywords'].lower()}">
	<meta name="author" content="Kashi Khabar">

	<!-- Open Graph for social media -->
	<meta property="og:title" content="{article['title']}">
	<meta property="og:description" content="{article['summary']}">
	<meta property="og:image" content="{article['image_url']}">
	<meta property="og:url" content="{article['source']}">
	<meta property="og:type" content="article">

	<!-- Twitter Card -->
	<meta name="twitter:card" content="summary_large_image">
	<meta name="twitter:title" content="{article['title']}">
	<meta name="twitter:description" content="{article['summary']}">
	<meta name="twitter:image" content="{article['image_url']}">

	<link rel="stylesheet" href="./style.css">
	<script>
		function toggleLanguage(lang) {{
			if (lang === 'en') {{
				document.getElementById('header-en').style.display = 'block';
				document.getElementById('header-hi').style.display = 'none';
				document.getElementById('english-content').style.display = 'block';
				document.getElementById('hindi-content').style.display = 'none';
			}} else {{
				document.getElementById('header-en').style.display = 'none';
				document.getElementById('header-hi').style.display = 'block';
				document.getElementById('english-content').style.display = 'none';
				document.getElementById('hindi-content').style.display = 'block';
			}}
		}}
	</script>
</head>
<body>
	<header id="header-en">
		<h1>Kashi Khabar</h1>
		<button class="language-toggle" onclick="toggleLanguage('en')">English</button>
		<button class="language-toggle" onclick="toggleLanguage('hi')">हिन्दी</button>
	</header>

	<header id="header-hi" style="display: none;">
		<h1>काशी ख़बर</h1>
		<button class="language-toggle" onclick="toggleLanguage('en')">English</button>
		<button class="language-toggle" onclick="toggleLanguage('hi')">हिन्दी</button>
	</header>

	<main>
		<div class="news-card">
			<img src="{article['image_url']}" alt="{article['title']}">
			
			<div id="english-content">
				<h2>{article['title']}</h2>
				<p class="date">{article['date']}</p>
				<p class="summary">{article['summary']}</p>
				<a href="{article['link']}" target="_blank" class="source">Read full article by {article['source']}</a>
				<p class="hashtags">{article['hashtags']}</p>
			</div>

			<div id="hindi-content" style="display: none;">
				<h2>{article['hindi_title']}</h2>
				<p class="date">{article['date']}</p>
				<p class="summary">{article['hindi_summary']}</p>
				<a href="{article['link']}" target="_blank" class="source">पूरा लेख पढ़ें: {article['source']}</a>
				<p class="hashtags">{article['hashtags']}</p>
			</div>
		</div>
	</main>
</body>
</html>
"""

	# CSS Content with better styling
	css_content = """/* Global Styles */
body {
    font-family: 'Poppins', sans-serif;
    background-color: #f8f9fa;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    color: #333;
}

/* Header */
header {
    width: 100%;
    background: linear-gradient(to right, #1e3c72, #2a5298);
    color: white;
    text-align: center;
    padding: 15px 0;
    font-size: 28px;
    font-weight: bold;
    letter-spacing: 1px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    position: relative;
}

.language-toggle {
    background: #f8f9fa;
    color: #1e3c72;
    border: 2px solid #1e3c72;
    padding: 10px 15px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    margin: 5px;
    transition: all 0.3s ease-in-out;
    font-weight: bold;
}

.language-toggle:hover {
    background: #1e3c72;
    color: white;
}

/* Main Content */
main {
    width: 90%;
    max-width: 850px;
    margin: 30px auto;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.news-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    margin-bottom: 25px;
    border: none;
    transition: transform 0.2s ease-in-out;
    text-align: center;
    padding: 20px;
}

.news-card:hover {
    transform: scale(1.03);
}

.news-card img {
    width: 100%;
    height: auto;
    border-radius: 10px;
    margin-bottom: 15px;
}

.news-content h2 {
    font-size: 26px;
    color: #1e3c72;
    margin-bottom: 10px;
    text-transform: capitalize;
}

.date {
    font-size: 14px;
    color: #777;
    margin-bottom: 8px;
}

.summary {
    font-size: 18px;
    color: #444;
    margin: 15px 0;
    line-height: 1.8;
    text-align: left;
    padding: 0 10px;
}

.source {
    display: inline-block;
    text-decoration: none;
    background: #1e3c72;
    color: white;
    padding: 12px 18px;
    border-radius: 8px;
    font-size: 16px;
    transition: background 0.3s ease-in-out;
    font-weight: bold;
}

.source:hover {
    background: #14365e;
}

.hashtags {
    margin-top: 15px;
    font-size: 14px;
    color: #555;
    font-style: italic;
    text-align: center;
    padding: 10px;
}

.hidden {
    display: none;
}
"""



	os.makedirs(directory, exist_ok=True)

	# File paths
	html_file_path = os.path.join(directory, "index.html")
	css_file_path = os.path.join(directory, "style.css")

	# Write HTML file
	with open(html_file_path, "w", encoding="utf-8") as html_f:
		html_f.write(html_content)

	# Write CSS file
	with open(css_file_path, "w") as css_f:
		css_f.write(css_content)

	print(f"Generated {html_file_path} and {css_file_path} successfully!")



if __name__ == '__main__':
	news = fetch_news()
	for article in news:
		directory = os.path.join("public\\articles", article['_id'])
		generate_news_page(article=article, directory=directory)
	
