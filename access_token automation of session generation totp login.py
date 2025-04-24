
    
#pip install pyotp
from kiteconnect import KiteConnect
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
from pyotp import TOTP
from selenium.webdriver.chrome.options import Options
    
    
cwd = os.chdir("C:\\Users\\USER\\OneDrive\\Desktop\\algo")
    
def autologin():
        token_path = "api_key.txt"
        key_secret = open(token_path,'r').read().split()
        kite = KiteConnect(api_key=key_secret[0])
        service = webdriver.chrome.service.Service('./chromedriver')
        service.start()
        options = Options()
        options.add_argument('--headless')  # Enable headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        #options = webdriver.ChromeOptions()
        #options.add_argument('--headless')
        #options = options.to_capabilities()
        driver = webdriver.Remote(service.service_url, options= options)
        driver.get(kite.login_url())
        driver.implicitly_wait(10)
        username = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[1]/input')
        password = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/input')
        username.send_keys(key_secret[2])
        password.send_keys(key_secret[3])
        driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[4]/button').click()
        totp = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div[2]/div/div[2]/form/div[1]/input')
        #totp_token = TOTP(key_secret[4])
        totp_token = TOTP("3MPQTCB4OQHQOGQPPAXHX3MGDZPFSASP")
        token = totp_token.now()
        print(token)
        totp.send_keys(token)
        time.sleep(10)
        request_token=driver.current_url.split('request_token=')[1][:32]
        print("********************************************************")
        print(request_token)
        print("********************************************************")
        with open('request_token.txt', 'w') as the_file:
            the_file.write(request_token)
        driver.quit()
    
autologin()
    
    
#generating and storing access token - valid till 6 am the next day
request_token = open("request_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
data = kite.generate_session(request_token, api_secret=key_secret[1])
with open('access_token.txt', 'w') as file:
    file.write(data["access_token"])
