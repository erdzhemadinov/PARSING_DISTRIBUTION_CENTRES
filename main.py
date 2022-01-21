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
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
import argparse
from datetime import datetime
from statistics import mode
from db_load import DbAction


class YandexMapParser:
    def __init__(self, _link,  sleep_time=0.1,
                 change_header_iter=10,save_after=100,
                 with_selenium=True, token=None,
                 _query="Ozon, пункты выдачи москва",
                 region='москва', _curr_date=datetime.now().strftime('%s'), _browser='firefox'):

        self.link = _link
        self.sleep_time = sleep_time
        self.change_header_iter = change_header_iter
        self._header = self._change_user_agent()
        self.save_after = save_after
        self.with_selenium = with_selenium

        self.query = _query
        self.region = region
        self.curr_date = _curr_date
        self.browser = _browser

        self._df = None

        if self.with_selenium:
            if self.browser == 'firefox':
                self.driver = webdriver.Firefox(executable_path='drivers/geckodriver_firefox')
            elif self.browser == 'chrome':
                self.driver = webdriver.Chrome(executable_path='drivers/chromedriver97')
        else:
            self.driver = None

        self.token = token

    @staticmethod
    def _change_user_agent():

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
        @param return_full_response: Boolean to indicate if you'd like to return the full response from Google. This
                        is useful if you'd like additional location details for storage or parsing later.

        @ param return_lat_lon: Boolean If you'd return only coordinates (lat, lon) as tuple.
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
            return output['latitude'], output['longitude']
        else:
            return output

    def parse_data(self):
        """
        This function parse yandex map and extract information
        :return:
        """

        # if selenium is switched off
        if not self.with_selenium:
            html_content = requests.get(self.link, headers=self._header)
            soup = BeautifulSoup(html_content.content, 'html.parser')
        else:
            # if selenium is on
            self.driver.get(self.link)

            # insert query in input in yandex map

            wait = WebDriverWait(self.driver, 15)
            el = wait.until(ec.visibility_of_element_located((By.CLASS_NAME, "input__control")))
            el.send_keys(self.query)
            el.send_keys(Keys.ENTER)

            # if we have scroll on site(if we have enough number of observations
            try:
                # get info about scroll
                wait = WebDriverWait(self.driver, 15)
                source = wait.until(ec.visibility_of_element_located(
                    (By.CLASS_NAME, "scroll__scrollbar-thumb")))

                source_ele = self.driver.find_element(By.CLASS_NAME, "scroll__scrollbar-thumb")
                target_ele = self.driver.find_element(By.CLASS_NAME, "scroll__scrollbar-thumb")

                target_ele_x_offset = target_ele.location.get("x")
                # target_ele_y_offset = target_ele.location.get("y")

                height = int(self.driver.execute_script(
                    "return document.documentElement.scrollHeight"
                ))
                # Performs dragAndDropBy onto the target element offset position
                last_len = -10e6

                while True:
                    # drag slider down till the end. Calculate length
                    # of slider current position and calculating offset as
                    #  height(height of window) - slider height - slider position
                    time.sleep(13)

                    slider = self.driver.find_elements_by_class_name('scroll__scrollbar-thumb')[0]
                    slider_size = slider.size

                    slider_w, slider_h = slider_size['width'], slider_size['height']

                    webdriver.ActionChains(self.driver).drag_and_drop_by_offset(source_ele, target_ele_x_offset,
                                                                                height - slider_h - slider.location.get(
                                                                                    "y")).perform()

                    time.sleep(4)
                    webdriver.ActionChains(self.driver).drag_and_drop_by_offset(source_ele, target_ele_x_offset,
                                                                                1).perform()

                    html = self.driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')

                    # calculating stop criteria. If no more new elements stop parsing
                    addresses = soup.find_all("div", {"class": "search-business-snippet-view__address"}, text=True)
                    addresses = [i.text.strip().replace("\xa0", " ") for i in addresses]
                    curr_len = len(addresses)

                    if last_len == curr_len:
                        break
                    else:
                        last_len = curr_len
            except TimeoutException:
                pass

            # extract information
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # extract addresses
            addresses = soup.find_all("div",
                                      {"class": "search-business-snippet-view__address"}, text=True)
            addresses = [i.text.strip().replace("\xa0", " ") for i in addresses]

            # extract rating
            # rate = soup.find_all("span",
            #                      {"class": "business-rating-badge-view__rating"}, text=True)
            # rate = [i.text.strip().replace("\xa0", " ").replace(",", ".") for i in rate]

            # extract categories
            typing = soup.find_all("div",
                                   {"class": "search-business-snippet-view__categories"}, text=True)
            typing = [i.text.strip().replace("\xa0", " ").replace(",", ".") for i in typing]

            # extract titles
            title = soup.find_all("div",
                                  {"class": "search-business-snippet-view__title"}, text=True)
            title = [i.text.strip().replace("\xa0", " ").replace(",", ".") for i in title]

            lat_list = []
            lon_list = []

            # geocoding via google
            for j in tqdm(addresses):

                sleep(0.2)
                lat, lon = self._get_google_results(j, False, True)
                lat_list.append(lat)
                lon_list.append(lon)

            # create dataframe
            self._df = pd.DataFrame({
                'ADDRESS': addresses,
                'TYPE_PP': mode(typing),
                'COMPANY_NAME': mode(title),
                'LAT': lat_list,
                'LON': lon_list,
                'REGION': self.region,
                'DATE_OF_LOADING': self.curr_date
            })

        # close drivers
        self.driver.close()
        self.driver.quit()

        return self._df


if __name__ == '__main__':
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument("-b", '--browser', choices=['firefox', 'chrome'],
                           action='store', type=str, default='chrome', required=True)
    my_parser.add_argument('-q', '--query', action='store', type=str, required=True, default="Ozon, пункты выдачи ")
    my_parser.add_argument('-l', '--range_left', action='store', type=int, default=0, required=False)
    my_parser.add_argument('-r', '--range_right', action='store', type=int, default=84,  required=False)
    my_parser.add_argument('-t', '--token', action='store', type=str, required=True)
    my_parser.add_argument('-sp', '--save_place', choices=['excel', 'database', 'both'],
                           action='store', type=str, required=True, default=['excel'])

    args = my_parser.parse_args()

    link = "https://yandex.ru/maps/?ll=84.163264%2C61.996842&z=3"

    search_string = args.query
    _slice = (args.range_left, args.range_right)
    browser = args.browser

    regions = pd.read_excel("regions.xlsx")['name'].values.tolist()

    df_all = None

    curr_date = datetime.today().strftime('%Y-%m-%d')

    for region_id in tqdm(range(_slice[0], _slice[1])):

        query = search_string + " " + regions[region_id]
        parser = YandexMapParser(_link=link,
                                 sleep_time=0.1, change_header_iter=10,
                                 save_after=100, with_selenium=True,
                                 token=args.token, _query=query,
                                 region=regions[region_id], _curr_date=curr_date, _browser=browser)

        if df_all is None:
            df_new = parser.parse_data()
            df_new['DATE_OF_LOADING_FIRST'] = datetime.today().strftime('%Y-%m-%d')
            df_all = df_new.copy()
        else:
            df_new = parser.parse_data()
            df_new['DATE_OF_LOADING_FIRST'] = datetime.today().strftime('%Y-%m-%d')

            df_all = df_all.append(df_new)

        if args.save_place in ['excel', 'both']:
            df_new.to_excel('./output/result_{0}_{1}.xlsx'.format(search_string, regions[region_id]), index=None)

            df_all.to_excel('./output/full_report_{0}.xlsx'.format(search_string), index=None)

        if args.save_place in ['database', 'both']:
            db_conn = DbAction('config_db.json')

            type_of_points = df_new['TYPE_PP'].values[0]
            type_of_company_name = df_new['COMPANY_NAME'].values[0]
            type_of_company_region = df_new['REGION'].values[0]

            df = db_conn.select(
                'SELECT * FROM  DATA_SCIENCE.PARSER_DELIVERY_POINTS WHERE TYPE_PP=\'{0}\' AND COMPANY_NAME=\'{1}\' AND REGION=\'{2}\'' \
                .format(type_of_points, type_of_company_name, type_of_company_region))

            if len(df) == 0:
                df_insert = df_new
            else:
                df_insert = db_conn.merge_dataframe_diff(df, df_new)

            db_conn.delete(
                "DELETE from DATA_SCIENCE.PARSER_DELIVERY_POINTS WHERE TYPE_PP=\'{0}\' AND COMPANY_NAME=\'{1}\' AND REGION=\'{2}\'  ".format(
                    type_of_points, type_of_company_name, type_of_company_region))

            db_conn.insert(df_insert, "DATA_SCIENCE",
                           "PARSER_DELIVERY_POINTS")
