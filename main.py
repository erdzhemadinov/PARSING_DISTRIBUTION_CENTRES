from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from time import sleep
import pandas as pd
from tqdm import tqdm
import time
from selenium.webdriver.common.keys import Keys
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import argparse
from datetime import datetime
from statistics import mode


class YandexMapParser():
    def __init__(self, link,  sleep_time=0.1,
                 change_header_iter=10,save_after=100,
                 with_selenium=True, google_token_file='token.txt',
                 query="Ozon, пункты выдачи москва",
                 region='москва', currdate=datetime.now().strftime('%s'), browser='firefox'):

        self.link = link
        self.sleep_time = sleep_time
        self.change_header_iter = change_header_iter
        self._header = self._change_user_agent()
        self.save_after = save_after
        self.with_selenium = with_selenium
        self.google_token_file = google_token_file
        self.query = query
        self.region = region
        self.currdate = currdate
        self.browser = browser

        self._df = None

        if self.with_selenium:
            if self.browser == 'firefox':
                self.driver = webdriver.Firefox(executable_path='drivers/geckodriver_firefox')
            elif self.browser == 'chrome':
                self.driver = webdriver.Chrome(executable_path='drivers/geckodriver_firefox')
        else:
            self.driver = None

        self.token = self._load_token()

    def _load_token(self):

        """
        This function load google token from txt file
        :return:
        token: string having token
        """
        #  load token
        with open(self.google_token_file) as f:
            lines = f.readlines()

        return str(lines[0])

    def _change_user_agent(self):

        """
        This function switch user anonymity

        :return:
        Dict having useragent fot higher am
        """

        _ua = UserAgent()
        return {'User-Agent': str(_ua.chrome)}

    def _get_google_results(self, address,  return_full_response=False, return_lat_lon=False):
        """
        Get geocode results from Google Maps Geocoding API.


        @param address: String address as accurate as possible. For Example "18 Grafton Street, Dublin, Ireland"
        @param api_key: String API key if present from google.
                        If supplied, requests will use your allowance from the Google API. If not, you
                        will be limited to the free usage of 2500 requests per day.
        @param return_full_response: Boolean to indicate if you'd like to return the full response from google. This
                        is useful if you'd like additional location details for storage or parsing later.

        @ param return_lat_lon: Boolean If you'd return only corrdinates (lat, lon) as tuple.
       """
        # Set up your Geocoding url
        geocode_url = "https://maps.googleapis.com/maps/api/geocode/json?address={}".format(address)
        if self.token is not None:
            geocode_url = geocode_url + "&key={}".format(self.token)

        # Ping google for the results:
        results = requests.get(geocode_url)
        # Results will be in JSON format - convert to dict using requests functionality
        results = results.json()

        # if there's no results or an error, return empty results.
        if len(results['results']) == 0:
            output = {
                "formatted_address": None,
                "latitude": None,
                "longitude": None,
                "accuracy": None,
                "google_place_id": None,
                "type": None,
                "postcode": None
            }
        else:
            answer = results['results'][0]
            output = {
                "formatted_address": answer.get('formatted_address'),
                "latitude": answer.get('geometry').get('location').get('lat'),
                "longitude": answer.get('geometry').get('location').get('lng'),
                "accuracy": answer.get('geometry').get('location_type'),
                "google_place_id": answer.get("place_id"),
                "type": ",".join(answer.get('types')),
                "postcode": ",".join([x['long_name'] for x in answer.get('address_components')
                                      if 'postal_code' in x.get('types')])
            }

        # Append some other details:
        output['input_string'] = address
        output['number_of_results'] = len(results['results'])
        output['status'] = results.get('status')
        if return_full_response is True:
            output['response'] = results
            return output
        elif return_lat_lon is True:
            return (output['latitude'], output['longitude'])
        else:
            return output

    def parse_data(self):
        """
        This function parse yandex map and extract information
        :return:
        """

        # if selenium is switched off
        if not self.with_selenium:
            htmlContent = requests.get(self.link, headers=self._header)
            soup = BeautifulSoup(htmlContent.content, 'html.parser')
        else:
            # if selenium is on
            self.driver.get(self.link)

            # insert query in input in yandex map

            wait = WebDriverWait(self.driver, 10)
            el = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "input__control")))
            el.send_keys(self.query)
            el.send_keys(Keys.ENTER)

            # if we have scroll on site(if we have enough number of observations
            try:
                # get info about scroll
                wait = WebDriverWait(self.driver, 10)
                source = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "scroll__scrollbar-thumb")))

                source_ele = self.driver.find_element(By.CLASS_NAME, "scroll__scrollbar-thumb")
                target_ele = self.driver.find_element(By.CLASS_NAME, "scroll__scrollbar-thumb")

                target_ele_x_offset = target_ele.location.get("x")
                target_ele_y_offset = target_ele.location.get("y")

                height = int(self.driver.execute_script("return document.documentElement.scrollHeight"))
                # Performs dragAndDropBy onto the target element offset position
                cnt = 0
                last_len = -10e6
                curr_len = -10e5
                while True:
                    # drag slider down till the end. Calculate length
                    # of slider current position and calculating offset as
                    #  height(height of windopw) - slider height - slider position
                    time.sleep(10)

                    slider = self.driver.find_elements_by_class_name('scroll__scrollbar-thumb')[0]
                    slider_size = slider.size

                    slider_w, slider_h = slider_size['width'], slider_size['height']

                    webdriver.ActionChains(self.driver).drag_and_drop_by_offset(source_ele, target_ele_x_offset,
                                                                                height - slider_h - slider.location.get(
                                                                                    "y")).perform()
                    webdriver.ActionChains(self.driver).drag_and_drop_by_offset(source_ele, target_ele_x_offset,
                                                                                1).perform()

                    html = self.driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')

                    # calculating stop criteria. If no more new elements stop parsing
                    addresses = soup.find_all("div", {"class": "search-business-snippet-view__address"}, text=True)
                    addresses = [i.text.strip().replace("\xa0", " ") for i in addresses]
                    curr_len = len(addresses)
                    # print(curr_len)

                    if last_len == curr_len:
                        break
                    else:
                        last_len = curr_len
            except TimeoutException:
                pass


            # extract information
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # extract adresses
            addresses = soup.find_all("div", {"class": "search-business-snippet-view__address"}, text=True)
            addresses = [i.text.strip().replace("\xa0", " ") for i in addresses]

            # extract rating
            rate = soup.find_all("span", {"class": "business-rating-badge-view__rating"}, text=True)
            rate = [i.text.strip().replace("\xa0", " ").replace(",", ".") for i in rate]

            # extract categories
            typing = soup.find_all("div", {"class": "search-business-snippet-view__categories"}, text=True)
            typing = [i.text.strip().replace("\xa0", " ").replace(",", ".") for i in typing]

            # extract titles
            title = soup.find_all("div", {"class": "search-business-snippet-view__title"}, text=True)
            title = [i.text.strip().replace("\xa0", " ").replace(",", ".") for i in title]

            lat_list = []
            lon_list = []

            # geocoding via google
            for i in tqdm(addresses):

                sleep(0.2)
                lat, lon = self._get_google_results(i, False, True)
                lat_list.append(lat)
                lon_list.append(lon)

            # create dataframe
            self._df = pd.DataFrame({
                'address': addresses,
                'type': mode(typing),
                'title': mode(title),
                'lat': lat_list,
                'lon': lon_list,
                'region': self.region,
                'timestamp': self.currdate
            })

        # colse drivers
        self.driver.close()
        self.driver.quit()

        return self._df


if __name__ == '__main__':

    my_parser = argparse.ArgumentParser()
    my_parser.add_argument("-b", '--browser', choices=['firefox', 'chrome'],
                           action='store', type=str, required=True)
    my_parser.add_argument('-q', '--query', action='store', type=str, required=True, default="Ozon, пункты выдачи ")
    my_parser.add_argument('-l', '--range_left', action='store', type=int, default=0, required=False)
    my_parser.add_argument('-r', '--range_right', action='store', type=int, default=86,  required=False)

    args = my_parser.parse_args()

    link = "https://yandex.ru/maps/?ll=84.163264%2C61.996842&z=3"

    search_string = args.query
    slice = (args.range_left, args.range_right)
    browser = args.browser

    regions = pd.read_excel("regions.xlsx")['name'].values.tolist()

    df = None
    currdate = datetime.now().strftime('%s')

    for i in tqdm(range(slice[0], slice[1])):

        query = search_string + " " + regions[i]
        parser = YandexMapParser(link=link,
                                 sleep_time=0.1, change_header_iter=10,
                                 save_after=100, with_selenium=True,
                                 google_token_file="token.txt", query=query,
                                 region=regions[i], currdate=currdate, )

        if df is None:
            df = parser.parse_data()
        else:
            df = df.append(parser.parse_data())
        # print("done {} shape of df is {}".format(regions[i], df.shape))

        df.to_excel('./output/result_full.xlsx', index=None)

