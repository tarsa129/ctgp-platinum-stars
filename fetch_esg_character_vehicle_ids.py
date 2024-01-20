# sourced from https://docs.google.com/spreadsheets/d/1nyAHd0mN7eVCb1RVRnMIhSQ4YPIe3O6R91yiR710SdY/edit#gid=209945353
import re
import chadsoft
import json

ghost_page_link_regex = re.compile(r"^https://(?:www\.)?chadsoft\.co\.uk/time-trials/rkgd/([0-9A-Fa-f]{2}/[0-9A-Fa-f]{2}/[0-9A-Fa-f]{36})\.html$")

def main(ghost_level):
    print(ghost_level)
    esg_driver_vehicle_ids = {}

    with open(ghost_level + "_htmls.txt", "r") as f:
        current_esg_links = f.readlines()

    track_names = []

    for esg_link in current_esg_links:
        esg_driver_vehicle_id = {}
        match_obj = ghost_page_link_regex.match(esg_link)
        if not match_obj:
            raise RuntimeError("Invalid chadsoft ghost page link!")

        ghost_id = match_obj.group(1)
        ghost_info, status_code = chadsoft.get(f"/rkgd/{ghost_id}.json")
        if status_code == 404:
            raise RuntimeError(f"Chadsoft ghost page \"{esg_link}\" doesn't exist!")

        esg_driver_vehicle_id["vehicleId"] = ghost_info["vehicleId"]
        esg_driver_vehicle_id["driverId"] = ghost_info["driverId"]
        esg_driver_vehicle_id["trackName"] = ghost_info["trackName"]
        esg_driver_vehicle_ids[ghost_info["trackId"]] = esg_driver_vehicle_id

        track_names.append( ghost_info["trackName"] )

        with open("temp_" + ghost_level + ".txt", "a+") as f:
            f.write(json.dumps(esg_driver_vehicle_ids))

    esg_driver_vehicle_ids_js = f"const {ghost_level}sgDriverVehicleIds = {json.dumps(esg_driver_vehicle_ids, indent=2)};"

    with open(ghost_level + "-driver-vehicle-ids.js", "w+") as f:
        f.write(esg_driver_vehicle_ids_js)

    if ghost_level == "easy":
        track_names_js = f"const trackNames = {json.dumps(track_names)};"
        with open("track-names.js", "w+") as f:
            f.write(track_names_js)

if __name__ == "__main__":
    for ghost_level in ("easy", "expert"):
        main(ghost_level)
