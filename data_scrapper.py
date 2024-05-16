import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import random
import time

# Create the 'output' directory if it doesn't exist
output_dir = "D:/Masters/2nd_semester/SWM/project/output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Configure logging settings
logging.basicConfig(filename="scraping.log", level=logging.INFO)

def scrape_linkedin_jobs(csv_file: str) -> None:
    # Read job titles from CSV file
    job_titles_df = pd.read_csv(csv_file)
    job_titles = job_titles_df['Job Title'].tolist()

    # Fixed location
    location = "Pakistan"

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    driver = webdriver.Chrome(options=options)

    for job_title in job_titles:
        logging.info(f'Starting LinkedIn job scrape for "{job_title}" in "{location}"...')

        driver.get(
            f"https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}"
        )

        # Scroll through the first 100 pages of search results on LinkedIn
        for i in range(200):
            logging.info(f"Scrolling to bottom of page {i+1}...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "/html/body/div[1]/div/main/section[2]/button")
                    )
                )
                element.click()
            except Exception:
                logging.info("Show more button not found, retrying...")
            time.sleep(random.choice(list(range(3, 7))))

        # Scrape the job postings
        jobs = []
        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_listings = soup.find_all(
            "div",
            class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
        )

        try:
            for job in job_listings:
                # Extract job details
                job_title = job.find("h3", class_="base-search-card__title").text.strip()
                job_company = job.find("h4", class_="base-search-card__subtitle").text.strip()
                job_location = job.find("span", class_="job-search-card__location").text.strip()
                apply_link = job.find("a", class_="base-card__full-link")["href"]
                job_posting_time = job.find("time")["datetime"].strip()  # Get datetime attribute
                
                # Extract number of applicants if available
                applicants_info = job.find("span", class_="job-search-card__applicant-count")
                num_applicants = applicants_info.text.split()[0] if applicants_info else None
                
                driver.get(apply_link)
                time.sleep(random.choice(list(range(5, 11))))
                try:
                    description_soup = BeautifulSoup(driver.page_source, "html.parser")
                    job_description = description_soup.find("div", class_="description__text description__text--rich").text.strip()
                    
                except AttributeError:
                    job_description = None
                    logging.warning("AttributeError occurred while retrieving job description.")
                    skills = None
                jobs.append(
                    {
                        "title": job_title,
                        "company": job_company,
                        "location": job_location,
                        "link": apply_link,
                        "description": job_description,
                        "posting_time": job_posting_time,
                        "applicants": num_applicants,
                    }
                )
                logging.info(f'Scraped "{job_title}" at {job_company} in {job_location} with posting time {job_posting_time}. Apply link: {apply_link}. Description: {job_description}. Applicants: {num_applicants}')

        except Exception as e:
            logging.error(f"An error occurred while scraping jobs: {str(e)}")

        # Replace spaces with underscores in job title for file name
        file_name = job_title.replace(" ", "_") + "_jobs.csv"        # Save job data to CSV
        df = pd.DataFrame(jobs)
        # Save job data to CSV in the 'output' directory
        file_path = os.path.join(output_dir, file_name)
        try:
            df.to_csv(file_path, index=False)
            logging.info(f"CSV file saved at: {file_path}")
        except OSError as e:
            logging.error(f"OSError: {e}")
            continue

    driver.quit()
    logging.info("Job scraping completed.")

if __name__ == "__main__":
    scrape_linkedin_jobs("job_titles_fifth_1.csv")
