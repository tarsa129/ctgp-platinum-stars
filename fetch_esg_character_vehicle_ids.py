# sourced from https://docs.google.com/spreadsheets/d/1nyAHd0mN7eVCb1RVRnMIhSQ4YPIe3O6R91yiR710SdY/edit#gid=209945353
import re
import chadsoft
import json

ghost_page_link_regex = re.compile(r"^https://(?:www\.)?chadsoft\.co\.uk/time-trials/rkgd/([0-9A-Fa-f]{2}/[0-9A-Fa-f]{2}/[0-9A-Fa-f]{36})\.html$")

def main():
    esg_driver_vehicle_ids = {}

    with open("current_esg_links.json", "r") as f:
        current_esg_links = json.load(f)

    for esg_link in current_esg_links:
        esg_driver_vehicle_id = {}
        match_obj = ghost_page_link_regex.match(esg_link)
        if not match_obj:
            raise RuntimeError("Invalid chadsoft ghost page link!")

        ghost_id = match_obj.group(1)
        ghost_info, status_code = chadsoft.get(f"/rkgd/{ghost_id}.json")
        if status_code == 404:
            raise RuntimeError(f"Chadsoft ghost page \"{ghost_page_link}\" doesn't exist!")

        esg_driver_vehicle_id["vehicleId"] = ghost_info["vehicleId"]
        esg_driver_vehicle_id["driverId"] = ghost_info["driverId"]
        esg_driver_vehicle_ids[ghost_info["trackId"]] = esg_driver_vehicle_id

    esg_driver_vehicle_ids_js = f"const esgDriverVehicleIds = {json.dumps(esg_driver_vehicle_ids, indent=2)};"

    with open("esg-driver-vehicle-ids.js", "w+") as f:
        f.write(esg_driver_vehicle_ids_js)

if __name__ == "__main__":
    main()
