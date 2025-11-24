import asyncio
import os
import time
import sys

from dotenv import load_dotenv

from browser_use import Agent, ChatOpenAI, Controller, Browser

from pydantic import BaseModel
from typing import List

load_dotenv()

# Increase timeout env (set higher if needed)
os.environ['BROWSER_USE_TIMEOUT'] = '60'

# Verify profile dir exists and is readable
profile_dir = '/home/arman/.config/google-chrome/Default'
if not os.path.exists(profile_dir):
    raise ValueError(f"Profile dir not found: {profile_dir}. Check path.")



# executable_path=' /usr/bin/chromium-snapshot-bin',
# user_data_dir=' ~/.config/chromium',
# profile_directory='Default',

# executable_path='/usr/bin/google-chrome-stable',  # Confirm with `which google-chrome`
# user_data_dir='/home/arman/.config/google-chrome',
# profile_directory='Default',

browser = Browser(
 	executable_path='/usr/bin/chromium-snapshot-bin',
 	user_data_dir='~/.config/chromium',
 	profile_directory='Default',
    headless=False,
    args=[
        '--remote-debugging-port=0',  # Dynamic CDP port—critical for connection
        '--no-sandbox',               # Linux stability
        '--disable-dev-shm-usage',    # Avoid shared mem issues
        '--disable-gpu',              # If GPU causes hangs
        '--disable-extensions-except=/path/to/any-needed',  # Skip if no extensions needed
        '--no-first-run',
        '--disable-default-apps',
    ],
    # Optional: env={'DEBUG_PORT': '0'} if needed
)


llm = ChatOpenAI(
    model='x-ai/grok-4.1-fast',  
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)


initial_actions = [
    {
        'navigate': {
            'url': 'https://sep5.ir/landing/sepas/carwash',
            'new_tab': True
        }
    }
]


agent = Agent(
    task='''this website would be a carwash app in persian language .
    after the form is rendered get me a sedan carwash with full vip for بخشایش street .
    in the decscription of the order add that i want to have my tires cleaned as well in farsi .
    confirm that the carwash has been successfully placed
    ''',
    llm=llm,
    use_vision=False,
    initial_actions=initial_actions,
    browser=browser
)


async def main():
    try:
        await agent.run(max_steps=20)  # More room for init + actions
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nDebug: If CDP failed, check for open Chrome window and manually visit http://localhost:<port>/json (port from logs).")
    finally:
        # Don't auto-close—inspect if needed
        input("Press Enter to close browser...")


if __name__ == "__main__":
    asyncio.run(main())