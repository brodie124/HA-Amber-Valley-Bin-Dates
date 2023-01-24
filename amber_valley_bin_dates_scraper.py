from datetime import datetime
import aiohttp


class AmberValleyBinDatesScraper:
    def __init__(self):
        self.urlPropertiesByPostcode = "https://info.ambervalley.gov.uk/WebServices/AVBCFeeds/GazetteerJSON.asmx/PropertyLookupFeed"
        self.urlRefuseCollectionDetails = "https://info.ambervalley.gov.uk/WebServices/AVBCFeeds/WasteCollectionJSON.asmx/GetCollectionDetailsByUPRN?uprn="
        self.configPostcode = None
        self.configUprn = None

    async def query_properties_by_postcode(self, postcode=None):
        if postcode is None:
            postcode = self.configPostcode

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "srchText": postcode
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.urlPropertiesByPostcode, data=data) as response:
                if response.status != 200:
                    return False

                property_list = await response.json()
                return property_list

    async def query_refuse_dates_by_property_id(self, uprn=None):
        if uprn is None:
            uprn = self.configUprn

        async with aiohttp.ClientSession() as session:
            async with session.get(self.urlRefuseCollectionDetails + uprn) as response:
                if response.status != 200:
                    return False

                refuse_collection_info = await response.json()
                return {
                    "recycling": datetime.strptime(refuse_collection_info['recyclingNextDate'], "%Y-%m-%dT%H:%M:%S"),
                    "domestic": datetime.strptime(refuse_collection_info['refuseNextDate'], "%Y-%m-%dT%H:%M:%S"),
                    "garden": datetime.strptime(refuse_collection_info['greenNextDate'], "%Y-%m-%dT%H:%M:%S")
                }

    def get_refuse_collection_id(self, property_list, property_selector):
        matching_addresses = [x for x in property_list if
                              x['addressComma'].lower().startswith(property_selector.lower())]
        if (len(matching_addresses) < 1):
            print("No matching addresses found for the given property selector!")
            return -1
        elif (len(matching_addresses) > 1):
            print("Multiple matching addresses found! Please specify a more specific property selector!")
            print("Found %i properties: " % len(matching_addresses))
            for i in range(0, len(matching_addresses)):
                print(matching_addresses[i]['addressComma'])
            return 0

        matched_property = matching_addresses[0]
        return matched_property['uprn']

# async def main():
#     t = AmberValleyBinDatesScraper()
#     t.configUprn = "100030002069"
#     print(await t.query_refuse_dates_by_property_id())
#
# asyncio.run(main())