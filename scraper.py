<<<<<<< HEAD
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import random

# Time Block 5 (2:10-2:40) - Scraper
async def scrape_naukri(role: str, location: str, pages: int = 3):
    """
    Scrapes job title, company, salary, and URL from Naukri for up to 3 pages.
    Implements playwright-stealth for basic bot dodging.
    """
    jobs = []
    
    # Simple formatter for Naukri URL search
    role_formatted = role.lower().replace(' ', '-')
    location_formatted = location.lower().replace(' ', '-')
    base_search_term = f"{role_formatted}-jobs-in-{location_formatted}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Randomize user agent slightly
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Apply stealth overrides to mask WebDriver signals
        await stealth_async(page)
        
        for i in range(1, pages + 1):
            url = f"https://www.naukri.com/{base_search_term}-{i}" if i > 1 else f"https://www.naukri.com/{base_search_term}"
            print(f"Scraping {url}...")
            
            try:
                # Wait until network is somewhat idle
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                
                # Wait for the main list or timeout
                # Target classes over multiple generations variations
                await page.wait_for_selector('.srp-jobtuple-wrapper, .jobTuple, .cust-job-tuple', timeout=10000)
                
                # Find the job cards on this page
                job_elements = await page.query_selector_all('.srp-jobtuple-wrapper, .jobTuple, .cust-job-tuple')
                
                for el in job_elements:
                    # Title
                    title_elem = await el.query_selector('.title')
                    title = await title_elem.inner_text() if title_elem else "Unknown Title"
                    
                    # Company
                    comp_elem = await el.query_selector('.comp-name, .subTitle')
                    company = await comp_elem.inner_text() if comp_elem else "Unknown Company"
                    
                    # URL
                    job_url = await title_elem.get_attribute('href') if title_elem else ""
                    
                    # Salary (often inside .salary or similar)
                    sal_elem = await el.query_selector('.sal-wrap, .salary')
                    salary = await sal_elem.inner_text() if sal_elem else "Not Disclosed"
                    
                    # Location
                    loc_elem = await el.query_selector('.locWdth, .location')
                    job_location = await loc_elem.inner_text() if loc_elem else location

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "salary": salary.strip(),
                        "location": job_location.strip(),
                        "url": job_url,
                        "board": "naukri"
                    })
                    
                # Artificial bot delay
                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Error scraping Naukri page {i}: {e}")
                
        await browser.close()
        return jobs

async def search_jobs(role: str, location: str, pages: int = 1):
    """Wrapper to search multiple job boards if needed. Focusing on Naukri for MVP."""
    print(f"Executing search for {role} in {location} across {pages} pages.")
    naukri_results = await scrape_naukri(role, location, pages=pages)
    return naukri_results

if __name__ == "__main__":
    jobs = asyncio.run(search_jobs("Software Engineer", "Bangalore", pages=1))
    print(f"Found {len(jobs)} jobs. Example:")
    if jobs:
        print(jobs[0])
=======
"""Job scraping module using Playwright."""
import asyncio
import random
from typing import List, Dict, Optional, Any
from urllib.parse import quote

from playwright.async_api import async_playwright, Page, Browser
from playwright_stealth import stealth_async

from config import settings, JOB_BOARDS


class JobScraper:
    """Playwright-based job scraper for multiple job boards."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.jobs: List[Dict[str, Any]] = []
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()
    
    async def create_page(self) -> Page:
        """Create a new page with stealth mode."""
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        await stealth_async(page)
        return page
    
    async def scrape_naukri(
        self,
        role: str,
        location: str,
        experience: Optional[int] = None,
        pages: int = 3
    ) -> List[Dict[str, Any]]:
        """Scrape jobs from Naukri.com."""
        jobs = []
        page = await self.create_page()
        
        try:
            encoded_role = quote(role)
            encoded_location = quote(location)
            
            for page_num in range(1, pages + 1):
                if experience:
                    url = f"{JOB_BOARDS['naukri']}/{encoded_role}-jobs-in-{encoded_location}-{experience}-to-{experience}-years-{page_num}"
                else:
                    url = f"{JOB_BOARDS['naukri']}/{encoded_role}-jobs-in-{encoded_location}-{page_num}"
                
                print(f"Scraping Naukri page {page_num}: {url}")
                
                try:
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    await page.wait_for_selector('.jobTuple, .srp-jobtuple-wrapper', timeout=10000)
                    job_cards = await page.query_selector_all('.jobTuple, .srp-jobtuple-wrapper')
                    
                    for card in job_cards:
                        try:
                            job = await self._extract_naukri_job(card)
                            if job and job.get('apply_url'):
                                job['source'] = 'naukri'
                                jobs.append(job)
                        except Exception as e:
                            print(f"Error extracting Naukri job: {e}")
                            continue
                    
                    print(f"Found {len(job_cards)} jobs on Naukri page {page_num}")
                    
                except Exception as e:
                    print(f"Error scraping Naukri page {page_num}: {e}")
                    continue
                
                await asyncio.sleep(random.uniform(2, 4))
                
        except Exception as e:
            print(f"Error in Naukri scraper: {e}")
        finally:
            await page.close()
        
        return jobs
    
    async def _extract_naukri_job(self, card) -> Optional[Dict[str, Any]]:
        """Extract job details from Naukri job card."""
        try:
            title_elem = await card.query_selector('.title, .job-title, a.title')
            title = await title_elem.inner_text() if title_elem else "Unknown"
            
            company_elem = await card.query_selector('.companyInfo, .company-name, .subTitle')
            company = await company_elem.inner_text() if company_elem else "Unknown"
            
            location_elem = await card.query_selector('.location, .locWdth')
            location = await location_elem.inner_text() if location_elem else "Not specified"
            
            salary_elem = await card.query_selector('.salary, .package')
            salary = await salary_elem.inner_text() if salary_elem else "Not disclosed"
            
            exp_elem = await card.query_selector('.experience, .expwdth')
            experience = await exp_elem.inner_text() if exp_elem else "Not specified"
            
            skills_elem = await card.query_selector('.tags, .key-skill')
            skills = await skills_elem.inner_text() if skills_elem else ""
            
            link_elem = await card.query_selector('a.title, a.job-title')
            apply_url = await link_elem.get_attribute('href') if link_elem else ""
            
            desc_elem = await card.query_selector('.job-description, .description')
            description = await desc_elem.inner_text() if desc_elem else ""
            
            return {
                'title': title.strip() if title else "Unknown",
                'company': company.strip() if company else "Unknown",
                'location': location.strip() if location else "Not specified",
                'salary': salary.strip() if salary else "Not disclosed",
                'experience_required': experience.strip() if experience else "Not specified",
                'skills_required': skills.strip() if skills else "",
                'description': description.strip() if description else "",
                'apply_url': apply_url if apply_url else ""
            }
            
        except Exception as e:
            print(f"Error extracting Naukri job details: {e}")
            return None
    
    async def scrape_indeed(
        self,
        role: str,
        location: str,
        experience: Optional[int] = None,
        pages: int = 3
    ) -> List[Dict[str, Any]]:
        """Scrape jobs from Indeed India."""
        jobs = []
        page = await self.create_page()
        
        try:
            for page_num in range(pages):
                start = page_num * 10
                url = f"{JOB_BOARDS['indeed']}/jobs?q={quote(role)}&l={quote(location)}&start={start}"
                
                print(f"Scraping Indeed page {page_num + 1}: {url}")
                
                try:
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    await page.wait_for_selector('[data-testid="jobTitle"], .jobTitle, .slider_container .slider_item', timeout=10000)
                    job_cards = await page.query_selector_all('.slider_container .slider_item, [data-testid="jobTitle"]')
                    
                    for card in job_cards:
                        try:
                            job = await self._extract_indeed_job(card, page)
                            if job and job.get('apply_url'):
                                job['source'] = 'indeed'
                                jobs.append(job)
                        except Exception as e:
                            print(f"Error extracting Indeed job: {e}")
                            continue
                    
                    print(f"Found {len(job_cards)} jobs on Indeed page {page_num + 1}")
                    
                except Exception as e:
                    print(f"Error scraping Indeed page {page_num + 1}: {e}")
                    continue
                
                await asyncio.sleep(random.uniform(2, 4))
                
        except Exception as e:
            print(f"Error in Indeed scraper: {e}")
        finally:
            await page.close()
        
        return jobs
    
    async def _extract_indeed_job(self, card, page) -> Optional[Dict[str, Any]]:
        """Extract job details from Indeed job card."""
        try:
            title_elem = await card.query_selector('h2 a, [data-testid="jobTitle"] a, .jobTitle a')
            title = await title_elem.inner_text() if title_elem else "Unknown"
            
            company_elem = await card.query_selector('.companyName, [data-testid="company-name"], .company')
            company = await company_elem.inner_text() if company_elem else "Unknown"
            
            location_elem = await card.query_selector('[data-testid="job-location"], .companyLocation, .location')
            location = await location_elem.inner_text() if location_elem else "Not specified"
            
            salary_elem = await card.query_selector('.salary-snippet-container, [data-testid="job-salary"], .salary')
            salary = await salary_elem.inner_text() if salary_elem else "Not disclosed"
            
            summary_elem = await card.query_selector('.job-snippet, [data-testid="job-summary"], .summary')
            summary = await summary_elem.inner_text() if summary_elem else ""
            
            link_elem = await card.query_selector('h2 a, [data-testid="jobTitle"] a')
            apply_url = ""
            if link_elem:
                href = await link_elem.get_attribute('href')
                if href:
                    apply_url = f"{JOB_BOARDS['indeed']}{href}" if href.startswith('/') else href
            
            return {
                'title': title.strip() if title else "Unknown",
                'company': company.strip() if company else "Unknown",
                'location': location.strip() if location else "Not specified",
                'salary': salary.strip() if salary else "Not disclosed",
                'experience_required': "Not specified",
                'skills_required': "",
                'description': summary.strip() if summary else "",
                'apply_url': apply_url
            }
            
        except Exception as e:
            print(f"Error extracting Indeed job details: {e}")
            return None
    
    async def search_jobs(
        self,
        role: str,
        location: str,
        experience: Optional[int] = None,
        pages: int = 3
    ) -> List[Dict[str, Any]]:
        """Search jobs across all job boards."""
        all_jobs = []
        
        # Scrape Naukri
        try:
            naukri_jobs = await self.scrape_naukri(role, location, experience, pages)
            all_jobs.extend(naukri_jobs)
            print(f"Total Naukri jobs: {len(naukri_jobs)}")
        except Exception as e:
            print(f"Error scraping Naukri: {e}")
        
        # Scrape Indeed
        try:
            indeed_jobs = await self.scrape_indeed(role, location, experience, pages)
            all_jobs.extend(indeed_jobs)
            print(f"Total Indeed jobs: {len(indeed_jobs)}")
        except Exception as e:
            print(f"Error scraping Indeed: {e}")
        
        # Remove duplicates based on company + title
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = f"{job.get('company', '')}-{job.get('title', '')}"
            if key not in seen and key != "Unknown-Unknown":
                seen.add(key)
                unique_jobs.append(job)
        
        print(f"Total unique jobs found: {len(unique_jobs)}")
        return unique_jobs
    
    async def search_jobs_for_suggestions(
        self,
        query: str,
        location: str,
        salary_range: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Quick search for job suggestions."""
        jobs = await self.search_jobs(query, location, pages=2)
        return jobs[:limit]


# Synchronous wrapper for easier usage
async def scrape_jobs_async(
    role: str,
    location: str,
    experience: Optional[int] = None,
    pages: int = 3
) -> List[Dict[str, Any]]:
    """Async function to scrape jobs."""
    async with JobScraper() as scraper:
        return await scraper.search_jobs(role, location, experience, pages)


def scrape_jobs(
    role: str,
    location: str,
    experience: Optional[int] = None,
    pages: int = 3
) -> List[Dict[str, Any]]:
    """Synchronous wrapper to scrape jobs."""
    return asyncio.run(scrape_jobs_async(role, location, experience, pages))


async def get_job_suggestions(
    query: str,
    location: str,
    salary_range: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Get job suggestions for immediate response."""
    async with JobScraper() as scraper:
        return await scraper.search_jobs_for_suggestions(query, location, salary_range, limit)
>>>>>>> 72fad7f (Member 1: Backend complete - FastAPI server, database, Twilio integration, resume parser)
