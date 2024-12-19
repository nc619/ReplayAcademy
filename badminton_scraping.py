from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import winsound
from dataclasses import dataclass
from typing import List

@dataclass
class Activity:
    name: str
    location: str
    date: str
    time: str
    duration: str
    spaces: int
    cost: str
    description: str

def setup_chrome_with_profile():
    chrome_options = Options()
    chrome_options.add_argument(f'user-data-dir=C:\\Users\\Nico\\AppData\\Local\\Google\\Chrome\\User Data')
    chrome_options.add_argument('profile-directory=Default')
    
    # Add these new options to fix the crash
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--remote-debugging-port=9222')  # Add a debugging port
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Make sure Chrome is not already running
    import os
    os.system("taskkill /im chrome.exe /f")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def extract_activities(driver) -> List[Activity]:
    activities = []
    
    print("Waiting for activities to load...")
    # Wait for the grid of activities to load
    activity_grid = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "xn-bookings-grid"))
    )
    
    # Get selected date from the calendar
    try:
        selected_date = driver.find_element(By.CSS_SELECTOR, ".day.selected .date").get_attribute('innerHTML')
        # Clean up the date string (remove HTML sup tags)
        selected_date = selected_date.replace('<sup>', '').replace('</sup>', '')
        print(f"Processing activities for {selected_date}...")
    except:
        selected_date = "Date not found"
        print("Warning: Could not determine current date")
    
    # Find all activity cards
    activity_cards = activity_grid.find_elements(By.TAG_NAME, "li")
    print(f"Found {len(activity_cards)} activities to process")
    
    for card in activity_cards:
        try:
            # Extract basic info
            heading = card.find_element(By.CLASS_NAME, "xn-heading").text
            print(f"  Processing {heading}...", end='\r')  # Use carriage return to not spam console
            
            # Extract content from xn-content div
            content = card.find_element(By.CLASS_NAME, "xn-content")
            location = content.find_element(By.CLASS_NAME, "xn-booking-location").text
            time = content.find_element(By.CLASS_NAME, "xn-booking-starttime").text
            duration = content.find_element(By.CLASS_NAME, "xn-booking-duration").text
            
            # Handle spaces conversion more gracefully
            try:
                spaces_text = content.find_element(By.CLASS_NAME, "xn-booking-spaces").text.split(" ")[0]
                spaces = int(spaces_text) if spaces_text.isdigit() else 0
            except:
                spaces = 0
            
            try:
                cost = content.find_element(By.CLASS_NAME, "xn-booking-cost").text
            except:
                cost = "N/A"
                
            # Get description
            try:
                description = card.find_element(
                    By.CLASS_NAME, "xn-booking-description-content"
                ).get_attribute("textContent")
            except:
                description = "No description available"
            
            activity = Activity(
                name=heading,
                location=location,
                date=selected_date,
                time=time,
                duration=duration,
                spaces=spaces,
                cost=cost,
                description=description
            )
            activities.append(activity)
            
        except Exception as e:
            print(f"\nError processing activity: {str(e)}")
            continue
    
    print("\nFinished processing all activities")        
    return activities

def select_next_days(driver, days=7):
    """Select the next 'days' days from the booking calendar."""
    try:
        print("Waiting for calendar to load...")
        day_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "day"))
        )
        
        print(f"Found {len(day_elements)} available days")
        # Click on the next 'days' days
        for i in range(min(days, len(day_elements))):
            day_name = day_elements[i].find_element(By.CLASS_NAME, "name").text
            print(f"Selecting {day_name}...")
            day_elements[i].click()
            time.sleep(1)  # Wait a moment for the page to update
        print("Finished selecting days")
    except Exception as e:
        print(f"Error selecting days: {str(e)}")

def login_and_navigate_to_bookings(driver):
    """Login and navigate to the bookings page."""
    print("Loading login page...")
    login_url = "https://www.imperial.ac.uk/sport/members/identity/login?signin=d28a2fdc1f269ce2536fe2dceb80ff20"
    driver.get(login_url)
    
    try:
        print("Waiting for login button...")
        # Wait for the login button to be clickable and click it
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'identity/external')]"))
        )
        print("Clicking login button...")
        login_button.click()
        print("Waiting for page to load after login...")
        time.sleep(5)  # Wait for the page to load after login
    except Exception as e:
        print(f"Error during login: {str(e)}")

def handle_alerts(driver):
    """Handle any alerts or announcements that might be present"""
    try:
        # Find all alert close buttons
        alert_buttons = driver.find_elements(By.CLASS_NAME, "xn-alert-close")
        for button in alert_buttons:
            if button.is_displayed():
                print("Closing alert message...")
                button.click()
                time.sleep(0.5)
        
        # Handle any other types of alerts/announcements
        alerts = driver.find_elements(By.CLASS_NAME, "xn-alerts")
        for alert in alerts:
            if alert.is_displayed():
                try:
                    close_button = alert.find_element(By.CLASS_NAME, "xn-close")
                    print("Closing announcement...")
                    close_button.click()
                    time.sleep(0.5)
                except:
                    pass
    except Exception as e:
        print(f"Warning: Error handling alerts: {str(e)}")

def check_for_availability(url, target_activity="Badminton", min_spaces=1):
    print("\n=== Starting Activity Checker ===")
    print(f"Target activity: {target_activity}")
    print(f"Minimum spaces required: {min_spaces}")
    print("\nInitializing Chrome...")
    driver = setup_chrome_with_profile()
    
    try:
        login_and_navigate_to_bookings(driver)  # Login and navigate to bookings
        print("\nNavigating to bookings page...")
        driver.get(url)
        
        iteration = 1
        while True:
            print(f"\n=== Checking iteration {iteration} ===")
            
            # Handle any alerts before proceeding
            handle_alerts(driver)
            
            found_sessions = False
            # Check each day
            for i in range(7):  # Check 7 days
                try:
                    # Get fresh day elements for each iteration
                    print("\nWaiting for calendar to load...")
                    day_elements = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, "day"))
                    )
                    
                    if i >= len(day_elements):
                        print(f"No more days available after day {i}")
                        break
                    
                    # Handle any alerts that might have appeared
                    handle_alerts(driver)
                    
                    day_name = day_elements[i].find_element(By.CLASS_NAME, "name").text
                    print(f"\nChecking {day_name}...")
                    
                    # Wait for element to be clickable
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(day_elements[i])
                    )
                    
                    # Scroll element into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", day_elements[i])
                    time.sleep(0.5)  # Wait for scroll to complete
                    
                    # Click the day
                    day_elements[i].click()
                    time.sleep(2)  # Wait longer for activities to update
                    
                    activities = extract_activities(driver)
                    
                    print(f"Filtering activities for {target_activity}...")
                    # Filter and check activities
                    available_activities = [
                        activity for activity in activities 
                        if target_activity.lower() in activity.name.lower() 
                        and activity.spaces >= min_spaces
                    ]
                    
                    if available_activities:
                        found_sessions = True
                        print("\n🎉 Available sessions found! 🎉")
                        for activity in available_activities:
                            print(f"\n📅 {activity.name} on {activity.date} at {activity.time}")
                            print(f"📍 Location: {activity.location}")
                            print(f"👥 Spaces: {activity.spaces}")
                            print(f"💰 Cost: {activity.cost}")
                        
                        # Play alert sound
                        winsound.Beep(1000, 1000)
                    else:
                        print(f"No available {target_activity} sessions found with {min_spaces} or more spaces for {day_name}")
                
                except Exception as e:
                    print(f"Error processing day {i+1}: {str(e)}")
                    # Refresh the page if we encounter a stale element
                    if "stale element" in str(e):
                        print("Refreshing page due to stale elements...")
                        driver.refresh()
                        time.sleep(2)
                    continue
            
            if not found_sessions:
                print("\nNo available sessions found for any day")
            
            print(f"\nWaiting 10 seconds before next check...")
            time.sleep(10)  # Check every 10 seconds
            iteration += 1
            
            # Refresh the page to avoid stale elements
            print("Refreshing page...")
            driver.refresh()
            time.sleep(2)  # Wait for page to reload
            
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
    finally:
        print("\nClosing Chrome...")
        driver.quit()
        print("=== Activity Checker Stopped ===")

if __name__ == "__main__":
    booking_url = "https://www.imperial.ac.uk/sport/members/en/Members/Bookings"
    check_for_availability(booking_url, target_activity="Gym", min_spaces=1)