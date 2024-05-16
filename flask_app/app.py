from flask import Flask, render_template, jsonify
import pymysql
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO  # For handling byte streams
import base64  # For encoding/decoding data in base64
from wordcloud import WordCloud  # For generating word clouds
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

app = Flask(__name__)

# MySQL Configuration
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'Password@082810'
DB_NAME = 'jobs_db'

@app.route('/')
def index():
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = conn.cursor()

    # Fetch total job postings count
    cursor.execute("SELECT COUNT(*) FROM job_details")
    total_job_postings = cursor.fetchone()[0]

    # Fetch unique job titles count
    cursor.execute("SELECT DISTINCT title FROM job_details")
    unique_job_titles_count = cursor.rowcount

    # Fetch unique cities and their count
    cursor.execute("SELECT DISTINCT city FROM job_details WHERE city != '' AND city IS NOT NULL")
    unique_cities = [row[0] for row in cursor.fetchall() if row[0]]
    unique_cities_count = len(unique_cities)

    # Fetch posting start date
    cursor.execute("SELECT MIN(posting_time) FROM job_details")
    start_date = cursor.fetchone()[0].strftime('%Y-%m-%d')

    # Fetch latest job posting time
    cursor.execute("SELECT MAX(posting_time) FROM job_details")
    latest_job_posting_time = cursor.fetchone()[0].strftime('%Y-%m-%d')

    #most frequent skills
    df = pd.read_sql("SELECT skills FROM job_details", conn)
    skills_list = df['skills'].str.split(',').explode().str.strip().tolist()
    skills_list = [skill for skill in skills_list if skill]
    skills_list = list(set(skills_list))
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(skills_list))
    
    plt.figure(figsize=(10, 6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    skill_chart_img_str = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()

    #daily job postings analysis for 2024
    cursor.execute("""
        SELECT DATE(posting_time) AS date, COUNT(*) AS count 
        FROM job_details 
        WHERE YEAR(posting_time) = 2024
        GROUP BY date
        ORDER BY date
    """)
    daily_data = cursor.fetchall()
    df_daily = pd.DataFrame(daily_data, columns=['Date', 'Count'])
    df_daily['Date'] = pd.to_datetime(df_daily['Date'])  # Convert 'Date' column to datetime
    fig, ax = plt.subplots()
    df_daily.plot(kind='line', x='Date', y='Count', ax=ax, figsize=(10, 6))
    ax.set_title('Daily Job Postings in 2024')
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Job Postings')
    plt.tight_layout()
    daily_chart_image = BytesIO()
    FigureCanvas(fig).print_png(daily_chart_image)
    daily_chart_image_encoded = base64.b64encode(daily_chart_image.getvalue()).decode()
    plt.close()

    cursor.close()
    conn.close()

    return render_template('index.html', total_job_postings=total_job_postings,
                           unique_job_titles_count=unique_job_titles_count,
                           unique_cities_count=unique_cities_count,
                           start_date=start_date,
                           latest_job_posting_time=latest_job_posting_time,skill_chart=skill_chart_img_str,
                           daily_chart=daily_chart_image_encoded)

@app.route('/data/city')
def data_city():
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT city, COUNT(*) AS count 
        FROM job_details 
        WHERE title IS NOT NULL AND title != ''
        GROUP BY city
        HAVING count >= 1
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    # Transform data into JSON format for Chart.js
    labels = [row[0] for row in data]
    values = [row[1] for row in data]
    return jsonify({'labels': labels, 'data': values})

@app.route('/data/province')
def data_province():
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT province, COUNT(*) AS count 
        FROM job_details 
        WHERE province IS NOT NULL AND province <> ''
        GROUP BY province
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    labels = [row[0] for row in data]
    values = [row[1] for row in data]
    return jsonify({'labels': labels, 'data': values})

@app.route('/data/job_titles')
def data_job_titles():
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, COUNT(*) AS count
        FROM job_details
        WHERE title IS NOT NULL AND title <> ''
        GROUP BY title
        HAVING COUNT(*) > 9
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    labels = [row[0] for row in data]
    values = [row[1] for row in data]
    return jsonify({'labels': labels, 'data': values})


if __name__ == '__main__':
    app.run(debug=True)
