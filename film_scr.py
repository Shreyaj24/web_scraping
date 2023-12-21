import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime


def recent_page_film_scrape():
    response_rr = requests.get(f"https://www.bbfc.co.uk/recently-rated")
    recently_rated_detail = []
    if response_rr.status_code == 200:
        recently_rated_html_content = response_rr.content
        recently_rated_soup = BeautifulSoup(recently_rated_html_content, 'html.parser')
        main_recent_added = recently_rated_soup.find('main', class_ = "Main_Main__46590")
        recent_added_list = main_recent_added.find_all('div', class_ = "SearchItem_SearchItem__3kbZF")
        for recent_added in recent_added_list:
            '''Detailed way to scrape information from movie page(DRY)'''
            anchor_tag = recent_added.find('a')
            href_rec = anchor_tag.get('href')
            recent_details_dict = scrape_film(href_rec)
            if type(recent_details_dict) == dict: 
                recently_rated_detail.append(recent_details_dict)
            else:
                print(recent_details_dict)

            '''Alternate way to scrape information from recent rated page itself(Gives limited information)'''
            #recent_dict = {}
            #rating_tag = recent_added.find('span', class_ = "Icon_Icon__9RCS8 SearchItem_Rating__2fbS8")['aria-label'].split()[1]
            #recent_tag_title = anchor_tag.find('h3').text
            #category = anchor_tag.find('span').text
            #release_date = recent_added.find('div', class_ ="Type_base__2EnB2 SearchItem_ReleaseDate__21k53")
            # if release_date != None:
            #     release_date = release_date.text.split()[2]
            # else:
            #     release_date = 'N/A'
            # print(f"{recent_tag_title}, {category}")
            # print(href_rec)
            # recent_dict["recent_tag_title"] = recent_tag_title
            # recent_dict["release_date"] = release_date
            # recent_dict["rating_tag"] = rating_tag
            # recent_dict["href_rec"] = href_rec
            # recent_dict["category"] = category
            #recently_rated_detail.append(recent_details_dict)
        recent_added_film_df = pd.DataFrame(recently_rated_detail)
        json_data_recent = recent_added_film_df.to_json(orient='records',date_format=None)
        json_data_recent.replace("\\/","-")
        print(json_data_recent)
        return recent_added_film_df
    else:
        return f'Recent added page not found with response status: {response_rr.status_code}'  

def scrape_film(movie_href):
    
    response = requests.get(f"https://www.bbfc.co.uk{movie_href}")
    
    if response.status_code == 200:
        movie_details = {}
        movie_html_content = response.content
        movie_soup = BeautifulSoup(movie_html_content, 'html.parser')

        '''Extracting film title'''
        title_h2 = movie_soup.find('h2', class_ = "MediaOutline_Title__3UY5z")
        span = title_h2.find('span')
        movie_details["title"]= span.text

        '''Extracting film rating'''
        rating_span = movie_soup.find('span', class_= "Icon_Icon__9RCS8 MediaOutline_Icon__3mXHF")
        movie_rating = rating_span['aria-label'].split()[1]
        movie_details["rating"] = movie_rating

        '''Extracting media type'''
        media_type_div = movie_soup.find('div', class_ ="MediaOutline_MediaType__AipEd")
        media_type = media_type_div.text
        movie_details["media_type"] = media_type

        '''Extracting key details'''
        keyList_ul = movie_soup.find('ul', class_ ="KeyDetails_List__1oCpD")
        key_li_list = keyList_ul.find_all('li', class_ ="ListItem_ListItem__klTTg")
        key_details = {}
        for li in key_li_list:
            h4_list = li.find_all('h4', class_ ="Type_base__2EnB2")
            if h4_list[0].text == 'Release date':
                release_date = datetime.datetime.strptime(h4_list[1].text, '%d/%m/%Y').date()
                key_details[h4_list[0].text] = str(release_date)
            else:
                key_details[h4_list[0].text] = h4_list[1].text
        movie_details["key_details"] = key_details 

        '''Extracting content advice data'''
        content_details = movie_soup.find('div', class_ ="VisualAdvice_VisualAdvice__icKUz")
        if content_details != None:
            grid_items = content_details.find_all('div', class_ = "GridItem_GridItem__Wegeu")
            content_advice = []
            for grid_item in grid_items:
                advice_details = {}
                content_title = grid_item.find('p',class_= "Type_base__2EnB2").text
                max_rating_count = len(grid_item.find_all('span'))
                current_rating_count = max_rating_count - len(grid_item.find_all('span', class_ ="VisualAdviceRating_unfilled__1D3DY"))
                advice_details["content_title"] = content_title
                advice_details["content_rating"] = current_rating_count
                advice_details["max_rating"] = max_rating_count
                content_advice.append(advice_details)
            movie_details["content_advice"] = content_advice
        else:
            print(f"content details are not available for {movie_details["title"]}")

        '''returning movie details dictionary with all the details'''
        return movie_details
    else:
        #movie_details["response_code"] = response.status_code
        return f'Movie not found with response status: {response.status_code}'  
    
def scrape_spreadsheet():
    response_spr = requests.get("https://docs.google.com/spreadsheets/d/1gdNU75_RPG69bsuAFQpZu670sHK9EzTwZWSLUERhMZ4/edit#gid=0")
    response_scr_cont = response_spr.content
    content_html_spr = BeautifulSoup(response_scr_cont, 'html.parser')
    xl_div = content_html_spr.find('div',id = '0-grid-table-container')
    tbody = xl_div.find('tbody')
    tr_spr_list = tbody.find_all('tr')
    title_list = []
    for tr_spr in tr_spr_list: 
        td = tr_spr.find('td')
        if td.text != '' and td.text != 'Title':
            title_list.append(td.text)
    return title_list   

''''''
def scrape_query_result():
    title_list = scrape_spreadsheet()
    title_details_list = []
    for title in title_list:
        url_title =f"https://www.bbfc.co.uk/search?q={title}"
        response_title = requests.get(url_title)
        if response_title.status_code == 200: 
            query_soup = BeautifulSoup(response_title.content, 'html.parser')
            result_div = query_soup.find('div', class_ ="GridItem_GridItem__Wegeu GridItem_m-100__32Nyd GridItem_t-100__Pq2Bq GridItem_tl-67__1OyMa")
            not_found = result_div.find('p',class_='BBFCSearchLayout_Title__1GdfR')
            if not_found == None:
                first_title = result_div.find('div', class_ ="SearchItem_SearchItem__3kbZF")
                anchor_tag_title = first_title.find('a')
                href_title = anchor_tag_title.get('href')
                title_details_dict = scrape_film(href_title)
                if type(title_details_dict) == dict:
                    title_details_list.append(title_details_dict)
                else:
                    print(title_details_dict)    
            else:
                print(f"No results found for movie {title}")
        else:
            print(f"Query page returned with status code : {response_title.status_code} for {title}")
    title_details_df = pd.DataFrame(title_details_list)
    pd.set_option('display.max_columns', None)
    print(title_details_df.head())
    #print(title_details_df.loc[title_details_df['title'] == 'Naked Lunch'])
    json_data = title_details_df.to_json(orient='records')
    print(json_data)
    return title_details_df


if __name__ == "__main__":
    #print(scrape_film("/release/1976-q29sbgvjdglvbjpwwc0xmdexnje0"))
    recent_page_film_scrape()
    #scrape_spreadsheet()
    #scrape_query_result()