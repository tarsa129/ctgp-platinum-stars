
const chadsoftPlayerPageLinkRegex = /^https:\/\/(?:www\.)?chadsoft\.co\.uk\/time-trials\/players\/([0-9A-Fa-f]{2}\/[0-9A-Fa-f]{14})\.html(?:#.+)?/;

let apiCallSavedPromises = new Map();

class StarData {
  constructor(bronze, silver, superSilver, gold, platinum){
    this.bronze = bronze;
    this.silver = silver;
    this.superSilver = superSilver;
    this.gold = gold;
    this.platinum = platinum;
  }

  combineData(bronze, silver, superSilver, gold, platinum){
    this.bronze |= bronze;
    this.silver |= silver;
    this.superSilver |= superSilver;
    this.gold |= gold;
    this.platinum |= platinum;
  }

  getArray(){
    return [this.bronze, this.silver, this.superSilver, this.gold, this.platinum];
  }
}

function setStarMessages(silverStarMessages)
{
  document.getElementById("star-count-message").innerText = silverStarMessages.countMessage;
  document.getElementById("star-count-table").innerHTML = silverStarMessages.tableString;
}

function createGetErrorMessage(status, statusText)
{
  let errorMessage;

  if (status === 404 || status === 0) {
    errorMessage = `Chadsoft player page does not exist!`;
  } else {
    errorMessage = `Error occurred with status code ${status}: ${statusText}.`;
  }

  return new Error(errorMessage);
}

async function requestsGetPromise(urlStr)
{
    console.log(`Starting ${urlStr} at ${performance.now()}.`);

    let savedPromise = apiCallSavedPromises.get(urlStr);
    if (savedPromise !== undefined) {
        console.log(`${urlStr}: using saved result`);
        return savedPromise;
    }

    let timeStart = performance.now();
    let promise = new Promise(function (resolve, reject) {
        let xmlHttp = new XMLHttpRequest();
        xmlHttp.open("GET", urlStr, true);
        xmlHttp.onload = function () {
            if (this.status >= 200 && this.status < 300) {
                let data = JSON.parse(xmlHttp.response);
                let timeEnd = performance.now();
                console.log(`${urlStr}: ${(timeEnd - timeStart)/1000.0}`);
                resolve(data);
            } else {
                reject(createGetErrorMessage(this.status, xmlHttp.statusText));
            }
        };
        xmlHttp.onerror = function () {
            reject(createGetErrorMessage(this.status, xmlHttp.statusText));
        };
        xmlHttp.send();
    });

    apiCallSavedPromises.set(urlStr, promise);
    return promise;
}


const listFormatter = new Intl.ListFormat("en", {style: "long", type: "conjunction"});

async function fetchPlayerPageAndCountNumStars(chadsoftPlayerPageLink) {
  const matchContents = chadsoftPlayerPageLink.match(chadsoftPlayerPageLinkRegex);
  console.log("matchContents:", matchContents);
  if (matchContents === null || matchContents.length !== 2) {
    return {
      countMessage: "Invalid chadsoft player page link!",
      tableString: ""
    }
  }

  let playerPageUrl = `https://tt.chadsoft.co.uk/players/${matchContents[1]}.json`

  let playerPageData;

  try {
    setStarMessages({
      countMessage: "Waiting for Chadsoft...",
      tableString: ""
    });
    playerPageData = await requestsGetPromise(playerPageUrl);
  } catch (e) {
    return {
      countMessage: e.message,
      tableString: ""
    }
  }

  let ghosts = playerPageData["ghosts"]
  if (ghosts === undefined || ghosts === null) {
    return {
      countMessage: "Chadsoft player page has no ghosts!",
      tableString: ""
    };
  }
  if (playerPageData["ghostCount"] !== ghosts.length) {
    document.getElementById("star-warning-message").innerText = "Warning: Not all ghosts could be downloaded from Chadsoft. This is likely because you have connected to the Chadsoft API too many times (e.g. many uses of this website, auto-tt-recorder, or viewing leaderboards on chadsoft.co.uk)";
  }

  let trackData = new Map()
  for (const trackName of trackNames){
    trackData.set(trackName, new StarData(false, false, false, false, false));
  }
  console.log(playerPageData);

  try {
    for (ghost of ghosts) {
      let stars = ghost["stars"];
      if (!stars) {
        continue;
      }

      let trackId = ghost["trackId"];
      let trackName = ghost["trackName"];

      if (!trackNames.includes(trackName)) {
        continue;
      }

      console.log(trackName);

      let hasBronzeStar = stars["bronze"];
      let hasSilverStar = stars["silver"];
      let hasSuperSilverStar = false;
      if (hasSilverStar) {
        let esgDriverVehicleId = easysgDriverVehicleIds[trackId];
        if (esgDriverVehicleId){
          console.log(esgDriverVehicleId);
          esgDriverId = esgDriverVehicleId["driverId"];
          esgVehicleId = esgDriverVehicleId["vehicleId"];
          ghostDriverId = ghost["driverId"];
          ghostVehicleId = ghost["vehicleId"];

          console.log( `${esgDriverId} ${esgVehicleId} ${ghostDriverId} ${ghostVehicleId}`);

          if (esgDriverId === ghostDriverId && esgVehicleId === ghostVehicleId) {
            hasSuperSilverStar = true;
          }
        } else {
          console.log(`No esgDriverVehicleId for ghost on ${ghost["trackName"]}: ${ghost["_links"]["item"]["href"]}, time: ${ghost["finishTimeSimple"]}, esgDriverVehicleId: ${esgDriverVehicleId}`);
        }
      }
      let hasGoldStar = stars["gold"];
      let hasPlatinumStar = false;
      if (hasGoldStar) {
        let esgDriverVehicleId = expertsgDriverVehicleIds[trackId];
        if (esgDriverVehicleId) {
          esgDriverId = esgDriverVehicleId["driverId"];
          esgVehicleId = esgDriverVehicleId["vehicleId"];
          ghostDriverId = ghost["driverId"];
          ghostVehicleId = ghost["vehicleId"];

          if (esgDriverId === ghostDriverId && esgVehicleId === ghostVehicleId) {
            hasPlatinumStar = true;
          }
        } else {
          console.log(`No esgDriverVehicleId for ghost on ${ghost["trackName"]}: ${ghost["_links"]["item"]["href"]}, time: ${ghost["finishTimeSimple"]}, esgDriverVehicleId: ${esgDriverVehicleId}`);
        }
      }


      trackData.get(trackName).combineData(hasBronzeStar, hasSilverStar, hasSuperSilverStar, hasGoldStar, hasPlatinumStar);

    }
  } catch (e) {
    return `Something went wrong, please contact the developer! Error message: ${e.message}.`;
  }

  console.log(trackData);

  let starCounts = [0, 0, 0, 0, 0];
  let tableBody = "";

  for (const [trackName, starData] of trackData) {
    tableBody += `<tr><td>${trackName}</td><td>${starData.bronze ? "x" : ""}</td><td>${starData.silver ? "x" : ""}</td><td>${starData.superSilver ? "x" : ""}</td><td>${starData.gold ? "x" : ""}</td><td>${starData.platinum ? "x" : ""}</td></tr>`
    trackStarArray = starData.getArray()
    trackStarArray.forEach( (element, index) => { if (element) {starCounts[index] += 1}} );
  }

  let tableHeader = "<tr><th>Track Name</th><th>Bronze</th><th>Silver</th><th>Super Silver</th><th>Gold</th><th>Platinum</th></tr>";
  let tableString = "<table>" + tableHeader + tableBody + "</table>"

  console.log(starCounts);

  return {
    countMessage: `You (${playerPageData['miiName']}) have ${starCounts[0]} bronze, ${starCounts[1]} silver, ${starCounts[2]} super silver, ${starCounts[3]} gold, and ${starCounts[4]} platinum stars`,
    tableString: tableString
  }
}

async function onSubmit(event) {
  event.preventDefault();
  event.stopPropagation();
  document.getElementById("star-warning-message").innerText = "";

  let chadsoftPlayerPageLink = event.target.elements["player-page"].value;
  let silverStarMessages = await fetchPlayerPageAndCountNumStars(chadsoftPlayerPageLink);
  setStarMessages(silverStarMessages);
  return false;
}
