# -*- coding: utf-8 -*-
import os
import re
import sys
import time

from bs4 import BeautifulSoup
from django.db.models import Q
from selenium.common.exceptions import InvalidArgumentException
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common.by import By

from catfood.data import result

sys.path.append('/home/ubuntu/django_catfood')
os.environ.setdefault("PYTHONUNBUFFERED;", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_catfood.settings")
import django

if 'setup' in dir(django):
    django.setup()

from catfood.models import Brand, ListSelector, Formula


def get_brand_list():
    with webdriver.WebDriver() as driver:
        for selector in ListSelector.objects.filter(product_path=""):
            driver.get(selector.base_url)
            data = input(f"{selector.title} 의 상품 리스트 패턴을 입력하세요.\n")
            if data:
                selector.product_path = data.strip()
            selector.save()


def regex_url(url_regex, target_url):
    if not target_url or type(target_url) is not str:
        return None
    pat = "^" + url_regex.replace("**", "[a-zA-Z0-9#?=]+") + "$"
    regex = re.compile(pat)
    if regex.match(target_url):
        return regex.match(target_url).group(0)


def find_all_urls(w_driver: webdriver.WebDriver, url_string: str):
    try:
        w_driver.get(url_string)
    except InvalidArgumentException as e:
        print(e.msg)
    w_driver.find_elements(By.CSS_SELECTOR, "a")
    soup = BeautifulSoup(w_driver.page_source, "html.parser")
    return [link.get("href") for link in soup.find_all("a")]


def search_urls_by_patterns():
    with webdriver.WebDriver() as driver:
        for brand in ListSelector.objects.all():
            pattern = brand.product_path
            all_urls = find_all_urls(driver, brand.base_url)
            print(all_urls)
            for url in all_urls:
                if url and regex_url(pattern, url):
                    Formula.objects.get_or_create(
                        brand=Brand.objects.get(english_name=brand.title),
                        product_url=url
                    )


def collect_urls_by_patterns():
    with webdriver.WebDriver() as driver:
        for brand, formulas in result.items():
            try:
                target = Brand.objects.get(english_name=brand)
            except Brand.DoesNotExist:
                print(f"{brand} 브랜드가 없습니다.")
                continue
            try:
                selector = ListSelector.objects.get(brand=target)
            except ListSelector.DoesNotExist:
                print(f"{brand} 브랜드 패턴이 없습니다.")
                for formula in formulas:
                    Formula.objects.get_or_create(
                        brand=target,
                        product_url=formula
                    )
                continue
            for formula in formulas:
                try:
                    if regex_url(selector.product_path, formula):
                        formula = formula.split("#")[0]
                        Formula.objects.get_or_create(
                            brand=target,
                            product_url=formula
                        )
                    all_urls = find_all_urls(driver, formula)
                    for url in all_urls:
                        if url and regex_url(selector.product_path, url):
                            url = url.split("#")[0]
                            formulas.append(url) if url not in formulas else None
                            print(url)
                            Formula.objects.get_or_create(
                                brand=target,
                                product_url=url
                            )
                except Exception as e:
                    print(e)
                    continue


def search_crawler():
    for brand in ListSelector.objects.all().order_by("id"):
        driver = webdriver.WebDriver()
        driver.implicitly_wait(10)
        pattern = brand.product_path
        base_urls = [brand.base_url]
        for b_url in base_urls:
            driver.get(b_url)
            time.sleep(3)
            try:
                driver.find_elements(By.CSS_SELECTOR, "a")
                soup = BeautifulSoup(driver.page_source, "html.parser")
                all_urls = [link.get("href") for link in soup.find_all("a")]
                for url in all_urls:
                    if regex_url(pattern, url):
                        url = url.split("#")[0]
                        base_urls.append(url) if url not in base_urls else None
                        print(url)
                        Formula.objects.get_or_create(
                            brand=Brand.objects.get(english_name=brand.title),
                            product_url=url
                        )
            except Exception as e:
                print(e)
        driver.quit()


def set_base_url_for_crawler():
    with webdriver.WebDriver() as driver:
        driver.maximize_window()
        for selector in ListSelector.objects.filter(base_url=""):
            print(selector.product_path)
            driver.get(selector.product_path.replace("**", ""))
            x = input(f"{selector.title} ")
            selector.base_url = driver.current_url
            selector.save()


def set_title_for_formulas():
    with webdriver.WebDriver() as driver:
        driver.maximize_window()
        driver.implicitly_wait(10)
        for formula in Formula.objects.filter(title="").order_by("brand_id"):
            try:
                driver.get(url=formula.product_url)
                title: str = driver.find_element(By.CSS_SELECTOR, "h1").text.replace("\\n", " ")
                title_str = f'{title.replace("&nbsp", " ").strip()} | {formula.brand.english_name}'
                if "403 Forbidden" in title:
                    raise Exception("403 Forbidden")
                elif "410 Gone" in title:
                    raise Exception("410 Gone")
                elif "찾을 수 없음" in title or "not found" in title or "404" in title:
                    raise Exception("No Product")
                elif Formula.objects.filter(title=title).exists():
                    raise Exception("Already Exist")
                formula.title = title_str
                print(formula.title)
                formula.save()
            except Exception as e:
                if e.__class__.__name__ == "Exception":
                    print(f"[ERROR] {e}", formula.product_url)
                else:
                    print(f"[ERROR] {e.__class__.__name__}", formula.product_url)


def set_selector_for_formula():
    with webdriver.WebDriver() as driver:
        driver.implicitly_wait(10)
        for brand in ListSelector.objects.filter(ingredients_selector=""):
            driver.get(brand.base_url)
            ingredient = input(f"{brand.title} ingredients path.").strip()
            brand.ingredients_selector = ingredient
            brand.save()


def set_ingredients_for_all():
    pass_list = []
    with webdriver.WebDriver() as driver:
        driver.implicitly_wait(10)
        driver.maximize_window()
        for formula in Formula.objects.filter(Q(ingredients=None) | Q(ingredients="")).order_by("brand"):
            try:
                if formula.brand in pass_list:
                    continue
                driver.get(formula.product_url)
                selector = ListSelector.objects.get(brand=formula.brand)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                new_ingredients_selector = input(f"{formula.brand} selector:").strip()
                if new_ingredients_selector == "delete":
                    formula.delete()
                    continue
                elif new_ingredients_selector == "pass":
                    pass_list.append(formula.brand)
                    continue
                elif new_ingredients_selector.startswith("/"):
                    formula.ingredients = new_ingredients_selector[1:]
                    formula.save()
                    continue
                elif new_ingredients_selector:
                    selector.ingredients_selector = new_ingredients_selector
                    selector.save()
                ingredients = soup.select(selector.ingredients_selector)
                ingredients = [ingredient.text.strip() for ingredient in ingredients]
                ingredient = ", ".join(ingredients)
                ingredient = re.sub(r"\s+", " ", ingredient.strip())
                ingredient = re.sub("(composition|ingredients?):? ?", "", ingredient, flags=re.IGNORECASE)
                ingredient = re.sub(r"(\d),(\d{,2})", r"\1.\2", ingredient)
                formula.ingredients = ingredient
                print(formula.ingredients)
                formula.save()
            except Exception as e:
                print(f"[ERROR] {e}", formula.product_url)


def set_analysis_for_all():
    done_list = []
    pass_list = []
    with webdriver.WebDriver() as driver:
        driver.implicitly_wait(10)
        driver.maximize_window()
        for formula in Formula.objects.filter(Q(analysis=None) | Q(analysis="")).order_by("brand_id"):
            try:
                if formula.brand in pass_list:
                    formula.analysis = "No Data"
                    formula.save()
                    continue
                driver.get(formula.product_url)
                selector = ListSelector.objects.get(brand=formula.brand)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                if formula.brand not in done_list:
                    new_analysis_selector = input(f"{formula.brand} analysis path. ").strip()
                    if new_analysis_selector:
                        if new_analysis_selector == "pass":
                            pass_list.append(formula.brand)
                            formula.analysis = "No Data"
                            formula.save()
                            continue
                        elif new_analysis_selector == "delete":
                            formula.delete()
                            continue
                        elif new_analysis_selector.startswith("/"):
                            analysis = new_analysis_selector[1:]
                            analysis = re.sub(r"\s+", " ", analysis.strip())
                            analysis = re.sub(r"\.+ +", ".", analysis.strip())
                            analysis = re.sub(r"\.{2,}", ".", analysis.strip())
                            analysis = re.sub(r"(\d),(\d{,2})", r"\1.\2", analysis)
                            analysis = re.sub("(analytical|additives?|constituents|guaranteed|analysis|nutrition)+:? ?",
                                              "", analysis, flags=re.IGNORECASE)
                            formula.analysis = analysis
                            formula.save()
                            continue
                        else:
                            selector.analysis_selector = new_analysis_selector
                            selector.save()
                        done_list.append(formula.brand)

                analysis = soup.select(selector.analysis_selector)
                analysis = [ana.text.strip() for ana in analysis]
                analysis = ", ".join(analysis)
                analysis = re.sub(r"\s+", " ", analysis.strip())
                analysis = re.sub(r"\.{2,}", ".", analysis.strip())
                analysis = re.sub("(analytical|additives?|constituents|guaranteed|analysis|nutrition):? ?", "",
                                  analysis,
                                  flags=re.IGNORECASE)
                analysis = re.sub(r"(\d),(\d{,2})", r"\1.\2", analysis)
                formula.analysis = analysis if analysis else None
                if not analysis:
                    done_list.remove(formula.brand)
                else:
                    print(formula.analysis)
                    formula.save()
            except Exception as e:
                print(f"[ERROR] {e}", formula.product_url)
    print(pass_list)


def show_ingredients():
    ingredients_list = {}
    for formula in Formula.objects.all():
        ingredients = formula.ingredients
        for ingredient in ingredients.split(", "):
            ingredient = ingredient.strip()
            ingredient = ingredient.capitalize()
            ingredient = ingredient.replace(")", "").replace("(", "").replace(".", "")
            if ingredient not in ingredients_list.keys():
                ingredients_list[ingredient] = 1
            else:
                ingredients_list[ingredient] += 1
    print(sorted(sorted(ingredients_list, key=lambda x: ingredients_list[x], reverse=True)[:500]))


def set_analysis():
    for formula in Formula.objects.all():
        analysis = formula.analysis.replace(", Cans Daily 1/2 To 3/43/4 To 1-1/21-1/2 To 2", "")
        analysis = re.sub(r"% (\d+\.?\d*)", r"\1 %", analysis)
        analysis = re.sub(r"(\(min\)|\(min\.\)|\(max\)|\(max\.\))", r"", analysis, flags=re.IGNORECASE)
        analysis = re.sub(r",?(Min |Max |Minimum |Maximum )", r"", analysis)
        analysis = re.sub(r"(, Not More Than|, Not Less Than|Minimum |Maximum )", r"", analysis, flags=re.IGNORECASE)
        analysis = re.sub(r"( Not More Than| Not Less Than|Minimum|Maximum)", r"", analysis, flags=re.IGNORECASE)
        analysis = re.sub(r" : ", r" ", analysis)
        analysis = re.sub(r"(\d+\.?\d*) \d+\.?\d* % %", r"\1 %", analysis)
        analysis = re.sub(r"(\d+\.?\d?) % ?--", r"\1 %", analysis)
        analysis = re.sub(r"(\w+)(mg/kg|iu/kg)", r"\1 \2", analysis)
        analysis = re.sub(r"([2-9])\.(\d{3})", r"\1,\2", analysis)
        analysis = re.sub(r"(\d{2})\.(0{3})", r"\1,\2", analysis)
        analysis = re.sub(r"(0{3})\.(\d{3})", r"\1,\2", analysis)
        analysis = analysis.replace("Iu", "IU").replace("Kg", "kg").replace("Mg", "mg")
        # print(re.findall(r"(\d+\.?,?\d* Kcal/kg)", analysis))
        # print([a.strip() for a in analysis.split(", ") if a.strip()])
        formula.analysis = analysis
        formula.save()
        print(analysis)


def set_analysis1():
    analysis_list = []
    exclude_list1 = [
        '®', '¼', '¼-', '¼:', '½', '½:', '¾', '—', '†', '•', '⅓',
        '⅓:', '⅔', '⅔:', '⅜', '⅜:', '⅝', '⅝+', '⅝:' ';', '<5', '=',
    ]
    for formula in Formula.objects.all():
        analysis = formula.analysis
        analysis = re.sub(r"[A-Z][0-9]{3,}", "", analysis)
        analysis = re.sub(r"\*+", "", analysis)
        analysis = re.sub(r"(\.,|,,)", ",", analysis)
        analysis = re.sub(r"[-—+]+", " ", analysis)
        analysis = re.compile("|".join(exclude_list1)).sub("", analysis)
        analysis = re.sub(r"\s+", " ", analysis)
        analysis = re.sub(r" , ", ", ", analysis)
        analysis = analysis\
            .replace("Ω", "Omega")\
            .replace("iu/kg", "IU/kg")\
            .replace("Zink", "Zinc")\
            .replace("Me/", "ME/")\
            .replace("Max.", "").strip()

        # formula.analysis = analysis
        # formula.save()
        for word in analysis.split():
            while word.startswith("(") or word.startswith("["):
                word = word[1:]
            while word.endswith(",") or word.endswith(":") or word.endswith(".") or word.endswith(")") or word.endswith(";"):
                word = word[:-1]
            if word.strip() not in analysis_list:
                analysis_list.append(word.strip())
    print(sorted(analysis_list), len(analysis_list))


def set_calorie():
    def save_calorie(product: Formula, calorie=None):
        if not calorie:
            product.calorie = "No data"
            return product.save()
        calorie = re.sub(r"\s+", " ", calorie.strip())
        calorie = re.sub(r"(\d)[,.]+(\d{3})", r"\1\2", calorie)
        calorie = re.sub(r"(\d{2,}),(\d{1,2})", r"\1.\2", calorie)
        calorie = re.sub(r"ME Cal/Tub ([0-9.]+)", r"\1 kcal/tub", calorie)
        calorie = re.sub(r"ME Cal/can ([0-9.]+)", r"\1 kcal/can", calorie)
        calorie = re.sub(r"ME\(Calculated\) (\d+)", r"\1 kcal/kg", calorie)
        calorie = re.sub(r"kcal/(\d+)g can", r"kcal/can(\1)", calorie)
        calorie = re.sub(r"(\d+) Cal/100g", r"\1 kcal/100g", calorie)
        calorie = re.sub(r"Metabolic energy \(Kcal/100g\): (\d+)", r"\1 kcal/100g", calorie)
        calorie = re.sub(r"Metabolisable Energy (\d+) Kcal / 100 g", r"\1 kcal/100g", calorie)
        calorie = re.sub(r"Kcal/kg", r"kcal/kg", calorie)
        product.calorie = calorie\
            .replace(" per ", "/")\
            .replace(" Per ", "/")\
            .replace(" / ", "/")\
            .replace("100 g", "100g")\
            .replace("Kc", "kc")\
            .replace("als", "al")\
            .replace("G", "g")\
            .replace("alories", "al")\
            .replace("ilogram", "g")\
            .replace(" ME", "")\
            .replace(" Energy", "")\
            .replace(" Metabolisable", "")\
            .replace(" me", "")
        return product.save()

    options = webdriver.Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    with webdriver.WebDriver(options=options) as driver:
        driver.maximize_window()
        for formula in Formula.objects.filter(calorie="").order_by("brand_id"):
            if formula.calorie:
                continue
            driver.get(formula.product_url)
            new_calorie = input(f"{formula.title} calorie: ").strip()
            if new_calorie == "delete":
                formula.delete()
            elif new_calorie == "rename":
                new_name = input(f"{formula.title} new name: ").strip()
                formula.title = new_name
                formula.save()
            elif new_calorie == "pass":
                save_calorie(formula)
                Formula.objects.filter(brand=formula.brand, calorie=None).update(calorie="No Data")
            elif new_calorie:
                save_calorie(formula, new_calorie)
                formula.save()
            else:
                save_calorie(formula)


def set_metabolizable_energy():
    for formula in Formula.objects.exclude(calorie="No Data").filter(energy=None).order_by("brand_id"):
        calorie = formula.calorie.replace('KCAL/Kg', 'kcal/kg').replace('kcal/Kg', 'kcal/kg')
        num1, cal, num2, kg = re.compile(r"([0-9.]+) (kcal|MJ)/([0-9.]*)(k?g|oz|can|cup|tub|lb)").search(calorie).groups()
        num1 = float(num1)
        if cal == "MJ":
            num1 *= 238.85
            cal = "kcal"
        num2 = float(num2) if num2.isdigit() else 1.0
        if kg == "kg":
            num2 *= 1
        else:
            if kg == "oz":
                num2 *= 0.0283495
            elif kg == "can":
                num2 *= 0.250
            elif kg == "cup":
                num2 *= 0.250
            elif kg == "tub":
                num2 *= 0.080
            elif kg == "lb":
                num2 *= 0.453592
            elif kg == "g":
                num2 *= 0.001
            kg = "kg"
        formula.calorie = calorie
        formula.energy = round(num1 / num2, 2)
        formula.save()


def extract_protein():
    protein_reg = [
        r"(?:crude |Crude |Roh)?P?p?rote?ie?ns?:?,? (?:Min.)?([0-9.]+) %",
        r"조?단백질? ([0-9.]+) %?",
        r"Protein,? (?:G \(crude\)|Crude) [0-9.]+ ([0-9.]+)",
        r"Proteina Bruta ([0-9.]+) %",
        r"Crude Protein \(not Less Than\) ([0-9.]+) %",
        r"Crude Protein \(([0-9.]+) \%\)",
        r"Crude Protein [0-9.]+ ([0-9.]+) % [0-9.]+ %"
    ]
    for formula in Formula.objects.exclude(analysis="No Data").filter(protein=None):
        formula.analysis = formula.analysis\
            .replace("’", ".")\
            .replace(";", "")\
            .replace("Á", "A")\
            .replace("ä", "a")\
            .replace("é", "e")\
            .replace("í", "i")\
            .replace("ï", "i")\
            .replace("í", "i")\
            .replace("ó", "o")\
            .replace("Ω", "omega")\
            .replace("<5 <5", "5")\
            .replace("0^5", "00000")
        protein = re.search("|".join(protein_reg), formula.analysis)
        if protein:
            formula.protein = [x for x in protein.groups() if x][0]
        formula.save()


def extract_fat():
    regex = [
        r"(조?지방 ([0-9.]+)",
        r"Fat Content:? ([0-9.]+) \%",
        r"Fats?:? ([0-9.]+) \%",
        r"Crude Fat Min\.([0-9.]+) \%",
        r"Crude Fats? And Oils? ([0-9.]+) \%",
        r"Crude Fats? & Oils? ([0-9.]+) \%",
        r"Crude Oils? And Fats? ([0-9.]+) \%",
        r"Crude Oils? & Fats? ([0-9.]+) \%",
        r"Fettgehalt:? ([0-9.]+) %",
        r"Fats \(([0-9.]+) \%\)",
        r"Grasa Bruta:? ([0-9.]+) \%",
        r"Crude Fat\, ([0-9.]+) \%",
        r"Crude Fat\, Min\.([0-9.]+) \%",
        r"Fat G \(crude\) [0-9.]+ ([0-9.]+)",
        r"Fat\, Crude ([0-9.]+) [0-9.]+ \% G",
        r"Aceites Y Grasas Brutos ([0-9.]+) \%",
        r"Crude Fat \(not Less Than\) ([0-9.]+) \%)"
    ]
    for formula in Formula.objects.exclude(analysis="No Data").filter(fat=None).order_by("brand_id"):
        fat = re.search("|".join(regex), formula.analysis)
        fat = re.findall(r"[0-9]+[0-9.]*", fat.group(1)) if fat else None
        if fat:
            formula.fat = float(fat[0])
            formula.save()


def extract_fiber():
    regexes = [
        r"Crude Fiber \(not More Than\) ([0-9\.]+) \%",
        r"(?:Crude)? Fibres?,?:? ([0-9\.]+) ?\%",
        r"(?:Crude)? Fibers?,?:? ([0-9\.]+) ?\%",
        r"Crude Fibre\, Max\.([0-9\.]+) \%",
        r"Crude Fibre \% ([0-9\.]+)",
        r"Fiber ([0-9\.]+) [0-9\.]+ \%",
        r"Fiber G \(crude\) [0-9\.]+ ([0-9\.]+)",
        r"Crude Fiber [0-9.]+ ([0-9\.]+) \%",
        r"Crude Fiber\,? Max\.([0-9\.]+) \%",
        r"Crude Fibers? \(([0-9\.]+) \%\)",
        r"Crude Cellulose ([0-9\.]+) \%",
        r"Crude Ber ([0-9\.]+) \%",
        r"Rohfaser\:? ([0-9\.]+) \%",
        r"Fibras? Brutas?\:? ([0-9\.]+) \%",
        r"조?섬유 ([0-9\.]+) ?\%?",
    ]
    for formula in Formula.objects.exclude(analysis="No Data").filter(fiber=None):
        fiber = re.findall("|".join(regexes), formula.analysis)
        fiber = fiber[0] if fiber else None
        fiber = [x for x in fiber if x] if fiber else None
        formula.fiber = float(fiber[0]) if fiber else None
        formula.save()


def extract_ash():
    regexes = [
        r"(?:Crude )?Ash,? ([0-9\.]+) ?\%",
        r"Minerals\/crude Ash ([0-9\.]+) \%",
        r"Rohasche ([0-9\.]+) \%",
        r"Crude Ash\: ([0-9\.]+) \%",
        r"Ash Max\.([0-9\.]+) \%",
        r"조?회분 ([0-9\.]+)",
        r"Ash\, Max\.([0-9\.]+) \%",
        r"Crude Ash \(([0-9\.]+) \%\)",
        r"Crude Ash \% ([0-9\.]+)",
        r"Ash ([0-9\.]+) [0-9\.]+ \% G",
        r"ash ([0-9\.]+) \%",
        r"Ceniza Bruta ([0-9\.]+) \%",
    ]
    for formula in Formula.objects.exclude(analysis="No Data").filter(ash=None):
        ash = re.findall("|".join(regexes), formula.analysis)
        if ash:
            formula.ash = float([a for a in ash[0] if a][0])
            formula.save()


def extract_moisture():
    regexes = [
        r"Moisture ([0-9\.]+) ?\%",
        r"Feuchtigkeit ([0-9\.]+) \%",
        r"Moisture\,?\:? ([0-9\.]+) \%",
        r"수분 ([0-9\.]+) \% 이하",
        r"Moisture Max\.([0-9\.]+) \%",
        r"Moisture\, Max\.([0-9\.]+) \%",
        r"Moisture ([0-9\.]+)",
        r"Water ?G? ([0-9\.]+)",
        r"Moisture \(([0-9\.]+) \%\)",
    ]
    for formula in Formula.objects.exclude(analysis="No Data").filter(moisture=None):
        moist = re.findall("|".join(regexes), formula.analysis)
        if moist:
            formula.moisture = float([a for a in moist[0] if a][0])
            formula.save()


def extract_carb():
    regexes = [
        r"Carbohydrates?:? ([0-9\.]+)",
        r"NFE ([0-9\.]+) \%",
        r"Carbohydrate G \(nfe\) [0-9\.]+ ([0-9\.]+)",
        r"Carbs ([0-9\.]+)",
        r"Carbohydrates \(calc\.\) ([0-9\.]+) \%",
        r"Carbohydrates \(([0-9\.]+) \%\)",
    ]
    for formula in Formula.objects.exclude(analysis="No Data").filter(carbohydrate=None):
        carbohydrate = re.findall("|".join(regexes), formula.analysis)
        if carbohydrate:
            formula.carbohydrate = float([a for a in carbohydrate[0] if a][0])
            formula.save()
    for formula in Formula.objects.exclude(analysis="No Data").filter(
        carbohydrate=None,
        fat__isnull=False,
        protein__isnull=False,
        moisture__isnull=False,
        ash__isnull=False,
        fiber__isnull=False,
    ):
        carbo = (100 - formula.fat - formula.protein - formula.moisture - formula.ash - formula.fiber)
        formula.carbohydrate = round(carbo, 2) if carbo > 0 else 0
        print(formula.carbohydrate)
        formula.save()


def extract_calcium():
    regexes = [
        r"Calcium:?,? ([0-9\.]+) ?\%?",
        r"Calcium \(ca\) ([0-9\.]+) \%",
        r"Calcium\, Min\.([0-9\.]+) \%",
        r"Calcium\, ([0-9\.]+) \%",
        r"Calcio ([0-9\.]+) \%",
        r"Calcium G [0-9\.]+ ?([0-9\.]+)",
        r"Calcium \d\.\d\d(\d\.\d\d)",
        r"Calcium \(not Less Than\) ([0-9\.]+) \%",
        r"Calcium \(mg\/kg\) ([0-9\.]+)",
        r"Calcium \(([0-9\.]+) \%\)",
        r"Calcium Min\.([0-9\.]+) \%",
    ]
    for formula in Formula.objects.exclude(analysis="No Data").filter(calcium=None):
        calcium = re.findall("|".join(regexes), formula.analysis)
        if calcium:
            formula.calcium = float([a for a in calcium[0] if a][0])
            formula.save()
    regexes = [
        r"Phosphoro?us:?,? ([0-9\.]+) ?\%?",
        r"Phosphorus \(ca\) ([0-9\.]+) \%",
        r"Phosphorus\, Min\.([0-9\.]+) \%",
        r"Phosphorus\, ([0-9\.]+) \%",
        r"Phosphor ([0-9\.]+) \%",
        r"Phosphorus G [0-9\.]+ ?([0-9\.]+)",
        r"Phosphorus \(not Less Than\) ([0-9\.]+) \%",
        r"Phosphorus \(mg\/kg\) ([0-9\.]+)",
        r"Phosphorus \(([0-9\.]+) \%\)",
        r"Phosphorus Min\.([0-9\.]+) \%",
    ]
    for formula in Formula.objects.exclude(analysis="No Data").filter(phosphorus=None):
        phosphorus = re.findall("|".join(regexes), formula.analysis)
        if phosphorus:
            formula.phosphorus = float([a for a in phosphorus[0] if a][0])
            formula.save()


if __name__ == '__main__':
    extract_calcium()
