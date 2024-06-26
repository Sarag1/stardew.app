# Purpose: Find all items that count for Full Shipment achievement.
#          Logic is ported from the game's source code.
# Source Code References:
# ------------------------- Full Shipment Achievement ------------------------ #
# - StardewValley/Utility.cs::hasFarmerShippedAllItems()
#   -> StardewValley/Utility.cs::getFarmerItemsShippedPercent()
#       -> StardewValley/Object.cs::isPotentialBasicShipped()
#
# We'll try and mimic this logic to get a list of all items that count for achievement.
# ------------------------ Crop Shipping Achievements ------------------------ #
# - StardewValley/Stats.cs::checkForShippingAchievements()
#
# 1.6 Update simplified the logic for monoculture and polyculture achievements.
# now, the Object information contains boolean flags for monoculture and polyculture.
#
# Content Files used: Crops.json, Objects.json
# Wiki Pages used: None

from tqdm import tqdm

from helpers.utils import load_content, save_json, isPotentialBasicShipped, load_data
from helpers.models import ShippingItem, ContentCropItem, ContentObjectModel, Object

# Load the content files
CROPS: dict[str, ContentCropItem] = load_content("Crops.json")
OBJECTS: dict[str, ContentObjectModel] = load_content("Objects.json")
DATA_OBJECTS: dict[str, Object] = load_data("objects.json")


# The key for CROPS is the seed item ID, so we need a map of crop item ID to seed item ID
# to lookup the crop information.
def build_crop_id_map() -> dict[str, str]:
    output: dict[str, str] = {}

    for k, v in CROPS.items():
        output[v["HarvestItemId"]] = k

    return output


def get_shipping_items() -> dict[str, ShippingItem]:
    output: dict[str, ShippingItem] = {}

    crop_to_seed_id = build_crop_id_map()

    # StardewValley/Utility.cs::getFarmerItemsShippedPercent()
    for k, v in tqdm(OBJECTS.items()):
        category = v.get("Category")

        if (
            category != -7
            and category != -2
            and (
                isPotentialBasicShipped(k, category, v.get("Type"), OBJECTS)
                or k == "372"
            )
            and k != "SmokedFish"
        ):

            # lookup the seed item ID in CROPS content file, using the harvest item id
            seed_id = crop_to_seed_id.get(k)
            # if the seed id exists, use it, otherwise use the item id
            item_id = seed_id if seed_id else k

            output[k] = {
                "itemID": k,
                "minVersion": DATA_OBJECTS[k].get("minVersion"),
                "monoculture": CROPS.get(item_id, {}).get("CountForMonoculture", False),
                "polyculture": CROPS.get(item_id, {}).get("CountForPolyculture", False),
                "seasons": CROPS.get(item_id, {}).get("Seasons", []),
            }

    return output


if __name__ == "__main__":
    shipping = get_shipping_items()

    # https://stardewvalleywiki.com/Shipping reference for counts
    # also you can CTRL+F "CountForPolyculture": true and "CountForMonoculture": true in Crops.json
    # 28 items count for polyculture
    assert len([c for c in shipping.values() if c["polyculture"]]) == 28
    # 33 items count for monoculture
    assert len([c for c in shipping.values() if c["monoculture"]]) == 33
    # # 155 total items count for Full Shipment
    print("Total Items counted for Full Shipment: ", len(shipping))
    assert len(shipping) == 154  # 145 as of 1.5, 1.6 added 10 new items

    save_json(shipping, "shipping.json", sort=True)
