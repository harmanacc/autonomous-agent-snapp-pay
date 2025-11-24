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


class Price(BaseModel):
    full_price: float
    discount_price: float
    discount_percentage: float
    product_name: str


class PriceList(BaseModel):
    prices: List[Price]


controller = Controller(output_model=PriceList)

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
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
    # model='x-ai/grok-4.1-fast',
    # model='x-ai/grok-4-fast',
    model='openai/gpt-oss-120b',
    # model='qwen/qwen3-coder-30b-a3b-instruct',
    # model='google/gemini-2.0-flash-001',
    # model='google/gemini-2.5-flash-lite',
    # model='openai/gpt-4o-mini',
    # model='openai/gpt-5-mini',
    # model='openai/gpt-oss-20b',
    # model='openai/gpt-5-nano',
    # model='minimax/minimax-m2',
    # model='z-ai/glm-4.6',
    # model='meta-llama/llama-4-scout',
    # model='qwen/qwen3-32b',
)


initial_actions = [
    {
        'navigate': {
            'url': 'https://snapppay.ir/timetable/?utm_source=snapppay&utm_medium=ecommerce&utm_campaign=Teasing',
            'new_tab': False
        }
    }
]


agent = Agent(
    task='''the website you are about to see is a e-commerce app in persian language . 
    navigate to https://snapppay.ir/timetable/?utm_source=snapppay&utm_medium=ecommerce&utm_campaign=Teasing
    give me a list of the found product which has the discount percentage more than 70% off . when you see the button for
    <button id="sp-more" class="sp-more" type="button">محصولات بیشتر ...</button>
    click on it for 3 times and wait 1 second . this will load more product .
    ''',
    llm=llm,
    use_vision=False,
    initial_actions=initial_actions,
    controller=controller,
    browser=browser
)


async def main():
    try:
        # Pre-kill for clean start
        os.system('pkill -f chrome || true')
        time.sleep(2)
        
        print("Launching with CDP enabled...")
        result = await agent.run(max_steps=20)  # More room for init + actions
        
        raw_data = result.final_result()
        data = PriceList.model_validate_json(raw_data)
        print(data)
        
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