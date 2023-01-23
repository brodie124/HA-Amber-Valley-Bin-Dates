import urllib.parse
import urllib3
import json
class AmberValleyBinDatesScraper:
    def __init__(self):
        self.http = urllib3.PoolManager()
        self.urlPropertiesByPostcode = "https://info.ambervalley.gov.uk/WebServices/AVBCFeeds/GazetteerJSON.asmx/PropertyLookupFeed"
        self.urlRefuseCollectionDetails = "https://info.ambervalley.gov.uk/WebServices/AVBCFeeds/WasteCollectionJSON.asmx/GetCollectionDetailsByUPRN?uprn="

    def query_properties_by_postcode(self, postcode):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = urllib.parse.urlencode({
            "srchText": postcode
        })

        result = self.http.request('POST', self.urlPropertiesByPostcode, body=data, headers=headers)
        if result.status != 200:
            return False

        property_list = json.loads(result.data.decode('utf-8'))
        return property_list

    def query_refuse_dates_by_property_id(self, uprn):
        result = self.http.request('GET', self.urlRefuseCollectionDetails + uprn)
        if result.status != 200:
            return False

        refuse_collection_info = json.loads(result.data.decode('utf-8'))
        return {
            "recycling": refuse_collection_info['recyclingNextDate'],
            "domestic": refuse_collection_info['refuseNextDate'],
            "garden": refuse_collection_info['greenNextDate']
        }

    def get_refuse_collection_id(self, property_list, property_selector):
        matching_addresses = [x for x in property_list if x['addressComma'].lower().startswith(property_selector.lower())]
        if(len(matching_addresses) < 1):
            print("No matching addresses found for the given property selector!")
            return -1
        elif(len(matching_addresses) > 1):
            print("Multiple matching addresses found! Please specify a more specific property selector!")
            print("Found %i properties: " % len(matching_addresses))
            for i in range(0, len(matching_addresses)):
                print(matching_addresses[i]['addressComma'])
            return 0

        matched_property = matching_addresses[0]
        return matched_property['uprn']



test = AmberValleyBinDatesScraper()
property_list = test.query_properties_by_postcode("DE55 4LN")
property_id = test.get_refuse_collection_id(property_list, "4 Castle Drive")
refuse_dates = test.query_refuse_dates_by_property_id(property_id)

print(refuse_dates)