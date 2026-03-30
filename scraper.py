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
