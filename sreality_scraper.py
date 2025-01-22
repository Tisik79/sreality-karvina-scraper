import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime

class SrealityScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def get_listing_urls(self):
        base_url = "https://www.sreality.cz/hledani/prodej/byty/karvina"
        page = 1
        all_links = []
        
        while True:
            params = {
                'velikost': '2+1',
                'strana': str(page)
            }
            
            print(f"\nStahuji stránku {page}...")
            response = requests.get(base_url, params=params, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = [
                link.get('href') for link in soup.find_all('a')
                if link.get('href') and 'detail/prodej/byt/2+1/karvina' in link.get('href')
            ]
            
            if not links:
                break
                
            all_links.extend(links)
            print(f"Nalezeno {len(links)} inzerátů na stránce {page}")
            
            next_page = False
            for link in soup.find_all('a'):
                if link.get('href') and f'strana={page+1}' in link.get('href'):
                    next_page = True
                    break
            
            if not next_page:
                break
                
            page += 1
            time.sleep(1)
        
        print(f"\nCelkem nalezeno {len(all_links)} inzerátů")
        return all_links

    def get_listing_details(self, url):
        try:
            full_url = f"https://www.sreality.cz{url}"
            print(f"Stahuji detail: {full_url}")
            
            response = requests.get(full_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            details = {}
            
            for dt in soup.find_all('dt', class_='MuiTypography-root'):
                label = dt.text.strip(':').lower()
                dd = dt.find_next('dd')
                if dd:
                    value = dd.text.strip()
                    details[label] = value
            
            # Extrakce ceny
            price = None
            if 'celková cena' in details:
                price = ''.join(filter(str.isdigit, details['celková cena']))

            # Extrakce plochy
            area = None
            if 'plocha' in details:
                area_match = re.search(r'(\d+)', details['plocha'])
                if area_match:
                    area = area_match.group(1)

            # Patro
            floor = None
            if 'stavba' in details:
                floor_match = re.search(r'(\d+)\. podlaží z (\d+)', details['stavba'])
                if floor_match:
                    floor = f"{floor_match.group(1)}/{floor_match.group(2)}"

            ownership = details.get('vlastnictví', 'Neuvedeno')

            condition = None
            if 'stavba' in details:
                condition_match = re.search(r'Ve? \w+(\s\w+)* stavu', details['stavba'])
                if condition_match:
                    condition = condition_match.group(0)

            balcony = "Ne"
            if 'příslušenství' in details:
                if any(word in details['příslušenství'].lower() for word in ['balkón', 'balkon', 'lodžie']):
                    balcony = "Ano"

            address = url.split('/')[-2].replace('-', ' ').title()
            
            if price and area:
                return {
                    'URL': full_url,
                    'Lokalita': address,
                    'Cena (Kč)': int(price),
                    'Plocha (m²)': int(area),
                    'Cena za m²': int(int(price)/int(area)),
                    'Patro': floor,
                    'Vlastnictví': ownership,
                    'Stav': condition,
                    'Balkón': balcony
                }
            
        except Exception as e:
            print(f"Chyba při zpracování inzerátu {full_url}: {e}")
            return None

    def save_to_excel(self, data, filename='byty_karvina.xlsx'):
        df = pd.DataFrame(data)
        df = df.sort_values('Cena (Kč)')

        # Přidání sloupce s ID
        df.reset_index(inplace=True)
        df.index += 1  # Začínáme od 1 místo od 0
        df.index.name = 'ID'

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Uložení dat do Excelu včetně indexu
            df.to_excel(writer, sheet_name='Byty 2+1 Karviná')
            
            # Získání pracovního sešitu a listu
            workbook = writer.book
            worksheet = writer.sheets['Byty 2+1 Karviná']
            
            # Formátování měnových sloupců (posunuto o jeden sloupec kvůli ID)
            for col_name in ['Cena (Kč)', 'Cena za m²']:
                col_idx = df.columns.get_loc(col_name) + 1  # +1 kvůli ID sloupci
                col_letter = chr(65 + col_idx)
                
                # Nastavení formátu pro všechny řádky v daném sloupci (kromě hlavičky)
                for row in range(2, len(df) + 2):
                    cell = worksheet[f'{col_letter}{row}']
                    cell.number_format = '#,##0 Kč'
            
            # Automatická šířka sloupců
            for column in worksheet.columns:
                max_length = 0
                column = list(column)
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width

        print(f"\nData byla uložena do souboru {filename}")
        
        # Výpis statistik
        print("\nStatistiky:")
        print(f"Počet nalezených bytů: {len(df)}")
        print(f"Průměrná cena: {df['Cena (Kč)'].mean():,.0f} Kč")
        print(f"Průměrná plocha: {df['Plocha (m²)'].mean():.1f} m²")
        print(f"Průměrná cena za m²: {df['Cena za m²'].mean():,.0f} Kč")
        print("\nRozdělení podle vlastnictví:")
        print(df['Vlastnictví'].value_counts())
        print("\nRozdělení podle stavu:")
        print(df['Stav'].value_counts())
        
        return df

def main():
    scraper = SrealityScraper()
    urls = scraper.get_listing_urls()
    
    listings_data = []
    for url in urls:
        details = scraper.get_listing_details(url)
        if details:
            listings_data.append(details)
        time.sleep(1)
    
    if listings_data:
        df = scraper.save_to_excel(listings_data, f'byty_karvina_{datetime.now().strftime("%Y%m%d")}.xlsx')
        print("\nPříklad dat:")
        print(df[['Lokalita', 'Cena (Kč)', 'Plocha (m²)', 'Vlastnictví', 'Stav', 'Balkón']].head())
    else:
        print("Nebyla nalezena žádná data")

if __name__ == "__main__":
    main()