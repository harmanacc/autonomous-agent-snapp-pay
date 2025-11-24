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

my_number = os.getenv('MY_PHONE_NUMBER')
print(f"My phone number: {my_number}")

product_name='برس موی گره‌گشا و حالت‌دهی پریمیوم باونس کرل'

main_pag_url='https://snapppay.ir/blackfriday/?utm_source=landing_ir&utm_medium=Hero_banner&utm_campaign=black-404&utm_content=timetable'

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


browser = Browser(
    
 	# executable_path='/usr/bin/firefox',
 	# # user_data_dir='~/.config/chromium',
 	# profile_directory='Default',
    # headless=False,
    # args=[
    #     '--remote-debugging-port=0', 
    #     '--no-sandbox',              
    #     '--disable-dev-shm-usage',   
    #     '--disable-gpu',             
    #     '--disable-extensions-except=/path/to/any-needed',  
    #     '--no-first-run',
    #     '--disable-default-apps',
    # ],
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
            'url': main_pag_url,
            'new_tab': False
        }
    }
]


agent = Agent(
    task='''
    <task>
    <description>
        You are an autonomous e-commerce shopping agent for a Persian site. 
        Your goal: Find and buy the specific product "{product_name}" from the discounted list, 
        using Snapp Pay if possible, and reach the banking payment page. 
        This is a one-shot task—decide intuitively on any unclear UI 
        (e.g., similar buttons, loading delays, minor text variations in Farsi) 
        to keep momentum; if stuck >5s, retry or skip to next logical step. 
        Use vision to scan for Farsi text/icons.
    </description>
    
    <checklist>
        <step id="1">
            <title>Navigate & Load Products</title>
            <instructions>
                - Go to: {main_pag_url}
                - Scan for products >70% off (look for discount badges like "70% تخفیف").
                - If "&lt;button id='sp-more' class='sp-more'&gt;محصولات بیشتر ...&lt;/button&gt;" visible, 
                if product is not seen yet, click it 3x (wait 1s between).to find the product.
            </instructions>
        </step>
        
        <step id="2">
            <title>Select & Prep Product</title>
            <instructions>
                - Search for "{product_name}" in the list (fuzzy match on Farsi/English).
                - If found, click its card to enter product page.
                - Scrape page for any coupon codes (e.g., "کد تخفیف", banners, popups—related to product/site). 
                  Store in context (e.g., "Coupon: ABC123") for later use; apply if auto-applicable.
                - Edge: If multiple matches, pick cheapest/highest discount. 
                  If not found, end with "Product not available."
            </instructions>
        </step>
        
        <step id="3">
            <title>Add to Cart</title>
            <instructions>
                - On product page, find & click "افزودن به سبد خرید" (or similar add-to-cart button/icon).
                - Confirm added (check cart icon count or toast). 
                  If prompt for quantity/variant, default to 1x standard.
            </instructions>
        </step>
        
        <step id="4">
            <title>Login if Needed</title>
            <instructions>
                - If login modal/page appears, enter phone {my_number}
                - Click "ادامه" or "ارسال کد". 
                if there was a need for email and password, find the ورود با رمز یکبار مصرف which is again an otp option.
                  Wait 5s for user to input OTP manually—do not touch OTP field.
                - Resume flow once logged in (refresh if needed).
                - if forced to enter some info like email, password, sex etc . add whatever is needed. does not matter .
            </instructions>
        </step>
        
        <step id="5">
            <title>Cart & Checkout</title>
            <instructions>
                - Click cart icon/button ("سبد خرید") to view cart.
                - Verify "{product_name}" in cart; remove extras if any.
                - Proceed to checkout ("تسویه حساب").
                - At payment: Scan for Snapp Pay option (button/radio/checkbox like "اسنپ‌پی"). 
                  Select it first—if unavailable, use default (e.g., card).
                - Apply any scraped coupons if field visible ("کد تخفیف").
                - Click final "پرداخت" or "تایید"—success if redirected to bank gateway 
                  (e.g., URL changes to shetab/zarinpal).
            </instructions>
        </step>
    </checklist>
    
    <success_metric>
        Reach bank payment page (URL shift + payment form). 
        End with "Purchase initiated: [final URL]". 
        If fail (e.g., OOS, error), log reason & stop.
    </success_metric>
    
    <guidelines>
        - Stay fast: &lt;2min total, no backtracking unless critical.
    </guidelines>
</task>
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