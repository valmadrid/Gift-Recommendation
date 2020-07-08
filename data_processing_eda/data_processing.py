import re
import json
import numpy as np

def extract_info(filename, folder_path):

    tag_remover = re.compile(
        "<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});|\r|\n|&#x?[^;]{2,4}")
    logo_remover = re.compile('\?.*')

    with open(folder_path + filename) as json_file:
        data = json.load(json_file)

    details_dict = {}

    details_dict["product_id"] = data["productId"]
    details_dict["name"] = tag_remover.sub(" ", data["displayName"])
    details_dict["brand_id"] = data["brand"]["brandId"]

    details_dict["brand_name"] = tag_remover.sub(" ",
                                                 data["brand"]["displayName"])

    short_desc = data[
        "quickLookDescription"] if "quickLookDescription" in data else data[
            "shortDescription"]

    details_dict["short_desc"] = tag_remover.sub(" ", short_desc).strip()

    details_dict["long_desc"] = tag_remover.sub(
        " ", data["longDescription"]
    ).strip() if "longDescription" in data else tag_remover.sub(
        " ", short_desc).strip()

    details_dict["sku"] = data["currentSku"]["skuId"]
    details_dict["sku_name"] = tag_remover.sub(
        " ", data["currentSku"]
        ["skuName"]) if "skuName" in data["currentSku"] else (
            data["currentSku"]["displayName"]).replace(
                data["currentSku"]["skuId"], "").strip()

    details_dict["list_price"] = float(
        data["currentSku"]["listPrice"].strip("$"))

    details_dict["variation"] = data["currentSku"]["variationTypeDisplayName"]

    if "regularChildSkus" in data:
        variants = []
        prices = []
        for i, sku in enumerate(data["regularChildSkus"]):
            variants.append({
                i + 1: {
                    "item":
                    sku["skuId"],
                    "item_name":
                    sku["skuName"]
                    if "skuName" in data["regularChildSkus"][i] else np.nan,
                    "list_price":
                    float(sku["listPrice"].strip("$"))
                }
            })
            prices.append(float(sku["listPrice"].strip("$")))

    details_dict[
        "variants"] = variants if "regularChildSkus" in data else np.nan
    details_dict["price_low"] = min(
        prices) if "regularChildSkus" in data else details_dict["list_price"]
    details_dict["price_high"] = max(
        prices) if "regularChildSkus" in data else details_dict["list_price"]

    details_dict["rating"] = data["rating"] if "rating" in data else np.nan
    details_dict["review_count"] = data["reviews"] if "reviews" in data else 0
    details_dict[
        "user_favorites"] = data["lovesCount"] if "lovesCount" in data else 0

    if "parentCategory" in data:
        category_1 = data["parentCategory"][
            "displayName"] if "parentCategory" in data else "nan"
        category_2 = data["parentCategory"]["parentCategory"][
            "displayName"] if (
                "parentCategory" in data["parentCategory"]) else "nan"
        category_3 = data["parentCategory"]["parentCategory"][
            "parentCategory"]["displayName"] if (
                "parentCategory" in data["parentCategory"] and "parentCategory"
                in data["parentCategory"]["parentCategory"]) else "nan"

        category_id_1 = data["parentCategory"][
            "categoryId"] if "parentCategory" in data else "nan"
        category_id_2 = data["parentCategory"]["parentCategory"][
            "categoryId"] if "parentCategory" in data[
                "parentCategory"] else "nan"
        category_id_3 = data["parentCategory"]["parentCategory"][
            "parentCategory"]["categoryId"] if (
                "parentCategory" in data["parentCategory"] and "parentCategory"
                in data["parentCategory"]["parentCategory"]) else "nan"

        category_id = [category_id_1, category_id_2, category_id_3]
        category = [category_1, category_2, category_3]

        details_dict["categories"] = [cat.lower() for cat in category if cat != "nan"]
        details_dict["categories"] = ["her" if x=="women" else x for x in details_dict["categories"]]
        details_dict["categories"] = ["him" if x=="men" else x for x in details_dict["categories"]]
        details_dict["categories_id"] = [id_ for id_ in category_id if id_ != "nan"]

    else:
        details_dict["categories"] = np.nan
        details_dict["categories_id"] = np.nan

    details_dict["full_url"] = data["fullSiteProductUrl"]
    details_dict[
        "image_url"] = "https://www.sephora.com/productimages/sku/s" + str(
            details_dict["sku"]) + "-main-Lhero.jpg"

    details_dict["ingredients"] = tag_remover.sub(
        " ", data["currentSku"]["ingredientDesc"]).strip(
        ) if "ingredientDesc" in data["currentSku"] else np.nan

    details_dict["suggested_usage"] = tag_remover.sub(
        " ",
        data["suggestedUsage"]).strip() if "suggestedUsage" in data else np.nan

    details_dict["brand_long"] = tag_remover.sub(
        "", data["brand"]["longDescription"])

    return details_dict

def extract_stats(filename, folder_path):
    
    with open(folder_path + filename) as json_file:
        reviews_data = json.load(json_file)
    
    reviews = []
    
    product_id = filename.replace("_stats.json", "")
    
    if reviews_data["TotalResults"] == 0 or reviews_data["HasErrors"] == True:
        return reviews
        
    else:
        for key, val in reviews_data["Includes"]["Products"].items():
            product_review = {}
            product_review["product_id"] = product_id
            for key2, val2 in val.items():
                if key2 == "ReviewStatistics":
                    for key3, val3, in val["ReviewStatistics"].items():
                        product_review[key3] = val3
            reviews.append(product_review)
            if len(reviews) == 1:
                return reviews